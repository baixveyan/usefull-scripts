from __future__ import annotations

import ctypes
import json
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import win32api
import win32con
import win32gui
import win32process

from wows_assistant.capture.windows import WindowInfo, get_client_rect


class EmergencyStopError(RuntimeError):
    pass


@dataclass(frozen=True)
class ClickAudit:
    occurred_at: str
    hwnd: int
    label: str
    client_x: int
    client_y: int
    screen_x: int
    screen_y: int
    executed: bool


@dataclass(frozen=True)
class KeyAudit:
    occurred_at: str
    hwnd: int
    label: str
    key: str
    executed: bool


class GuardedClickExecutor:
    """Minimal live input with foreground and F12 emergency-stop guards."""

    def __init__(self, window: WindowInfo, audit_path: str | Path) -> None:
        self.window = window
        self.audit_path = Path(audit_path)

    @staticmethod
    def emergency_stop_pressed() -> bool:
        return bool(win32api.GetAsyncKeyState(win32con.VK_F12) & 0x8000)

    def check_emergency_stop(self) -> None:
        if self.emergency_stop_pressed():
            raise EmergencyStopError("F12 emergency stop pressed")

    def focus_target(self, *, timeout_seconds: float = 3.0) -> None:
        self.check_emergency_stop()
        if not win32gui.IsWindow(self.window.hwnd) or win32gui.IsIconic(self.window.hwnd):
            raise RuntimeError("目标游戏窗口不存在或已最小化")
        self._request_foreground()
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            self.check_emergency_stop()
            if win32gui.GetForegroundWindow() == self.window.hwnd:
                return
            time.sleep(0.05)
        raise RuntimeError("无法确认游戏窗口位于前台，拒绝输入")

    def _request_foreground(self) -> None:
        try:
            win32gui.SetForegroundWindow(self.window.hwnd)
        except win32gui.error:
            pass
        if win32gui.GetForegroundWindow() == self.window.hwnd:
            return

        user32 = ctypes.windll.user32
        current_thread = win32api.GetCurrentThreadId()
        foreground = win32gui.GetForegroundWindow()
        foreground_thread = (
            win32process.GetWindowThreadProcessId(foreground)[0] if foreground else 0
        )
        target_thread = win32process.GetWindowThreadProcessId(self.window.hwnd)[0]
        attached: list[int] = []
        try:
            for thread_id in {foreground_thread, target_thread}:
                if (
                    thread_id
                    and thread_id != current_thread
                    and user32.AttachThreadInput(current_thread, thread_id, True)
                ):
                    attached.append(thread_id)
            win32gui.BringWindowToTop(self.window.hwnd)
            try:
                win32gui.SetForegroundWindow(self.window.hwnd)
            except win32gui.error:
                pass
        finally:
            for thread_id in reversed(attached):
                user32.AttachThreadInput(current_thread, thread_id, False)

    def click_client(self, client_x: int, client_y: int, *, label: str) -> ClickAudit:
        self.focus_target()
        rect = get_client_rect(self.window.hwnd)
        if not (0 <= client_x < rect.width and 0 <= client_y < rect.height):
            raise ValueError("点击坐标超出游戏客户区")
        screen_x = rect.left + client_x
        screen_y = rect.top + client_y
        self.check_emergency_stop()
        win32api.SetCursorPos((screen_x, screen_y))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.06)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        audit = ClickAudit(
            occurred_at=datetime.now(UTC).isoformat(),
            hwnd=self.window.hwnd,
            label=label,
            client_x=client_x,
            client_y=client_y,
            screen_x=screen_x,
            screen_y=screen_y,
            executed=True,
        )
        self._append_audit(audit)
        return audit

    def press_key(self, key: str, *, label: str) -> KeyAudit:
        self.focus_target()
        normalized_key = key.upper()
        if normalized_key == "ESC":
            virtual_key = win32con.VK_ESCAPE
        elif len(normalized_key) == 1:
            virtual_key = ord(normalized_key)
        else:
            raise ValueError("当前只允许单字符按键或 ESC")
        self.check_emergency_stop()
        win32api.keybd_event(virtual_key, 0, 0, 0)
        time.sleep(0.08)
        win32api.keybd_event(virtual_key, 0, win32con.KEYEVENTF_KEYUP, 0)
        audit = KeyAudit(
            occurred_at=datetime.now(UTC).isoformat(),
            hwnd=self.window.hwnd,
            label=label,
            key=key.upper(),
            executed=True,
        )
        self._append_audit(audit)
        return audit

    def _append_audit(self, audit: ClickAudit | KeyAudit) -> None:
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(asdict(audit), ensure_ascii=False) + "\n")
