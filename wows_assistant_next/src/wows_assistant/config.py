from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class NavigationConfig:
    map_x_ratio: float = 0.65
    map_y_ratio: float = 0.75

    @classmethod
    def load(cls, path: str | Path) -> NavigationConfig:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        navigation = data.get("navigation", {})
        config = cls(
            map_x_ratio=float(navigation.get("map_x_ratio", cls.map_x_ratio)),
            map_y_ratio=float(navigation.get("map_y_ratio", cls.map_y_ratio)),
        )
        if not (0.0 < config.map_x_ratio < 1.0 and 0.0 < config.map_y_ratio < 1.0):
            raise ValueError("地图导航坐标比例必须位于 0 和 1 之间")
        return config
