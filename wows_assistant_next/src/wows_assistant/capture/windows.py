from __future__ import annotations

import ctypes
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import mss
import numpy as np
import win32gui
import win32process
import win32ui

from wows_assistant.models import BoundingBox, FrameRef, ImageFrame, utc_from_timestamp


@dataclass(frozen=True)
class ClientRect:
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    def as_mss_monitor(self) -> dict[str, int]:
        return {"left": self.left, "top": self.top, "width": self.width, "height": self.height}


@dataclass(frozen=True)
class WindowInfo:
    hwnd: int
    title: str
    process_id: int
    visible: bool
    minimized: bool
    client: ClientRect


def enable_dpi_awareness() -> str:
    """Enable per-monitor-v2 DPI awareness without changing system settings."""

    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
        user32.SetProcessDpiAwarenessContext.restype = ctypes.c_bool
        per_monitor_v2 = ctypes.c_void_p(-4 & ((1 << (ctypes.sizeof(ctypes.c_void_p) * 8)) - 1))
        if user32.SetProcessDpiAwarenessContext(per_monitor_v2):
            return "per-monitor-v2"
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return "per-monitor"
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        return "system"
    except (AttributeError, OSError):
        return "unavailable"


def get_client_rect(hwnd: int) -> ClientRect:
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    screen_left, screen_top = win32gui.ClientToScreen(hwnd, (left, top))
    screen_right, screen_bottom = win32gui.ClientToScreen(hwnd, (right, bottom))
    width = screen_right - screen_left
    height = screen_bottom - screen_top
    if width <= 0 or height <= 0:
        raise ValueError(f"窗口客户区尺寸无效: hwnd={hwnd}, {width}x{height}")
    return ClientRect(screen_left, screen_top, width, height)


def list_windows(*, visible_only: bool = True) -> list[WindowInfo]:
    enable_dpi_awareness()
    windows: list[WindowInfo] = []

    def callback(hwnd: int, _: Any) -> bool:
        try:
            if not win32gui.IsWindow(hwnd):
                return True
            visible = bool(win32gui.IsWindowVisible(hwnd))
            if visible_only and not visible:
                return True
            title = win32gui.GetWindowText(hwnd).strip()
            if not title:
                return True
            minimized = bool(win32gui.IsIconic(hwnd))
            client = get_client_rect(hwnd)
            _, process_id = win32process.GetWindowThreadProcessId(hwnd)
        except (ValueError, win32gui.error):
            return True
        windows.append(
            WindowInfo(
                hwnd=hwnd,
                title=title,
                process_id=process_id,
                visible=visible,
                minimized=minimized,
                client=client,
            )
        )
        return True

    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def native_callback(hwnd: int, _: int) -> bool:
        return callback(int(hwnd), None)

    native_callback_ref = callback_type(native_callback)
    user32 = ctypes.windll.user32
    user32.EnumWindows.argtypes = [callback_type, ctypes.c_void_p]
    user32.EnumWindows.restype = ctypes.c_bool
    if not user32.EnumWindows(native_callback_ref, None):
        error = ctypes.get_last_error()
        if error:
            raise OSError(error, "EnumWindows failed")
    return sorted(windows, key=lambda window: (window.title.casefold(), window.hwnd))


def find_windows(title_contains: str, *, windows: list[WindowInfo] | None = None) -> list[WindowInfo]:
    needle = title_contains.casefold().strip()
    if not needle:
        raise ValueError("窗口标题匹配文本不能为空")
    candidates = list_windows() if windows is None else windows
    return [window for window in candidates if needle in window.title.casefold()]


def select_window(title_contains: str, *, windows: list[WindowInfo] | None = None) -> WindowInfo:
    matches = find_windows(title_contains, windows=windows)
    usable = [window for window in matches if not window.minimized]
    if not usable:
        raise LookupError(f"未找到可截图窗口: {title_contains!r}")
    return max(usable, key=lambda window: window.client.width * window.client.height)


class WindowsCapture:
    """Read-only client-area capture. It never focuses or restores a window."""

    def capture(
        self,
        window: WindowInfo,
        *,
        frame_id: int = 0,
        backend: str = "printwindow",
    ) -> ImageFrame:
        if window.minimized:
            raise ValueError("不能截取最小化窗口")
        current_rect = get_client_rect(window.hwnd)
        if backend == "printwindow":
            image = self._capture_printwindow(window.hwnd, current_rect)
        elif backend == "screen":
            foreground = win32gui.GetForegroundWindow()
            if foreground != window.hwnd:
                raise RuntimeError("screen 后端要求目标窗口处于前台，已拒绝截取其他窗口画面")
            with mss.mss() as screenshotter:
                raw = np.asarray(screenshotter.grab(current_rect.as_mss_monitor()))
            image = cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)
        else:
            raise ValueError(f"未知截图后端: {backend}")
        ref = FrameRef(
            frame_id=frame_id,
            timestamp=utc_from_timestamp(time.time()),
            source=f"window:{window.hwnd}:{window.title}",
            width=current_rect.width,
            height=current_rect.height,
        )
        return ImageFrame(ref, image)

    def capture_screen_region(
        self,
        window: WindowInfo,
        region: BoundingBox,
        *,
        frame_id: int = 0,
    ) -> ImageFrame:
        """Capture only a normalized client subregion from the foreground window."""
        if win32gui.GetForegroundWindow() != window.hwnd:
            raise RuntimeError("局部 screen 截图要求目标游戏窗口处于前台")
        rect = get_client_rect(window.hwnd)
        x1, y1, x2, y2 = region.to_pixels(rect.width, rect.height)
        monitor = {
            "left": rect.left + x1,
            "top": rect.top + y1,
            "width": x2 - x1,
            "height": y2 - y1,
        }
        with mss.mss() as screenshotter:
            raw = np.asarray(screenshotter.grab(monitor))
        image = cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)
        ref = FrameRef(
            frame_id=frame_id,
            timestamp=utc_from_timestamp(time.time()),
            source=f"window-region:{window.hwnd}:{window.title}",
            width=monitor["width"],
            height=monitor["height"],
        )
        return ImageFrame(ref, image)

    @staticmethod
    def _capture_printwindow(hwnd: int, rect: ClientRect) -> np.ndarray:
        window_dc_handle = win32gui.GetDC(hwnd)
        window_dc = win32ui.CreateDCFromHandle(window_dc_handle)
        memory_dc = window_dc.CreateCompatibleDC()
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(window_dc, rect.width, rect.height)
        memory_dc.SelectObject(bitmap)
        try:
            # PW_CLIENTONLY | PW_RENDERFULLCONTENT. This does not focus the window.
            result = ctypes.windll.user32.PrintWindow(hwnd, memory_dc.GetSafeHdc(), 3)
            if result != 1:
                raise OSError("PrintWindow 未能渲染目标窗口")
            raw = np.frombuffer(bitmap.GetBitmapBits(True), dtype=np.uint8)
            bgra = raw.reshape((rect.height, rect.width, 4))
            image = cv2.cvtColor(bgra, cv2.COLOR_BGRA2BGR)
            if float(image.std()) < 1.0:
                raise RuntimeError("PrintWindow 返回空白画面")
            return image
        finally:
            win32gui.DeleteObject(bitmap.GetHandle())
            memory_dc.DeleteDC()
            window_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, window_dc_handle)


def save_frame(frame: ImageFrame, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output), frame.image):
        raise OSError(f"无法写入截图: {output}")
    return output
