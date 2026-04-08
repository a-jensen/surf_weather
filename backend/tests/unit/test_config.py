"""Tests for config loader."""
import tempfile
from pathlib import Path

import pytest
import yaml

from surf_weather.config import load_lakes
from surf_weather.models.lake import LakeConfig


SAMPLE_YAML = """
lakes:
  - id: deer_creek
    name: Deer Creek Reservoir
    state: UT
    latitude: 40.4083
    longitude: -111.5297
    usgs_site_id: "10159000"
    conditions_provider: usgs
  - id: jordanelle
    name: Jordanelle Reservoir
    state: UT
    latitude: 40.6097
    longitude: -111.4203
    usgs_site_id: null
    conditions_provider: usgs
"""


class TestLoadLakes:
    def _write_yaml(self, content: str) -> Path:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        tmp.write(content)
        tmp.close()
        return Path(tmp.name)

    def test_loads_list_of_lake_configs(self):
        path = self._write_yaml(SAMPLE_YAML)
        lakes = load_lakes(path)
        assert len(lakes) == 2

    def test_returns_lake_config_instances(self):
        path = self._write_yaml(SAMPLE_YAML)
        lakes = load_lakes(path)
        assert all(isinstance(lake, LakeConfig) for lake in lakes)

    def test_parses_id_and_name(self):
        path = self._write_yaml(SAMPLE_YAML)
        lakes = load_lakes(path)
        assert lakes[0].id == "deer_creek"
        assert lakes[0].name == "Deer Creek Reservoir"

    def test_parses_coordinates(self):
        path = self._write_yaml(SAMPLE_YAML)
        lakes = load_lakes(path)
        assert lakes[0].latitude == pytest.approx(40.4083)
        assert lakes[0].longitude == pytest.approx(-111.5297)

    def test_parses_usgs_site_id(self):
        path = self._write_yaml(SAMPLE_YAML)
        lakes = load_lakes(path)
        assert lakes[0].usgs_site_id == "10159000"

    def test_parses_null_usgs_site_id(self):
        path = self._write_yaml(SAMPLE_YAML)
        lakes = load_lakes(path)
        assert lakes[1].usgs_site_id is None

    def test_parses_state(self):
        path = self._write_yaml(SAMPLE_YAML)
        lakes = load_lakes(path)
        assert lakes[0].state == "UT"

    def test_parses_conditions_provider(self):
        path = self._write_yaml(SAMPLE_YAML)
        lakes = load_lakes(path)
        assert lakes[0].conditions_provider == "usgs"

    def test_parses_history_provider_defaults_to_none(self):
        path = self._write_yaml(SAMPLE_YAML)
        lakes = load_lakes(path)
        assert lakes[0].history_provider is None

    def test_raises_on_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_lakes(Path("/nonexistent/path.yaml"))

    def test_parses_history_provider_when_set(self):
        yaml_with_history = SAMPLE_YAML.replace(
            "conditions_provider: usgs\n  - id: jordanelle",
            "conditions_provider: usgs\n    history_provider: cuwcd\n  - id: jordanelle",
        )
        path = self._write_yaml(yaml_with_history)
        lakes = load_lakes(path)
        assert lakes[0].history_provider == "cuwcd"

    def test_loads_actual_lakes_yaml(self):
        actual = Path(__file__).parent.parent.parent / "config" / "lakes.yaml"
        lakes = load_lakes(actual)
        assert len(lakes) == 10
        ids = {lake.id for lake in lakes}
        assert "deer_creek" in ids
        assert "jordanelle" in ids

    def test_actual_deer_creek_has_history_provider(self):
        actual = Path(__file__).parent.parent.parent / "config" / "lakes.yaml"
        lakes = load_lakes(actual)
        deer_creek = next(l for l in lakes if l.id == "deer_creek")
        assert deer_creek.history_provider == "usbr"
        assert deer_creek.conditions_provider == "state_parks"
