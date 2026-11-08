from __future__ import annotations

import sys
from pathlib import Path

from PyQt5 import QtCore, QtGui, QtWidgets


class LauncherWindow(QtWidgets.QMainWindow):
    """Small control panel that starts the existing guarded port flow."""

    def __init__(self, *, config_path: str = "config/default.yaml") -> None:
        super().__init__()
        self.config_path = config_path
        self.settings = QtCore.QSettings("WoWSAssistantNext", "Launcher")
        self.process = QtCore.QProcess(self)
        self.process.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.started.connect(self._started)
        self.process.finished.connect(self._finished)
        self.setWindowTitle("WoWS Assistant Next")
        self.setMinimumSize(680, 520)
        self._build_ui()

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QtWidgets.QLabel("战舰世界自动流程")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title)

        hint = QtWidgets.QLabel(
            "设置舰船与模式后点击开始。只有点击开始后才会操作游戏；F12 可紧急停止。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #d7b86a; padding: 8px; background: #292929;")
        layout.addWidget(hint)

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignRight)
        self.ship = QtWidgets.QComboBox()
        self.ship.setEditable(True)
        self.ship.addItems(self._saved_items("ships", ["那不勒斯"]))
        self.ship.setCurrentText("那不勒斯")
        self.add_ship_button = QtWidgets.QPushButton("添加舰船")
        self.add_ship_button.clicked.connect(self._prompt_add_ship)
        ship_row = QtWidgets.QHBoxLayout()
        ship_row.addWidget(self.ship, 1)
        ship_row.addWidget(self.add_ship_button)
        self.mode = QtWidgets.QComboBox()
        self.mode.setEditable(True)
        self.mode.addItems(
            self._saved_items("modes", ["联合作战", "随机战", "排位战"])
        )
        self.mode.setCurrentText("联合作战")
        self.add_mode_button = QtWidgets.QPushButton("添加模式")
        self.add_mode_button.clicked.connect(self._prompt_add_mode)
        mode_row = QtWidgets.QHBoxLayout()
        mode_row.addWidget(self.mode, 1)
        mode_row.addWidget(self.add_mode_button)
        self.title_match = QtWidgets.QLineEdit("战舰世界")
        form.addRow("舰船：", ship_row)
        form.addRow("战斗模式：", mode_row)
        form.addRow("游戏窗口标题：", self.title_match)
        layout.addLayout(form)

        self.navigate = QtWidgets.QCheckBox("进入战斗后自动设置导航")
        self.navigate.setChecked(True)
        self.return_port = QtWidgets.QCheckBox("战斗结束后自动回到港口")
        self.return_port.setChecked(True)
        self.continuous = QtWidgets.QCheckBox(
            "连续作战（结算后点击继续战斗）"
        )
        self.continuous.setChecked(True)
        self.continuous.toggled.connect(self._continuous_changed)
        layout.addWidget(self.navigate)
        layout.addWidget(self.return_port)
        layout.addWidget(self.continuous)
        self._continuous_changed(True)

        buttons = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton("开始")
        self.start_button.setMinimumHeight(42)
        self.start_button.clicked.connect(self._start)
        self.stop_button = QtWidgets.QPushButton("停止进程")
        self.stop_button.setMinimumHeight(42)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._stop)
        buttons.addWidget(self.start_button, 2)
        buttons.addWidget(self.stop_button, 1)
        layout.addLayout(buttons)

        self.status = QtWidgets.QLabel("就绪：程序尚未运行")
        layout.addWidget(self.status)
        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(2000)
        self.log.setPlaceholderText("运行日志将显示在这里……")
        layout.addWidget(self.log, 1)
        self.setCentralWidget(central)

    def _saved_items(self, key: str, defaults: list[str]) -> list[str]:
        saved = self.settings.value(key, [], type=list)
        return list(dict.fromkeys([*defaults, *(str(item) for item in saved if str(item).strip())]))

    def _store_combo(self, key: str, combo: QtWidgets.QComboBox) -> None:
        self.settings.setValue(key, [combo.itemText(index) for index in range(combo.count())])

    def _add_item(self, key: str, combo: QtWidgets.QComboBox, value: str) -> bool:
        value = value.strip()
        if not value:
            return False
        matches = combo.findText(value, QtCore.Qt.MatchFixedString)
        if matches < 0:
            combo.addItem(value)
        combo.setCurrentText(value)
        self._store_combo(key, combo)
        return True

    def _prompt_add_ship(self) -> None:
        value, accepted = QtWidgets.QInputDialog.getText(self, "添加舰船", "请输入游戏中显示的完整舰名：")
        if accepted:
            self._add_item("ships", self.ship, value)

    def _prompt_add_mode(self) -> None:
        value, accepted = QtWidgets.QInputDialog.getText(self, "添加模式", "请输入游戏中显示的完整模式名：")
        if accepted:
            self._add_item("modes", self.mode, value)

    def _start(self) -> None:
        if self.process.state() != QtCore.QProcess.NotRunning:
            return
        ship = self.ship.currentText().strip()
        mode = self.mode.currentText().strip()
        title = self.title_match.text().strip()
        if not ship or not mode or not title:
            QtWidgets.QMessageBox.warning(self, "参数不完整", "舰船、模式和窗口标题不能为空。")
            return
        self._add_item("ships", self.ship, ship)
        self._add_item("modes", self.mode, mode)
        arguments = [
            "-c",
            "from wows_assistant.cli import main; raise SystemExit(main())",
            "port-test",
            "--ship", ship,
            "--mode", mode,
            "--title", title,
            "--wait-timeout", "600",
            "--battle-end-timeout", "1800",
            "--config", self.config_path,
            "--confirm-live-input",
        ]
        if self.navigate.isChecked():
            arguments.append("--navigate-map-center")
        if self.return_port.isChecked():
            arguments.append("--return-port-after-battle")
        if self.continuous.isChecked():
            arguments.append("--continuous")
        self.log.clear()
        self.log.appendPlainText(f"启动：{ship} | {mode}")
        self.process.setWorkingDirectory(str(Path.cwd()))
        environment = QtCore.QProcessEnvironment.systemEnvironment()
        environment.insert("PYTHONIOENCODING", "utf-8")
        environment.insert("PYTHONUTF8", "1")
        self.process.setProcessEnvironment(environment)
        self.process.start(sys.executable, arguments)

    def _started(self) -> None:
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.ship.setEnabled(False)
        self.mode.setEnabled(False)
        self.add_ship_button.setEnabled(False)
        self.add_mode_button.setEnabled(False)
        self.navigate.setEnabled(False)
        self.return_port.setEnabled(False)
        self.continuous.setEnabled(False)
        self.status.setText("运行中：按 F12 可紧急停止")

    def _read_output(self) -> None:
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if data:
            self.log.moveCursor(QtGui.QTextCursor.End)
            self.log.insertPlainText(data)
            self.log.ensureCursorVisible()

    def _stop(self) -> None:
        if self.process.state() == QtCore.QProcess.NotRunning:
            return
        self.status.setText("正在停止……")
        self.process.terminate()
        QtCore.QTimer.singleShot(3000, self._kill_if_running)

    def _kill_if_running(self) -> None:
        if self.process.state() != QtCore.QProcess.NotRunning:
            self.process.kill()

    def _finished(self, exit_code: int, _status: QtCore.QProcess.ExitStatus) -> None:
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.ship.setEnabled(True)
        self.mode.setEnabled(True)
        self.add_ship_button.setEnabled(True)
        self.add_mode_button.setEnabled(True)
        self.navigate.setEnabled(True)
        self.continuous.setEnabled(True)
        self._continuous_changed(self.continuous.isChecked())
        self.status.setText(f"已结束：退出码 {exit_code}")

    def _continuous_changed(self, checked: bool) -> None:
        if checked:
            self.return_port.setChecked(False)
        self.return_port.setEnabled(
            not checked and self.process.state() == QtCore.QProcess.NotRunning
        )

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if self.process.state() != QtCore.QProcess.NotRunning:
            answer = QtWidgets.QMessageBox.question(
                self,
                "任务正在运行",
                "关闭窗口将停止自动化进程，是否继续？",
            )
            if answer != QtWidgets.QMessageBox.Yes:
                event.ignore()
                return
            self.process.kill()
            self.process.waitForFinished(2000)
        super().closeEvent(event)
