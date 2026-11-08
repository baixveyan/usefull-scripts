from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass

from wows_assistant.capture.windows import WindowInfo, WindowsCapture
from wows_assistant.models import ImageFrame


@dataclass
class CaptureStats:
    frames: int = 0
    started_at: float = 0.0
    last_frame_at: float = 0.0

    @property
    def elapsed_seconds(self) -> float:
        return max(0.0, self.last_frame_at - self.started_at)

    @property
    def measured_fps(self) -> float:
        if self.frames < 2 or self.elapsed_seconds <= 0:
            return 0.0
        return (self.frames - 1) / self.elapsed_seconds


class RateLimitedWindowSource:
    def __init__(
        self,
        window: WindowInfo,
        *,
        target_fps: float = 5.0,
        capture: WindowsCapture | None = None,
        clock: Callable[[], float] = time.perf_counter,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if target_fps <= 0:
            raise ValueError("target_fps must be positive")
        self.window = window
        self.target_fps = target_fps
        self.capture = capture or WindowsCapture()
        self.clock = clock
        self.sleeper = sleeper
        self.stats = CaptureStats()

    def frames(self, *, limit: int | None = None) -> Iterator[ImageFrame]:
        interval = 1.0 / self.target_fps
        next_frame_at = self.clock()
        self.stats.started_at = next_frame_at
        frame_id = 0
        while limit is None or frame_id < limit:
            now = self.clock()
            if now < next_frame_at:
                self.sleeper(next_frame_at - now)
            frame = self.capture.capture(self.window, frame_id=frame_id)
            captured_at = self.clock()
            self.stats.frames += 1
            self.stats.last_frame_at = captured_at
            yield frame
            frame_id += 1
            next_frame_at = max(next_frame_at + interval, captured_at)

