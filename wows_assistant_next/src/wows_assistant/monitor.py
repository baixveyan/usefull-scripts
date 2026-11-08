from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from wows_assistant.capture.windows import WindowInfo, WindowsCapture
from wows_assistant.models import ImageFrame, OcrResult, Scene
from wows_assistant.perception.ocr import OcrEngine
from wows_assistant.perception.scene import SceneClassification, SceneClassifier
from wows_assistant.perception.stability import SceneStabilizer, StableScene


@dataclass(frozen=True)
class CaptureMetrics:
    frame_id: int = -1
    capture_ms: float = 0.0
    measured_fps: float = 0.0
    captured_at: datetime | None = None


@dataclass(frozen=True)
class AnalysisMetrics:
    ocr_ms: float = 0.0
    analyzed_frame_id: int = -1
    analyzed_at: datetime | None = None


@dataclass(frozen=True)
class MonitorSnapshot:
    frame: ImageFrame | None
    ocr: tuple[OcrResult, ...]
    classification: SceneClassification
    stable_scene: StableScene
    capture: CaptureMetrics
    analysis: AnalysisMetrics
    error: str | None


def unknown_classification() -> SceneClassification:
    return SceneClassification(Scene.UNKNOWN, 0.0, (), {})


def unknown_stable_scene() -> StableScene:
    return StableScene(Scene.UNKNOWN, 0.0, 0, False)


class MonitorStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._frame: ImageFrame | None = None
        self._ocr: tuple[OcrResult, ...] = ()
        self._classification = unknown_classification()
        self._stable_scene = unknown_stable_scene()
        self._capture = CaptureMetrics()
        self._analysis = AnalysisMetrics()
        self._error: str | None = None

    def update_frame(self, frame: ImageFrame, metrics: CaptureMetrics) -> None:
        with self._lock:
            self._frame = frame
            self._capture = metrics
            self._error = None

    def update_analysis(
        self,
        ocr: tuple[OcrResult, ...],
        classification: SceneClassification,
        stable_scene: StableScene,
        metrics: AnalysisMetrics,
    ) -> None:
        with self._lock:
            self._ocr = ocr
            self._classification = classification
            self._stable_scene = stable_scene
            self._analysis = metrics
            self._error = None

    def set_error(self, message: str) -> None:
        with self._lock:
            self._error = message

    def latest_frame_copy(self) -> ImageFrame | None:
        with self._lock:
            if self._frame is None:
                return None
            return ImageFrame(self._frame.ref, self._frame.image.copy())

    def snapshot(self, *, copy_frame: bool = True) -> MonitorSnapshot:
        with self._lock:
            frame = self._frame
            if copy_frame and frame is not None:
                frame = ImageFrame(frame.ref, frame.image.copy())
            return MonitorSnapshot(
                frame=frame,
                ocr=self._ocr,
                classification=self._classification,
                stable_scene=self._stable_scene,
                capture=self._capture,
                analysis=self._analysis,
                error=self._error,
            )


class ReadOnlyMonitorController:
    """Capture and perception only. This class has no action-execution dependency."""

    def __init__(
        self,
        window: WindowInfo,
        *,
        capture_fps: float = 2.0,
        ocr_interval_seconds: float = 5.0,
        backend: str = "printwindow",
        stable_frames: int = 3,
        capture: WindowsCapture | None = None,
    ) -> None:
        if capture_fps <= 0 or ocr_interval_seconds < 0:
            raise ValueError("invalid monitor timing")
        self.window = window
        self.capture_fps = capture_fps
        self.ocr_interval_seconds = ocr_interval_seconds
        self.backend = backend
        self.capture = capture or WindowsCapture()
        self.store = MonitorStore()
        self._stabilizer = SceneStabilizer(required_frames=stable_frames)
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []

    @property
    def running(self) -> bool:
        return any(thread.is_alive() for thread in self._threads)

    @property
    def stopping(self) -> bool:
        return self._stop.is_set() and self.running

    def start(self) -> None:
        if self.running:
            return
        self._stop.clear()
        self._threads = [
            threading.Thread(target=self._capture_loop, name="capture", daemon=True),
            threading.Thread(target=self._analysis_loop, name="analysis", daemon=True),
        ]
        for thread in self._threads:
            thread.start()

    def stop(self, *, timeout: float = 2.0) -> None:
        self._stop.set()
        for thread in self._threads:
            thread.join(timeout=timeout)

    def _capture_loop(self) -> None:
        interval = 1.0 / self.capture_fps
        frame_id = 0
        last_captured: float | None = None
        while not self._stop.is_set():
            started = time.perf_counter()
            try:
                frame = self.capture.capture(
                    self.window,
                    frame_id=frame_id,
                    backend=self.backend,
                )
                finished = time.perf_counter()
                measured_fps = 0.0 if last_captured is None else 1.0 / max(finished - last_captured, 1e-6)
                last_captured = finished
                self.store.update_frame(
                    frame,
                    CaptureMetrics(
                        frame_id=frame_id,
                        capture_ms=(finished - started) * 1000.0,
                        measured_fps=measured_fps,
                        captured_at=datetime.now(UTC),
                    ),
                )
                frame_id += 1
            except Exception as exc:  # diagnostics loop must remain alive
                self.store.set_error(f"capture: {type(exc).__name__}: {exc}")
            remaining = interval - (time.perf_counter() - started)
            self._stop.wait(max(0.0, remaining))

    def _analysis_loop(self) -> None:
        ocr_engine: OcrEngine | None = None
        classifier = SceneClassifier()
        while not self._stop.is_set():
            frame = self.store.latest_frame_copy()
            if frame is None:
                self._stop.wait(0.1)
                continue
            try:
                ocr_engine = ocr_engine or OcrEngine()
                run = ocr_engine.recognize(frame.image)
                classification = classifier.classify(run.results)
                stable = self._stabilizer.update(classification)
                self.store.update_analysis(
                    run.results,
                    classification,
                    stable,
                    AnalysisMetrics(
                        ocr_ms=run.elapsed_ms,
                        analyzed_frame_id=frame.ref.frame_id,
                        analyzed_at=datetime.now(UTC),
                    ),
                )
            except Exception as exc:  # diagnostics loop must remain alive
                self.store.set_error(f"analysis: {type(exc).__name__}: {exc}")
            self._stop.wait(self.ocr_interval_seconds)
