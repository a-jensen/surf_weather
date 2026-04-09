from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class LakeConfig:
    """Static lake definition loaded from lakes.yaml."""

    id: str
    name: str
    state: str
    latitude: float
    longitude: float
    usgs_site_id: Optional[str]
    conditions_provider: str
    cuwcd_set_name: Optional[str] = None
    state_park_slug: Optional[str] = None
    usgs_level_param: str = "00065"
    history_provider: Optional[str] = None
    usbr_site_id: Optional[int] = None
    lake_level_unit: Optional[str] = None
    full_pool_elevation_ft: Optional[float] = None
    dead_pool_elevation_ft: Optional[float] = None


@dataclass(frozen=True)
class HistoricalPoint:
    """A single timestamped measurement."""

    timestamp: datetime
    value: float


@dataclass(frozen=True)
class LakeConditions:
    """Current and recent lake state from a data provider."""

    lake_id: str
    water_temp_c: Optional[float]
    water_level_ft: Optional[float]
    water_level_history: list[HistoricalPoint] = field(default_factory=list)
    water_temp_history: list[HistoricalPoint] = field(default_factory=list)
    water_level_pct: Optional[float] = None
    data_as_of: Optional[datetime] = None
    provider_name: str = "unknown"
