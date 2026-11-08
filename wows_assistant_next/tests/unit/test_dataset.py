from pathlib import Path

from wows_assistant.dataset import DatasetManifest, DatasetSample
from wows_assistant.models import Scene


def test_manifest_round_trip_and_missing_file_check(tmp_path: Path) -> None:
    samples = tmp_path / "samples"
    samples.mkdir()
    (samples / "exists.png").touch()
    manifest_path = tmp_path / "manifest.yaml"
    manifest = DatasetManifest(
        name="test",
        root="samples",
        samples=[
            DatasetSample(path="exists.png", scene=Scene.PORT),
            DatasetSample(path="missing.png", scene=Scene.BATTLE),
        ],
    )
    manifest.save(manifest_path)

    loaded = DatasetManifest.load(manifest_path)
    assert loaded == manifest
    assert loaded.validate_files(manifest_path) == [samples / "missing.png"]

