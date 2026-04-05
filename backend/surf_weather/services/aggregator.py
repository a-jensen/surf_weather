from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models.combined import LakeDetail, LakeSummary
from ..models.lake import LakeConditions, LakeConfig
from ..providers.base import LakeDataProvider, WeatherProvider
from ..providers.lake_data.registry import LakeDataProviderRegistry

logger = logging.getLogger(__name__)

_MAX_WORKERS = 8


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

        def fetch(lake: LakeConfig) -> LakeSummary | None:
            # Fetch weather and conditions independently so one failure
            # doesn't hide the other.
            try:
                forecast = self._weather.get_forecast(lake)
            except Exception:
                logger.exception("Failed to fetch weather for lake '%s'", lake.id)
                return None

            try:
                provider = self._registry.get_provider(lake)
                conditions = provider.get_conditions(lake)
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
                forecast=forecast.daily,
            )

        results: dict[str, LakeSummary | None] = {}
        with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
            futures = {executor.submit(fetch, lake): lake for lake in lakes}
            for future in as_completed(futures):
                lake = futures[future]
                results[lake.id] = future.result()

        return [results[lake.id] for lake in lakes if results.get(lake.id) is not None]

    def get_detail(self, lake_id: str) -> LakeDetail:
        if lake_id not in self._lakes:
            raise KeyError(f"Lake not found: {lake_id}")

        lake = self._lakes[lake_id]
        provider = self._registry.get_provider(lake)

        with ThreadPoolExecutor(max_workers=2) as executor:
            conditions_future = executor.submit(provider.get_conditions, lake)
            forecast_future = executor.submit(self._weather.get_forecast, lake)

            try:
                conditions = conditions_future.result()
            except Exception:
                logger.exception("Failed to fetch conditions for lake '%s'", lake.id)
                conditions = _empty_conditions(lake, "provider error")

            forecast = forecast_future.result()  # propagate weather errors to caller

        return LakeDetail(
            lake_id=lake.id,
            name=lake.name,
            state=lake.state,
            latitude=lake.latitude,
            longitude=lake.longitude,
            conditions=conditions,
            weather=forecast,
        )
