from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import httpx

from ...models.lake import HistoricalPoint, LakeConditions, LakeConfig
from ..base import LakeDataProvider

LAKE_POWELL_URL = "https://lakepowell.water-data.com/"

# Current elevation: <strong>Last Reading: 3528.13 on ...</strong>
_LAST_READING_RE = re.compile(r"Last Reading:\s*([\d.]+)")
# Percent full: "Lake Powell is <strong>23.55% of Full Pool</strong>"
_PCT_FULL_RE = re.compile(r"([\d.]+)%\s+of\s+Full\s+Pool")
# Highcharts xAxis categories: categories: ['Apr 7', 'Apr 8', ...]
_CATEGORIES_RE = re.compile(r"categories:\s*\[([^\]]+)\]")
# Highcharts Elevation series data array
_ELEVATION_SERIES_RE = re.compile(
    r"""name:\s*['"]Elevation['"].*?data:\s*\[([^\]]+)\]""",
    re.DOTALL,
)


class LakePowellProvider(LakeDataProvider):
    """Lake Powell water level provider.

    Scrapes https://lakepowell.water-data.com/ for current elevation (feet MSL),
    percent full, and 365-day historical elevation embedded in Highcharts JS.
    Water temperature is not reliably available from this source.
    """

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=httpx.Timeout(connect=30.0, read=30.0, write=10.0, pool=10.0),
            follow_redirects=True,
            headers={"User-Agent": "surf-weather/1.0 (reservoir data aggregator)"},
        )

    @property
    def provider_name(self) -> str:
        return "lake_powell_water_data"

    def supports_lake(self, lake: LakeConfig) -> bool:
        return lake.conditions_provider == "lake_powell"

    def get_conditions(self, lake: LakeConfig) -> LakeConditions:
        resp = self._client.get(LAKE_POWELL_URL)
        resp.raise_for_status()
        html = resp.text

        elevation = self._parse_current_elevation(html)
        pct_full = self._parse_pct_full(html)
        history = self._parse_history(html)
        as_of = history[-1].timestamp if history else None

        return LakeConditions(
            lake_id=lake.id,
            water_temp_c=None,
            water_level_ft=elevation,
            water_level_pct=pct_full,
            water_level_history=history,
            water_temp_history=[],
            data_as_of=as_of,
            provider_name=self.provider_name,
        )

    @staticmethod
    def _parse_current_elevation(html: str) -> float | None:
        m = _LAST_READING_RE.search(html)
        return float(m.group(1)) if m else None

    @staticmethod
    def _parse_pct_full(html: str) -> float | None:
        m = _PCT_FULL_RE.search(html)
        return float(m.group(1)) if m else None

    @staticmethod
    def _parse_history(html: str) -> list[HistoricalPoint]:
        cat_m = _CATEGORIES_RE.search(html)
        elev_m = _ELEVATION_SERIES_RE.search(html)
        if not cat_m or not elev_m:
            return []

        categories = [s.strip().strip("'\"") for s in cat_m.group(1).split(",")]

        try:
            elevations = [float(v.strip()) for v in elev_m.group(1).split(",") if v.strip()]
        except ValueError:
            return []

        if not categories or not elevations:
            return []

        dates = LakePowellProvider._reconstruct_dates(categories)
        return [
            HistoricalPoint(timestamp=dates[i], value=elevations[i])
            for i in range(min(len(dates), len(elevations)))
        ]

    @staticmethod
    def _reconstruct_dates(categories: list[str]) -> list[datetime]:
        """Map 'Mon Day' category strings to datetimes for a rolling 12-month window.

        The site serves the past 365 days ending approximately yesterday. We find
        the year of the last entry by checking which year puts it within 10 days
        of today, then work backwards for all earlier entries.
        """
        today = datetime.now(tz=timezone.utc).date()
        last_str = categories[-1].strip()

        last_date = None
        for year_offset in [0, -1]:
            year = today.year + year_offset
            try:
                candidate = datetime.strptime(f"{last_str} {year}", "%b %d %Y").date()
                if (today - candidate).days <= 10:
                    last_date = candidate
                    break
            except ValueError:
                continue

        if last_date is None:
            last_date = today - timedelta(days=1)

        n = len(categories)
        result = []
        for i in range(n):
            d = last_date - timedelta(days=(n - 1 - i))
            result.append(datetime(d.year, d.month, d.day, tzinfo=timezone.utc))
        return result
