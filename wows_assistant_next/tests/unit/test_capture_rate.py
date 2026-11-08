import numpy as np

from wows_assistant.capture.rate import RateLimitedWindowSource
from wows_assistant.capture.windows import ClientRect, WindowInfo
from wows_assistant.models import FrameRef, ImageFrame, utc_from_timestamp


class FakeCapture:
    def capture(self, window: WindowInfo, *, frame_id: int = 0) -> ImageFrame:
        image = np.zeros((window.client.height, window.client.width, 3), dtype=np.uint8)
        ref = FrameRef(
            frame_id=frame_id,
            timestamp=utc_from_timestamp(0),
            source="fake",
            width=window.client.width,
            height=window.client.height,
        )
        return ImageFrame(ref, image)


def test_rate_limited_source_generates_requested_count() -> None:
    times = iter([0.0, 0.0, 0.0, 0.1, 0.1, 0.2, 0.2])
    window = WindowInfo(1, "test", 1, True, False, ClientRect(0, 0, 4, 3))
    source = RateLimitedWindowSource(
        window,
        target_fps=10,
        capture=FakeCapture(),  # type: ignore[arg-type]
        clock=lambda: next(times),
        sleeper=lambda _: None,
    )
    frames = list(source.frames(limit=2))
    assert [frame.ref.frame_id for frame in frames] == [0, 1]

