from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import httpx

from ...models.lake import HistoricalPoint, LakeConditions, LakeConfig
from ..base import LakeDataProvider

USGS_DV_URL = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/daily/items"
PARAM_GAGE_HEIGHT = "00065"
PARAM_WATER_TEMP = "00010"
HISTORY_DAYS = 90
INVALID_VALUES = {"-999999", ""}
MAX_LIMIT = 10000


class USGSProvider(LakeDataProvider):
    """USGS NWIS provider for lakes with registered gauge sites.

    Uses the USGS OGC API daily-values endpoint for both current readings and
    history. The most recent daily value entry is used as the "current" reading.

    A persistent httpx.Client is used so that the TLS session is established
    once and reused across all concurrent lake requests.
    """

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=httpx.Timeout(connect=30.0, read=30.0, write=10.0, pool=10.0),
            follow_redirects=True,
        )

    @property
    def provider_name(self) -> str:
        return "usgs_nwis"

    def supports_lake(self, lake: LakeConfig) -> bool:
        return lake.data_provider == "usgs"

    def get_conditions(self, lake: LakeConfig) -> LakeConditions:
        if lake.usgs_site_id is None:
            return LakeConditions(
                lake_id=lake.id,
                water_temp_c=None,
                water_level_ft=None,
                water_level_history=[],
                water_temp_history=[],
                data_as_of=None,
                provider_name=self.provider_name,
            )

        data = self._fetch_dv(lake.usgs_site_id, level_param=lake.usgs_level_param)

        return LakeConditions(
            lake_id=lake.id,
            water_temp_c=data["latest_temp_c"],
            water_level_ft=data["latest_level_ft"],
            water_level_history=data["levels"],
            water_temp_history=data["temps"],
            data_as_of=data["as_of"],
            provider_name=self.provider_name,
        )

    def get_historical(self, lake: LakeConfig, start_date: date, end_date: date) -> dict:
        """Fetch daily values for an arbitrary date range. Returns keys:
        levels, temps, latest_level_ft, latest_temp_c, as_of."""
        if lake.usgs_site_id is None:
            return {"levels": [], "temps": [], "latest_level_ft": None, "latest_temp_c": None, "as_of": None}
        return self._fetch_dv(lake.usgs_site_id, start_date, end_date, level_param=lake.usgs_level_param)

    def _fetch_dv(
        self,
        site_id: str,
        start: date | None = None,
        end: date | None = None,
        level_param: str = PARAM_GAGE_HEIGHT,
    ) -> dict:
        if end is None:
            end = datetime.now(tz=timezone.utc).date()
        if start is None:
            start = end - timedelta(days=HISTORY_DAYS)

        location_id = f"USGS-{site_id}"
        datetime_range = f"{start.isoformat()}/{end.isoformat()}"

        levels = self._fetch_param(location_id, level_param, datetime_range)
        temps = self._fetch_param(location_id, PARAM_WATER_TEMP, datetime_range)

        latest_level = levels[-1].value if levels else None
        latest_temp = temps[-1].value if temps else None
        as_of = levels[-1].timestamp if levels else (temps[-1].timestamp if temps else None)

        return {
            "levels": levels,
            "temps": temps,
            "latest_level_ft": latest_level,
            "latest_temp_c": latest_temp,
            "as_of": as_of,
        }

    def _fetch_param(self, location_id: str, param_code: str, datetime_range: str) -> list[HistoricalPoint]:
        """Fetch all daily values for one parameter, handling pagination."""
        points: list[HistoricalPoint] = []
        offset = 0

        while True:
            resp = self._client.get(
                USGS_DV_URL,
                params={
                    "monitoring_location_id": location_id,
                    "parameter_code": param_code,
                    "datetime": datetime_range,
                    "statistic_id": "00003",  # mean daily value
                    "limit": MAX_LIMIT,
                    "offset": offset,
                    "f": "json",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            for feature in data.get("features", []):
                props = feature["properties"]
                raw = props.get("value")
                if raw in INVALID_VALUES or raw is None:
                    continue
                points.append(
                    HistoricalPoint(
                        timestamp=datetime.fromisoformat(props["time"]),
                        value=float(raw),
                    )
                )

            returned = data.get("numberReturned", 0)
            if returned < MAX_LIMIT:
                break
            offset += MAX_LIMIT

        return points
