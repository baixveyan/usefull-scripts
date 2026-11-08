from wows_assistant.models import BoundingBox, OcrResult
from wows_assistant.perception.battle_phase import (
    BattlePhase,
    ConsecutivePhaseGate,
    classify_battle_phase,
)


def ocr(text: str, *, x: float = 0.9, y: float = 0.03) -> OcrResult:
    return OcrResult(
        text=text,
        confidence=0.99,
        bbox=BoundingBox(x1=x, y1=y, x2=min(x + 0.05, 1.0), y2=y + 0.03),
    )


def test_battle_start_banner_is_active() -> None:
    assert classify_battle_phase([ocr("战斗开始", x=0.4, y=0.3)]).phase is BattlePhase.ACTIVE


def test_running_match_clock_is_active() -> None:
    result = classify_battle_phase([ocr("18:58")])
    assert result.phase is BattlePhase.ACTIVE
    assert result.evidence == ("match_clock:18:58",)


def test_twenty_minute_clock_is_countdown_boundary() -> None:
    assert classify_battle_phase([ocr("20:00")]).phase is BattlePhase.COUNTDOWN


def test_desktop_clock_outside_region_is_ignored() -> None:
    assert classify_battle_phase([ocr("18:58", x=0.4)]).phase is BattlePhase.UNKNOWN


def test_active_phase_requires_two_consecutive_updates() -> None:
    gate = ConsecutivePhaseGate(required=2)
    assert gate.update(BattlePhase.ACTIVE) is False
    assert gate.update(BattlePhase.UNKNOWN) is False
    assert gate.update(BattlePhase.ACTIVE) is False
    assert gate.update(BattlePhase.ACTIVE) is True
