from pathlib import Path

import cv2
import numpy as np

from wows_assistant.capture.directory import DirectoryFrameSource


def test_directory_source_reads_images_in_name_order(tmp_path: Path) -> None:
    image = np.zeros((24, 32, 3), dtype=np.uint8)
    assert cv2.imwrite(str(tmp_path / "b.png"), image)
    assert cv2.imwrite(str(tmp_path / "A.png"), image)
    (tmp_path / "ignored.txt").write_text("ignored", encoding="utf-8")

    frames = list(DirectoryFrameSource(tmp_path))

    assert [Path(frame.ref.source).name for frame in frames] == ["A.png", "b.png"]
    assert [frame.ref.frame_id for frame in frames] == [0, 1]
    assert frames[0].image.shape == (24, 32, 3)

