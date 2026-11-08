from __future__ import annotations

import json
import re
import statistics
import time
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path

from wows_assistant.actions.live_input import GuardedClickExecutor
from wows_assistant.capture.windows import WindowInfo, WindowsCapture, save_frame
from wows_assistant.config import NavigationConfig
from wows_assistant.models import BoundingBox, ImageFrame, OcrResult, Scene
from wows_assistant.perception.battle_phase import (
    BattlePhase,
    ConsecutivePhaseGate,
    classify_battle_phase,
    classify_match_clock_text,
)
from wows_assistant.perception.map_navigation import (
    MapNavigationTarget,
    annotate_map_navigation,
    find_minimap_position,
    tactical_map_grid_is_visible,
    target_from_minimap_position,
)
from wows_assistant.perception.ocr import OcrEngine, OcrRun
from wows_assistant.perception.scene import SceneClassification, SceneClassifier


@dataclass(frozen=True)
class TextTarget:
    query: str
    result: OcrResult

    def center_pixels(self, width: int, height: int) -> tuple[int, int]:
        x1, y1, x2, y2 = self.result.bbox.to_pixels(width, height)
        return ((x1 + x2) // 2, (y1 + y2) // 2)


@dataclass(frozen=True)
class PortObservation:
    frame: ImageFrame
    ocr: OcrRun
    classification: SceneClassification
    screenshot_path: Path


@dataclass(frozen=True)
class PortFlowResult:
    status: str
    scene: Scene
    message: str
    clicks: tuple[str, ...]
    screenshots: tuple[str, ...]


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    return "".join(normalized.casefold().split())


def ship_is_sunk(results: tuple[OcrResult, ...] | list[OcrResult]) -> bool:
    """Detect the post-destruction spectator HUD using text or zero HP."""
    for result in results:
        if result.confidence < 0.80:
            continue
        text = normalize_text(result.text)
        if "战舰已被" in text and "摧毁" in text:
            return True
        center_x = (result.bbox.x1 + result.bbox.x2) / 2
        center_y = (result.bbox.y1 + result.bbox.y2) / 2
        if (
            center_x <= 0.25
            and 0.65 <= center_y <= 0.90
            and re.fullmatch(r"0[/／]\d{3,6}", text)
        ):
            return True
    return False


def find_text_target(
    query: str,
    results: tuple[OcrResult, ...] | list[OcrResult],
    *,
    region: BoundingBox | None = None,
    minimum_confidence: float = 0.80,
) -> TextTarget:
    normalized_query = normalize_text(query)
    candidates: list[OcrResult] = []
    for result in results:
        if result.confidence < minimum_confidence:
            continue
        center_x = (result.bbox.x1 + result.bbox.x2) / 2
        center_y = (result.bbox.y1 + result.bbox.y2) / 2
        if region is not None and not (
            region.x1 <= center_x <= region.x2 and region.y1 <= center_y <= region.y2
        ):
            continue
        if normalize_text(result.text) == normalized_query:
            candidates.append(result)
    if not candidates:
        raise LookupError(f"OCR 未找到唯一文本: {query!r}")
    if len(candidates) > 1:
        details = [(item.text, item.confidence) for item in candidates]
        raise LookupError(f"OCR 文本不唯一: {query!r}, candidates={details}")
    return TextTarget(query, candidates[0])


class PortBattleFlow:
    def __init__(
        self,
        window: WindowInfo,
        *,
        output_dir: str | Path,
        live_input: bool,
        navigation: NavigationConfig | None = None,
    ) -> None:
        self.window = window
        self.output_dir = Path(output_dir)
        self.live_input = live_input
        self.navigation = navigation or NavigationConfig()
        self.capture = WindowsCapture()
        self.ocr = OcrEngine()
        self.classifier = SceneClassifier()
        self.executor = GuardedClickExecutor(window, self.output_dir / "click-audit.jsonl")
        self.clicks: list[str] = []
        self.screenshots: list[str] = []
        self._observation_index = 0

    def run(
        self,
        *,
        ship_name: str,
        mode_name: str,
        wait_timeout_seconds: float = 300.0,
        select_only: bool = False,
        navigate_map_center: bool = False,
        continue_battle_after_result: bool = False,
        return_port_after_battle: bool = False,
        battle_end_timeout_seconds: float = 1800.0,
    ) -> PortFlowResult:
        initial = self.observe("initial")
        if initial.classification.scene is not Scene.PORT:
            return self._result("blocked", initial.classification.scene, "当前未可靠识别为港口")

        ship_region = BoundingBox(x1=0.0, y1=0.55, x2=1.0, y2=1.0)
        ship = find_text_target(ship_name, initial.ocr.results, region=ship_region)
        self._click_target(
            ship,
            initial.frame,
            f"select_ship:{ship_name}",
            y_offset=-35,
        )
        if not self.live_input:
            mode = self._find_current_mode(initial, mode_name)
            join = find_text_target(
                "加入战斗",
                initial.ocr.results,
                region=BoundingBox(x1=0.25, y1=0.0, x2=0.75, y2=0.12),
            )
            return self._result(
                "dry_run_ready",
                Scene.PORT,
                f"已定位舰船、模式和加入战斗: {ship.query}, {mode.query}, {join.query}",
            )

        self._interruptible_wait(2.0)
        after_ship = self.observe("after-ship")
        if not self._selected_ship_is(after_ship, ship_name):
            pitch = self._estimate_card_pitch(initial)
            retry_x, retry_y = ship.center_pixels(initial.frame.ref.width, initial.frame.ref.height)
            retry_x += max(100, pitch // 2)
            retry_y -= 35
            self.executor.click_client(retry_x, retry_y, label=f"select_ship_retry:{ship_name}")
            self.clicks.append(
                f"select_ship_retry:{ship_name}@{retry_x},{retry_y}:executed=True"
            )
            self._interruptible_wait(2.0)
            after_ship = self.observe("after-ship-retry")
        if not self._selected_ship_is(after_ship, ship_name):
            return self._result(
                "ship_not_selected",
                after_ship.classification.scene,
                f"两次受限点击后仍未在当前舰船信息区确认到 {ship_name!r}，禁止加入战斗",
            )
        try:
            self._find_current_mode(after_ship, mode_name)
        except LookupError:
            changer = find_text_target(
                "更改战斗模式",
                after_ship.ocr.results,
                region=BoundingBox(x1=0.45, y1=0.0, x2=0.75, y2=0.12),
            )
            self._click_target(changer, after_ship.frame, "open_battle_mode")
            self._interruptible_wait(2.0)
            mode_menu = self.observe("mode-menu")
            target_mode = find_text_target(mode_name, mode_menu.ocr.results)
            self._click_target(target_mode, mode_menu.frame, f"select_mode:{mode_name}")
            self._interruptible_wait(2.0)
            self._find_current_mode(self.observe("mode-confirm"), mode_name)

        if select_only:
            return self._result(
                "ship_selected",
                Scene.PORT,
                f"已确认当前舰船为 {ship_name!r}，未点击加入战斗",
            )

        ready = self.observe("ready-to-join")
        join = find_text_target(
            "加入战斗",
            ready.ocr.results,
            region=BoundingBox(x1=0.25, y1=0.0, x2=0.75, y2=0.12),
        )
        self._click_target(join, ready.frame, "join_battle")
        return self._wait_for_battle(
            wait_timeout_seconds,
            navigate_map_center,
            return_port_after_battle,
            battle_end_timeout_seconds,
            continue_battle_after_result,
        )

    def resume_wait_and_navigate(
        self,
        *,
        timeout_seconds: float = 600.0,
        navigate_map_center: bool = True,
        return_port_after_battle: bool = False,
        battle_end_timeout_seconds: float = 1800.0,
        continue_battle_after_result: bool = False,
    ) -> PortFlowResult:
        """Resume after Join Battle without issuing any port clicks."""
        return self._wait_for_battle(
            timeout_seconds,
            navigate_map_center=navigate_map_center,
            return_port_after_battle=return_port_after_battle,
            battle_end_timeout_seconds=battle_end_timeout_seconds,
            continue_battle_after_result=continue_battle_after_result,
        )

    def _selected_ship_is(self, observation: PortObservation, ship_name: str) -> bool:
        query = normalize_text(ship_name)
        for item in observation.ocr.results:
            center_x = (item.bbox.x1 + item.bbox.x2) / 2
            center_y = (item.bbox.y1 + item.bbox.y2) / 2
            if (
                item.confidence >= 0.80
                and 0.60 <= center_x <= 1.0
                and 0.04 <= center_y <= 0.30
                and query in normalize_text(item.text)
            ):
                return True
        return False

    @staticmethod
    def _estimate_card_pitch(observation: PortObservation) -> int:
        width = observation.frame.ref.width
        markers = sorted(
            ((item.bbox.x1 + item.bbox.x2) * width / 2)
            for item in observation.ocr.results
            if item.bbox.y1 > 0.75 and "50%" in normalize_text(item.text)
        )
        gaps = [b - a for a, b in pairwise(markers) if 180 <= b - a <= 380]
        return round(statistics.median(gaps)) if gaps else round(width * 0.112)

    def observe(
        self, label: str, *, ocr_roi: BoundingBox | None = None
    ) -> PortObservation:
        self.executor.check_emergency_stop()
        last_error: Exception | None = None
        for attempt in range(1, 6):
            try:
                try:
                    frame = self.capture.capture(
                        self.window, frame_id=self._observation_index
                    )
                except (OSError, RuntimeError) as printwindow_error:
                    if not self.live_input:
                        raise
                    # DirectX games can return a successful but completely black
                    # PrintWindow frame. Live flows may safely focus the already
                    # selected game window and capture its visible client area.
                    self.executor.focus_target()
                    try:
                        frame = self.capture.capture(
                            self.window,
                            frame_id=self._observation_index,
                            backend="screen",
                        )
                    except (OSError, RuntimeError) as screen_error:
                        raise RuntimeError(
                            f"PrintWindow 截图失败: {printwindow_error}; "
                            f"前台屏幕截图也失败: {screen_error}"
                        ) from screen_error
                break
            except (OSError, RuntimeError) as error:
                last_error = error
                self._write_capture_error(label, attempt, error)
                self._interruptible_wait(2.0)
        else:
            raise RuntimeError("连续五次窗口截图失败") from last_error
        self._observation_index += 1
        path = self.output_dir / f"{self._observation_index:02d}-{label}.png"
        save_frame(frame, path)
        self.screenshots.append(str(path))
        ocr = self.ocr.recognize(frame.image, roi=ocr_roi)
        classification = self.classifier.classify(ocr.results)
        self._write_observation(label, classification, ocr)
        return PortObservation(frame, ocr, classification, path)

    def _find_current_mode(self, observation: PortObservation, mode_name: str) -> TextTarget:
        return find_text_target(
            mode_name,
            observation.ocr.results,
            region=BoundingBox(x1=0.45, y1=0.0, x2=0.75, y2=0.12),
        )

    def _click_target(
        self,
        target: TextTarget,
        frame: ImageFrame,
        label: str,
        *,
        y_offset: int = 0,
    ) -> None:
        x, y = target.center_pixels(frame.ref.width, frame.ref.height)
        y += y_offset
        if self.live_input:
            self.executor.click_client(x, y, label=label)
        self.clicks.append(f"{label}@{x},{y}:executed={self.live_input}")

    def _wait_for_battle(
        self,
        timeout_seconds: float,
        navigate_map_center: bool,
        return_port_after_battle: bool = False,
        battle_end_timeout_seconds: float = 1800.0,
        continue_battle_after_result: bool = False,
    ) -> PortFlowResult:
        deadline = time.monotonic() + timeout_seconds
        last_scene = Scene.UNKNOWN
        while time.monotonic() < deadline:
            self._interruptible_wait(5.0)
            observation = self.observe("transition")
            last_scene = observation.classification.scene
            phase = classify_battle_phase(observation.ocr.results)
            if last_scene is Scene.BATTLE or phase.phase in {
                BattlePhase.COUNTDOWN,
                BattlePhase.ACTIVE,
            }:
                if navigate_map_center:
                    return self._wait_for_battle_start_and_navigate(
                        deadline,
                        return_port_after_battle=return_port_after_battle,
                        battle_end_timeout_seconds=battle_end_timeout_seconds,
                        continue_battle_after_result=continue_battle_after_result,
                    )
                if continue_battle_after_result:
                    return self._wait_for_result_and_continue(
                        battle_end_timeout_seconds
                    )
                if return_port_after_battle:
                    return self._wait_for_result_and_return(
                        battle_end_timeout_seconds
                    )
                return self._result("battle_entered", last_scene, "已识别进入战斗，流程停止")
            if last_scene is Scene.PORT and len(self.screenshots) > 4:
                # Do not click again; report instead of creating a join loop.
                return self._result("returned_to_port", last_scene, "加入战斗后再次识别到港口")
        return self._result("timeout", last_scene, "等待进入战斗超时")

    def _wait_for_battle_start_and_navigate(
        self,
        deadline: float,
        *,
        return_port_after_battle: bool = False,
        battle_end_timeout_seconds: float = 1800.0,
        continue_battle_after_result: bool = False,
    ) -> PortFlowResult:
        active_gate = ConsecutivePhaseGate(required=2)
        while time.monotonic() < deadline:
            self._interruptible_wait(2.0)
            self.executor.focus_target()
            frame = self.capture.capture_screen_region(
                self.window,
                BoundingBox(x1=0.86, y1=0.0, x2=0.94, y2=0.05),
                frame_id=self._observation_index,
            )
            self._observation_index += 1
            path = self.output_dir / f"{self._observation_index:02d}-match-clock.png"
            save_frame(frame, path)
            self.screenshots.append(str(path))
            clock_ocr = self.ocr.recognize(frame.image, detect_text=False)
            clock_text = clock_ocr.results[0].text if clock_ocr.results else ""
            phase = classify_match_clock_text(clock_text)
            self._write_phase(phase.phase, phase.evidence)
            if active_gate.update(phase.phase):
                self._interruptible_wait(3.0)
                navigation: MapNavigationTarget | None = None
                last_navigation_error: LookupError | None = None
                for navigation_attempt in range(1, 4):
                    map_confirmed_open = False
                    try:
                        battle_view = self.observe(
                            f"minimap-position-attempt-{navigation_attempt}"
                        )
                        minimap_position = find_minimap_position(
                            battle_view.frame.image
                        )
                        self.executor.press_key(
                            "M", label=f"open_tactical_map:{navigation_attempt}"
                        )
                        self._interruptible_wait(1.0)
                        map_view = self.observe(f"map-open-attempt-{navigation_attempt}")
                        map_confirmed_open = self._tactical_map_is_open(map_view)
                        if not map_confirmed_open:
                            raise LookupError("按 M 后未确认战术大地图已打开")
                        navigation = target_from_minimap_position(
                            map_view.frame.image, minimap_position
                        )
                        self._write_navigation(navigation)
                        annotated = annotate_map_navigation(
                            map_view.frame.image, navigation
                        )
                        annotated_path = self.output_dir / "map-navigation-annotated.png"
                        save_frame(
                            ImageFrame(map_view.frame.ref, annotated), annotated_path
                        )
                        self.screenshots.append(str(annotated_path))
                        for point_index, (target_x, target_y) in enumerate(
                            navigation.target_points, start=1
                        ):
                            self.executor.click_client(
                                target_x,
                                target_y,
                                label=f"autopilot_map_opposite:{point_index}",
                            )
                            self._interruptible_wait(0.25)
                        self._interruptible_wait(1.0)
                    except LookupError as error:
                        navigation = None
                        last_navigation_error = error
                        self._write_navigation_failure(navigation_attempt, error)
                    finally:
                        if map_confirmed_open:
                            self.executor.press_key(
                                "M", label=f"close_tactical_map:{navigation_attempt}"
                            )
                    if navigation is not None:
                        break
                    if navigation_attempt < 3:
                        self._interruptible_wait(10.0)
                if navigation is None:
                    return self._result(
                        "navigation_failed",
                        Scene.BATTLE,
                        f"地图导航连续三次识别失败: {last_navigation_error}",
                    )
                self._interruptible_wait(1.0)
                self.observe("navigation-complete")
                if continue_battle_after_result:
                    return self._wait_for_result_and_continue(
                        battle_end_timeout_seconds
                    )
                if return_port_after_battle:
                    return self._wait_for_result_and_return(battle_end_timeout_seconds)
                return self._result(
                    "navigation_started",
                    Scene.BATTLE,
                    "已识别己方地图位置并点击正对面目标，关闭地图后流程停止",
                )
        return self._result("timeout", Scene.BATTLE, "等待战斗倒计时结束超时")

    def _wait_for_result_and_return(self, timeout_seconds: float) -> PortFlowResult:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            self._interruptible_wait(15.0)
            observation = self.observe("waiting-battle-end")
            try:
                target = find_text_target(
                    "回到港口",
                    observation.ocr.results,
                    region=BoundingBox(x1=0.35, y1=0.70, x2=0.95, y2=1.0),
                )
            except LookupError:
                continue
            self._click_target(target, observation.frame, "return_to_port")
            return self._wait_for_port_after_result(180.0)
        return self._result("battle_end_timeout", Scene.BATTLE, "等待战斗结算超时")

    def _wait_for_result_and_continue(self, timeout_seconds: float) -> PortFlowResult:
        deadline = time.monotonic() + timeout_seconds
        next_motion_key = "W"
        escaped_destroyed_battle = False
        while time.monotonic() < deadline:
            self._interruptible_wait(5.0)
            observation = self.observe("waiting-continue-battle")
            target: TextTarget | None = None
            for query in ("继续战斗!", "继续战斗！", "继续战斗"):
                try:
                    target = find_text_target(
                        query,
                        observation.ocr.results,
                        region=BoundingBox(x1=0.35, y1=0.70, x2=0.95, y2=1.0),
                    )
                    break
                except LookupError:
                    continue
            if target is None:
                if ship_is_sunk(observation.ocr.results):
                    if not escaped_destroyed_battle:
                        self.executor.press_key(
                            "ESC", label="leave_destroyed_battle"
                        )
                        escaped_destroyed_battle = True
                    continue
                if not escaped_destroyed_battle:
                    self.executor.press_key(
                        next_motion_key,
                        label=f"battle_motion_pulse:{next_motion_key.lower()}",
                    )
                    next_motion_key = "S" if next_motion_key == "W" else "W"
                continue
            self._click_target(target, observation.frame, "continue_battle")
            return self._result(
                "continue_battle_clicked",
                Scene.RESULT,
                "已识别并点击继续战斗，等待下一局",
            )
        return self._result(
            "continue_battle_timeout",
            Scene.BATTLE,
            "等待结算页继续战斗按钮超时",
        )

    def _wait_for_port_after_result(self, timeout_seconds: float) -> PortFlowResult:
        deadline = time.monotonic() + timeout_seconds
        last_scene = Scene.RESULT
        while time.monotonic() < deadline:
            self._interruptible_wait(5.0)
            observation = self.observe("waiting-return-port")
            last_scene = observation.classification.scene
            if last_scene is Scene.PORT:
                return self._result(
                    "cycle_completed", Scene.PORT, "已完成战斗并确认返回港口"
                )
        return self._result("return_port_timeout", last_scene, "点击后等待返回港口超时")

    def _write_phase(self, phase: BattlePhase, evidence: tuple[str, ...]) -> None:
        payload = {
            "observed_at": datetime.now(UTC).isoformat(),
            "label": "battle_phase",
            "phase": phase.value,
            "evidence": list(evidence),
        }
        with (self.output_dir / "observations.jsonl").open(
            "a", encoding="utf-8", newline="\n"
        ) as stream:
            stream.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _write_navigation(self, navigation: MapNavigationTarget) -> None:
        payload = {
            "observed_at": datetime.now(UTC).isoformat(),
            "label": "map_navigation",
            "large_arrow": navigation.large_arrow,
            "small_arrow": navigation.small_arrow,
            "own_grid": navigation.own_grid,
            "target_grid": navigation.target_grid,
            "target": [navigation.target_x, navigation.target_y],
            "target_points": [list(point) for point in navigation.target_points],
            "map_bounds": list(navigation.map_bounds),
            "mini_map_bounds": list(navigation.mini_map_bounds),
            "calibration_source": navigation.calibration_source,
        }
        with (self.output_dir / "observations.jsonl").open(
            "a", encoding="utf-8", newline="\n"
        ) as stream:
            stream.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _write_navigation_failure(self, attempt: int, error: LookupError) -> None:
        payload = {
            "observed_at": datetime.now(UTC).isoformat(),
            "label": "map_navigation_failure",
            "attempt": attempt,
            "retry_after_seconds": 10 if attempt < 3 else None,
            "error": str(error),
        }
        with (self.output_dir / "observations.jsonl").open(
            "a", encoding="utf-8", newline="\n"
        ) as stream:
            stream.write(json.dumps(payload, ensure_ascii=False) + "\n")

    @staticmethod
    def _tactical_map_is_open(observation: PortObservation) -> bool:
        if tactical_map_grid_is_visible(observation.frame.image):
            return True
        visible_text = " ".join(normalize_text(item.text) for item in observation.ocr.results)
        return any(
            marker in visible_text
            for marker in (normalize_text("自动驾驶控制"), normalize_text("战术地图模式"))
        )

    def _interruptible_wait(self, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            self.executor.check_emergency_stop()
            time.sleep(min(0.1, max(0.0, deadline - time.monotonic())))

    def _write_observation(
        self,
        label: str,
        classification: SceneClassification,
        ocr: OcrRun,
    ) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "observed_at": datetime.now(UTC).isoformat(),
            "label": label,
            "scene": classification.scene.value,
            "confidence": classification.confidence,
            "evidence": classification.evidence,
            "ocr_count": len(ocr.results),
            "ocr_ms": ocr.elapsed_ms,
        }
        with (self.output_dir / "observations.jsonl").open(
            "a", encoding="utf-8", newline="\n"
        ) as stream:
            stream.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _write_capture_error(self, label: str, attempt: int, error: Exception) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "observed_at": datetime.now(UTC).isoformat(),
            "label": label,
            "scene": "capture_error",
            "attempt": attempt,
            "recoverable": attempt < 5,
            "error": str(error),
        }
        with (self.output_dir / "observations.jsonl").open(
            "a", encoding="utf-8", newline="\n"
        ) as stream:
            stream.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _result(self, status: str, scene: Scene, message: str) -> PortFlowResult:
        result = PortFlowResult(
            status=status,
            scene=scene,
            message=message,
            clicks=tuple(self.clicks),
            screenshots=tuple(self.screenshots),
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            "completed_at": datetime.now(UTC).isoformat(),
            "status": status,
            "scene": scene.value,
            "message": message,
            "clicks": list(self.clicks),
            "screenshots": list(self.screenshots),
            "navigation": {
                "map_x_ratio": self.navigation.map_x_ratio,
                "map_y_ratio": self.navigation.map_y_ratio,
            },
        }
        (self.output_dir / "run-summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result
