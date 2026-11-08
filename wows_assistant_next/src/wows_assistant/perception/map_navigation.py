from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class MapNavigationTarget:
    large_arrow: tuple[int, int]
    small_arrow: tuple[int, int]
    own_grid: str
    target_grid: str
    target_x: int
    target_y: int
    target_points: tuple[tuple[int, int], ...]
    map_bounds: tuple[int, int, int, int]
    mini_map_bounds: tuple[int, int, int, int]
    calibration_source: str


@dataclass(frozen=True)
class MiniMapPosition:
    own_marker: tuple[int, int]
    own_grid: str
    target_grid: str
    grid_x: float
    grid_y: float
    mini_map_bounds: tuple[int, int, int, int]


def _dynamic_map_bounds(image: np.ndarray) -> tuple[
    tuple[int, int, int, int], tuple[int, int, int, int], str
]:
    """Calibrate tactical/minimap rectangles from their long grid borders."""
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 40, 100)
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        threshold=max(50, round(width * 0.04)),
        minLineLength=max(120, round(width * 0.12)),
        maxLineGap=max(8, round(width * 0.006)),
    )
    horizontal: list[tuple[int, int, int]] = []
    vertical: list[tuple[int, int, int]] = []
    if lines is not None:
        for x1, y1, x2, y2 in lines[:, 0]:
            if abs(y2 - y1) <= max(3, round(height * 0.003)):
                horizontal.append((round((y1 + y2) / 2), min(x1, x2), max(x1, x2)))
            if abs(x2 - x1) <= max(3, round(width * 0.002)):
                vertical.append((round((x1 + x2) / 2), min(y1, y2), max(y1, y2)))

    mini_vertical = [
        line for line in vertical
        if line[0] > width * 0.70 and line[2] - line[1] > height * 0.25
    ]
    if mini_vertical:
        mini_left = min(line[0] for line in mini_vertical)
        mini_bottom = max(line[2] for line in mini_vertical)
        # Repeated internal grid lines make the full square width more stable
        # than any single partly occluded top border.
        xs = sorted({line[0] for line in mini_vertical})
        mini_right = max(xs)
        mini_size = mini_right - mini_left
        mini_top = mini_bottom - mini_size
        if width * 0.245 <= mini_size <= width * 0.30:
            mini_bounds = tuple(
                int(value) for value in (mini_left, mini_top, mini_right, mini_bottom)
            )
        else:
            mini_bounds = (
                round(width * 0.74), round(height * 0.54),
                round(width * 0.998), round(height * 0.995),
            )
    else:
        mini_bounds = (
            round(width * 0.74), round(height * 0.54),
            round(width * 0.998), round(height * 0.995),
        )

    long_center_lines = [
        line for line in horizontal
        if line[2] - line[1] > width * 0.35
        and line[1] < width * 0.45
        and line[2] > width * 0.60
    ]
    top_lines = [line for line in long_center_lines if height * 0.04 < line[0] < height * 0.22]
    bottom_lines = [
        line for line in horizontal
        if height * 0.68 < line[0] < height * 0.94
        and line[2] - line[1] > width * 0.18
        and line[1] < width * 0.65
        and line[2] > width * 0.60
    ]
    if top_lines and bottom_lines:
        top_line = min(top_lines, key=lambda line: line[0])
        bottom_line = max(bottom_lines, key=lambda line: line[0])
        right = round((top_line[2] + bottom_line[2]) / 2)
        # The tactical grid is square. Its lower border is often partly hidden
        # by the HUD, so derive the left edge from the detected vertical span.
        side = bottom_line[0] - top_line[0]
        left = right - side
        map_bounds = (left, top_line[0], right, bottom_line[0])
        source = "grid-lines"
    else:
        map_bounds = (
            round(width * 0.26), round(height * 0.055),
            round(width * 0.72), round(height * 0.88),
        )
        source = "ratio-fallback"
    return map_bounds, mini_bounds, source


