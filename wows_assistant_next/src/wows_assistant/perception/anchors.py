from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from wows_assistant.models import BoundingBox, Detection


@dataclass(frozen=True)
class TemplateAnchor:
    label: str
    template_path: Path
    threshold: float = 0.85
    search_roi: BoundingBox | None = None


class TemplateAnchorLocator:
    def locate(self, image: np.ndarray, anchor: TemplateAnchor) -> Detection | None:
        template = cv2.imread(str(anchor.template_path), cv2.IMREAD_COLOR)
        if template is None:
            raise FileNotFoundError(anchor.template_path)
        image_height, image_width = image.shape[:2]
        offset_x = 0
        offset_y = 0
        search = image
        if anchor.search_roi is not None:
            x1, y1, x2, y2 = anchor.search_roi.to_pixels(image_width, image_height)
            offset_x, offset_y = x1, y1
            search = image[y1:y2, x1:x2]
        template_height, template_width = template.shape[:2]
        if template_height > search.shape[0] or template_width > search.shape[1]:
            return None
        scores = cv2.matchTemplate(search, template, cv2.TM_CCOEFF_NORMED)
        _, score, _, location = cv2.minMaxLoc(scores)
        if score < anchor.threshold:
            return None
        left = location[0] + offset_x
        top = location[1] + offset_y
        bbox = BoundingBox(
            x1=left / image_width,
            y1=top / image_height,
            x2=(left + template_width) / image_width,
            y2=(top + template_height) / image_height,
        )
        return Detection(
            label=anchor.label,
            confidence=float(score),
            bbox=bbox,
            source="template",
            attributes={"template": str(anchor.template_path)},
        )

