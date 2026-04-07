"""Tests for the Lake Powell water-data.com provider."""
from datetime import datetime, timezone

import httpx
import pytest
import respx

import surf_weather.providers.lake_data.lake_powell as lake_powell_module
from surf_weather.models.lake import LakeConditions, LakeConfig
from surf_weather.providers.lake_data.lake_powell import LAKE_POWELL_URL, LakePowellProvider

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

FIXED_TODAY = datetime(2026, 4, 6, 12, 0, tzinfo=timezone.utc)


def _make_html(
    *,
    last_reading: str = "3528.13",
    pct_full: str = "23.55",
    categories: str = "'Apr 4', 'Apr 5', 'Apr 6'",
    elevations: str = "3528.10, 3528.12, 3528.13",
) -> str:
    """Build a minimal HTML page that looks like lakepowell.water-data.com."""
    return f"""
    <html><body>
    <p><strong>Last Reading: {last_reading} on Sunday, April 5th, 2026</strong></p>
    <p>By content, Lake Powell is <strong>{pct_full}% of Full Pool</strong> (24,322,000 af)</p>
    <script>
    $('#container2').highcharts({{
        xAxis: {{
            categories: [{categories}]
        }},
        series: [
            {{
                type: 'area',
                name: 'Elevation',
                visible: true,
                data: [{elevations}]
            }},
            {{
                name: 'Inflow',
                visible: false,
                data: [9000, 9100, 9200]
            }}
        ]
    }});
    </script>
    </body></html>
    """


@pytest.fixture
def lake_powell() -> LakeConfig:
    return LakeConfig(
        id="lake_powell",
        name="Lake Powell",
        state="UT",
        latitude=37.0579,
        longitude=-111.3051,
        usgs_site_id=None,
        conditions_provider="lake_powell",
    )


@pytest.fixture
def lake_powell_html() -> str:
    return _make_html()


@pytest.fixture
def frozen_datetime(monkeypatch):
    """Freeze datetime.now() inside the provider module to FIXED_TODAY."""

    class _MockDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return FIXED_TODAY

    monkeypatch.setattr(lake_powell_module, "datetime", _MockDatetime)
    return FIXED_TODAY


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLakePowellProvider:
    @pytest.fixture(autouse=True)
    def provider(self):
        self.provider = LakePowellProvider()

    def test_provider_name(self):
        assert self.provider.provider_name == "lake_powell_water_data"

    def test_supports_lake_powell(self, lake_powell):
        assert self.provider.supports_lake(lake_powell) is True

    def test_does_not_support_other_providers(self, fake_lake_with_gauge):
        assert self.provider.supports_lake(fake_lake_with_gauge) is False

    @respx.mock
    def test_returns_lake_conditions_instance(self, lake_powell, lake_powell_html, frozen_datetime):
        respx.get(LAKE_POWELL_URL).mock(return_value=httpx.Response(200, text=lake_powell_html))

        result = self.provider.get_conditions(lake_powell)

        assert isinstance(result, LakeConditions)
        assert result.lake_id == "lake_powell"

    @respx.mock
    def test_parses_current_elevation(self, lake_powell, lake_powell_html, frozen_datetime):
        respx.get(LAKE_POWELL_URL).mock(return_value=httpx.Response(200, text=lake_powell_html))

        result = self.provider.get_conditions(lake_powell)

        assert result.water_level_ft == pytest.approx(3528.13)

    @respx.mock
    def test_parses_pct_full(self, lake_powell, lake_powell_html, frozen_datetime):
        respx.get(LAKE_POWELL_URL).mock(return_value=httpx.Response(200, text=lake_powell_html))

        result = self.provider.get_conditions(lake_powell)

        assert result.water_level_pct == pytest.approx(23.55)

    @respx.mock
    def test_water_temp_is_none(self, lake_powell, lake_powell_html, frozen_datetime):
        """Water temperature is not reliably published by this source."""
        respx.get(LAKE_POWELL_URL).mock(return_value=httpx.Response(200, text=lake_powell_html))

        result = self.provider.get_conditions(lake_powell)

        assert result.water_temp_c is None

    @respx.mock
    def test_parses_elevation_history(self, lake_powell, lake_powell_html, frozen_datetime):
        respx.get(LAKE_POWELL_URL).mock(return_value=httpx.Response(200, text=lake_powell_html))

        result = self.provider.get_conditions(lake_powell)

        assert len(result.water_level_history) == 3
        assert result.water_level_history[0].value == pytest.approx(3528.10)
        assert result.water_level_history[1].value == pytest.approx(3528.12)
        assert result.water_level_history[2].value == pytest.approx(3528.13)

    @respx.mock
    def test_history_dates_are_chronological(self, lake_powell, lake_powell_html, frozen_datetime):
        respx.get(LAKE_POWELL_URL).mock(return_value=httpx.Response(200, text=lake_powell_html))

        result = self.provider.get_conditions(lake_powell)

        timestamps = [p.timestamp for p in result.water_level_history]
        assert timestamps == sorted(timestamps)

    @respx.mock
    def test_history_last_date_matches_last_category(self, lake_powell, lake_powell_html, frozen_datetime):
        """Last history entry should be dated Apr 6, 2026 (the last category = today)."""
        respx.get(LAKE_POWELL_URL).mock(return_value=httpx.Response(200, text=lake_powell_html))

        result = self.provider.get_conditions(lake_powell)

        last = result.water_level_history[-1].timestamp
        assert last == datetime(2026, 4, 6, tzinfo=timezone.utc)

    @respx.mock
    def test_data_as_of_is_set(self, lake_powell, lake_powell_html, frozen_datetime):
        respx.get(LAKE_POWELL_URL).mock(return_value=httpx.Response(200, text=lake_powell_html))

        result = self.provider.get_conditions(lake_powell)

        assert isinstance(result.data_as_of, datetime)

    @respx.mock
    def test_provider_name_in_result(self, lake_powell, lake_powell_html, frozen_datetime):
        respx.get(LAKE_POWELL_URL).mock(return_value=httpx.Response(200, text=lake_powell_html))

        result = self.provider.get_conditions(lake_powell)

        assert result.provider_name == "lake_powell_water_data"

    @respx.mock
    def test_missing_elevation_returns_none(self, lake_powell, frozen_datetime):
        html = _make_html(last_reading="")
        respx.get(LAKE_POWELL_URL).mock(return_value=httpx.Response(200, text=html))

        result = self.provider.get_conditions(lake_powell)

        assert result.water_level_ft is None

    @respx.mock
    def test_missing_pct_full_returns_none(self, lake_powell, frozen_datetime):
        html = "<html><body><strong>Last Reading: 3528.13 on Sunday</strong></body></html>"
        respx.get(LAKE_POWELL_URL).mock(return_value=httpx.Response(200, text=html))

        result = self.provider.get_conditions(lake_powell)

        assert result.water_level_pct is None

    @respx.mock
    def test_missing_highcharts_data_returns_empty_history(self, lake_powell, frozen_datetime):
        html = "<html><body><strong>Last Reading: 3528.13 on Sunday</strong><strong>23.55% of Full Pool</strong></body></html>"
        respx.get(LAKE_POWELL_URL).mock(return_value=httpx.Response(200, text=html))

        result = self.provider.get_conditions(lake_powell)

        assert result.water_level_history == []
        assert result.data_as_of is None

    @respx.mock
    def test_raises_on_http_error(self, lake_powell):
        respx.get(LAKE_POWELL_URL).mock(return_value=httpx.Response(503))

        with pytest.raises(httpx.HTTPStatusError):
            self.provider.get_conditions(lake_powell)


