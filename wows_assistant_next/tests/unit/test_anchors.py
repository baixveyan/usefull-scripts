from pathlib import Path

import cv2
import numpy as np

from wows_assistant.models import BoundingBox
from wows_assistant.perception.anchors import TemplateAnchor, TemplateAnchorLocator


def test_template_anchor_locates_synthetic_pattern(tmp_path: Path) -> None:
    template = np.zeros((20, 30, 3), dtype=np.uint8)
    cv2.circle(template, (15, 10), 6, (255, 255, 255), -1)
    image = np.zeros((100, 200, 3), dtype=np.uint8)
    image[40:60, 80:110] = template
    path = tmp_path / "anchor.png"
    assert cv2.imwrite(str(path), template)
    anchor = TemplateAnchor(
        "synthetic",
        path,
        threshold=0.99,
        search_roi=BoundingBox(x1=0.25, y1=0.2, x2=0.75, y2=0.8),
    )
    detection = TemplateAnchorLocator().locate(image, anchor)
    assert detection is not None
    assert detection.label == "synthetic"
    assert detection.bbox.to_pixels(200, 100) == (80, 40, 110, 60)

