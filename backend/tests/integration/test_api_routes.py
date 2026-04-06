"""Integration tests for API routes using FastAPI TestClient."""
import pytest
from fastapi.testclient import TestClient

from surf_weather.main import create_app
from surf_weather.providers.base import LakeDataProvider, WeatherProvider
from surf_weather.models.lake import LakeConfig, LakeConditions
from surf_weather.models.weather import WeatherForecast
from surf_weather.providers.lake_data.registry import LakeDataProviderRegistry
from surf_weather.services.aggregator import Aggregator


class _FakeWeatherProvider(WeatherProvider):
    def __init__(self, forecast: WeatherForecast):
        self._forecast = forecast

    @property
    def provider_name(self) -> str:
        return "fake_weather"

    def get_forecast(self, lake: LakeConfig) -> WeatherForecast:
        return self._forecast


class _FakeLakeProvider(LakeDataProvider):
    def __init__(self, conditions: LakeConditions):
        self._conditions = conditions

    @property
    def provider_name(self) -> str:
        return "fake_lake"

    def supports_lake(self, lake: LakeConfig) -> bool:
        return True

    def get_conditions(self, lake: LakeConfig) -> LakeConditions:
        return self._conditions


@pytest.fixture
def test_client(fake_lake_with_gauge, fake_weather_forecast, fake_lake_conditions):
    registry = LakeDataProviderRegistry()
    registry.register(_FakeLakeProvider(fake_lake_conditions))

    aggregator = Aggregator(
        weather_provider=_FakeWeatherProvider(fake_weather_forecast),
        lake_registry=registry,
        lakes=[fake_lake_with_gauge],
    )
    app = create_app(aggregator=aggregator)
    return TestClient(app)


class TestHealthRoute:
    def test_health_returns_200(self, test_client):
        resp = test_client.get("/health")
        assert resp.status_code == 200

    def test_health_returns_ok(self, test_client):
        resp = test_client.get("/health")
        assert resp.json()["status"] == "ok"


class TestLakesListRoute:
    def test_lakes_returns_200(self, test_client):
        resp = test_client.get("/lakes")
        assert resp.status_code == 200

    def test_lakes_returns_list(self, test_client):
        resp = test_client.get("/lakes")
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1

    def test_lake_summary_has_id(self, test_client):
        resp = test_client.get("/lakes")
        lake = resp.json()[0]
        assert lake["lake_id"] == "deer_creek"

    def test_lake_summary_has_name(self, test_client):
        resp = test_client.get("/lakes")
        lake = resp.json()[0]
        assert lake["name"] == "Deer Creek Reservoir"

    def test_lake_summary_has_forecast(self, test_client):
        resp = test_client.get("/lakes")
        lake = resp.json()[0]
        assert len(lake["forecast"]) == 7

    def test_lake_summary_has_conditions(self, test_client):
        resp = test_client.get("/lakes")
        lake = resp.json()[0]
        assert lake["current_water_temp_c"] == pytest.approx(18.5)
        assert lake["current_water_level_ft"] == pytest.approx(4712.3)


class TestLakeDetailRoute:
    def test_detail_returns_200(self, test_client):
        resp = test_client.get("/lakes/deer_creek")
        assert resp.status_code == 200

    def test_detail_has_lake_id(self, test_client):
        resp = test_client.get("/lakes/deer_creek")
        assert resp.json()["lake_id"] == "deer_creek"

    def test_detail_has_conditions(self, test_client):
        resp = test_client.get("/lakes/deer_creek")
        detail = resp.json()
        assert "conditions" in detail
        assert detail["conditions"]["water_temp_c"] == pytest.approx(18.5)

    def test_detail_has_weather_with_hourly(self, test_client):
        resp = test_client.get("/lakes/deer_creek")
        detail = resp.json()
        assert "weather" in detail
        assert len(detail["weather"]["daily"]) == 7
        assert len(detail["weather"]["hourly"]) > 0

    def test_detail_has_history(self, test_client):
        resp = test_client.get("/lakes/deer_creek")
        conditions = resp.json()["conditions"]
        assert isinstance(conditions["water_level_history"], list)

    def test_unknown_lake_returns_404(self, test_client):
        resp = test_client.get("/lakes/nonexistent")
        assert resp.status_code == 404