class TestReconstructDates:
    """Unit tests for _reconstruct_dates independent of HTTP."""

    def test_three_consecutive_days(self, frozen_datetime):
        # 'Apr 4', 'Apr 5', 'Apr 6' — last entry is today (Apr 6, 2026)
        dates = LakePowellProvider._reconstruct_dates(["Apr 4", "Apr 5", "Apr 6"])

        assert len(dates) == 3
        assert dates[0] == datetime(2026, 4, 4, tzinfo=timezone.utc)
        assert dates[1] == datetime(2026, 4, 5, tzinfo=timezone.utc)
        assert dates[2] == datetime(2026, 4, 6, tzinfo=timezone.utc)

    def test_year_rollover(self, monkeypatch):
        # Set "today" to Jan 10 so that a window ending Jan 5 (5 days ago) is in range.
        # This exercises the path where early entries fall in the prior calendar year.
        fixed = datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc)

        class _MockDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return fixed

        monkeypatch.setattr(lake_powell_module, "datetime", _MockDatetime)

        from datetime import date, timedelta

        end = date(2026, 1, 5)
        n = 100
        cats = [(end - timedelta(days=(n - 1 - i))).strftime("%b %-d") for i in range(n)]

        dates = LakePowellProvider._reconstruct_dates(cats)

        # Jan 5, 2026 − 99 days = Sep 28, 2025 (spans the Dec 31 → Jan 1 rollover)
        assert dates[0] == datetime(2025, 9, 28, tzinfo=timezone.utc)
        assert dates[-1] == datetime(2026, 1, 5, tzinfo=timezone.utc)

    def test_single_entry(self, frozen_datetime):
        dates = LakePowellProvider._reconstruct_dates(["Apr 6"])

        assert len(dates) == 1
        assert dates[0] == datetime(2026, 4, 6, tzinfo=timezone.utc)


class TestParseHelpers:
    """Direct tests for the static parsing methods."""

    def test_parse_elevation_standard(self):
        html = "<strong>Last Reading: 3528.13 on Sunday, April 5th, 2026</strong>"
        assert LakePowellProvider._parse_current_elevation(html) == pytest.approx(3528.13)

    def test_parse_elevation_missing(self):
        assert LakePowellProvider._parse_current_elevation("<html></html>") is None

    def test_parse_pct_full_standard(self):
        html = "Lake Powell is <strong>23.55% of Full Pool</strong>"
        assert LakePowellProvider._parse_pct_full(html) == pytest.approx(23.55)

    def test_parse_pct_full_integer(self):
        html = "Lake Powell is <strong>100% of Full Pool</strong>"
        assert LakePowellProvider._parse_pct_full(html) == pytest.approx(100.0)

    def test_parse_pct_full_missing(self):
        assert LakePowellProvider._parse_pct_full("<html></html>") is None
