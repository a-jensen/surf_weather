"""Tests for the Utah State Parks lake data provider."""
import httpx
import pytest
import respx

from surf_weather.models.lake import LakeConditions, LakeConfig
from surf_weather.providers.lake_data.state_parks import STATE_PARKS_BASE, StateParksProvider


@pytest.fixture
def east_canyon() -> LakeConfig:
    return LakeConfig(
        id="east_canyon",
        name="East Canyon Reservoir",
        state="UT",
        latitude=40.9306,
        longitude=-111.6014,
        usgs_site_id=None,
        data_provider="state_parks",
        state_park_slug="east-canyon",
    )


@pytest.fixture
def lake_no_slug() -> LakeConfig:
    return LakeConfig(
        id="unknown",
        name="Unknown Lake",
        state="UT",
        latitude=40.0,
        longitude=-111.0,
        usgs_site_id=None,
        data_provider="state_parks",
        state_park_slug=None,
    )


EAST_CANYON_URL = f"{STATE_PARKS_BASE}/east-canyon/current-conditions/"


class TestStateParksProvider:
    @pytest.fixture(autouse=True)
    def provider(self):
        self.provider = StateParksProvider()

    def test_provider_name(self):
        assert self.provider.provider_name == "ut_state_parks"

    def test_supports_state_parks_lake(self, east_canyon):
        assert self.provider.supports_lake(east_canyon) is True

    def test_does_not_support_usgs_lake(self, fake_lake_with_gauge):
        assert self.provider.supports_lake(fake_lake_with_gauge) is False

    @respx.mock
    def test_returns_lake_conditions(self, east_canyon, state_parks_html):
        respx.get(EAST_CANYON_URL).mock(return_value=httpx.Response(200, text=state_parks_html))

        result = self.provider.get_conditions(east_canyon)

        assert isinstance(result, LakeConditions)
        assert result.lake_id == "east_canyon"

    @respx.mock
    def test_parses_temperature_f_to_c(self, east_canyon, state_parks_html):
        """52°F should convert to ≈11.11°C."""
        respx.get(EAST_CANYON_URL).mock(return_value=httpx.Response(200, text=state_parks_html))

        result = self.provider.get_conditions(east_canyon)

        assert result.water_temp_c == pytest.approx(11.11, abs=0.01)

    @respx.mock
    def test_parses_level_pct(self, east_canyon, state_parks_html):
        respx.get(EAST_CANYON_URL).mock(return_value=httpx.Response(200, text=state_parks_html))

        result = self.provider.get_conditions(east_canyon)

        assert result.water_level_pct == pytest.approx(77.0)

    @respx.mock
    def test_water_level_ft_is_none(self, east_canyon, state_parks_html):
        """State parks only provides %; ft should be None."""
        respx.get(EAST_CANYON_URL).mock(return_value=httpx.Response(200, text=state_parks_html))

        result = self.provider.get_conditions(east_canyon)

        assert result.water_level_ft is None

    @respx.mock
    def test_missing_temp_returns_none(self, east_canyon):
        html = '<html><body><div class="waterconditionResults"><div class="feeditem waterlevel"><span>Water Level:</span>65%</div></div></body></html>'
        respx.get(EAST_CANYON_URL).mock(return_value=httpx.Response(200, text=html))

        result = self.provider.get_conditions(east_canyon)

        assert result.water_temp_c is None
        assert result.water_level_pct == pytest.approx(65.0)

    @respx.mock
    def test_missing_level_returns_none(self, east_canyon):
        html = '<html><body><div class="waterconditionResults"><div class="feeditem watertemp"><span>Water Temp:</span>60&deg; F</div></div></body></html>'
        respx.get(EAST_CANYON_URL).mock(return_value=httpx.Response(200, text=html))

        result = self.provider.get_conditions(east_canyon)

        assert result.water_level_pct is None
        assert result.water_temp_c == pytest.approx(15.56, abs=0.01)

    @respx.mock
    def test_raises_on_http_error(self, east_canyon):
        respx.get(EAST_CANYON_URL).mock(return_value=httpx.Response(404))

        with pytest.raises(httpx.HTTPStatusError):
            self.provider.get_conditions(east_canyon)

    def test_null_slug_returns_empty_conditions(self, lake_no_slug):
        result = self.provider.get_conditions(lake_no_slug)

        assert result.water_temp_c is None
        assert result.water_level_ft is None
        assert result.water_level_pct is None
