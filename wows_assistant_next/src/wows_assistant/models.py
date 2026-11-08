from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, Field, field_validator


class Scene(StrEnum):
    UNKNOWN = "unknown"
    PORT = "port"
    QUEUE = "queue"
    LOADING = "loading"
    BATTLE = "battle"
    RESULT = "result"


class BoundingBox(BaseModel):
    """Normalized xyxy coordinates in the inclusive range 0..1."""

    x1: float = Field(ge=0.0, le=1.0)
    y1: float = Field(ge=0.0, le=1.0)
    x2: float = Field(ge=0.0, le=1.0)
    y2: float = Field(ge=0.0, le=1.0)

    @field_validator("x2")
    @classmethod
    def validate_x2(cls, value: float, info: Any) -> float:
        if "x1" in info.data and value <= info.data["x1"]:
            raise ValueError("x2 must be greater than x1")
        return value

    @field_validator("y2")
    @classmethod
    def validate_y2(cls, value: float, info: Any) -> float:
        if "y1" in info.data and value <= info.data["y1"]:
            raise ValueError("y2 must be greater than y1")
        return value

    def to_pixels(self, width: int, height: int) -> tuple[int, int, int, int]:
        return (
            round(self.x1 * width),
            round(self.y1 * height),
            round(self.x2 * width),
            round(self.y2 * height),
        )


class FrameRef(BaseModel):
    frame_id: int = Field(ge=0)
    timestamp: datetime
    source: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class Detection(BaseModel):
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BoundingBox
    source: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class OcrResult(BaseModel):
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BoundingBox
    source: str = "rapidocr"


class PerceptionResult(BaseModel):
    frame: FrameRef
    scene: Scene = Scene.UNKNOWN
    scene_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    detections: list[Detection] = Field(default_factory=list)
    ocr: list[OcrResult] = Field(default_factory=list)
    timings_ms: dict[str, float] = Field(default_factory=dict)


class WorldState(BaseModel):
    observed_at: datetime
    scene: Scene = Scene.UNKNOWN
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    stable_frames: int = Field(default=0, ge=0)
    speed_knots: float | None = Field(default=None, ge=0.0)
    heading_degrees: float | None = Field(default=None, ge=0.0, lt=360.0)
    target_distance_km: float | None = Field(default=None, ge=0.0)
    facts: dict[str, Any] = Field(default_factory=dict)


class ActionKind(StrEnum):
    NOOP = "noop"
    KEY_PRESS = "key_press"
    KEY_HOLD = "key_hold"
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"


class ActionIntent(BaseModel):
    intent_id: str
    created_at: datetime
    kind: ActionKind = ActionKind.NOOP
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)
    expires_at: datetime | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class EventEnvelope(BaseModel):
    schema_version: Literal[1] = 1
    event_type: Literal["perception", "world_state", "action_intent"]
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any]


class ImageFrame:
    """In-memory BGR frame; pixel data is intentionally excluded from JSON logs."""

    def __init__(self, ref: FrameRef, image: np.ndarray) -> None:
        if image.ndim != 3 or image.shape[2] not in (3, 4):
            raise ValueError("image must have shape HxWx3 or HxWx4")
        if image.shape[1] != ref.width or image.shape[0] != ref.height:
            raise ValueError("image dimensions do not match FrameRef")
        self.ref = ref
        self.image = image


SerializableEvent = PerceptionResult | WorldState | ActionIntent


def event_type_for(value: SerializableEvent) -> str:
    if isinstance(value, PerceptionResult):
        return "perception"
    if isinstance(value, WorldState):
        return "world_state"
    if isinstance(value, ActionIntent):
        return "action_intent"
    raise TypeError(f"unsupported event: {type(value)!r}")


def utc_from_timestamp(timestamp: float) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=UTC)
