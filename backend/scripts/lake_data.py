#!/usr/bin/env python3
"""CLI script to fetch and display lake data from a LakeDataProvider."""
from __future__ import annotations

import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import click

# Allow running from the backend directory without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from surf_weather.config import load_lakes
from surf_weather.models.lake import LakeConfig
from surf_weather.providers.lake_data.cuwcd import CUWCDProvider
from surf_weather.providers.lake_data.registry import LakeDataProviderRegistry
from surf_weather.providers.lake_data.state_parks import StateParksProvider
from surf_weather.providers.lake_data.usgs import USGSProvider


def build_registry() -> LakeDataProviderRegistry:
    registry = LakeDataProviderRegistry()
    registry.register(CUWCDProvider())
    registry.register(StateParksProvider())
    registry.register(USGSProvider())
    return registry


def c_to_f(c: float) -> float:
    return c * 9 / 5 + 32


@click.command()
@click.argument("lake_id")
@click.option(
    "-p",
    "--plot",
    is_flag=True,
    default=False,
    help="Plot historical temperature and lake level instead of showing current conditions.",
)
@click.option(
    "--years",
    default=10,
    show_default=True,
    type=click.IntRange(1, 50),
    help="Number of past years to include in the plot (ignored without -p).",
)
@click.option(
    "--list-lakes",
    is_flag=True,
    default=False,
    help="List available lake IDs and exit.",
)
def main(lake_id: str, plot: bool, years: int, list_lakes: bool) -> None:
    """Fetch lake data for LAKE_ID.

    LAKE_ID is the lake identifier from lakes.yaml (e.g. deer_creek, pineview).
    Pass --list-lakes to see all available IDs.
    """
    lakes = load_lakes()
    lakes_by_id = {l.id: l for l in lakes}

    if list_lakes:
        click.echo("Available lakes:")
        for l in lakes:
            history = f"+{l.history_provider}" if l.history_provider else ""
            click.echo(f"  {l.id:20s}  {l.name}  [{l.conditions_provider}{history}]")
        return

    if lake_id not in lakes_by_id:
        available = ", ".join(lakes_by_id.keys())
        raise click.BadParameter(
            f"Unknown lake '{lake_id}'. Available: {available}", param_hint="LAKE_ID"
        )

    lake: LakeConfig = lakes_by_id[lake_id]
    registry = build_registry()

    try:
        registry.get_provider(lake)
    except ValueError as e:
        raise click.ClickException(str(e))

    if plot:
        _plot_historical(lake, registry, years)
    else:
        _show_current(lake, registry)


def _show_current(lake: LakeConfig, registry: LakeDataProviderRegistry) -> None:
    provider = registry.get_provider(lake)
    click.echo(f"Fetching current conditions for {lake.name} via {provider.provider_name}…")
    conditions = provider.get_conditions(lake)

    click.echo(f"\n{'='*40}")
    click.echo(f"  {lake.name}")
    click.echo(f"{'='*40}")

    if conditions.water_temp_c is not None:
        click.echo(f"  Water temperature : {conditions.water_temp_c:.1f} °C  ({c_to_f(conditions.water_temp_c):.1f} °F)")
    else:
        click.echo("  Water temperature : N/A")

    if conditions.water_level_ft is not None:
        click.echo(f"  Water level       : {conditions.water_level_ft:.2f} ft")
    elif conditions.water_level_pct is not None:
        click.echo(f"  Water level       : {conditions.water_level_pct:.1f}% full")
    else:
        click.echo("  Water level       : N/A")

    if conditions.data_as_of:
        click.echo(f"  Data as of        : {conditions.data_as_of.strftime('%Y-%m-%d %H:%M')}")

    click.echo(f"  Provider          : {conditions.provider_name}")


def _plot_historical(lake: LakeConfig, registry: LakeDataProviderRegistry, years: int) -> None:
    try:
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
    except ImportError:
        raise click.ClickException(
            "matplotlib is required for plotting. Install it with: pip install matplotlib"
        )

    # Prefer the dedicated history_provider; fall back to the conditions provider
    provider = registry.get_history_provider(lake) or registry.get_provider(lake)

    # Only USGS and CUWCD support multi-year historical fetches
    if not isinstance(provider, (USGSProvider, CUWCDProvider)):
        raise click.ClickException(
            f"Historical plotting is not supported for the '{provider.provider_name}' provider."
        )

    today = date.today()
    current_year = today.year
    target_years = list(range(current_year - years + 1, current_year + 1))

    click.echo(f"Fetching {years} years of history for {lake.name}…")

    start = date(target_years[0], 1, 1)
    end = date(current_year, 12, 31)
    data = provider.get_historical(lake, start, end)

    levels = data["levels"]
    temps = data["temps"]

    if not levels and not temps:
        click.echo("No historical data returned for the requested range.")
        return

    # Determine if data spans the requested range — CUWCD only returns ~30 days
    # regardless of start/end, so warn and fall back to a raw time-series plot.
    all_points = levels + temps
    timestamps = [pt.timestamp for pt in all_points]
    span_days = (max(timestamps) - min(timestamps)).days
    requested_days = years * 365

    if span_days < 60:
        if requested_days > span_days + 7:
            click.echo(
                f"Warning: requested {years} year(s) of data but the "
                f"'{provider.provider_name}' provider only has ~{span_days} days available. "
                "Showing available data as a time series."
            )
        _plot_time_series(lake, levels, temps, plt, mticker)
    else:
        _plot_year_over_year(lake, levels, temps, target_years, years, plt, mticker)


