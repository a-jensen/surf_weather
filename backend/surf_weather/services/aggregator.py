from __future__ import annotations

import dataclasses
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from ..models.combined import LakeDetail, LakeSummary
from ..models.lake import LakeConditions, LakeConfig
from ..models.weather import WeatherForecast
from ..providers.base import LakeDataProvider, WeatherProvider
from ..providers.lake_data.registry import LakeDataProviderRegistry

logger = logging.getLogger(__name__)

_MAX_WORKERS = 8


_WEATHER_UNAVAILABLE = "Weather forecast temporarily unavailable"


def _empty_forecast(lake: LakeConfig) -> WeatherForecast:
    return WeatherForecast(
        lake_id=lake.id,
        timezone="America/Denver",
        daily=[],
        hourly=[],
        fetched_at=datetime.now(tz=timezone.utc).isoformat(),
    )


def _empty_conditions(lake: LakeConfig, reason: str) -> LakeConditions:
    """Return null conditions when a lake data fetch fails."""
    logger.warning("Returning empty conditions for lake '%s': %s", lake.id, reason)
    return LakeConditions(
        lake_id=lake.id,
        water_temp_c=None,
        water_level_ft=None,
        water_level_history=[],
        water_temp_history=[],
        data_as_of=None,
        provider_name="unavailable",
    )


def _merge_history(conditions: LakeConditions, registry: LakeDataProviderRegistry, lake: LakeConfig) -> LakeConditions:
    """Overlay history from the history_provider if configured and different from the conditions provider."""
    history_provider = registry.get_history_provider(lake)
    if not history_provider:
        return conditions
    try:
        history_data = history_provider.get_conditions(lake)

        overrides: dict = {
            "water_level_history": history_data.water_level_history or conditions.water_level_history,
            "water_temp_history": history_data.water_temp_history or conditions.water_temp_history,
        }

        # Derive % full from the latest USBR elevation when both pool elevations are known.
        if (
            lake.full_pool_elevation_ft is not None
            and lake.dead_pool_elevation_ft is not None
            and history_data.water_level_ft is not None
        ):
            elev = history_data.water_level_ft
            pool_range = lake.full_pool_elevation_ft - lake.dead_pool_elevation_ft
            pct = (elev - lake.dead_pool_elevation_ft) / pool_range * 100
            overrides["water_level_ft"] = elev
            overrides["water_level_pct"] = round(max(0.0, min(100.0, pct)), 2)

        return dataclasses.replace(conditions, **overrides)
    except Exception:
        logger.warning(
            "Failed to fetch history for lake '%s' via '%s'",
            lake.id, history_provider.provider_name,
        )
        return conditions


class Aggregator:
    """Combines weather and lake data providers into API response shapes."""

    def __init__(
        self,
        weather_provider: WeatherProvider,
        lake_registry: LakeDataProviderRegistry,
        lakes: list[LakeConfig],
    ) -> None:
        self._weather = weather_provider
        self._registry = lake_registry
        self._lakes = {lake.id: lake for lake in lakes}

    def get_all_summaries(self) -> list[LakeSummary]:
        lakes = list(self._lakes.values())

        def fetch(lake: LakeConfig) -> LakeSummary:
            weather_error: str | None = None
            forecast_daily = []

            try:
                forecast = self._weather.get_forecast(lake)
                forecast_daily = forecast.daily
            except Exception:
                logger.exception("Failed to fetch weather for lake '%s'", lake.id)
                weather_error = _WEATHER_UNAVAILABLE

            try:
                provider = self._registry.get_provider(lake)
                conditions = provider.get_conditions(lake)
                conditions = _merge_history(conditions, self._registry, lake)
            except Exception:
                logger.exception("Failed to fetch conditions for lake '%s'", lake.id)
                conditions = _empty_conditions(lake, "provider error")

            return LakeSummary(
                lake_id=lake.id,
                name=lake.name,
                state=lake.state,
                latitude=lake.latitude,
                longitude=lake.longitude,
                current_water_temp_c=conditions.water_temp_c,
                current_water_level_ft=conditions.water_level_ft,
                current_water_level_pct=conditions.water_level_pct,
                forecast=forecast_daily,
                weather_error=weather_error,
            )

        results: dict[str, LakeSummary] = {}
        with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
            futures = {executor.submit(fetch, lake): lake for lake in lakes}
            for future in as_completed(futures):
                lake = futures[future]
                results[lake.id] = future.result()

        return [results[lake.id] for lake in lakes if lake.id in results]

    def get_detail(self, lake_id: str) -> LakeDetail:
        if lake_id not in self._lakes:
            raise KeyError(f"Lake not found: {lake_id}")

        lake = self._lakes[lake_id]
        provider = self._registry.get_provider(lake)
        weather_error: str | None = None

        with ThreadPoolExecutor(max_workers=2) as executor:
            conditions_future = executor.submit(provider.get_conditions, lake)
            forecast_future = executor.submit(self._weather.get_forecast, lake)

            try:
                conditions = conditions_future.result()
                conditions = _merge_history(conditions, self._registry, lake)
            except Exception:
                logger.exception("Failed to fetch conditions for lake '%s'", lake.id)
                conditions = _empty_conditions(lake, "provider error")

            try:
                forecast = forecast_future.result()
            except Exception:
                logger.exception("Failed to fetch weather for lake '%s'", lake.id)
                weather_error = _WEATHER_UNAVAILABLE
                forecast = _empty_forecast(lake)

        return LakeDetail(
            lake_id=lake.id,
            name=lake.name,
            state=lake.state,
            latitude=lake.latitude,
            longitude=lake.longitude,
            conditions=conditions,
            weather=forecast,
            weather_error=weather_error,
            lake_level_unit=lake.lake_level_unit,
            full_pool_elevation_ft=lake.full_pool_elevation_ft,
            dead_pool_elevation_ft=lake.dead_pool_elevation_ft,
        )
