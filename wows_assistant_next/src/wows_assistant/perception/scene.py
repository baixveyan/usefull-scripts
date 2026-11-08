from __future__ import annotations

from dataclasses import dataclass, field

from wows_assistant.models import Detection, OcrResult, Scene


@dataclass(frozen=True)
class SceneRule:
    scene: Scene
    text_weights: dict[str, float]
    anchor_weights: dict[str, float] = field(default_factory=dict)
    threshold: float = 0.55


@dataclass(frozen=True)
class SceneClassification:
    scene: Scene
    confidence: float
    evidence: tuple[str, ...]
    scores: dict[Scene, float]


DEFAULT_SCENE_RULES = (
    SceneRule(
        Scene.PORT,
        {"加入战斗": 0.65, "港口": 0.25, "装备": 0.12, "选择港口": 0.12},
        {"join_battle_button": 0.65},
    ),
    SceneRule(
        Scene.QUEUE,
        {"离开队列": 0.65, "匹配中": 0.55, "等待战斗": 0.45, "队列": 0.25},
        {"leave_queue_button": 0.65},
    ),
    SceneRule(
        Scene.LOADING,
        {"正在加载": 0.60, "等待玩家": 0.60, "任务": 0.20, "提示": 0.15},
        {"battle_loading": 0.65},
    ),
    SceneRule(
        Scene.BATTLE,
        {"自动驾驶": 0.45, "占领": 0.30, "航速": 0.30, "战斗开始": 0.55},
        {"minimap": 0.45, "ship_compass": 0.45},
    ),
    SceneRule(
        Scene.RESULT,
        {
            "战斗结果": 0.65,
            "回到港口": 0.65,
            "返回港口": 0.55,
            "继续战斗": 0.65,
            "个人成绩": 0.35,
            "个人战绩": 0.45,
            "胜利": 0.35,
            "失败": 0.35,
        },
        {"return_to_port_button": 0.60},
    ),
)


class SceneClassifier:
    def __init__(self, rules: tuple[SceneRule, ...] = DEFAULT_SCENE_RULES) -> None:
        self.rules = rules

    def classify(
        self,
        ocr: tuple[OcrResult, ...] | list[OcrResult],
        detections: tuple[Detection, ...] | list[Detection] = (),
    ) -> SceneClassification:
        texts = [(item.text.casefold(), item.confidence) for item in ocr]
        anchors = {item.label: item.confidence for item in detections}
        scores: dict[Scene, float] = {}
        evidence_by_scene: dict[Scene, list[str]] = {}
        for rule in self.rules:
            score = 0.0
            evidence: list[str] = []
            for keyword, weight in rule.text_weights.items():
                matches = [confidence for text, confidence in texts if keyword.casefold() in text]
                if matches:
                    contribution = weight * max(matches)
                    score += contribution
                    evidence.append(f"ocr:{keyword}:{contribution:.3f}")
            for label, weight in rule.anchor_weights.items():
                if label in anchors:
                    contribution = weight * anchors[label]
                    score += contribution
                    evidence.append(f"anchor:{label}:{contribution:.3f}")
            scores[rule.scene] = min(1.0, score)
            evidence_by_scene[rule.scene] = evidence

        best_rule = max(self.rules, key=lambda rule: scores[rule.scene])
        best_score = scores[best_rule.scene]
        if best_score < best_rule.threshold:
            return SceneClassification(Scene.UNKNOWN, best_score, (), scores)
        return SceneClassification(
            best_rule.scene,
            best_score,
            tuple(evidence_by_scene[best_rule.scene]),
            scores,
        )
