"""Tests for provider registries."""
import pytest

from surf_weather.providers.lake_data.registry import LakeDataProviderRegistry
from surf_weather.providers.base import LakeDataProvider
from surf_weather.models.lake import LakeConfig, LakeConditions


class _FakeProvider(LakeDataProvider):
    """Test double that supports only a specific state."""

    def __init__(self, state: str, name: str = "fake"):
        self._state = state
        self._name = name

    @property
    def provider_name(self) -> str:
        return self._name

    def supports_lake(self, lake: LakeConfig) -> bool:
        return lake.state == self._state

    def get_conditions(self, lake: LakeConfig) -> LakeConditions:
        return LakeConditions(
            lake_id=lake.id,
            water_temp_c=None,
            water_level_ft=None,
            provider_name=self._name,
        )


class TestLakeDataProviderRegistry:
    def _lake(self, state: str) -> LakeConfig:
        return LakeConfig(
            id="test", name="Test Lake", state=state,
            latitude=40.0, longitude=-111.0,
            usgs_site_id=None, conditions_provider="usgs",
        )

    def test_returns_matching_provider(self):
        registry = LakeDataProviderRegistry()
        registry.register(_FakeProvider("UT"))

        provider = registry.get_provider(self._lake("UT"))

        assert provider.provider_name == "fake"

    def test_first_match_wins(self):
        registry = LakeDataProviderRegistry()
        registry.register(_FakeProvider("UT", "first"))
        registry.register(_FakeProvider("UT", "second"))

        provider = registry.get_provider(self._lake("UT"))

        assert provider.provider_name == "first"

    def test_raises_when_no_provider_matches(self):
        registry = LakeDataProviderRegistry()
        registry.register(_FakeProvider("UT"))

        with pytest.raises(ValueError, match="No LakeDataProvider"):
            registry.get_provider(self._lake("CA"))

    def test_multiple_states_routed_correctly(self):
        registry = LakeDataProviderRegistry()
        registry.register(_FakeProvider("UT", "ut_provider"))
        registry.register(_FakeProvider("CA", "ca_provider"))

        assert registry.get_provider(self._lake("UT")).provider_name == "ut_provider"
        assert registry.get_provider(self._lake("CA")).provider_name == "ca_provider"

    def test_empty_registry_raises(self):
        registry = LakeDataProviderRegistry()

        with pytest.raises(ValueError):
            registry.get_provider(self._lake("UT"))

    def test_get_history_provider_returns_none_when_not_configured(self):
        registry = LakeDataProviderRegistry()
        registry.register(_FakeProvider("UT", "ut_provider"))
        lake = self._lake("UT")  # history_provider is None by default

        assert registry.get_history_provider(lake) is None

    def test_get_history_provider_returns_correct_provider(self):
        registry = LakeDataProviderRegistry()
        registry.register(_FakeProvider("UT", "conditions_p"))
        registry.register(_FakeProvider("UT", "history_p"))
        lake = LakeConfig(
            id="test", name="Test", state="UT",
            latitude=40.0, longitude=-111.0,
            usgs_site_id=None, conditions_provider="usgs",
            history_provider="history_p",
        )

        assert registry.get_history_provider(lake).provider_name == "history_p"

    def test_get_history_provider_returns_none_for_unknown_name(self):
        registry = LakeDataProviderRegistry()
        registry.register(_FakeProvider("UT", "some_provider"))
        lake = LakeConfig(
            id="test", name="Test", state="UT",
            latitude=40.0, longitude=-111.0,
            usgs_site_id=None, conditions_provider="usgs",
            history_provider="nonexistent",
        )

        assert registry.get_history_provider(lake) is None
