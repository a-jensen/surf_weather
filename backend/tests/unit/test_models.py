"""Tests for domain models — written before implementation (TDD)."""
from datetime import date, datetime, timezone

import pytest

from surf_weather.models.lake import HistoricalPoint, LakeConditions, LakeConfig
from surf_weather.models.weather import DailyForecast, HourlyForecast, WeatherForecast
from surf_weather.models.combined import LakeDetail, LakeSummary


# ---------------------------------------------------------------------------
# LakeConfig
# ---------------------------------------------------------------------------

class TestLakeConfig:
    def test_creates_with_usgs_site(self):
        lake = LakeConfig(
            id="deer_creek",
            name="Deer Creek Reservoir",
            state="UT",
            latitude=40.4083,
            longitude=-111.5297,
            usgs_site_id="10159000",
            conditions_provider="usgs",
        )
        assert lake.id == "deer_creek"
        assert lake.usgs_site_id == "10159000"

    def test_creates_without_usgs_site(self):
        lake = LakeConfig(
            id="jordanelle",
            name="Jordanelle Reservoir",
            state="UT",
            latitude=40.6097,
            longitude=-111.4203,
            usgs_site_id=None,
            conditions_provider="usgs",
        )
        assert lake.usgs_site_id is None

    def test_is_immutable(self):
        lake = LakeConfig(
            id="deer_creek",
            name="Deer Creek",
            state="UT",
            latitude=40.0,
            longitude=-111.0,
            usgs_site_id="10159000",
            conditions_provider="usgs",
        )
        with pytest.raises(Exception):
            lake.id = "other"  # type: ignore[misc]

    def test_has_lat_lon(self):
        lake = LakeConfig(
            id="x", name="X", state="UT",
            latitude=41.0, longitude=-112.0,
            usgs_site_id=None, conditions_provider="usgs",
        )
        assert lake.latitude == 41.0
        assert lake.longitude == -112.0


# ---------------------------------------------------------------------------
# HistoricalPoint
# ---------------------------------------------------------------------------

class TestHistoricalPoint:
    def test_creates(self):
        ts = datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc)
        pt = HistoricalPoint(timestamp=ts, value=4712.5)
        assert pt.timestamp == ts
        assert pt.value == 4712.5

    def test_is_immutable(self):
        ts = datetime(2024, 6, 1, tzinfo=timezone.utc)
        pt = HistoricalPoint(timestamp=ts, value=100.0)
        with pytest.raises(Exception):
            pt.value = 200.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# LakeConditions
# ---------------------------------------------------------------------------

class TestLakeConditions:
    def _make(self, **kwargs):
        defaults = dict(
            lake_id="deer_creek",
            water_temp_c=18.5,
            water_level_ft=4712.3,
            water_level_history=[],
            water_temp_history=[],
            data_as_of=datetime(2024, 6, 1, tzinfo=timezone.utc),
            provider_name="usgs_nwis",
        )
        defaults.update(kwargs)
        return LakeConditions(**defaults)

    def test_full_conditions(self):
        c = self._make()
        assert c.lake_id == "deer_creek"
        assert c.water_temp_c == 18.5
        assert c.water_level_ft == 4712.3
        assert c.provider_name == "usgs_nwis"

    def test_null_conditions_for_ungauged_lake(self):
        c = self._make(water_temp_c=None, water_level_ft=None, data_as_of=None)
        assert c.water_temp_c is None
        assert c.water_level_ft is None
        assert c.data_as_of is None

    def test_with_history(self):
        ts = datetime(2024, 6, 1, tzinfo=timezone.utc)
        pts = [HistoricalPoint(timestamp=ts, value=4710.0)]
        c = self._make(water_level_history=pts)
        assert len(c.water_level_history) == 1
        assert c.water_level_history[0].value == 4710.0


# ---------------------------------------------------------------------------
# DailyForecast
# ---------------------------------------------------------------------------

class TestDailyForecast:
    def _make(self, **kwargs):
        defaults = dict(
            date=date(2024, 6, 1),
            temp_high_f=85.0,
            temp_low_f=62.0,
            wind_speed_mph=8.5,
            wind_direction_deg=225.0,
            precip_probability_pct=10.0,
            weather_code=1,
            cape_max_jkg=0.0,
            has_thunderstorm_risk=False,
        )
        defaults.update(kwargs)
        return DailyForecast(**defaults)

    def test_creates(self):
        d = self._make()
        assert d.temp_high_f == 85.0
        assert d.has_thunderstorm_risk is False

    def test_thunderstorm_risk_flag(self):
        d = self._make(weather_code=95, has_thunderstorm_risk=True)
        assert d.has_thunderstorm_risk is True

    def test_cape_value(self):
        d = self._make(cape_max_jkg=750.0, has_thunderstorm_risk=True)
        assert d.cape_max_jkg == 750.0

    def test_is_immutable(self):
        d = self._make()
        with pytest.raises(Exception):
            d.temp_high_f = 99.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# HourlyForecast
