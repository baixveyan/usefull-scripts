from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from wows_assistant.actions.live_input import GuardedClickExecutor
from wows_assistant.capture.windows import WindowInfo, WindowsCapture, save_frame
from wows_assistant.models import BoundingBox, Scene
from wows_assistant.perception.ocr import OcrEngine
from wows_assistant.perception.scene import SceneClassifier
from wows_assistant.tasks.port_flow import find_text_target

ResultAction = Literal["return_port", "continue_battle"]


@dataclass(frozen=True)
class ResultFlowResult:
    status: str
    scene: Scene
    action: ResultAction
    executed: bool
    screenshots: tuple[str, ...]


class BattleResultFlow:
    def __init__(
        self,
        window: WindowInfo,
        *,
        output_dir: str | Path,
        live_input: bool,
    ) -> None:
        self.window = window
        self.output_dir = Path(output_dir)
        self.live_input = live_input
        self.capture = WindowsCapture()
        self.ocr = OcrEngine()
        self.classifier = SceneClassifier()
        self.executor = GuardedClickExecutor(window, self.output_dir / "click-audit.jsonl")
        self.screenshots: list[str] = []
        self.frame_id = 0

    def run(self, action: ResultAction, *, timeout_seconds: float = 120.0) -> ResultFlowResult:
        scene, results, width, height = self._observe("initial")
        if scene is not Scene.RESULT:
            return self._result("not_result_screen", scene, action, False)
        button_text = "回到港口" if action == "return_port" else "继续战斗!"
        try:
            target = find_text_target(
                button_text,
                results,
                region=BoundingBox(x1=0.35, y1=0.70, x2=0.95, y2=1.0),
            )
        except LookupError:
            if action != "continue_battle":
                raise
            target = find_text_target(
                "继续战斗！",
                results,
                region=BoundingBox(x1=0.35, y1=0.70, x2=0.95, y2=1.0),
            )
        x, y = target.center_pixels(width, height)
        if not self.live_input:
            return self._result("dry_run_ready", scene, action, False)
        self.executor.click_client(x, y, label=f"result:{action}")
        return self._wait_for_target(action, timeout_seconds)

    def _observe(self, label: str) -> tuple[Scene, tuple, int, int]:
        self.executor.check_emergency_stop()
        frame = self.capture.capture(self.window, frame_id=self.frame_id)
        self.frame_id += 1
        path = self.output_dir / f"{self.frame_id:02d}-{label}.png"
        save_frame(frame, path)
        self.screenshots.append(str(path))
        ocr = self.ocr.recognize(frame.image)
        classification = self.classifier.classify(ocr.results)
        return classification.scene, ocr.results, frame.ref.width, frame.ref.height

    def _wait_for_target(
        self,
        action: ResultAction,
        timeout_seconds: float,
    ) -> ResultFlowResult:
        deadline = time.monotonic() + timeout_seconds
        last_scene = Scene.UNKNOWN
        accepted = (
            {Scene.PORT}
            if action == "return_port"
            else {Scene.QUEUE, Scene.LOADING, Scene.BATTLE}
        )
        while time.monotonic() < deadline:
            self._wait(5.0)
            last_scene, _, _, _ = self._observe("waiting")
            if last_scene in accepted:
                return self._result("verified", last_scene, action, True)
        return self._result("timeout", last_scene, action, True)

    def _wait(self, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            self.executor.check_emergency_stop()
            time.sleep(min(0.1, max(0.0, deadline - time.monotonic())))

    def _result(
        self,
        status: str,
        scene: Scene,
        action: ResultAction,
        executed: bool,
    ) -> ResultFlowResult:
        return ResultFlowResult(status, scene, action, executed, tuple(self.screenshots))

