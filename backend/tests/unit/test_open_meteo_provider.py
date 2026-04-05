"""Tests for the Open-Meteo weather provider."""
from datetime import date

import pytest
import respx
import httpx

from surf_weather.providers.weather.open_meteo import OpenMeteoProvider, BASE_URL
from surf_weather.models.weather import WeatherForecast


class TestOpenMeteoProvider:
    @pytest.fixture(autouse=True)
    def provider(self):
        self.provider = OpenMeteoProvider()

    def test_provider_name(self):
        assert self.provider.provider_name == "open_meteo"

    @respx.mock
    def test_get_forecast_returns_weather_forecast(self, fake_lake_with_gauge, open_meteo_fixture):
        respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=open_meteo_fixture))

        result = self.provider.get_forecast(fake_lake_with_gauge)

        assert isinstance(result, WeatherForecast)
        assert result.lake_id == fake_lake_with_gauge.id
        assert result.timezone == "America/Denver"

    @respx.mock
    def test_returns_7_daily_forecasts(self, fake_lake_with_gauge, open_meteo_fixture):
        respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=open_meteo_fixture))

        result = self.provider.get_forecast(fake_lake_with_gauge)

        assert len(result.daily) == 7

    @respx.mock
    def test_daily_forecast_has_correct_temps(self, fake_lake_with_gauge, open_meteo_fixture):
        respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=open_meteo_fixture))

        result = self.provider.get_forecast(fake_lake_with_gauge)
        first_day = result.daily[0]

        assert first_day.temp_high_f == 85.0
        assert first_day.temp_low_f == 60.0

    @respx.mock
    def test_daily_forecast_has_correct_wind(self, fake_lake_with_gauge, open_meteo_fixture):
        respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=open_meteo_fixture))

        result = self.provider.get_forecast(fake_lake_with_gauge)
        first_day = result.daily[0]

        assert first_day.wind_speed_mph == 8.5
        assert first_day.wind_direction_deg == 225.0

    @respx.mock
    def test_daily_forecast_has_precip_probability(self, fake_lake_with_gauge, open_meteo_fixture):
        respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=open_meteo_fixture))

        result = self.provider.get_forecast(fake_lake_with_gauge)

        assert result.daily[0].precip_probability_pct == 10.0

    @respx.mock
    def test_detects_thunderstorm_by_weather_code(self, fake_lake_with_gauge, open_meteo_fixture):
        """Day index 4 has weather_code=95 (thunderstorm)."""
        respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=open_meteo_fixture))

        result = self.provider.get_forecast(fake_lake_with_gauge)

        assert result.daily[4].has_thunderstorm_risk is True
        assert result.daily[4].weather_code == 95

    @respx.mock
    def test_detects_lightning_risk_by_cape(self, fake_lake_with_gauge, open_meteo_fixture):
        """Day index 4 also has CAPE=800 J/kg > threshold."""
        respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=open_meteo_fixture))

        result = self.provider.get_forecast(fake_lake_with_gauge)

        assert result.daily[4].cape_max_jkg == 800.0

    @respx.mock
    def test_no_thunderstorm_risk_on_clear_day(self, fake_lake_with_gauge, open_meteo_fixture):
        """Day index 0 has weather_code=1, CAPE=0."""
        respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=open_meteo_fixture))

        result = self.provider.get_forecast(fake_lake_with_gauge)

        assert result.daily[0].has_thunderstorm_risk is False

    @respx.mock
    def test_date_parsed_correctly(self, fake_lake_with_gauge, open_meteo_fixture):
        respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=open_meteo_fixture))

        result = self.provider.get_forecast(fake_lake_with_gauge)

        assert result.daily[0].date == date(2024, 6, 1)
        assert result.daily[6].date == date(2024, 6, 7)

    @respx.mock
    def test_hourly_forecasts_returned(self, fake_lake_with_gauge, open_meteo_fixture):
        respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=open_meteo_fixture))

        result = self.provider.get_forecast(fake_lake_with_gauge)

        assert len(result.hourly) == 3  # fixture has 3 hourly entries
        assert result.hourly[0].temp_f == 65.0

    @respx.mock
    def test_fetched_at_is_set(self, fake_lake_with_gauge, open_meteo_fixture):
        respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=open_meteo_fixture))

        result = self.provider.get_forecast(fake_lake_with_gauge)

        assert result.fetched_at  # non-empty string

    @respx.mock
    def test_raises_on_http_error(self, fake_lake_with_gauge):
        respx.get(BASE_URL).mock(return_value=httpx.Response(500))

        with pytest.raises(httpx.HTTPStatusError):
            self.provider.get_forecast(fake_lake_with_gauge)

    @respx.mock
    def test_cape_above_threshold_sets_risk_even_without_thunderstorm_code(
        self, fake_lake_with_gauge, open_meteo_fixture
    ):
        """High hourly CAPE on day 0 triggers risk even with non-thunderstorm weather code."""
        import copy
        fixture = copy.deepcopy(open_meteo_fixture)
        # Override all daily weather codes to non-thunderstorm
        fixture["daily"]["weather_code"] = [1] * 7
        # Add an hourly entry on day 0 with CAPE above threshold
        fixture["hourly"]["time"].insert(0, "2024-06-01T06:00")
        fixture["hourly"]["temperature_2m"].insert(0, 70.0)
        fixture["hourly"]["wind_speed_10m"].insert(0, 5.0)
        fixture["hourly"]["wind_direction_10m"].insert(0, 180.0)
        fixture["hourly"]["precipitation_probability"].insert(0, 0)
        fixture["hourly"]["weather_code"].insert(0, 1)
        fixture["hourly"]["cape"].insert(0, 600.0)  # > 500 J/kg threshold

        respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=fixture))

        result = self.provider.get_forecast(fake_lake_with_gauge)

        assert result.daily[0].has_thunderstorm_risk is True
