from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from wows_assistant.models import BoundingBox, FrameRef


def test_bbox_converts_normalized_coordinates() -> None:
    box = BoundingBox(x1=0.1, y1=0.2, x2=0.5, y2=0.75)
    assert box.to_pixels(1920, 1080) == (192, 216, 960, 810)


def test_bbox_rejects_reversed_coordinates() -> None:
    with pytest.raises(ValidationError):
        BoundingBox(x1=0.5, y1=0.2, x2=0.1, y2=0.75)


def test_frame_ref_is_timezone_aware_serializable() -> None:
    frame = FrameRef(
        frame_id=1,
        timestamp=datetime.now(UTC),
        source="frame.png",
        width=100,
        height=50,
    )
    assert FrameRef.model_validate_json(frame.model_dump_json()) == frame