def annotate_map_navigation(
    image: np.ndarray, navigation: MapNavigationTarget
) -> np.ndarray:
    annotated = image.copy()
    left, top, right, bottom = navigation.map_bounds
    cell_width = (right - left) / 10
    cell_height = (bottom - top) / 10

    def grid_box(grid: str) -> tuple[int, int, int, int]:
        row = ord(grid[0]) - ord("A")
        column = int(grid[1:]) - 1
        return (
            round(left + column * cell_width),
            round(top + row * cell_height),
            round(left + (column + 1) * cell_width),
            round(top + (row + 1) * cell_height),
        )

    own_box = grid_box(navigation.own_grid)
    target_box = grid_box(navigation.target_grid)
    cv2.rectangle(annotated, own_box[:2], own_box[2:], (255, 255, 255), 4)
    cv2.rectangle(annotated, target_box[:2], target_box[2:], (0, 255, 255), 4)
    cv2.rectangle(
        annotated,
        navigation.mini_map_bounds[:2],
        navigation.mini_map_bounds[2:],
        (255, 255, 0),
        2,
    )
    cv2.circle(annotated, navigation.large_arrow, 18, (255, 255, 255), 3)
    cv2.circle(annotated, navigation.small_arrow, 18, (255, 255, 255), 3)
    for index, point in enumerate(navigation.target_points, start=1):
        cv2.circle(annotated, point, 12, (0, 255, 255), 3)
        cv2.putText(
            annotated,
            str(index),
            (point[0] + 10, point[1] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )
    cv2.putText(
        annotated,
        f"OWN {navigation.own_grid} -> TARGET {navigation.target_grid} [{navigation.calibration_source}]",
        (left, max(35, top - 20)),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 255),
        3,
        cv2.LINE_AA,
    )
    return annotated


def _large_map_arrows(
    image: np.ndarray, bounds: tuple[int, int, int, int]
) -> list[tuple[int, int]]:
    height, width = image.shape[:2]
    left, top, right, bottom = bounds
    scale = min(width / 2560, height / 1440)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (0, 0, 175), (180, 85, 255))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates: list[tuple[int, int]] = []
    for contour in contours:
        area = cv2.contourArea(contour)
        x, y, box_width, box_height = cv2.boundingRect(contour)
        if not (
            left < x < right
            and top < y < bottom
            and 100 * scale**2 <= area <= 320 * scale**2
            and 12 * scale <= box_width <= 42 * scale
            and 12 * scale <= box_height <= 42 * scale
            # The own-ship arrow rotates with heading, so diagonal and
            # near-horizontal silhouettes must remain eligible.
            and 0.45 <= box_height / box_width <= 2.20
        ):
            continue
        polygon = cv2.approxPolyDP(contour, 0.06 * cv2.arcLength(contour, True), True)
        hull_area = cv2.contourArea(cv2.convexHull(contour))
        solidity = area / max(hull_area, 1.0)
        extent = area / max(float(box_width * box_height), 1.0)
        is_arrow_shape = len(polygon) == 3 or (
            len(polygon) == 4 and solidity >= 0.65 and extent <= 0.50
        )
        if not is_arrow_shape or solidity < 0.40:
            continue
        # Reject white UI glyphs over neutral gray panels. Tactical-map sea
        # around the player marker stays strongly blue/saturated even when
        # islands overlap part of the sampling ring.
        center_x, center_y = x + box_width // 2, y + box_height // 2
        radius = 25
        patch = hsv[
            max(0, center_y - radius) : min(height, center_y + radius + 1),
            max(0, center_x - radius) : min(width, center_x + radius + 1),
        ]
        if patch.size == 0 or float(np.median(patch[..., 1])) < 120:
            continue
        moments = cv2.moments(contour)
        if moments["m00"]:
            contour_x = round(moments["m10"] / moments["m00"])
            contour_y = round(moments["m01"] / moments["m00"])
            if left < contour_x < right and top < contour_y < bottom:
                candidates.append((contour_x, contour_y))
    if not candidates:
        raise LookupError("大地图未找到亮色竖向箭头候选")
    return candidates


