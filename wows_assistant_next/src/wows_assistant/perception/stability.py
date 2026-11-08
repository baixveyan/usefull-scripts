from __future__ import annotations

from dataclasses import dataclass

from wows_assistant.models import Scene
from wows_assistant.perception.scene import SceneClassification


@dataclass(frozen=True)
class StableScene:
    scene: Scene
    confidence: float
    consecutive_frames: int
    changed: bool


class SceneStabilizer:
    def __init__(self, *, required_frames: int = 3, minimum_confidence: float = 0.55) -> None:
        if required_frames < 1:
            raise ValueError("required_frames must be at least one")
        self.required_frames = required_frames
        self.minimum_confidence = minimum_confidence
        self._candidate = Scene.UNKNOWN
        self._count = 0
        self._stable = Scene.UNKNOWN
        self._stable_confidence = 0.0

    def update(self, classification: SceneClassification) -> StableScene:
        candidate = (
            classification.scene
            if classification.confidence >= self.minimum_confidence
            else Scene.UNKNOWN
        )
        if candidate == self._candidate:
            self._count += 1
        else:
            self._candidate = candidate
            self._count = 1

        changed = False
        if self._count >= self.required_frames and candidate != self._stable:
            self._stable = candidate
            self._stable_confidence = classification.confidence
            changed = True
        elif candidate == self._stable:
            self._stable_confidence = classification.confidence

        return StableScene(
            scene=self._stable,
            confidence=self._stable_confidence,
            consecutive_frames=self._count,
            changed=changed,
        )

