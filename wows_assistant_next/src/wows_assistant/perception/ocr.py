from __future__ import annotations

import os
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import ClassVar

import numpy as np
from rapidocr_onnxruntime import RapidOCR

from wows_assistant.models import BoundingBox, OcrResult


@dataclass(frozen=True)
class OcrRun:
    results: tuple[OcrResult, ...]
    elapsed_ms: float


class OcrEngine:
    _dll_handles: ClassVar[list[object]] = []

    def __init__(self, engine: RapidOCR | None = None, *, prefer_gpu: bool = True) -> None:
        self.engine = engine or self._cached_engine(prefer_gpu)

    @classmethod
    @lru_cache(maxsize=2)
    def _cached_engine(cls, prefer_gpu: bool) -> RapidOCR:
        if prefer_gpu:
            try:
                import onnxruntime as ort
                import torch

                ort.set_default_logger_severity(3)
                torch_lib = Path(torch.__file__).parent / "lib"
                if torch_lib.is_dir() and hasattr(os, "add_dll_directory"):
                    cls._dll_handles.append(os.add_dll_directory(str(torch_lib)))
            except (ImportError, OSError):
                pass
        return RapidOCR(
            det_use_cuda=prefer_gpu,
            cls_use_cuda=prefer_gpu,
            rec_use_cuda=prefer_gpu,
        )

    @property
    def providers(self) -> tuple[str, ...]:
        return tuple(self.engine.text_rec.session.session.get_providers())

    def recognize(
        self,
        image: np.ndarray,
        *,
        roi: BoundingBox | None = None,
        detect_text: bool = True,
    ) -> OcrRun:
        height, width = image.shape[:2]
        offset_x = 0
        offset_y = 0
        target = image
        if roi is not None:
            x1, y1, x2, y2 = roi.to_pixels(width, height)
            offset_x, offset_y = x1, y1
            target = image[y1:y2, x1:x2]
            if target.size == 0:
                raise ValueError("OCR ROI 为空")

        started = time.perf_counter()
        if detect_text:
            raw_results, _ = self.engine(target)
        else:
            raw_results, _ = self.engine(
                target, use_det=False, use_cls=False, use_rec=True
            )
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        converted: list[OcrResult] = []
        if not detect_text:
            if not raw_results:
                return OcrRun(results=(), elapsed_ms=elapsed_ms)
            text, confidence = raw_results[0]
            if not str(text).strip():
                return OcrRun(results=(), elapsed_ms=elapsed_ms)
            return OcrRun(
                results=(
                    OcrResult(
                        text=str(text).strip(),
                        confidence=float(confidence),
                        bbox=roi or BoundingBox(x1=0.0, y1=0.0, x2=1.0, y2=1.0),
                    ),
                ),
                elapsed_ms=elapsed_ms,
            )
        for polygon, text, confidence in raw_results or []:
            xs = [float(point[0]) + offset_x for point in polygon]
            ys = [float(point[1]) + offset_y for point in polygon]
            x1 = max(0.0, min(xs) / width)
            y1 = max(0.0, min(ys) / height)
            x2 = min(1.0, max(xs) / width)
            y2 = min(1.0, max(ys) / height)
            if x2 <= x1 or y2 <= y1:
                continue
            converted.append(
                OcrResult(
                    text=str(text).strip(),
                    confidence=float(confidence),
                    bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
                )
            )
        return OcrRun(results=tuple(converted), elapsed_ms=elapsed_ms)
