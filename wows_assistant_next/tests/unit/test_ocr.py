import numpy as np

from wows_assistant.models import BoundingBox
from wows_assistant.perception.ocr import OcrEngine


class FakeRapidOcr:
    def __call__(self, image: np.ndarray) -> tuple[list[list[object]], list[float]]:
        height, width = image.shape[:2]
        result: list[object] = [
            [[0, 0], [width, 0], [width, height], [0, height]],
            "港口",
            0.98,
        ]
        return [result], [0.0, 0.0, 0.0]


def test_ocr_roi_is_mapped_back_to_full_frame() -> None:
    image = np.zeros((100, 200, 3), dtype=np.uint8)
    engine = OcrEngine(engine=FakeRapidOcr())  # type: ignore[arg-type]
    run = engine.recognize(
        image,
        roi=BoundingBox(x1=0.25, y1=0.2, x2=0.75, y2=0.8),
    )
    assert len(run.results) == 1
    assert run.results[0].text == "港口"
    assert run.results[0].bbox == BoundingBox(x1=0.25, y1=0.2, x2=0.75, y2=0.8)

