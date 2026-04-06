"""Shared fixtures for all tests."""
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from surf_weather.models.lake import HistoricalPoint, LakeConditions, LakeConfig
from surf_weather.models.weather import DailyForecast, HourlyForecast, WeatherForecast

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fake_lake_with_gauge() -> LakeConfig:
    return LakeConfig(
        id="deer_creek",
        name="Deer Creek Reservoir",
        state="UT",
        latitude=40.4083,
        longitude=-111.5297,
        usgs_site_id="10159000",
        conditions_provider="usgs",
    )


@pytest.fixture
def fake_lake_no_gauge() -> LakeConfig:
    return LakeConfig(
        id="jordanelle",
        name="Jordanelle Reservoir",
        state="UT",
        latitude=40.6097,
        longitude=-111.4203,
        usgs_site_id=None,
        conditions_provider="usgs",
    )


@pytest.fixture
def fake_lake_conditions(fake_lake_with_gauge) -> LakeConditions:
    pts = [
        HistoricalPoint(timestamp=datetime(2024, 3, d, tzinfo=timezone.utc), value=4710.0 + d)
        for d in range(1, 4)
    ]
    return LakeConditions(
        lake_id=fake_lake_with_gauge.id,
        water_temp_c=18.5,
        water_level_ft=4712.3,
        water_level_history=pts,
        water_temp_history=pts,
        data_as_of=datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc),
        provider_name="usgs_nwis",
    )


@pytest.fixture
def fake_daily_forecast() -> DailyForecast:
    return DailyForecast(
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


@pytest.fixture
def fake_weather_forecast(fake_lake_with_gauge, fake_daily_forecast) -> WeatherForecast:
    daily = [fake_daily_forecast for _ in range(7)]
    hourly = [
        HourlyForecast(
            iso_time=f"2024-06-01T{h:02d}:00",
            temp_f=70.0,
            wind_speed_mph=8.0,
            wind_direction_deg=225.0,
            precip_probability_pct=5.0,
            weather_code=1,
            cape_jkg=0.0,
        )
        for h in range(24)
    ]
    return WeatherForecast(
        lake_id=fake_lake_with_gauge.id,
        timezone="America/Denver",
        daily=daily,
        hourly=hourly,
        fetched_at="2024-06-01T00:00:00Z",
    )


@pytest.fixture
def open_meteo_fixture() -> dict:
    return json.loads((FIXTURES_DIR / "open_meteo_response.json").read_text())


@pytest.fixture
def cuwcd_current_fixture() -> dict:
    """CUWCD current-data response for Deer Creek (public_dc)."""
    return {
        "MetaData": {"DataQuality": "PROVISIONAL DATA - SUBJECT TO CHANGE"},
        "Name": "public_dc",
        "ReportDataGroups": [
            {
                "Name": "Current Data",
                "Tags": [
                    {
                        "Tag": "OREM\\DC\\ANALOG\\RES_LVL",
                        "Metadata": {
                            "Description": "Orem Deer Creek Reservoir Level",
                            "ParameterDescription": "Elevation",
                            "Units": "ft",
                        },
                        "Values": [
                            {"ts": "2026-04-05T16:08:00", "val": 5410.5},
                        ],
                    },
                    {
                        "Tag": "DC_CALC_PCT_FULL_FCV",
                        "Metadata": {
                            "Description": "Percent Full",
                            "ParameterDescription": "Pct Full",
                            "Units": "%",
                        },
                        "Values": [
                            {"ts": "2026-04-05T16:08:00", "val": 89.05},
                        ],
                    },
                ],
            }
        ],
    }


@pytest.fixture
def cuwcd_trend_fixture() -> dict:
    """CUWCD trend response (30-day history) for Deer Creek (public_dc_trend)."""
    return {
        "MetaData": {"DataQuality": "PROVISIONAL DATA - SUBJECT TO CHANGE"},
        "Name": "public_dc_trend",
        "ReportDataGroups": [
            {
                "Name": "Current Data",
                "Tags": [
                    {
                        "Tag": "DC_CALC_PCT_FULL_FCV",
                        "Metadata": {
                            "Description": "Percent Full",
                            "ParameterDescription": "Pct Full",
                            "Units": "%",
                        },
                        "Values": [
                            {"ts": "2026-03-06T00:00:00", "val": 87.0},
                            {"ts": "2026-03-07T00:00:00", "val": 88.0},
                            {"ts": "2026-04-05T00:00:00", "val": 89.05},
                        ],
                    },
                ],
            }
        ],
    }


@pytest.fixture
def state_parks_html() -> str:
    """Minimal HTML snippet matching the Utah State Parks waterconditionResults widget."""
    return """
    <html><body>
    <div class="waterconditionResults">
      <div class="feeditem watertemp"><span>Water Temp:</span>52&deg; F</div>
      <div class="feeditem waterlevel"><span>Water Level:</span>77%</div>
    </div>
    </body></html>
    """


@pytest.fixture
def usgs_dv_fixture() -> dict:
    """GeoJSON response for gage height (00065) — 4 entries, 1 invalid."""
    return json.loads((FIXTURES_DIR / "usgs_dv_response.json").read_text())


@pytest.fixture
def usgs_temp_fixture() -> dict:
    """GeoJSON response for water temperature (00010) — 4 entries, 1 invalid."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "monitoring_location_id": "USGS-10159000",
                    "parameter_code": "00010",
                    "time": "2024-03-01",
                    "value": "15.0",
                },
                "geometry": None,
            },
            {
                "type": "Feature",
                "properties": {
                    "monitoring_location_id": "USGS-10159000",
                    "parameter_code": "00010",
                    "time": "2024-03-02",
                    "value": "16.0",
                },
                "geometry": None,
            },
            {
                "type": "Feature",
                "properties": {
                    "monitoring_location_id": "USGS-10159000",
                    "parameter_code": "00010",
                    "time": "2024-03-03",
                    "value": "",
                },
                "geometry": None,
            },
            {
                "type": "Feature",
                "properties": {
                    "monitoring_location_id": "USGS-10159000",
                    "parameter_code": "00010",
                    "time": "2024-03-04",
                    "value": "18.5",
                },
                "geometry": None,
            },
        ],
        "numberReturned": 4,
    }
