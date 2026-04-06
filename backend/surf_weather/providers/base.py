from __future__ import annotations

from abc import ABC, abstractmethod

from ..models.lake import LakeConfig, LakeConditions
from ..models.weather import WeatherForecast


class WeatherProvider(ABC):
    """Fetches weather forecasts for a given lake location."""

    @abstractmethod
    def get_forecast(self, lake: LakeConfig) -> WeatherForecast:
        """Return a 7-day forecast for the lake's coordinates."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable identifier, e.g. 'open_meteo'."""
        ...


class LakeDataProvider(ABC):
    """Fetches real-time and historical lake conditions."""

    @abstractmethod
    def get_conditions(self, lake: LakeConfig) -> LakeConditions:
        """Fetch current conditions and history for one lake."""
        ...

    @abstractmethod
    def supports_lake(self, lake: LakeConfig) -> bool:
        """Return True if this provider can serve the given lake."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable identifier, e.g. 'usgs_nwis'."""
        ...
