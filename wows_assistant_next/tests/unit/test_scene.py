from wows_assistant.models import BoundingBox, OcrResult, Scene
from wows_assistant.perception.scene import SceneClassification, SceneClassifier
from wows_assistant.perception.stability import SceneStabilizer


def ocr(text: str, confidence: float = 1.0) -> OcrResult:
    return OcrResult(
        text=text,
        confidence=confidence,
        bbox=BoundingBox(x1=0.1, y1=0.1, x2=0.2, y2=0.2),
    )


def test_port_scene_uses_multiple_explainable_signals() -> None:
    result = SceneClassifier().classify([ocr("加入战斗", 0.99), ocr("港口", 0.98)])
    assert result.scene is Scene.PORT
    assert result.confidence > 0.85
    assert any("加入战斗" in item for item in result.evidence)


def test_weak_generic_text_stays_unknown() -> None:
    result = SceneClassifier().classify([ocr("任务", 0.99)])
    assert result.scene is Scene.UNKNOWN


def test_actual_chinese_result_buttons_identify_result_scene() -> None:
    result = SceneClassifier().classify([ocr("回到港口", 0.99), ocr("继续战斗!", 0.99)])
    assert result.scene is Scene.RESULT
    assert result.confidence == 1.0


def test_stabilizer_requires_consecutive_frames() -> None:
    stabilizer = SceneStabilizer(required_frames=3)
    port = SceneClassification(Scene.PORT, 0.9, (), {Scene.PORT: 0.9})
    assert stabilizer.update(port).scene is Scene.UNKNOWN
    assert stabilizer.update(port).scene is Scene.UNKNOWN
    stable = stabilizer.update(port)
    assert stable.scene is Scene.PORT
    assert stable.changed is True


def test_stabilizer_resets_on_interruption() -> None:
    stabilizer = SceneStabilizer(required_frames=2)
    port = SceneClassification(Scene.PORT, 0.9, (), {Scene.PORT: 0.9})
    unknown = SceneClassification(Scene.UNKNOWN, 0.1, (), {})
    stabilizer.update(port)
    stabilizer.update(unknown)
    assert stabilizer.update(port).scene is Scene.UNKNOWN
