from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


THUNDERSTORM_CODES = {95, 96, 99}
CAPE_LIGHTNING_THRESHOLD_JKG = 500.0


@dataclass(frozen=True)
class DailyForecast:
    """One day's summary for the lake list view."""

    date: date
    temp_high_f: float
    temp_low_f: float
    wind_speed_mph: float
    wind_direction_deg: float
    precip_probability_pct: float
    weather_code: int
    cape_max_jkg: float
    has_thunderstorm_risk: bool


@dataclass(frozen=True)
class HourlyForecast:
    """Hourly data for the detail view."""

    iso_time: str
    temp_f: float
    wind_speed_mph: float
    wind_direction_deg: float
    precip_probability_pct: float
    weather_code: int
    cape_jkg: float


@dataclass(frozen=True)
class WeatherForecast:
    """7-day forecast for a lake location."""

    lake_id: str
    timezone: str
    daily: list[DailyForecast]
    hourly: list[HourlyForecast]
    fetched_at: str
