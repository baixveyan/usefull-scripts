from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import cv2
from PyQt5 import QtCore, QtGui, QtWidgets

from wows_assistant.monitor import MonitorSnapshot, ReadOnlyMonitorController
from wows_assistant.perception.debug import annotate_scene


class MonitorWindow(QtWidgets.QMainWindow):
    def __init__(self, controller: ReadOnlyMonitorController, output_dir: Path) -> None:
        super().__init__()
        self.controller = controller
        self.output_dir = output_dir
        self._last_snapshot: MonitorSnapshot | None = None
        self.setWindowTitle("WoWS Assistant Next - 只读监控器")
        self.resize(1400, 900)
        self._build_ui()
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._refresh)
        self.timer.start(200)
        self.controller.start()

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(central)

        warning = QtWidgets.QLabel("只读模式：不会发送键盘、鼠标输入，也不会激活游戏窗口")
        warning.setStyleSheet("color: #ffcc66; background: #292929; padding: 8px; font-weight: bold;")
        layout.addWidget(warning)

        metrics = QtWidgets.QHBoxLayout()
        self.scene_label = QtWidgets.QLabel("候选场景: unknown")
        self.stable_label = QtWidgets.QLabel("稳定场景: unknown")
        self.performance_label = QtWidgets.QLabel("等待帧...")
        metrics.addWidget(self.scene_label)
        metrics.addWidget(self.stable_label)
        metrics.addStretch(1)
        metrics.addWidget(self.performance_label)
        layout.addLayout(metrics)

        self.image_label = QtWidgets.QLabel("等待游戏截图...")
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setMinimumSize(800, 450)
        self.image_label.setStyleSheet("background: #111; color: #aaa;")
        layout.addWidget(self.image_label, 1)

        bottom = QtWidgets.QHBoxLayout()
        self.detail = QtWidgets.QPlainTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setMaximumBlockCount(500)
        bottom.addWidget(self.detail, 1)
        controls = QtWidgets.QVBoxLayout()
        self.toggle_button = QtWidgets.QPushButton("暂停")
        self.toggle_button.clicked.connect(self._toggle)
        save_button = QtWidgets.QPushButton("保存当前调试帧")
        save_button.clicked.connect(self._save_current)
        controls.addWidget(self.toggle_button)
        controls.addWidget(save_button)
        controls.addStretch(1)
        bottom.addLayout(controls)
        layout.addLayout(bottom)
        self.setCentralWidget(central)

    def _toggle(self) -> None:
        if self.controller.stopping:
            return
        if self.controller.running:
            self.controller.stop()
            self.toggle_button.setText("正在停止 OCR...")
            self.toggle_button.setEnabled(False)
        else:
            self.controller.start()
            self.toggle_button.setText("暂停")

    def _refresh(self) -> None:
        if (
            not self.controller.running
            and not self.controller.stopping
            and self.toggle_button.text() == "正在停止 OCR..."
        ):
            self.toggle_button.setText("继续")
            self.toggle_button.setEnabled(True)
        snapshot = self.controller.store.snapshot()
        self._last_snapshot = snapshot
        classification = snapshot.classification
        self.scene_label.setText(
            f"候选场景: {classification.scene.value} ({classification.confidence:.3f})"
        )
        stable = snapshot.stable_scene
        self.stable_label.setText(
            f"稳定场景: {stable.scene.value} | 连续证据: {stable.consecutive_frames}"
        )
        self.performance_label.setText(
            f"帧 {snapshot.capture.frame_id} | {snapshot.capture.capture_ms:.1f} ms | "
            f"{snapshot.capture.measured_fps:.1f} FPS | OCR {snapshot.analysis.ocr_ms:.0f} ms"
        )
        lines = [*classification.evidence]
        if snapshot.error:
            lines.append(f"ERROR: {snapshot.error}")
        lines.append(f"OCR 数量: {len(snapshot.ocr)}")
        lines.append(f"OCR 帧: {snapshot.analysis.analyzed_frame_id}")
        self.detail.setPlainText("\n".join(lines))

        if snapshot.frame is None:
            return
        annotated = annotate_scene(
            snapshot.frame.image,
            classification,
            ocr=snapshot.ocr,
        )
        rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb.shape
        qimage = QtGui.QImage(rgb.data, width, height, channels * width, QtGui.QImage.Format_RGB888).copy()
        pixmap = QtGui.QPixmap.fromImage(qimage).scaled(
            self.image_label.size(),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation,
        )
        self.image_label.setPixmap(pixmap)

    def _save_current(self) -> None:
        snapshot = self._last_snapshot
        if snapshot is None or snapshot.frame is None:
            return
        annotated = annotate_scene(
            snapshot.frame.image,
            snapshot.classification,
            ocr=snapshot.ocr,
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / datetime.now(UTC).strftime("monitor-%Y%m%d-%H%M%S.png")
        cv2.imwrite(str(path), annotated)
        self.statusBar().showMessage(f"已保存: {path}", 5000)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.timer.stop()
        self.controller.stop()
        super().closeEvent(event)
