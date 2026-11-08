import pytest

from wows_assistant.capture.windows import ClientRect, WindowInfo, find_windows, select_window


def make_window(hwnd: int, title: str, width: int, height: int, minimized: bool = False) -> WindowInfo:
    return WindowInfo(
        hwnd=hwnd,
        title=title,
        process_id=100 + hwnd,
        visible=True,
        minimized=minimized,
        client=ClientRect(0, 0, width, height),
    )


def test_find_windows_is_case_insensitive() -> None:
    windows = [make_window(1, "WORLD OF WARSHIPS", 1920, 1080), make_window(2, "Notes", 800, 600)]
    assert [window.hwnd for window in find_windows("World of Warships", windows=windows)] == [1]


def test_select_window_chooses_largest_usable_match() -> None:
    windows = [
        make_window(1, "World of Warships", 1280, 720),
        make_window(2, "World of Warships", 1920, 1080),
        make_window(3, "World of Warships", 2560, 1440, minimized=True),
    ]
    assert select_window("warships", windows=windows).hwnd == 2


def test_select_window_rejects_missing_match() -> None:
    with pytest.raises(LookupError):
        select_window("warships", windows=[])