def _confirm_small_map_arrow(
    image: np.ndarray,
    expected_x: int,
    expected_y: int,
    bounds: tuple[int, int, int, int],
) -> tuple[int, int]:
    height, width = image.shape[:2]
    left, top, right, bottom = bounds
    scale = min(width / 2560, height / 1440)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (0, 0, 120), (180, 140, 255))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates: list[tuple[float, int, int]] = []
    for contour in contours:
        area = cv2.contourArea(contour)
        x, y, box_width, box_height = cv2.boundingRect(contour)
        if not (
            left <= x < right
            and top <= y < bottom
            and 20 * scale**2 <= area <= 800 * scale**2
            and 5 * scale <= box_width <= 90 * scale
            # The arrow can merge vertically with ship name/distance glyphs.
            # Cross-map error remains the deciding guard against UI clutter.
            and 7 * scale <= box_height <= 90 * scale
        ):
            continue
        center_x, center_y = x + box_width // 2, y + box_height // 2
        distance = float(np.hypot(center_x - expected_x, center_y - expected_y))
        if distance <= 80 * scale:
            candidates.append((distance, center_x, center_y))
    if not candidates:
        raise LookupError(
            f"小地图预测位置附近未确认到亮色己方箭头: expected=({expected_x},{expected_y})"
        )
    candidates.sort()
    if len(candidates) > 1 and candidates[1][0] - candidates[0][0] < 4:
        raise LookupError(f"小地图箭头候选距离过于接近: candidates={candidates[:3]}")
    _, center_x, center_y = candidates[0]
    return center_x, center_y


def _find_with_bounds(
    image: np.ndarray,
    map_bounds: tuple[int, int, int, int],
    mini_bounds: tuple[int, int, int, int],
    calibration_source: str,
) -> MapNavigationTarget:
    left, top, right, bottom = map_bounds
    mini_left, mini_top, mini_right, mini_bottom = mini_bounds
    height, width = image.shape[:2]
    scale = min(width / 2560, height / 1440)
    confirmed: list[tuple[float, int, int, float, float, tuple[int, int]]] = []
    for large_x, large_y in _large_map_arrows(image, map_bounds):
        grid_x = float(np.clip((large_x - left) / (right - left), 0.0, 0.9999))
        grid_y = float(np.clip((large_y - top) / (bottom - top), 0.0, 0.9999))
        expected_small_x = round(mini_left + grid_x * (mini_right - mini_left))
        expected_small_y = round(mini_top + grid_y * (mini_bottom - mini_top))
        try:
            small_arrow = _confirm_small_map_arrow(
                image, expected_small_x, expected_small_y, mini_bounds
            )
        except LookupError:
            continue
        mapping_error = float(
            np.hypot(
                small_arrow[0] - expected_small_x,
                small_arrow[1] - expected_small_y,
            )
        )
        confirmed.append(
            (mapping_error, large_x, large_y, grid_x, grid_y, small_arrow)
        )
    confirmed.sort()
    # UI labels and distance text can merge into the minimap marker and shift
    # its component centroid. Allow up to 80 reference pixels, while retaining
    # the independent runner-up ambiguity guard below.
    if not confirmed or confirmed[0][0] > 80 * scale:
        raise LookupError(f"小地图与大地图交叉确认不唯一: candidates={confirmed}")
    if len(confirmed) > 1 and confirmed[1][0] - confirmed[0][0] < 10 * scale:
        raise LookupError(f"小地图与大地图交叉确认不唯一: candidates={confirmed}")
    _, large_x, large_y, grid_x, grid_y, small_arrow = confirmed[0]

    return _build_target(
        large_arrow=(large_x, large_y),
        small_arrow=small_arrow,
        grid_x=grid_x,
        grid_y=grid_y,
        map_bounds=map_bounds,
        mini_bounds=mini_bounds,
        calibration_source=calibration_source,
    )


def _build_target(
    *,
    large_arrow: tuple[int, int],
    small_arrow: tuple[int, int],
    grid_x: float,
    grid_y: float,
    map_bounds: tuple[int, int, int, int],
    mini_bounds: tuple[int, int, int, int],
    calibration_source: str,
) -> MapNavigationTarget:
    left, top, right, bottom = map_bounds
    column = min(9, int(grid_x * 10))
    row = min(9, int(grid_y * 10))
    target_row = 9 - row
    target_column = 9 - column
    own_grid = f"{chr(ord('A') + row)}{column + 1}"
    target_grid = f"{chr(ord('A') + target_row)}{target_column + 1}"
    target_x = round(left + (target_column + 0.5) / 10 * (right - left))
    target_y = round(top + (target_row + 0.5) / 10 * (bottom - top))
    # Use inset corners rather than exact grid intersections. Invalid points on
    # islands are ignored by the game, while any valid point can establish a
    # route; the center is attempted last.
    target_points = tuple(
        (
            round(left + (target_column + offset_x) / 10 * (right - left)),
            round(top + (target_row + offset_y) / 10 * (bottom - top)),
        )
        for offset_x, offset_y in (
            (0.20, 0.20),
            (0.80, 0.20),
            (0.20, 0.80),
            (0.80, 0.80),
            (0.50, 0.50),
        )
    )
    return MapNavigationTarget(
        large_arrow, small_arrow, own_grid, target_grid,
        target_x, target_y, target_points,
        map_bounds, mini_bounds, calibration_source
    )


