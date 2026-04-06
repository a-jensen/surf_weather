from __future__ import annotations

from ..base import LakeDataProvider
from ...models.lake import LakeConfig


class LakeDataProviderRegistry:
    """Resolves the correct LakeDataProvider(s) for a given lake.

    Registration order matters for get_provider() (first match wins).
    get_history_provider() matches by provider_name directly.
    """

    def __init__(self) -> None:
        self._providers: list[LakeDataProvider] = []

    def register(self, provider: LakeDataProvider) -> None:
        self._providers.append(provider)

    def get_provider(self, lake: LakeConfig) -> LakeDataProvider:
        """Return the conditions provider for the lake."""
        for p in self._providers:
            if p.supports_lake(lake):
                return p
        raise ValueError(
            f"No LakeDataProvider registered for lake '{lake.id}' "
            f"(conditions_provider={lake.conditions_provider!r})"
        )

    def get_history_provider(self, lake: LakeConfig) -> LakeDataProvider | None:
        """Return the provider used for historical data, or None if not configured."""
        if not lake.history_provider:
            return None
        for p in self._providers:
            if p.provider_name == lake.history_provider:
                return p
        return None
