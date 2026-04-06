from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.get("/lakes")
def list_lakes(request: Request) -> list[dict]:
    aggregator = request.app.state.aggregator
    summaries = aggregator.get_all_summaries()
    return [_summary_to_dict(s) for s in summaries]


@router.get("/lakes/{lake_id}")
def get_lake(lake_id: str, request: Request) -> dict:
    aggregator = request.app.state.aggregator
    try:
        detail = aggregator.get_detail(lake_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Lake '{lake_id}' not found")
    return _detail_to_dict(detail)


def _summary_to_dict(s) -> dict:
    return {
        "lake_id": s.lake_id,
        "name": s.name,
        "state": s.state,
        "latitude": s.latitude,
        "longitude": s.longitude,
        "current_water_temp_c": s.current_water_temp_c,
        "current_water_level_ft": s.current_water_level_ft,
        "current_water_level_pct": s.current_water_level_pct,
        "forecast": [_daily_to_dict(d) for d in s.forecast],
    }


def _detail_to_dict(d) -> dict:
    return {
        "lake_id": d.lake_id,
        "name": d.name,
        "state": d.state,
        "latitude": d.latitude,
        "longitude": d.longitude,
        "conditions": _conditions_to_dict(d.conditions),
        "weather": _forecast_to_dict(d.weather),
    }


def _conditions_to_dict(c) -> dict:
    return {
        "lake_id": c.lake_id,
        "water_temp_c": c.water_temp_c,
        "water_level_ft": c.water_level_ft,
        "water_level_pct": c.water_level_pct,
        "water_level_history": [
            {"timestamp": pt.timestamp.isoformat(), "value": pt.value}
            for pt in c.water_level_history
        ],
        "water_temp_history": [
            {"timestamp": pt.timestamp.isoformat(), "value": pt.value}
            for pt in c.water_temp_history
        ],
        "data_as_of": c.data_as_of.isoformat() if c.data_as_of else None,
        "provider_name": c.provider_name,
    }


def _forecast_to_dict(f) -> dict:
    return {
        "lake_id": f.lake_id,
        "timezone": f.timezone,
        "daily": [_daily_to_dict(d) for d in f.daily],
        "hourly": [_hourly_to_dict(h) for h in f.hourly],
        "fetched_at": f.fetched_at,
    }


def _daily_to_dict(d) -> dict:
    return {
        "date": d.date.isoformat(),
        "temp_high_f": d.temp_high_f,
        "temp_low_f": d.temp_low_f,
        "wind_speed_mph": d.wind_speed_mph,
        "wind_direction_deg": d.wind_direction_deg,
        "precip_probability_pct": d.precip_probability_pct,
        "weather_code": d.weather_code,
        "cape_max_jkg": d.cape_max_jkg,
        "has_thunderstorm_risk": d.has_thunderstorm_risk,
    }


def _hourly_to_dict(h) -> dict:
    return {
        "iso_time": h.iso_time,
        "temp_f": h.temp_f,
        "wind_speed_mph": h.wind_speed_mph,
        "wind_direction_deg": h.wind_direction_deg,
        "precip_probability_pct": h.precip_probability_pct,
        "weather_code": h.weather_code,
        "cape_jkg": h.cape_jkg,
    }
