"""Tests for the lake_data CLI script."""
import sys
from pathlib import Path

import httpx
import pytest
import respx
from click.testing import CliRunner

# The script lives outside the package; make it importable.
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from lake_data import main  # noqa: E402

from surf_weather.providers.lake_data.cuwcd import CUWCD_API_URL
from surf_weather.providers.lake_data.state_parks import STATE_PARKS_BASE


DEER_CREEK_CURRENT_URL = f"{CUWCD_API_URL}/public_dc"
DEER_CREEK_TREND_URL = f"{CUWCD_API_URL}/public_dc_trend"
DEER_CREEK_STATE_PARKS_URL = f"{STATE_PARKS_BASE}/deer-creek/current-conditions/"
EAST_CANYON_URL = f"{STATE_PARKS_BASE}/east-canyon/current-conditions/"


@pytest.fixture
def runner():
    return CliRunner()


def mock_deer_creek_state_parks(state_parks_html: str) -> None:
    """Mock the State Parks current-conditions page for deer_creek."""
    respx.get(DEER_CREEK_STATE_PARKS_URL).mock(
        return_value=httpx.Response(200, text=state_parks_html)
    )


def mock_deer_creek_cuwcd(current_fixture: dict, trend_fixture: dict) -> None:
    """Mock CUWCD endpoints for deer_creek (used for history)."""
    respx.get(DEER_CREEK_CURRENT_URL).mock(return_value=httpx.Response(200, json=current_fixture))
    respx.get(DEER_CREEK_TREND_URL).mock(return_value=httpx.Response(200, json=trend_fixture))


class TestLakeDataScriptCurrent:
    """Default mode: display current conditions for deer_creek (state_parks provider)."""

    @respx.mock
    def test_shows_lake_name(self, runner, state_parks_html):
        mock_deer_creek_state_parks(state_parks_html)

        result = runner.invoke(main, ["deer_creek"])

        assert result.exit_code == 0, result.output
        assert "Deer Creek" in result.output

    @respx.mock
    def test_shows_pct_full_for_deer_creek(self, runner, state_parks_html):
        mock_deer_creek_state_parks(state_parks_html)

        result = runner.invoke(main, ["deer_creek"])

        assert result.exit_code == 0, result.output
        assert "77" in result.output
        assert "%" in result.output

    @respx.mock
    def test_shows_water_temperature_for_deer_creek(self, runner, state_parks_html):
        """State Parks provider returns temperature for deer_creek."""
        mock_deer_creek_state_parks(state_parks_html)

        result = runner.invoke(main, ["deer_creek"])

        assert result.exit_code == 0, result.output
        # 52°F → 11.11°C
        assert "11.1" in result.output

    @respx.mock
    def test_shows_pct_full_for_east_canyon(self, runner, state_parks_html):
        """State Parks provider (east_canyon) shows % full."""
        respx.get(EAST_CANYON_URL).mock(return_value=httpx.Response(200, text=state_parks_html))

        result = runner.invoke(main, ["east_canyon"])

        assert result.exit_code == 0, result.output
        assert "77" in result.output
        assert "%" in result.output

    @respx.mock
    def test_shows_water_temperature_from_state_parks(self, runner, state_parks_html):
        """State Parks provider returns temperature."""
        respx.get(EAST_CANYON_URL).mock(return_value=httpx.Response(200, text=state_parks_html))

        result = runner.invoke(main, ["east_canyon"])

        assert result.exit_code == 0, result.output
        # 52°F → 11.11°C
        assert "11.1" in result.output

    @respx.mock
    def test_shows_provider_name_state_parks(self, runner, state_parks_html):
        mock_deer_creek_state_parks(state_parks_html)

        result = runner.invoke(main, ["deer_creek"])

        assert result.exit_code == 0, result.output
        assert "state_parks" in result.output.lower() or "ut_state_parks" in result.output.lower()

    @respx.mock
    def test_shows_data_as_of(self, runner, state_parks_html):
        mock_deer_creek_state_parks(state_parks_html)

        result = runner.invoke(main, ["deer_creek"])

        assert result.exit_code == 0, result.output
        # State Parks as_of is set to datetime.now() when data is parsed — just check a year
        assert "202" in result.output


class TestLakeDataScriptErrors:
    """Error handling and edge cases."""

    def test_unknown_lake_exits_nonzero(self, runner):
        result = runner.invoke(main, ["no_such_lake"])

        assert result.exit_code != 0
        assert "no_such_lake" in result.output

    def test_list_lakes_shows_deer_creek(self, runner):
        result = runner.invoke(main, ["--list-lakes", "deer_creek"])

        assert result.exit_code == 0
        assert "deer_creek" in result.output
        assert "Deer Creek" in result.output

    def test_list_lakes_shows_all_configured_lakes(self, runner):
        result = runner.invoke(main, ["--list-lakes", "deer_creek"])

        assert result.exit_code == 0
        for lake_id in ("deer_creek", "pineview", "east_canyon", "rockport", "echo"):
            assert lake_id in result.output

    @respx.mock
    def test_http_error_propagates(self, runner):
        respx.get(DEER_CREEK_STATE_PARKS_URL).mock(return_value=httpx.Response(503))

        result = runner.invoke(main, ["deer_creek"])

        assert result.exit_code != 0


pytest.importorskip("matplotlib", reason="matplotlib not installed")
import matplotlib.pyplot  # noqa: E402


class TestLakeDataScriptPlot:
    """Plot mode — matplotlib.pyplot.show is patched to prevent a window opening.
    deer_creek has history_provider=cuwcd, so the CUWCD trend endpoint is used for -p.
    """

    @respx.mock
    def test_plot_flag_runs_without_error(self, runner, cuwcd_trend_fixture, monkeypatch):
        respx.get(DEER_CREEK_TREND_URL).mock(return_value=httpx.Response(200, json=cuwcd_trend_fixture))
        monkeypatch.setattr(matplotlib.pyplot, "show", lambda: None)  # prevent window

        result = runner.invoke(main, ["deer_creek", "-p", "--years", "1"])

        assert result.exit_code == 0, result.output

    @respx.mock
    def test_plot_mentions_lake_name(self, runner, cuwcd_trend_fixture, monkeypatch):
        respx.get(DEER_CREEK_TREND_URL).mock(return_value=httpx.Response(200, json=cuwcd_trend_fixture))
        monkeypatch.setattr(matplotlib.pyplot, "show", lambda: None)  # prevent window

        result = runner.invoke(main, ["deer_creek", "-p", "--years", "1"])

        assert "Deer Creek" in result.output
