from pathlib import Path

import pytest

from wows_assistant.config import NavigationConfig


def test_navigation_config_loads_ratios(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("navigation:\n  map_x_ratio: 0.4\n  map_y_ratio: 0.8\n", encoding="utf-8")
    assert NavigationConfig.load(path) == NavigationConfig(0.4, 0.8)


def test_navigation_config_rejects_edge_ratio(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("navigation:\n  map_x_ratio: 0\n  map_y_ratio: 0.75\n", encoding="utf-8")
    with pytest.raises(ValueError):
        NavigationConfig.load(path)


def test_navigation_config_defaults_to_right_lower_target(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("{}\n", encoding="utf-8")
    assert NavigationConfig.load(path) == NavigationConfig(0.65, 0.75)
