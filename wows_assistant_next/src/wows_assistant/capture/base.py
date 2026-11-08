from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from wows_assistant.models import ImageFrame


class FrameSource(Protocol):
    def __iter__(self) -> Iterator[ImageFrame]: ...

