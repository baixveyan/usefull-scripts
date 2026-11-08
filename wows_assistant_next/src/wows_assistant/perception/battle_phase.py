from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from wows_assistant.models import OcrResult


class BattlePhase(str, Enum):
    COUNTDOWN = "countdown"
    ACTIVE = "active"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class BattlePhaseResult:
    phase: BattlePhase
    evidence: tuple[str, ...]


@dataclass
class ConsecutivePhaseGate:
    required: int = 2
    _phase: BattlePhase = BattlePhase.UNKNOWN
    _count: int = 0

    def update(self, phase: BattlePhase) -> bool:
        if phase is self._phase:
            self._count += 1
        else:
            self._phase = phase
            self._count = 1
        return phase is BattlePhase.ACTIVE and self._count >= self.required


_MATCH_CLOCK = re.compile(r"^(\d{1,2}):([0-5]\d)$")


def classify_match_clock_text(text: str) -> BattlePhaseResult:
    match = _MATCH_CLOCK.fullmatch("".join(text.split()))
    if match is None:
        return BattlePhaseResult(BattlePhase.UNKNOWN, ())
    minutes, seconds = (int(value) for value in match.groups())
    total_seconds = minutes * 60 + seconds
    if total_seconds < 20 * 60:
        return BattlePhaseResult(BattlePhase.ACTIVE, (f"match_clock:{minutes}:{seconds:02d}",))
    if total_seconds == 20 * 60:
        return BattlePhaseResult(BattlePhase.COUNTDOWN, ("match_clock:20:00",))
    return BattlePhaseResult(BattlePhase.UNKNOWN, ())


def classify_battle_phase(results: tuple[OcrResult, ...] | list[OcrResult]) -> BattlePhaseResult:
    texts = ["".join(item.text.split()) for item in results if item.confidence >= 0.75]
    if any("战斗开始" in text for text in texts):
        return BattlePhaseResult(BattlePhase.ACTIVE, ("ocr:战斗开始",))

    for item in results:
        center_x = (item.bbox.x1 + item.bbox.x2) / 2
        center_y = (item.bbox.y1 + item.bbox.y2) / 2
        if item.confidence < 0.75 or center_x < 0.80 or center_y > 0.10:
            continue
        phase = classify_match_clock_text(item.text)
        if phase.phase is not BattlePhase.UNKNOWN:
            return phase
    return BattlePhaseResult(BattlePhase.UNKNOWN, ())
