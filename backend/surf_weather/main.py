from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import load_lakes
from .providers.lake_data.cuwcd import CUWCDProvider
from .providers.lake_data.registry import LakeDataProviderRegistry
from .providers.lake_data.state_parks import StateParksProvider
from .providers.lake_data.usgs import USGSProvider
from .providers.weather.registry import get_weather_provider
from .routers import health, lakes
from .services.aggregator import Aggregator


def create_app(aggregator: Aggregator | None = None) -> FastAPI:
    app = FastAPI(title="Surf Weather API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    if aggregator is None:
        aggregator = _build_aggregator()

    app.state.aggregator = aggregator

    app.include_router(health.router)
    app.include_router(lakes.router)

    return app


def _build_aggregator() -> Aggregator:
    all_lakes = load_lakes()

    registry = LakeDataProviderRegistry()
    registry.register(CUWCDProvider())
    registry.register(StateParksProvider())
    registry.register(USGSProvider())

    return Aggregator(
        weather_provider=get_weather_provider(),
        lake_registry=registry,
        lakes=all_lakes,
    )


app = create_app()
