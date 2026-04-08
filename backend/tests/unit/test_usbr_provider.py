"""Tests for the USBR HydroData lake data provider."""
from datetime import datetime, timezone

import httpx
import pytest
import respx

from surf_weather.models.lake import LakeConditions, LakeConfig
from surf_weather.providers.lake_data.usbr import USBR_HYDRODATA_URL, USBRProvider

WILLARD_BAY_URL = USBR_HYDRODATA_URL.format(site_id=925)


@pytest.fixture
def willard_bay() -> LakeConfig:
    return LakeConfig(
        id="willard_bay",
        name="Willard Bay",
        state="UT",
        latitude=41.3897,
        longitude=-112.0997,
        usgs_site_id=None,
        conditions_provider="state_parks",
        history_provider="usbr",
        usbr_site_id=925,
    )


@pytest.fixture
def lake_no_usbr_id() -> LakeConfig:
    return LakeConfig(
        id="unknown",
        name="Unknown Lake",
        state="UT",
        latitude=41.0,
        longitude=-112.0,
        usgs_site_id=None,
        conditions_provider="state_parks",
    )


def _make_payload(rows: list[list]) -> dict:
    """Build a minimal USBR HydroData JSON payload."""
    return {"columns": ["datetime", "pool elevation"], "data": rows}


class TestUSBRProvider:
    @pytest.fixture(autouse=True)
    def provider(self):
        self.provider = USBRProvider()

    def test_provider_name(self):
        assert self.provider.provider_name == "usbr"

    def test_supports_usbr_conditions_lake(self):
        lake = LakeConfig(
            id="x", name="X", state="UT", latitude=0, longitude=0,
            usgs_site_id=None, conditions_provider="usbr", usbr_site_id=925,
        )
        assert self.provider.supports_lake(lake) is True

    def test_does_not_support_state_parks_lake(self, willard_bay):
        assert self.provider.supports_lake(willard_bay) is False

    def test_null_site_id_returns_empty_conditions(self, lake_no_usbr_id):
        result = self.provider.get_conditions(lake_no_usbr_id)
        assert result.water_level_ft is None
        assert result.water_level_history == []
        assert result.data_as_of is None

    @respx.mock
    def test_returns_lake_conditions_instance(self, willard_bay):
        payload = _make_payload([
            ["2026-04-06", 4217.0],
            ["2026-04-07", 4217.1],
        ])
        respx.get(WILLARD_BAY_URL).mock(return_value=httpx.Response(200, json=payload))

        result = self.provider.get_conditions(willard_bay)

        assert isinstance(result, LakeConditions)
        assert result.lake_id == "willard_bay"

    @respx.mock
    def test_current_level_is_last_non_null_entry(self, willard_bay):
        payload = _make_payload([
            ["2026-04-06", 4217.0],
            ["2026-04-07", 4217.13],
        ])
        respx.get(WILLARD_BAY_URL).mock(return_value=httpx.Response(200, json=payload))

        result = self.provider.get_conditions(willard_bay)

        assert result.water_level_ft == pytest.approx(4217.13)

    @respx.mock
    def test_skips_null_values(self, willard_bay):
        payload = _make_payload([
            ["2026-04-05", 4216.9],
            ["2026-04-06", None],
            ["2026-04-07", 4217.13],
        ])
        respx.get(WILLARD_BAY_URL).mock(return_value=httpx.Response(200, json=payload))

        result = self.provider.get_conditions(willard_bay)

        assert len(result.water_level_history) == 2
        assert result.water_level_ft == pytest.approx(4217.13)

    @respx.mock
    def test_history_only_includes_last_90_days(self, willard_bay):
        """Rows older than 90 days should be filtered out."""
        payload = _make_payload([
            ["2020-01-01", 4200.0],   # old — excluded
            ["2026-04-06", 4217.0],   # recent — included
            ["2026-04-07", 4217.13],  # recent — included
        ])
        respx.get(WILLARD_BAY_URL).mock(return_value=httpx.Response(200, json=payload))

        result = self.provider.get_conditions(willard_bay)

        assert len(result.water_level_history) == 2

    @respx.mock
    def test_history_is_chronological(self, willard_bay):
        payload = _make_payload([
            ["2026-04-05", 4216.9],
            ["2026-04-06", 4217.0],
            ["2026-04-07", 4217.13],
        ])
        respx.get(WILLARD_BAY_URL).mock(return_value=httpx.Response(200, json=payload))

        result = self.provider.get_conditions(willard_bay)

        timestamps = [p.timestamp for p in result.water_level_history]
        assert timestamps == sorted(timestamps)

    @respx.mock
    def test_history_timestamps_are_utc(self, willard_bay):
        payload = _make_payload([["2026-04-07", 4217.13]])
        respx.get(WILLARD_BAY_URL).mock(return_value=httpx.Response(200, json=payload))

        result = self.provider.get_conditions(willard_bay)

        assert result.water_level_history[0].timestamp.tzinfo == timezone.utc

    @respx.mock
    def test_data_as_of_matches_last_history_point(self, willard_bay):
        payload = _make_payload([
            ["2026-04-06", 4217.0],
            ["2026-04-07", 4217.13],
        ])
        respx.get(WILLARD_BAY_URL).mock(return_value=httpx.Response(200, json=payload))

        result = self.provider.get_conditions(willard_bay)

        assert result.data_as_of == datetime(2026, 4, 7, tzinfo=timezone.utc)

    @respx.mock
    def test_water_temp_is_none(self, willard_bay):
        payload = _make_payload([["2026-04-07", 4217.13]])
        respx.get(WILLARD_BAY_URL).mock(return_value=httpx.Response(200, json=payload))

        result = self.provider.get_conditions(willard_bay)

        assert result.water_temp_c is None
        assert result.water_temp_history == []

    @respx.mock
    def test_provider_name_in_result(self, willard_bay):
        payload = _make_payload([["2026-04-07", 4217.13]])
        respx.get(WILLARD_BAY_URL).mock(return_value=httpx.Response(200, json=payload))

        result = self.provider.get_conditions(willard_bay)

        assert result.provider_name == "usbr"

    @respx.mock
    def test_empty_data_returns_null_level(self, willard_bay):
        payload = _make_payload([])
        respx.get(WILLARD_BAY_URL).mock(return_value=httpx.Response(200, json=payload))

        result = self.provider.get_conditions(willard_bay)

        assert result.water_level_ft is None
        assert result.water_level_history == []
        assert result.data_as_of is None

    @respx.mock
    def test_raises_on_http_error(self, willard_bay):
        respx.get(WILLARD_BAY_URL).mock(return_value=httpx.Response(503))

        with pytest.raises(httpx.HTTPStatusError):
            self.provider.get_conditions(willard_bay)