# ---------------------------------------------------------------------------

class TestHourlyForecast:
    def test_creates(self):
        h = HourlyForecast(
            iso_time="2024-06-01T14:00",
            temp_f=82.0,
            wind_speed_mph=12.0,
            wind_direction_deg=270.0,
            precip_probability_pct=5.0,
            weather_code=1,
            cape_jkg=0.0,
        )
        assert h.temp_f == 82.0
        assert h.iso_time == "2024-06-01T14:00"


# ---------------------------------------------------------------------------
# WeatherForecast
# ---------------------------------------------------------------------------

class TestWeatherForecast:
    def _daily(self, d: date) -> DailyForecast:
        return DailyForecast(
            date=d, temp_high_f=80.0, temp_low_f=60.0,
            wind_speed_mph=10.0, wind_direction_deg=180.0,
            precip_probability_pct=0.0, weather_code=0,
            cape_max_jkg=0.0, has_thunderstorm_risk=False,
        )

    def _hourly(self) -> HourlyForecast:
        return HourlyForecast(
            iso_time="2024-06-01T00:00", temp_f=65.0,
            wind_speed_mph=5.0, wind_direction_deg=90.0,
            precip_probability_pct=0.0, weather_code=0, cape_jkg=0.0,
        )

    def test_creates_with_7_days(self):
        days = [self._daily(date(2024, 6, i)) for i in range(1, 8)]
        hours = [self._hourly() for _ in range(168)]
        wf = WeatherForecast(
            lake_id="deer_creek",
            timezone="America/Denver",
            daily=days,
            hourly=hours,
            fetched_at="2024-06-01T00:00:00Z",
        )
        assert len(wf.daily) == 7
        assert len(wf.hourly) == 168
        assert wf.lake_id == "deer_creek"


# ---------------------------------------------------------------------------
# LakeSummary
# ---------------------------------------------------------------------------

class TestLakeSummary:
    def _daily(self) -> DailyForecast:
        return DailyForecast(
            date=date(2024, 6, 1), temp_high_f=80.0, temp_low_f=60.0,
            wind_speed_mph=10.0, wind_direction_deg=180.0,
            precip_probability_pct=0.0, weather_code=0,
            cape_max_jkg=0.0, has_thunderstorm_risk=False,
        )

    def test_creates(self):
        s = LakeSummary(
            lake_id="deer_creek",
            name="Deer Creek Reservoir",
            state="UT",
            latitude=40.4083,
            longitude=-111.5297,
            current_water_temp_c=18.5,
            current_water_level_ft=4712.3,
            current_water_level_pct=89.0,
            forecast=[self._daily() for _ in range(7)],
        )
        assert s.lake_id == "deer_creek"
        assert len(s.forecast) == 7

    def test_null_conditions_allowed(self):
        s = LakeSummary(
            lake_id="jordanelle",
            name="Jordanelle Reservoir",
            state="UT",
            latitude=40.6097,
            longitude=-111.4203,
            current_water_temp_c=None,
            current_water_level_ft=None,
            forecast=[self._daily() for _ in range(7)],
        )
        assert s.current_water_temp_c is None
        assert s.current_water_level_ft is None


# ---------------------------------------------------------------------------
# LakeDetail
# ---------------------------------------------------------------------------

class TestLakeDetail:
    def test_creates(self):
        conditions = LakeConditions(
            lake_id="deer_creek",
            water_temp_c=18.5,
            water_level_ft=4712.3,
            water_level_history=[],
            water_temp_history=[],
            data_as_of=None,
            provider_name="usgs_nwis",
        )
        daily = [
            DailyForecast(
                date=date(2024, 6, i), temp_high_f=80.0, temp_low_f=60.0,
                wind_speed_mph=10.0, wind_direction_deg=180.0,
                precip_probability_pct=0.0, weather_code=0,
                cape_max_jkg=0.0, has_thunderstorm_risk=False,
            )
            for i in range(1, 8)
        ]
        forecast = WeatherForecast(
            lake_id="deer_creek",
            timezone="America/Denver",
            daily=daily,
            hourly=[],
            fetched_at="2024-06-01T00:00:00Z",
        )
        detail = LakeDetail(
            lake_id="deer_creek",
            name="Deer Creek Reservoir",
            state="UT",
            latitude=40.4083,
            longitude=-111.5297,
            conditions=conditions,
            weather=forecast,
        )
        assert detail.lake_id == "deer_creek"
        assert detail.conditions.water_temp_c == 18.5
        assert len(detail.weather.daily) == 7
