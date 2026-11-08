import pytest

from wows_assistant.models import BoundingBox, OcrResult
from wows_assistant.tasks.port_flow import find_text_target, normalize_text, ship_is_sunk


def item(text: str, confidence: float, y1: float = 0.7, y2: float = 0.8) -> OcrResult:
    return OcrResult(
        text=text,
        confidence=confidence,
        bbox=BoundingBox(x1=0.2, y1=y1, x2=0.4, y2=y2),
    )


def test_normalize_text_handles_width_and_spaces() -> None:
    assert normalize_text(" 联合 作战 ") == normalize_text("联合作战")


def test_find_ship_name_inside_carousel_region() -> None:
    target = find_text_target(
        "那不勒斯",
        [item("那不勒斯", 0.99), item("那不勒斯", 0.99, 0.2, 0.3)],
        region=BoundingBox(x1=0.0, y1=0.55, x2=1.0, y2=1.0),
    )
    assert target.result.text == "那不勒斯"


def test_find_text_rejects_ambiguous_matches() -> None:
    with pytest.raises(LookupError, match="不唯一"):
        find_text_target("加入战斗", [item("加入战斗", 0.99), item("加入战斗", 0.98)])


def test_find_text_rejects_low_confidence() -> None:
    with pytest.raises(LookupError, match="未找到"):
        find_text_target("加入战斗", [item("加入战斗", 0.5)])


def test_selected_ship_verification_region_excludes_carousel() -> None:
    selected_region = BoundingBox(x1=0.75, y1=0.05, x2=1.0, y2=0.25)
    with pytest.raises(LookupError):
        find_text_target("那不勒斯", [item("那不勒斯", 0.99)], region=selected_region)


def test_ship_is_sunk_accepts_destroyed_message() -> None:
    assert ship_is_sunk([item("您的战舰已被玩家摧毁", 0.98)])


def test_ship_is_sunk_accepts_zero_hp_in_lower_left_hud() -> None:
    hp = OcrResult(
        text="0/40200",
        confidence=0.94,
        bbox=BoundingBox(x1=0.08, y1=0.75, x2=0.12, y2=0.77),
    )
    assert ship_is_sunk([hp])


def test_ship_is_sunk_rejects_zero_score_outside_hp_hud() -> None:
    score = OcrResult(
        text="0/1000",
        confidence=0.99,
        bbox=BoundingBox(x1=0.48, y1=0.08, x2=0.52, y2=0.10),
    )
    assert not ship_is_sunk([score])
