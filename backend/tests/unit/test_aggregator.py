"""Tests for the aggregator service."""
import dataclasses
from datetime import datetime, timezone

import pytest

from surf_weather.services.aggregator import Aggregator
from surf_weather.models.combined import LakeDetail, LakeSummary
from surf_weather.providers.base import LakeDataProvider, WeatherProvider
from surf_weather.models.lake import LakeConfig, LakeConditions, HistoricalPoint
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

    def test_summary_includes_water_level_pct(self, fake_weather_forecast, fake_lake_with_gauge):
        conditions = LakeConditions(
            lake_id=fake_lake_with_gauge.id,
            water_temp_c=None,
            water_level_ft=None,
            water_level_pct=89.0,
            provider_name="cuwcd",
        )
        registry = LakeDataProviderRegistry()
        registry.register(_FakeLakeProvider(conditions))
        aggregator = Aggregator(
            weather_provider=_FakeWeatherProvider(fake_weather_forecast),
            lake_registry=registry,
            lakes=[fake_lake_with_gauge],
        )
        summaries = aggregator.get_all_summaries()
        assert summaries[0].current_water_level_pct == pytest.approx(89.0)

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


# ---------------------------------------------------------------------------
# Multi-provider merge behaviour
# ---------------------------------------------------------------------------

class _RaisingProvider(LakeDataProvider):
    """Provider that always raises on get_conditions."""

    @property
    def provider_name(self) -> str:
        return "raising"

    def supports_lake(self, lake: LakeConfig) -> bool:
        return False

    def get_conditions(self, lake: LakeConfig) -> LakeConditions:
        raise RuntimeError("simulated fetch failure")


class TestAggregatorMultiProvider:
    """Verify conditions/history merge when a lake has two providers configured."""

    def _dual_provider_lake(self) -> LakeConfig:
        return LakeConfig(
            id="deer_creek",
            name="Deer Creek Reservoir",
            state="UT",
            latitude=40.4083,
            longitude=-111.5297,
            usgs_site_id=None,
            conditions_provider="state_parks",
            history_provider="cuwcd",
        )

    def _conditions_provider_result(self) -> LakeConditions:
        return LakeConditions(
            lake_id="deer_creek",
            water_temp_c=11.1,
            water_level_ft=None,
            water_level_pct=77.0,
            water_level_history=[],
            provider_name="ut_state_parks",
        )

    def _history_provider_result(self) -> LakeConditions:
        pts = [
            HistoricalPoint(timestamp=datetime(2026, 3, d, tzinfo=timezone.utc), value=85.0 + d)
            for d in range(1, 4)
        ]
        return LakeConditions(
            lake_id="deer_creek",
            water_temp_c=None,
            water_level_ft=None,
            water_level_pct=89.0,
            water_level_history=pts,
            provider_name="cuwcd",
        )

    def _make_aggregator(self, fake_weather_forecast, conditions_result, history_result):
        lake = self._dual_provider_lake()

        class _ConditionsProvider(LakeDataProvider):
            @property
            def provider_name(self):
                return "state_parks"

            def supports_lake(self, l):
                return l.conditions_provider == "state_parks"

            def get_conditions(self, l):
                return dataclasses.replace(conditions_result, lake_id=l.id)

        class _HistoryProvider(LakeDataProvider):
            @property
            def provider_name(self):
                return "cuwcd"

            def supports_lake(self, l):
                return False  # not used for conditions

            def get_conditions(self, l):
                return dataclasses.replace(history_result, lake_id=l.id)

        registry = LakeDataProviderRegistry()
        registry.register(_ConditionsProvider())
        registry.register(_HistoryProvider())
        return Aggregator(
            weather_provider=_FakeWeatherProvider(fake_weather_forecast),
            lake_registry=registry,
            lakes=[lake],
        )

    def test_merge_uses_conditions_from_primary_provider(self, fake_weather_forecast):
        aggregator = self._make_aggregator(
            fake_weather_forecast,
            self._conditions_provider_result(),
            self._history_provider_result(),
        )
        detail = aggregator.get_detail("deer_creek")
        assert detail.conditions.water_temp_c == pytest.approx(11.1)
        assert detail.conditions.water_level_pct == pytest.approx(77.0)
        assert detail.conditions.provider_name == "ut_state_parks"

    def test_merge_uses_history_from_history_provider(self, fake_weather_forecast):
        aggregator = self._make_aggregator(
            fake_weather_forecast,
            self._conditions_provider_result(),
            self._history_provider_result(),
        )
        detail = aggregator.get_detail("deer_creek")
        assert len(detail.conditions.water_level_history) == 3

    def test_merge_falls_back_gracefully_if_history_provider_fails(self, fake_weather_forecast):
        lake = self._dual_provider_lake()

        class _ConditionsProvider(LakeDataProvider):
            @property
            def provider_name(self):
                return "state_parks"

            def supports_lake(self, l):
                return l.conditions_provider == "state_parks"

            def get_conditions(self, l):
                return dataclasses.replace(self._conditions_provider_result(), lake_id=l.id)

            def _conditions_provider_result(self):
                return LakeConditions(
                    lake_id=lake.id, water_temp_c=11.1, water_level_ft=None,
                    water_level_pct=77.0, provider_name="ut_state_parks",
                )

        class _FailingHistoryProvider(LakeDataProvider):
            @property
            def provider_name(self):
                return "cuwcd"

            def supports_lake(self, l):
                return False

            def get_conditions(self, l):
                raise RuntimeError("simulated failure")

        registry = LakeDataProviderRegistry()
        registry.register(_ConditionsProvider())
        registry.register(_FailingHistoryProvider())
        aggregator = Aggregator(
            weather_provider=_FakeWeatherProvider(fake_weather_forecast),
            lake_registry=registry,
            lakes=[lake],
        )
        detail = aggregator.get_detail("deer_creek")
        # conditions still present; history is empty (failure was suppressed)
        assert detail.conditions.water_temp_c == pytest.approx(11.1)
        assert detail.conditions.water_level_history == []
