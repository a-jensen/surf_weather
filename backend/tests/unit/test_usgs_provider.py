"""Tests for the USGS NWIS lake data provider."""
from datetime import datetime

import httpx
import pytest
import respx

from surf_weather.models.lake import LakeConditions
from surf_weather.providers.lake_data.usgs import (
    PARAM_GAGE_HEIGHT,
    PARAM_WATER_TEMP,
    USGS_DV_URL,
    USGSProvider,
)


def mock_usgs(level_fixture: dict, temp_fixture: dict):
    """Return a respx mock that routes by parameter_code query param."""
    return respx.mock(
        assert_all_called=False,
    )


def setup_param_mocks(level_fixture: dict, temp_fixture: dict) -> None:
    """Register per-parameter mocks on the current respx.mock context."""
    respx.get(USGS_DV_URL, params__contains={"parameter_code": PARAM_GAGE_HEIGHT}).mock(
        return_value=httpx.Response(200, json=level_fixture)
    )
    respx.get(USGS_DV_URL, params__contains={"parameter_code": PARAM_WATER_TEMP}).mock(
        return_value=httpx.Response(200, json=temp_fixture)
    )


class TestUSGSProvider:
    @pytest.fixture(autouse=True)
    def provider(self):
        self.provider = USGSProvider()

    def test_provider_name(self):
        assert self.provider.provider_name == "usgs_nwis"

    def test_supports_lake_with_site_id(self, fake_lake_with_gauge):
        assert self.provider.supports_lake(fake_lake_with_gauge) is True

    def test_supports_lake_without_site_id(self, fake_lake_no_gauge):
        assert self.provider.supports_lake(fake_lake_no_gauge) is True

    @respx.mock
    def test_get_conditions_returns_lake_conditions(
        self, fake_lake_with_gauge, usgs_dv_fixture, usgs_temp_fixture
    ):
        setup_param_mocks(usgs_dv_fixture, usgs_temp_fixture)

        result = self.provider.get_conditions(fake_lake_with_gauge)

        assert isinstance(result, LakeConditions)
        assert result.lake_id == fake_lake_with_gauge.id

    @respx.mock
    def test_parses_water_level_from_dv(
        self, fake_lake_with_gauge, usgs_dv_fixture, usgs_temp_fixture
    ):
        """Current water level is the most recent valid DV entry."""
        setup_param_mocks(usgs_dv_fixture, usgs_temp_fixture)

        result = self.provider.get_conditions(fake_lake_with_gauge)

        # Fixture last valid level is 4712.30
        assert result.water_level_ft == pytest.approx(4712.30, abs=0.01)

    @respx.mock
    def test_parses_water_temp_from_dv(
        self, fake_lake_with_gauge, usgs_dv_fixture, usgs_temp_fixture
    ):
        """Current water temp is the most recent valid DV entry."""
        setup_param_mocks(usgs_dv_fixture, usgs_temp_fixture)

        result = self.provider.get_conditions(fake_lake_with_gauge)

        # Fixture last valid temp is 18.5
        assert result.water_temp_c == pytest.approx(18.5, abs=0.01)

    @respx.mock
    def test_parses_history_and_skips_invalid_values(
        self, fake_lake_with_gauge, usgs_dv_fixture, usgs_temp_fixture
    ):
        """The fixtures have -999999 and '' values that should be skipped."""
        setup_param_mocks(usgs_dv_fixture, usgs_temp_fixture)

        result = self.provider.get_conditions(fake_lake_with_gauge)

        # 4 entries, 1 invalid (-999999) → 3 valid
        assert len(result.water_level_history) == 3
        # 4 entries, 1 invalid ('') → 3 valid
        assert len(result.water_temp_history) == 3

    @respx.mock
    def test_history_values_are_correct(
        self, fake_lake_with_gauge, usgs_dv_fixture, usgs_temp_fixture
    ):
        setup_param_mocks(usgs_dv_fixture, usgs_temp_fixture)

        result = self.provider.get_conditions(fake_lake_with_gauge)

        assert result.water_level_history[0].value == 4710.0
        assert result.water_level_history[1].value == 4711.0
        assert result.water_level_history[2].value == 4712.30

    @respx.mock
    def test_data_as_of_is_set(self, fake_lake_with_gauge, usgs_dv_fixture, usgs_temp_fixture):
        setup_param_mocks(usgs_dv_fixture, usgs_temp_fixture)

        result = self.provider.get_conditions(fake_lake_with_gauge)

        assert isinstance(result.data_as_of, datetime)

    @respx.mock
    def test_provider_name_in_result(self, fake_lake_with_gauge, usgs_dv_fixture, usgs_temp_fixture):
        setup_param_mocks(usgs_dv_fixture, usgs_temp_fixture)

        result = self.provider.get_conditions(fake_lake_with_gauge)

        assert result.provider_name == "usgs_nwis"

    @respx.mock
    def test_handles_missing_temp_gracefully(self, fake_lake_with_gauge, usgs_dv_fixture):
        """When temp request returns no features, water_temp_c should be None."""
        setup_param_mocks(usgs_dv_fixture, {"type": "FeatureCollection", "features": [], "numberReturned": 0})

        result = self.provider.get_conditions(fake_lake_with_gauge)

        assert result.water_temp_c is None
        assert result.water_level_ft == pytest.approx(4712.30, abs=0.01)

    @respx.mock
    def test_raises_on_http_error(self, fake_lake_with_gauge):
        respx.get(USGS_DV_URL).mock(return_value=httpx.Response(503))

        with pytest.raises(httpx.HTTPStatusError):
            self.provider.get_conditions(fake_lake_with_gauge)


class TestUSGSProviderNullSite:
    """Provider returns empty conditions when lake has no site ID."""

    @pytest.fixture(autouse=True)
    def provider(self):
        self.provider = USGSProvider()

    def test_get_conditions_for_no_gauge_lake(self, fake_lake_no_gauge):
        result = self.provider.get_conditions(fake_lake_no_gauge)
        assert result.water_level_ft is None
        assert result.water_temp_c is None
        assert result.water_level_history == []
        assert result.water_temp_history == []
        assert result.data_as_of is None
