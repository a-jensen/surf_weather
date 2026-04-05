from __future__ import annotations

from pathlib import Path

import yaml

from .models.lake import LakeConfig

DEFAULT_LAKES_PATH = Path(__file__).parent.parent / "config" / "lakes.yaml"


def load_lakes(path: Path = DEFAULT_LAKES_PATH) -> list[LakeConfig]:
    """Load lake definitions from a YAML file."""
    if not path.exists():
        raise FileNotFoundError(f"Lakes config not found: {path}")

    with path.open() as f:
        data = yaml.safe_load(f)

    return [
        LakeConfig(
            id=entry["id"],
            name=entry["name"],
            state=entry["state"],
            latitude=float(entry["latitude"]),
            longitude=float(entry["longitude"]),
            usgs_site_id=entry.get("usgs_site_id"),
            data_provider=entry["data_provider"],
            cuwcd_set_name=entry.get("cuwcd_set_name"),
            state_park_slug=entry.get("state_park_slug"),
            usgs_level_param=entry.get("usgs_level_param", "00065"),
        )
        for entry in data["lakes"]
    ]
