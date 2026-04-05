from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .lake import LakeConditions
from .weather import DailyForecast, WeatherForecast


@dataclass(frozen=True)
class LakeSummary:
    """Response shape for GET /lakes — list view with 7-day strip."""

    lake_id: str
    name: str
    state: str
    latitude: float
    longitude: float
    current_water_temp_c: Optional[float]
    current_water_level_ft: Optional[float]
    forecast: list[DailyForecast]


@dataclass(frozen=True)
class LakeDetail:
    """Response shape for GET /lakes/{lake_id} — full detail view."""

    lake_id: str
    name: str
    state: str
    latitude: float
    longitude: float
    conditions: LakeConditions
    weather: WeatherForecast
