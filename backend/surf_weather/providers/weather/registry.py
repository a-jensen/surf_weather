from ..base import WeatherProvider
from .open_meteo import OpenMeteoProvider


def get_weather_provider() -> WeatherProvider:
    """Return the configured weather provider (Open-Meteo by default)."""
    return OpenMeteoProvider()
