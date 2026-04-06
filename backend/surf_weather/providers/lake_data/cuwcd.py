from __future__ import annotations

from datetime import datetime

import httpx

from ...models.lake import HistoricalPoint, LakeConditions, LakeConfig
from ..base import LakeDataProvider

# api2.cuwcd.gov is the real API; data.cuwcd.gov/datasets/ redirects there.
CUWCD_API_URL = "https://api2.cuwcd.gov/Internal/Historical/ReportDataSets"


class CUWCDProvider(LakeDataProvider):
    """Central Utah Water Conservancy District (CUWCD) provider.

    Uses the CUWCD public data API to fetch current and 30-day historical
    reservoir elevation and percent-full readings.

    Covers: Deer Creek, Jordanelle, Utah Lake (and other CUWCD-managed
    reservoirs). Does not provide water temperature.
    """

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=httpx.Timeout(connect=30.0, read=30.0, write=10.0, pool=10.0),
            follow_redirects=True,
        )

    @property
    def provider_name(self) -> str:
        return "cuwcd"

    def supports_lake(self, lake: LakeConfig) -> bool:
        return lake.conditions_provider == "cuwcd"

    def get_conditions(self, lake: LakeConfig) -> LakeConditions:
        if lake.cuwcd_set_name is None:
            return LakeConditions(
                lake_id=lake.id,
                water_temp_c=None,
                water_level_ft=None,
                water_level_history=[],
                water_temp_history=[],
                data_as_of=None,
                provider_name=self.provider_name,
            )

        current = self._fetch_set(lake.cuwcd_set_name)
        history = self._fetch_set(f"{lake.cuwcd_set_name}_trend")

        level_pct = current.get("pct_full")
        as_of = current.get("as_of")
        pct_history = history.get("pct_full_history", [])

        return LakeConditions(
            lake_id=lake.id,
            water_temp_c=None,
            water_level_ft=None,
            water_level_pct=level_pct,
            water_level_history=pct_history,
            water_temp_history=[],
            data_as_of=as_of,
            provider_name=self.provider_name,
        )

    def get_historical(self, lake: LakeConfig, start_date: "date", end_date: "date") -> dict:
        """Return trend data in the same dict format as USGSProvider.get_historical.
        CUWCD only exposes ~30 days of history via the _trend endpoint."""
        from datetime import date  # noqa: F401 — keep import local
        if lake.cuwcd_set_name is None:
            return {"levels": [], "temps": [], "latest_level_ft": None, "latest_temp_c": None, "as_of": None}
        parsed = self._fetch_set(f"{lake.cuwcd_set_name}_trend")
        levels = parsed.get("pct_full_history", [])
        return {
            "levels": levels,
            "temps": [],
            "latest_level_ft": levels[-1].value if levels else None,
            "latest_temp_c": None,
            "as_of": levels[-1].timestamp if levels else None,
        }

    def _fetch_set(self, set_name: str) -> dict:
        resp = self._client.get(
            f"{CUWCD_API_URL}/{set_name}",
            params={"DisplayType": "JSON", "DateSortAsc": "true"},
        )
        resp.raise_for_status()
        return self._parse(resp.json())

    def _parse(self, data: dict) -> dict:
        pct_full: float | None = None
        as_of: datetime | None = None
        pct_full_history: list[HistoricalPoint] = []

        for group in data.get("ReportDataGroups", []):
            for tag in group.get("Tags", []):
                param = tag.get("Metadata", {}).get("ParameterDescription", "")
                values = tag.get("Values", [])
                if not values:
                    continue

                if param == "Pct Full" and pct_full is None:
                    latest = values[-1]
                    pct_full = float(latest["val"])
                    as_of = datetime.fromisoformat(latest["ts"])
                    pct_full_history = [
                        HistoricalPoint(
                            timestamp=datetime.fromisoformat(v["ts"]),
                            value=float(v["val"]),
                        )
                        for v in values
                        if v.get("val") is not None
                    ]

        return {
            "pct_full": pct_full,
            "as_of": as_of,
            "pct_full_history": pct_full_history,
        }
