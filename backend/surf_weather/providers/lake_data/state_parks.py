from __future__ import annotations

import re
from datetime import datetime, timezone

import httpx

from ...models.lake import LakeConditions, LakeConfig
from ..base import LakeDataProvider

STATE_PARKS_BASE = "https://stateparks.utah.gov/parks"

# Matches: Water Temp:</span>45° F  or  Water Temp:</span>45.5° F
_TEMP_RE = re.compile(
    r'class="feeditem watertemp"[^>]*>.*?<span>[^<]*</span>\s*([\d.]+)\s*(?:°|&deg;)\s*F',
    re.DOTALL | re.IGNORECASE,
)
# Matches: Water Level:</span>87.2%
_LEVEL_RE = re.compile(
    r'class="feeditem waterlevel"[^>]*>.*?<span>[^<]*</span>\s*([\d.]+)\s*%',
    re.DOTALL | re.IGNORECASE,
)


def _f_to_c(f: float) -> float:
    return (f - 32) * 5 / 9


class StateParksProvider(LakeDataProvider):
    """Utah State Parks current-conditions page scraper.

    Parses water temperature (°F → °C) and water level (% full) from the
    WordPress widget rendered server-side on each park's current-conditions page.

    Note: data is manually updated by park staff and may be days old.
    """

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=httpx.Timeout(connect=30.0, read=30.0, write=10.0, pool=10.0),
            follow_redirects=True,
            headers={"User-Agent": "surf-weather/1.0 (reservoir data aggregator)"},
        )

    @property
    def provider_name(self) -> str:
        return "ut_state_parks"

    def supports_lake(self, lake: LakeConfig) -> bool:
        return lake.data_provider == "state_parks"

    def get_conditions(self, lake: LakeConfig) -> LakeConditions:
        slug = lake.state_park_slug
        if slug is None:
            return LakeConditions(
                lake_id=lake.id,
                water_temp_c=None,
                water_level_ft=None,
                water_level_history=[],
                water_temp_history=[],
                data_as_of=None,
                provider_name=self.provider_name,
            )

        url = f"{STATE_PARKS_BASE}/{slug}/current-conditions/"
        resp = self._client.get(url)
        resp.raise_for_status()
        html = resp.text

        temp_c = self._parse_temp(html)
        level_pct = self._parse_level(html)

        as_of = datetime.now(tz=timezone.utc) if (temp_c is not None or level_pct is not None) else None

        return LakeConditions(
            lake_id=lake.id,
            water_temp_c=temp_c,
            water_level_ft=None,
            water_level_pct=level_pct,
            water_level_history=[],
            water_temp_history=[],
            data_as_of=as_of,
            provider_name=self.provider_name,
        )

    @staticmethod
    def _parse_temp(html: str) -> float | None:
        m = _TEMP_RE.search(html)
        if m:
            return round(_f_to_c(float(m.group(1))), 2)
        return None

    @staticmethod
    def _parse_level(html: str) -> float | None:
        m = _LEVEL_RE.search(html)
        if m:
            return float(m.group(1))
        return None
