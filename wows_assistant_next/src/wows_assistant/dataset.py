from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from wows_assistant.models import Scene


class DatasetSample(BaseModel):
    path: str
    scene: Scene = Scene.UNKNOWN
    tags: list[str] = Field(default_factory=list)
    note: str = ""


class DatasetManifest(BaseModel):
    schema_version: int = 1
    name: str
    root: str = "."
    samples: list[DatasetSample] = Field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path) -> DatasetManifest:
        manifest_path = Path(path)
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        return cls.model_validate(data)

    def save(self, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump(mode="json")
        output.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def validate_files(self, manifest_path: str | Path) -> list[Path]:
        base = Path(manifest_path).resolve().parent / self.root
        return [base / sample.path for sample in self.samples if not (base / sample.path).is_file()]

