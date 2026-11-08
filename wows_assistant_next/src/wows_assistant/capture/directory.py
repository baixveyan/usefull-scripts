from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import cv2

from wows_assistant.models import FrameRef, ImageFrame, utc_from_timestamp

SUPPORTED_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".bmp", ".webp"})


class DirectoryFrameSource:
    """Deterministic offline frame source ordered by case-insensitive filename."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        if not self.directory.is_dir():
            raise NotADirectoryError(self.directory)

    def paths(self) -> list[Path]:
        return sorted(
            (
                path
                for path in self.directory.iterdir()
                if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
            ),
            key=lambda path: path.name.casefold(),
        )

    def __iter__(self) -> Iterator[ImageFrame]:
        for frame_id, path in enumerate(self.paths()):
            image = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError(f"无法读取图片: {path}")
            height, width = image.shape[:2]
            ref = FrameRef(
                frame_id=frame_id,
                timestamp=utc_from_timestamp(path.stat().st_mtime),
                source=str(path.resolve()),
                width=width,
                height=height,
            )
            yield ImageFrame(ref, image)

