from datetime import UTC, datetime

import numpy as np

from wows_assistant.models import FrameRef, ImageFrame, Scene
from wows_assistant.monitor import CaptureMetrics, MonitorStore


def test_monitor_store_returns_independent_frame_copy() -> None:
    store = MonitorStore()
    image = np.zeros((10, 20, 3), dtype=np.uint8)
    frame = ImageFrame(
        FrameRef(
            frame_id=1,
            timestamp=datetime.now(UTC),
            source="test",
            width=20,
            height=10,
        ),
        image,
    )
    store.update_frame(frame, CaptureMetrics(frame_id=1))
    snapshot = store.snapshot()
    assert snapshot.frame is not None
    snapshot.frame.image[:] = 255
    original = store.snapshot()
    assert original.frame is not None
    assert int(original.frame.image.max()) == 0
    assert original.classification.scene is Scene.UNKNOWN

