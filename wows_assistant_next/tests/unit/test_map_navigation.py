import cv2
import numpy as np

from wows_assistant.perception.map_navigation import (
    annotate_map_navigation,
    find_opposite_map_target,
)


def test_large_and_small_arrows_cross_confirm_grid() -> None:
    image = np.full((1440, 2560, 3), (45, 25, 10), dtype=np.uint8)
    large = np.array([[1700, 1080], [1691, 1105], [1709, 1105]], dtype=np.int32)
    cv2.fillConvexPoly(image, large, (255, 255, 255))
    small = np.array([[2460, 1320], [2452, 1342], [2468, 1342]], dtype=np.int32)
    cv2.fillConvexPoly(image, small, (230, 230, 230))
    result = find_opposite_map_target(image)
    assert result.own_grid.startswith("I")
    assert result.target_grid.startswith("B")
    assert result.target_grid.endswith("2")
    assert result.target_y < 500
    assert len(result.target_points) == 5
    assert result.target_points[-1] == (result.target_x, result.target_y)
    annotated = annotate_map_navigation(image, result)
    assert np.count_nonzero(annotated != image) > 0


def test_missing_small_map_confirmation_is_rejected() -> None:
    image = np.zeros((1000, 1600, 3), dtype=np.uint8)
    large = np.array([[1100, 750], [1090, 775], [1110, 775]], dtype=np.int32)
    cv2.fillConvexPoly(image, large, (255, 255, 255))
    try:
        find_opposite_map_target(image)
    except LookupError:
        return
    raise AssertionError("large map arrow without small map confirmation must be rejected")
