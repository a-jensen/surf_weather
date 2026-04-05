from __future__ import annotations

from ..base import LakeDataProvider
from ...models.lake import LakeConfig


class LakeDataProviderRegistry:
    """Resolves the correct LakeDataProvider for a given lake.

    Registration order matters: first match wins.
    """

    def __init__(self) -> None:
        self._providers: list[LakeDataProvider] = []

    def register(self, provider: LakeDataProvider) -> None:
        self._providers.append(provider)

    def get_provider(self, lake: LakeConfig) -> LakeDataProvider:
        for p in self._providers:
            if p.supports_lake(lake):
                return p
        raise ValueError(
            f"No LakeDataProvider registered for lake '{lake.id}' "
            f"(state={lake.state}, data_provider={lake.data_provider})"
        )