def find_minimap_position(image: np.ndarray) -> MiniMapPosition:
    """Locate own ship from the strongest minimap range circle and white marker."""
    height, width = image.shape[:2]
    _, mini_bounds, _ = _dynamic_map_bounds(image)
    left, top, right, bottom = mini_bounds
    crop = image[top:bottom, left:right]
    if crop.size == 0:
        raise LookupError("小地图边界无效")
    scale = min(width / 2560, height / 1440)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 1.5)
    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=max(12, round(18 * scale)),
        param1=100,
        param2=35,
        minRadius=max(15, round(25 * scale)),
        maxRadius=max(80, round(260 * scale)),
    )
    if circles is None:
        raise LookupError("小地图未找到射程/探测圆")
    errors: list[str] = []
    for circle_x, circle_y, _ in np.round(circles[0]).astype(int)[:20]:
        expected_x, expected_y = int(left + circle_x), int(top + circle_y)
        try:
            _confirm_small_map_arrow(
                image, expected_x, expected_y, mini_bounds
            )
        except LookupError as exc:
            errors.append(str(exc))
            continue
        grid_x = float(np.clip((expected_x - left) / (right - left), 0.0, 0.9999))
        grid_y = float(np.clip((expected_y - top) / (bottom - top), 0.0, 0.9999))
        column = min(9, int(grid_x * 10))
        row = min(9, int(grid_y * 10))
        return MiniMapPosition(
            (expected_x, expected_y),
            f"{chr(ord('A') + row)}{column + 1}",
            f"{chr(ord('A') + 9 - row)}{10 - column}",
            grid_x,
            grid_y,
            mini_bounds,
        )
    raise LookupError(f"小地图射程圆附近未确认己方白色标记: {errors[:3]}")


def target_from_minimap_position(
    tactical_image: np.ndarray, position: MiniMapPosition
) -> MapNavigationTarget:
    map_bounds, _, source = _dynamic_map_bounds(tactical_image)
    left, top, right, bottom = map_bounds
    projected = (
        round(left + position.grid_x * (right - left)),
        round(top + position.grid_y * (bottom - top)),
    )
    return _build_target(
        large_arrow=projected,
        small_arrow=position.own_marker,
        grid_x=position.grid_x,
        grid_y=position.grid_y,
        map_bounds=map_bounds,
        mini_bounds=position.mini_map_bounds,
        calibration_source=f"minimap-only+{source}",
    )


def tactical_map_grid_is_visible(image: np.ndarray) -> bool:
    """Return true only when long tactical-grid borders were dynamically found."""
    _, _, source = _dynamic_map_bounds(image)
    return source == "grid-lines"


def find_opposite_map_target(image: np.ndarray) -> MapNavigationTarget:
    height, width = image.shape[:2]
    dynamic_map, dynamic_mini, source = _dynamic_map_bounds(image)
    aspect_ratio = width / height
    if source == "ratio-fallback" and abs(aspect_ratio - 16 / 9) > 0.15:
        raise LookupError(
            f"非 16:9 画面未完成动态网格校准: aspect_ratio={aspect_ratio:.3f}"
        )
    attempts = [(dynamic_map, dynamic_mini, source)]
    if source == "grid-lines" and abs(aspect_ratio - 16 / 9) <= 0.15:
        attempts.append(
            (
                (
                    round(width * 0.26), round(height * 0.055),
                    round(width * 0.72), round(height * 0.88),
                ),
                (
                    round(width * 0.74), round(height * 0.54),
                    round(width * 0.998), round(height * 0.995),
                ),
                "ratio-fallback",
            )
        )
    errors: list[str] = []
    for map_bounds, mini_bounds, calibration_source in attempts:
        try:
            return _find_with_bounds(
                image, map_bounds, mini_bounds, calibration_source
            )
        except LookupError as exc:
            errors.append(f"{calibration_source}: {exc}")
    raise LookupError("; ".join(errors))