def _plot_time_series(lake: LakeConfig, levels, temps, plt, mticker) -> None:
    """Raw daily time-series plot — used when data window is too short for year-over-year."""
    import matplotlib.dates as mdates

    date_range = (
        f"{min(pt.timestamp for pt in levels + temps).strftime('%b %d, %Y')}"
        f" – {max(pt.timestamp for pt in levels + temps).strftime('%b %d, %Y')}"
    )
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    fig.suptitle(f"{lake.name} — {date_range}", fontsize=14)
    ax_temp, ax_level = axes

    has_temp = bool(temps)
    has_level = bool(levels)

    if has_temp:
        xs = [pt.timestamp for pt in temps]
        ys = [c_to_f(pt.value) for pt in temps]
        ax_temp.plot(xs, ys, marker="o", markersize=3, color="tab:red")

    if has_level:
        xs = [pt.timestamp for pt in levels]
        ys = [pt.value for pt in levels]
        ax_level.plot(xs, ys, marker="o", markersize=3, color="tab:blue")

    level_unit = "% Full" if isinstance(levels[0].value, float) and levels and levels[0].value <= 100 else "ft"

    ax_temp.set_ylabel("Water Temperature (°F)")
    ax_temp.grid(True, alpha=0.3)
    ax_level.set_ylabel(f"Water Level ({level_unit})")
    ax_level.grid(True, alpha=0.3)
    ax_level.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax_level.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()

    if not has_temp and not has_level:
        click.echo("No historical data returned for the requested range.")
        plt.close(fig)
        return

    plt.tight_layout()
    plt.show()


def _plot_year_over_year(lake: LakeConfig, levels, temps, target_years, years, plt, mticker) -> None:
    """Year-over-year monthly averages — used when multiple years of data are available."""
    from collections import defaultdict as _dd

    level_by_year_month: dict[int, dict[int, list[float]]] = _dd(lambda: _dd(list))
    temp_by_year_month: dict[int, dict[int, list[float]]] = _dd(lambda: _dd(list))

    for pt in levels:
        if pt.timestamp.year in target_years:
            level_by_year_month[pt.timestamp.year][pt.timestamp.month].append(pt.value)

    for pt in temps:
        if pt.timestamp.year in target_years:
            temp_by_year_month[pt.timestamp.year][pt.timestamp.month].append(pt.value)

    months = list(range(1, 13))
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    colormap = plt.cm.tab20
    colors = [colormap(i / max(len(target_years) - 1, 1)) for i in range(len(target_years))]

    fig, (ax_temp, ax_level) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    fig.suptitle(f"{lake.name} — Historical Data ({target_years[0]}–{target_years[-1]})", fontsize=14)

    has_temp = False
    has_level = False

    for i, year in enumerate(target_years):
        color = colors[i]
        label = str(year)

        temp_vals = [
            c_to_f(sum(temp_by_year_month[year][m]) / len(temp_by_year_month[year][m]))
            if temp_by_year_month[year][m] else None
            for m in months
        ]
        if any(v is not None for v in temp_vals):
            xs = [m for m, v in zip(months, temp_vals) if v is not None]
            ys = [v for v in temp_vals if v is not None]
            ax_temp.plot(xs, ys, marker="o", markersize=3, color=color, label=label)
            has_temp = True

        level_vals = [
            sum(level_by_year_month[year][m]) / len(level_by_year_month[year][m])
            if level_by_year_month[year][m] else None
            for m in months
        ]
        if any(v is not None for v in level_vals):
            xs = [m for m, v in zip(months, level_vals) if v is not None]
            ys = [v for v in level_vals if v is not None]
            ax_level.plot(xs, ys, marker="o", markersize=3, color=color, label=label)
            has_level = True

    ax_temp.set_ylabel("Water Temperature (°F)")
    ax_temp.grid(True, alpha=0.3)
    if has_temp:
        ax_temp.legend(loc="upper right", fontsize=8, ncol=max(1, years // 5))

    ax_level.set_ylabel("Water Level (ft)")
    ax_level.set_xlabel("Month")
    ax_level.grid(True, alpha=0.3)
    ax_level.xaxis.set_major_locator(mticker.FixedLocator(months))
    ax_level.xaxis.set_major_formatter(mticker.FixedFormatter(month_labels))
    if has_level:
        ax_level.legend(loc="upper right", fontsize=8, ncol=max(1, years // 5))

    if not has_temp and not has_level:
        click.echo("No historical data returned for the requested range.")
        plt.close(fig)
        return

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
