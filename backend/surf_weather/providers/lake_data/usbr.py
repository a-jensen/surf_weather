from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from ...models.lake import HistoricalPoint, LakeConditions, LakeConfig
from ..base import LakeDataProvider

USBR_HYDRODATA_URL = "https://www.usbr.gov/uc/water/hydrodata/reservoir_data/{site_id}/json/49.json"
HISTORY_DAYS = 90


class USBRProvider(LakeDataProvider):
    """Bureau of Reclamation Upper Colorado HydroData provider.

    Fetches pool elevation (ft MSL) from the USBR HydroData static JSON files
    at www.usbr.gov/uc/water/hydrodata/reservoir_data/{site_id}/json/49.json.

    Each file contains the full period of record (back to ~1986). Only the
    most recent HISTORY_DAYS days are returned as history; the latest non-null
    entry is used as the current water level.

    Does not provide water temperature.
    """

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=httpx.Timeout(connect=30.0, read=60.0, write=10.0, pool=10.0),
            follow_redirects=True,
        )

    @property
    def provider_name(self) -> str:
        return "usbr"

    def supports_lake(self, lake: LakeConfig) -> bool:
        return lake.conditions_provider == "usbr"

    def get_conditions(self, lake: LakeConfig) -> LakeConditions:
        if lake.usbr_site_id is None:
            return LakeConditions(
                lake_id=lake.id,
                water_temp_c=None,
                water_level_ft=None,
                water_level_history=[],
                water_temp_history=[],
                data_as_of=None,
                provider_name=self.provider_name,
            )

        history = self._fetch_elevation(lake.usbr_site_id)
        current = history[-1].value if history else None
        as_of = history[-1].timestamp if history else None

        return LakeConditions(
            lake_id=lake.id,
            water_temp_c=None,
            water_level_ft=current,
            water_level_history=history,
            water_temp_history=[],
            data_as_of=as_of,
            provider_name=self.provider_name,
        )

    def _fetch_elevation(self, site_id: int) -> list[HistoricalPoint]:
        url = USBR_HYDRODATA_URL.format(site_id=site_id)
        resp = self._client.get(url)
        resp.raise_for_status()
        payload = resp.json()

        cutoff = datetime.now(tz=timezone.utc).date() - timedelta(days=HISTORY_DAYS)

        points: list[HistoricalPoint] = []
        for row in payload.get("data", []):
            date_str, value = row[0], row[1]
            if value is None:
                continue
            row_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if row_date < cutoff:
                continue
            points.append(
                HistoricalPoint(
                    timestamp=datetime(row_date.year, row_date.month, row_date.day, tzinfo=timezone.utc),
                    value=float(value),
                )
            )

        return points
