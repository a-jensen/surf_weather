"""Tests for the CUWCD lake data provider."""
from datetime import datetime

import httpx
import pytest
import respx

from surf_weather.models.lake import LakeConditions, LakeConfig
from surf_weather.providers.lake_data.cuwcd import CUWCD_API_URL, CUWCDProvider


@pytest.fixture
def deer_creek() -> LakeConfig:
    return LakeConfig(
        id="deer_creek",
        name="Deer Creek Reservoir",
        state="UT",
        latitude=40.4083,
        longitude=-111.5297,
        usgs_site_id=None,
        data_provider="cuwcd",
        cuwcd_set_name="public_dc",
    )


@pytest.fixture
def lake_no_set_name() -> LakeConfig:
    return LakeConfig(
        id="unknown",
        name="Unknown Lake",
        state="UT",
        latitude=40.0,
        longitude=-111.0,
        usgs_site_id=None,
        data_provider="cuwcd",
        cuwcd_set_name=None,
    )


class TestCUWCDProvider:
    @pytest.fixture(autouse=True)
    def provider(self):
        self.provider = CUWCDProvider()

    def test_provider_name(self):
        assert self.provider.provider_name == "cuwcd"

    def test_supports_cuwcd_lake(self, deer_creek):
        assert self.provider.supports_lake(deer_creek) is True

    def test_does_not_support_usgs_lake(self, fake_lake_with_gauge):
        assert self.provider.supports_lake(fake_lake_with_gauge) is False

    @respx.mock
    def test_get_conditions_returns_lake_conditions(
        self, deer_creek, cuwcd_current_fixture, cuwcd_trend_fixture
    ):
        respx.get(f"{CUWCD_API_URL}/public_dc").mock(return_value=httpx.Response(200, json=cuwcd_current_fixture))
        respx.get(f"{CUWCD_API_URL}/public_dc_trend").mock(return_value=httpx.Response(200, json=cuwcd_trend_fixture))

        result = self.provider.get_conditions(deer_creek)

        assert isinstance(result, LakeConditions)
        assert result.lake_id == "deer_creek"

    @respx.mock
    def test_parses_elevation(self, deer_creek, cuwcd_current_fixture, cuwcd_trend_fixture):
        respx.get(f"{CUWCD_API_URL}/public_dc").mock(return_value=httpx.Response(200, json=cuwcd_current_fixture))
        respx.get(f"{CUWCD_API_URL}/public_dc_trend").mock(return_value=httpx.Response(200, json=cuwcd_trend_fixture))

        result = self.provider.get_conditions(deer_creek)

        assert result.water_level_ft == pytest.approx(5410.5, abs=0.01)

    @respx.mock
    def test_parses_pct_full(self, deer_creek, cuwcd_current_fixture, cuwcd_trend_fixture):
        respx.get(f"{CUWCD_API_URL}/public_dc").mock(return_value=httpx.Response(200, json=cuwcd_current_fixture))
        respx.get(f"{CUWCD_API_URL}/public_dc_trend").mock(return_value=httpx.Response(200, json=cuwcd_trend_fixture))

        result = self.provider.get_conditions(deer_creek)

        assert result.water_level_pct == pytest.approx(89.05, abs=0.01)

    @respx.mock
    def test_no_temperature(self, deer_creek, cuwcd_current_fixture, cuwcd_trend_fixture):
        respx.get(f"{CUWCD_API_URL}/public_dc").mock(return_value=httpx.Response(200, json=cuwcd_current_fixture))
        respx.get(f"{CUWCD_API_URL}/public_dc_trend").mock(return_value=httpx.Response(200, json=cuwcd_trend_fixture))

        result = self.provider.get_conditions(deer_creek)

        assert result.water_temp_c is None

    @respx.mock
    def test_parses_elevation_history(self, deer_creek, cuwcd_current_fixture, cuwcd_trend_fixture):
        respx.get(f"{CUWCD_API_URL}/public_dc").mock(return_value=httpx.Response(200, json=cuwcd_current_fixture))
        respx.get(f"{CUWCD_API_URL}/public_dc_trend").mock(return_value=httpx.Response(200, json=cuwcd_trend_fixture))

        result = self.provider.get_conditions(deer_creek)

        # Trend fixture has 3 elevation entries
        assert len(result.water_level_history) == 3
        assert result.water_level_history[0].value == pytest.approx(5405.0)
        assert result.water_level_history[-1].value == pytest.approx(5410.5)

    @respx.mock
    def test_data_as_of_is_set(self, deer_creek, cuwcd_current_fixture, cuwcd_trend_fixture):
        respx.get(f"{CUWCD_API_URL}/public_dc").mock(return_value=httpx.Response(200, json=cuwcd_current_fixture))
        respx.get(f"{CUWCD_API_URL}/public_dc_trend").mock(return_value=httpx.Response(200, json=cuwcd_trend_fixture))

        result = self.provider.get_conditions(deer_creek)

        assert isinstance(result.data_as_of, datetime)

    @respx.mock
    def test_raises_on_http_error(self, deer_creek):
        respx.get(f"{CUWCD_API_URL}/public_dc").mock(return_value=httpx.Response(503))

        with pytest.raises(httpx.HTTPStatusError):
            self.provider.get_conditions(deer_creek)

    def test_null_set_name_returns_empty_conditions(self, lake_no_set_name):
        result = self.provider.get_conditions(lake_no_set_name)

        assert result.water_level_ft is None
        assert result.water_temp_c is None
        assert result.water_level_history == []
