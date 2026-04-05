"""Tests for the aggregator service."""
import dataclasses

import pytest

from surf_weather.services.aggregator import Aggregator
from surf_weather.models.combined import LakeDetail, LakeSummary
from surf_weather.providers.base import LakeDataProvider, WeatherProvider
from surf_weather.models.lake import LakeConfig, LakeConditions
from surf_weather.models.weather import WeatherForecast
from surf_weather.providers.lake_data.registry import LakeDataProviderRegistry


class _FakeWeatherProvider(WeatherProvider):
    def __init__(self, forecast: WeatherForecast):
        self._forecast = forecast

    @property
    def provider_name(self) -> str:
        return "fake_weather"

    def get_forecast(self, lake: LakeConfig) -> WeatherForecast:
        return dataclasses.replace(self._forecast, lake_id=lake.id)


class _FakeLakeProvider(LakeDataProvider):
    def __init__(self, conditions: LakeConditions):
        self._conditions = conditions

    @property
    def provider_name(self) -> str:
        return "fake_lake"

    def supports_lake(self, lake: LakeConfig) -> bool:
        return True

    def get_conditions(self, lake: LakeConfig) -> LakeConditions:
        return dataclasses.replace(self._conditions, lake_id=lake.id)


class TestAggregator:
    @pytest.fixture
    def aggregator(self, fake_weather_forecast, fake_lake_conditions, fake_lake_with_gauge):
        registry = LakeDataProviderRegistry()
        registry.register(_FakeLakeProvider(fake_lake_conditions))
        return Aggregator(
            weather_provider=_FakeWeatherProvider(fake_weather_forecast),
            lake_registry=registry,
            lakes=[fake_lake_with_gauge],
        )

    def test_get_all_summaries_returns_list(self, aggregator):
        summaries = aggregator.get_all_summaries()
        assert isinstance(summaries, list)
        assert len(summaries) == 1

    def test_summary_has_lake_id(self, aggregator, fake_lake_with_gauge):
        summaries = aggregator.get_all_summaries()
        assert summaries[0].lake_id == fake_lake_with_gauge.id

    def test_summary_has_7_day_forecast(self, aggregator):
        summaries = aggregator.get_all_summaries()
        assert len(summaries[0].forecast) == 7

    def test_summary_includes_current_conditions(self, aggregator):
        summaries = aggregator.get_all_summaries()
        s = summaries[0]
        assert s.current_water_temp_c == 18.5
        assert s.current_water_level_ft == 4712.3

    def test_get_detail_returns_lake_detail(self, aggregator, fake_lake_with_gauge):
        detail = aggregator.get_detail(fake_lake_with_gauge.id)
        assert isinstance(detail, LakeDetail)

    def test_get_detail_has_conditions_with_history(self, aggregator):
        detail = aggregator.get_detail("deer_creek")
        assert len(detail.conditions.water_level_history) > 0

    def test_get_detail_has_full_weather(self, aggregator):
        detail = aggregator.get_detail("deer_creek")
        assert len(detail.weather.daily) == 7
        assert len(detail.weather.hourly) > 0

    def test_get_detail_raises_for_unknown_lake(self, aggregator):
        with pytest.raises(KeyError):
            aggregator.get_detail("nonexistent_lake")

    def test_summary_is_lake_summary_instance(self, aggregator):
        summaries = aggregator.get_all_summaries()
        assert isinstance(summaries[0], LakeSummary)

    def test_null_conditions_for_ungauged_lake(self, fake_weather_forecast, fake_lake_no_gauge):
        null_conditions = LakeConditions(
            lake_id=fake_lake_no_gauge.id,
            water_temp_c=None,
            water_level_ft=None,
            provider_name="usgs_nwis",
        )
        registry = LakeDataProviderRegistry()
        registry.register(_FakeLakeProvider(null_conditions))
        aggregator = Aggregator(
            weather_provider=_FakeWeatherProvider(fake_weather_forecast),
            lake_registry=registry,
            lakes=[fake_lake_no_gauge],
        )
        summaries = aggregator.get_all_summaries()
        assert summaries[0].current_water_temp_c is None
        assert summaries[0].current_water_level_ft is None
