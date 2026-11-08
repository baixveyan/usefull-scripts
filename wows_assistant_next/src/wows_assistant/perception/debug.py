from __future__ import annotations

import cv2
import numpy as np

from wows_assistant.models import Detection, OcrResult
from wows_assistant.perception.scene import SceneClassification


def annotate_scene(
    image: np.ndarray,
    classification: SceneClassification,
    *,
    ocr: tuple[OcrResult, ...] | list[OcrResult] = (),
    detections: tuple[Detection, ...] | list[Detection] = (),
    minimum_ocr_confidence: float = 0.85,
) -> np.ndarray:
    output = image.copy()
    height, width = output.shape[:2]
    for item in ocr:
        if item.confidence < minimum_ocr_confidence:
            continue
        x1, y1, x2, y2 = item.bbox.to_pixels(width, height)
        cv2.rectangle(output, (x1, y1), (x2, y2), (80, 220, 80), 1)
    for item in detections:
        x1, y1, x2, y2 = item.bbox.to_pixels(width, height)
        cv2.rectangle(output, (x1, y1), (x2, y2), (0, 180, 255), 2)
    label = f"scene={classification.scene.value} confidence={classification.confidence:.3f}"
    cv2.rectangle(output, (10, 10), (650, 55), (0, 0, 0), -1)
    cv2.putText(output, label, (22, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (80, 255, 80), 2)
    return output

