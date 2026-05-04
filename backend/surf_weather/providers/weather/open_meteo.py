from __future__ import annotations

import time
from datetime import date, datetime, timezone

import httpx

from ...models.lake import LakeConfig
from ...models.weather import (
    CAPE_LIGHTNING_THRESHOLD_JKG,
    THUNDERSTORM_CODES,
    DailyForecast,
    HourlyForecast,
    WeatherForecast,
)
from ..base import WeatherProvider

BASE_URL = "https://api.open-meteo.com/v1/forecast"
_MAX_RETRIES = 4
_RETRY_BASE_DELAY = 1.0  # seconds; doubles each attempt


class OpenMeteoProvider(WeatherProvider):
    """Open-Meteo weather forecast provider (no API key required)."""

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=httpx.Timeout(connect=30.0, read=30.0, write=10.0, pool=10.0),
            follow_redirects=True,
        )

    @property
    def provider_name(self) -> str:
        return "open_meteo"

    def get_forecast(self, lake: LakeConfig) -> WeatherForecast:
        params = {
            "latitude": lake.latitude,
            "longitude": lake.longitude,
            "hourly": (
                "temperature_2m,wind_speed_10m,wind_direction_10m,"
                "precipitation_probability,weather_code,cape"
            ),
            "daily": (
                "temperature_2m_max,temperature_2m_min,"
                "precipitation_probability_max,wind_speed_10m_max,"
                "wind_direction_10m_dominant,weather_code"
            ),
            "forecast_days": 10,
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "America/Denver",
        }
        resp = None
        for attempt in range(_MAX_RETRIES):
            resp = self._client.get(BASE_URL, params=params)
            if resp.status_code != 429:
                break
            if attempt < _MAX_RETRIES - 1:
                delay = float(resp.headers.get("Retry-After", _RETRY_BASE_DELAY * (2 ** attempt)))
                time.sleep(delay)
        resp.raise_for_status()
        return self._parse(lake.id, resp.json())

    def _parse(self, lake_id: str, data: dict) -> WeatherForecast:
        daily_raw = data["daily"]
        hourly_raw = data["hourly"]

        # Build a map of date string → max hourly CAPE for that day
        daily_cape: dict[str, float] = {}
        for i, ts in enumerate(hourly_raw["time"]):
            day = ts[:10]  # "2024-06-01T14:00" → "2024-06-01"
            cape = hourly_raw["cape"][i] or 0.0
            daily_cape[day] = max(daily_cape.get(day, 0.0), cape)

        daily = [
            self._parse_daily(daily_raw, i, daily_cape)
            for i in range(len(daily_raw["time"]))
        ]
        hourly = [
            self._parse_hourly(hourly_raw, i)
            for i in range(len(hourly_raw["time"]))
        ]

        return WeatherForecast(
            lake_id=lake_id,
            timezone=data["timezone"],
            daily=daily,
            hourly=hourly,
            fetched_at=datetime.now(tz=timezone.utc).isoformat(),
        )

    def _parse_daily(self, raw: dict, i: int, daily_cape: dict[str, float]) -> DailyForecast:
        day_str = raw["time"][i]
        cape = daily_cape.get(day_str, 0.0)
        wcode = raw["weather_code"][i]
        has_risk = wcode in THUNDERSTORM_CODES or cape > CAPE_LIGHTNING_THRESHOLD_JKG
        return DailyForecast(
            date=date.fromisoformat(day_str),
            temp_high_f=raw["temperature_2m_max"][i],
            temp_low_f=raw["temperature_2m_min"][i],
            wind_speed_mph=raw["wind_speed_10m_max"][i],
            wind_direction_deg=raw["wind_direction_10m_dominant"][i],
            precip_probability_pct=float(raw["precipitation_probability_max"][i]),
            weather_code=wcode,
            cape_max_jkg=cape,
            has_thunderstorm_risk=has_risk,
        )

    def _parse_hourly(self, raw: dict, i: int) -> HourlyForecast:
        return HourlyForecast(
            iso_time=raw["time"][i],
            temp_f=raw["temperature_2m"][i],
            wind_speed_mph=raw["wind_speed_10m"][i],
            wind_direction_deg=raw["wind_direction_10m"][i],
            precip_probability_pct=float(raw["precipitation_probability"][i]),
            weather_code=raw["weather_code"][i],
            cape_jkg=raw["cape"][i] or 0.0,
        )
