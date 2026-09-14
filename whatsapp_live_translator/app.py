from __future__ import annotations

import ctypes
import ctypes.wintypes
import difflib
import hashlib
import json
import queue
import re
import sqlite3
import sys
import threading
import time
import tkinter as tk
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

import numpy as np
from PIL import Image, ImageGrab, ImageTk
from rapidocr_onnxruntime import RapidOCR


APP_NAME = "WhatsApp 多会话翻译"
BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_FILE = DATA_DIR / "chats.db"
AVATAR_DIR = DATA_DIR / "avatars"
MEDIA_PLACEHOLDER = "[图片/视频]"
TARGETS = {
    "简体中文": "zh-CN", "繁体中文": "zh-TW", "英语": "en",
    "法语": "fr", "西班牙语": "es", "德语": "de", "日语": "ja", "韩语": "ko",
}
LANGUAGES = {"自动识别": "auto", **TARGETS}

user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi
try:
    user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception:
    pass


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


def window_text(hwnd: int) -> str:
    size = user32.GetWindowTextLengthW(hwnd) + 1
    buf = ctypes.create_unicode_buffer(size)
    user32.GetWindowTextW(hwnd, buf, size)
    return buf.value


def class_name(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def find_whatsapp_window() -> int:
    matches: list[int] = []
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    def visit(hwnd, _param):
        if user32.IsWindowVisible(hwnd) and window_text(hwnd) == "WhatsApp":
            if class_name(hwnd) == "WinUIDesktopWin32WindowClass":
                matches.append(int(hwnd))
        return True
    user32.EnumWindows(callback_type(visit), 0)
    return matches[0] if matches else 0


def get_rect(hwnd: int) -> tuple[int, int, int, int] | None:
    rect = RECT()
    if not hwnd:
        return None
    # DWMWA_EXTENDED_FRAME_BOUNDS excludes the invisible resize border that
    # otherwise creates a visible gap and height mismatch beside WhatsApp.
    if dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(rect), ctypes.sizeof(rect)) != 0:
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return None
    return rect.left, rect.top, rect.right, rect.bottom


def foreground_belongs_to(hwnd: int) -> bool:
    foreground = user32.GetForegroundWindow()
    return bool(hwnd and (foreground == hwnd or user32.GetAncestor(foreground, 2) == hwnd))


def caption_height(hwnd: int) -> int:
    dpi = user32.GetDpiForWindow(hwnd) if hasattr(user32, "GetDpiForWindow") else 96
    if hasattr(user32, "GetSystemMetricsForDpi"):
        caption = user32.GetSystemMetricsForDpi(4, dpi)
        frame = user32.GetSystemMetricsForDpi(33, dpi)
        return max(42, caption + frame * 2)
    return 50


def is_chinese(text: str) -> bool:
    letters = re.findall(r"[A-Za-z\u3400-\u9fff]", text)
    return bool(letters) and len(re.findall(r"[\u3400-\u9fff]", text)) / len(letters) >= 0.3


def guess_source(text: str) -> str:
    low = " " + text.lower() + " "
    if is_chinese(text): return "zh-CN"
    if re.search(r"[¿¡ñáéíóúü]", low) or any(f" {w} " in low for w in ("hola", "gracias", "usted", "para", "buenos")): return "es"
    if re.search(r"[àâçèéêëîïôùûüÿœ]", low) or any(f" {w} " in low for w in ("bonjour", "merci", "vous", "avec", "pour")): return "fr"
    return "en"


def online_translate(text: str, target: str, timeout: int = 15) -> str:
    params = urllib.parse.urlencode({"client": "at", "sl": "auto", "tl": target, "dt": "t", "q": text})
    request = urllib.request.Request(
        "https://translate.google.com/translate_a/single?" + params,
        headers={"User-Agent": "GoogleTranslate/6.45.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        result = "".join(p[0] for p in data[0] if p and p[0]).strip()
        if result: return result
    except Exception:
        pass
    source = guess_source(text)
    params = urllib.parse.urlencode({"q": text, "langpair": f"{source}|{target}"})
    request = urllib.request.Request("https://api.mymemory.translated.net/get?" + params, headers={"User-Agent": "WhatsAppSideTranslator/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    result = data.get("responseData", {}).get("translatedText", "").strip()
    if not result: raise RuntimeError("翻译服务没有返回内容")
    return result


class Store:
    def __init__(self) -> None:
        DATA_DIR.mkdir(exist_ok=True)
        self.db = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.lock = threading.Lock()
        with self.db:
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS chats (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, avatar_hash TEXT NOT NULL DEFAULT '',
                    target TEXT NOT NULL DEFAULT 'zh-CN', last_seen TEXT NOT NULL,
                    peer_lang TEXT NOT NULL DEFAULT 'auto', my_lang TEXT NOT NULL DEFAULT 'zh-CN'
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id TEXT NOT NULL, stamp TEXT NOT NULL,
                    direction TEXT NOT NULL, original TEXT NOT NULL, translation TEXT NOT NULL DEFAULT '',
                    fingerprint TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL
                );
            """)
            columns = {row[1] for row in self.db.execute("PRAGMA table_info(chats)")}
            if "peer_lang" not in columns:
                self.db.execute("ALTER TABLE chats ADD COLUMN peer_lang TEXT NOT NULL DEFAULT 'auto'")
            if "my_lang" not in columns:
                self.db.execute("ALTER TABLE chats ADD COLUMN my_lang TEXT NOT NULL DEFAULT 'zh-CN'")
        self.merge_duplicate_chats()
        self.clear_messages()

    def clear_messages(self) -> None:
        with self.lock, self.db:
            self.db.execute("DELETE FROM messages")

    def merge_duplicate_chats(self) -> None:
        with self.lock, self.db:
            rows = self.db.execute("SELECT id,name,last_seen FROM chats ORDER BY last_seen DESC").fetchall()
            groups: dict[str, list[tuple[str,str,str]]] = {}
            for row in rows:
                groups.setdefault(self.normalize_name(row[1]), []).append(row)
            for duplicates in groups.values():
                if len(duplicates) < 2: continue
                keeper = duplicates[0][0]
                for duplicate_id, _name, _seen in duplicates[1:]:
                    self.db.execute("UPDATE messages SET chat_id=? WHERE chat_id=?", (keeper, duplicate_id))
                    self.db.execute("DELETE FROM chats WHERE id=?", (duplicate_id,))

    def upsert_chat(self, chat_id: str, name: str, avatar_hash: str = "") -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with self.lock, self.db:
            self.db.execute("""INSERT INTO chats(id,name,avatar_hash,last_seen) VALUES(?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET name=excluded.name, avatar_hash=excluded.avatar_hash, last_seen=excluded.last_seen""",
                (chat_id, name, avatar_hash, now))

    def chats(self):
        with self.lock:
            return self.db.execute("SELECT id,name,target,last_seen FROM chats ORDER BY last_seen DESC").fetchall()

    @staticmethod
    def normalize_name(name: str) -> str:
        compact = re.sub(r"\s+", "", name).lower()
        phone = re.sub(r"\D", "", compact)
        if len(phone) >= 7:
            return "phone:" + phone
        return "name:" + re.sub(r"[^\w\u3400-\u9fff]", "", compact)

    def resolve_chat_id(self, name: str, avatar_hash: str) -> str:
        normalized = self.normalize_name(name)
        with self.lock:
            rows = self.db.execute("SELECT id,name FROM chats").fetchall()
        for chat_id, old_name in rows:
            if self.normalize_name(old_name) == normalized:
                return chat_id
        if len(rows) == 1 and re.fullmatch(r"(?:[01]?\d|2[0-3]):[0-5]\d", rows[0][1].strip()):
            return rows[0][0]
        return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:16]

    def target(self, chat_id: str) -> str:
        with self.lock:
            row = self.db.execute("SELECT target FROM chats WHERE id=?", (chat_id,)).fetchone()
        return row[0] if row else "zh-CN"

    def set_target(self, chat_id: str, target: str) -> None:
        with self.lock, self.db:
            self.db.execute("UPDATE chats SET target=? WHERE id=?", (target, chat_id))

    def languages(self, chat_id: str) -> tuple[str, str]:
        with self.lock:
            row = self.db.execute("SELECT peer_lang,my_lang FROM chats WHERE id=?", (chat_id,)).fetchone()
        return (row[0], row[1]) if row else ("auto", "zh-CN")

    def set_languages(self, chat_id: str, peer_lang: str, my_lang: str) -> None:
        with self.lock, self.db:
            self.db.execute("UPDATE chats SET peer_lang=?,my_lang=? WHERE id=?", (peer_lang, my_lang, chat_id))

    def set_detected_peer_language(self, chat_id: str, detected: str) -> None:
        with self.lock, self.db:
            self.db.execute("UPDATE chats SET peer_lang=? WHERE id=? AND peer_lang='auto'", (detected, chat_id))

    def add_message(self, chat_id: str, stamp: str, direction: str, original: str, translation: str = "", fingerprint: str | None = None, deduplicate: bool = True) -> int | None:
        canonical = self.canonical_message(original)
        if not canonical:
            return None
        # OCR may change spaces, punctuation, ticks, or one character between
        # scans. Compare against recent messages before relying on an exact hash.
        with self.lock:
            recent = self.db.execute(
                "SELECT stamp,original,created_at FROM messages WHERE chat_id=? AND direction=? ORDER BY id DESC LIMIT 40",
                (chat_id, direction),
            ).fetchall()
        now = datetime.now()
        for old_stamp, old_original, created_at in (recent if deduplicate else []):
            old = self.canonical_message(old_original)
            if not old:
                continue
            same_minute = old_stamp == stamp
            try:
                recent_scan = (now - datetime.fromisoformat(created_at)).total_seconds() <= 20
            except ValueError:
                recent_scan = True
            exact = old == canonical
            contained = min(len(old), len(canonical)) >= 5 and (old in canonical or canonical in old)
            similar = min(len(old), len(canonical)) >= 8 and difflib.SequenceMatcher(None, old, canonical).ratio() >= .88
            if recent_scan and same_minute and (exact or contained or similar):
                return None
        fingerprint_source = f"{chat_id}|{stamp}|{direction}|{canonical}"
        if not deduplicate:
            fingerprint_source += f"|{time.time_ns()}"
        fingerprint = fingerprint or hashlib.sha1(fingerprint_source.encode()).hexdigest()
        try:
            with self.lock, self.db:
                cur = self.db.execute("INSERT INTO messages(chat_id,stamp,direction,original,translation,fingerprint,created_at) VALUES(?,?,?,?,?,?,?)",
                    (chat_id, stamp, direction, original, translation, fingerprint, datetime.now().isoformat(timespec="seconds")))
                return int(cur.lastrowid)
        except sqlite3.IntegrityError:
            return None

    @staticmethod
    def canonical_message(text: str) -> str:
        if text == MEDIA_PLACEHOLDER:
            return text
        text = re.sub(r"(?:[01]?\d|2[0-3]):[0-5]\d", "", text)
        text = re.sub(r"[✓✔√]+", "", text)
        return re.sub(r"[^0-9A-Za-z\u3400-\u9fffÀ-ÿ]+", "", text).lower()

    def set_translation(self, message_id: int, translation: str) -> None:
        with self.lock, self.db:
            self.db.execute("UPDATE messages SET translation=? WHERE id=?", (translation, message_id))

    def messages(self, chat_id: str):
        with self.lock:
            return self.db.execute("SELECT id,stamp,direction,original,translation FROM messages WHERE chat_id=? ORDER BY id", (chat_id,)).fetchall()


class WhatsAppSidecar:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("620x720+1300+80")
        self.root.minsize(560, 520)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#111b21")
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)
        self.store = Store()
        self.ocr = RapidOCR()
        self.events: queue.Queue[tuple] = queue.Queue()
        self.current_chat = ""
        self.current_name = "未识别会话"
        self.observed_chat = ""
        self.observed_name = ""
        self.whatsapp_hwnd = 0
        self.monitoring = tk.BooleanVar(value=True)
        self.follow_chat = tk.BooleanVar(value=True)
        self.ocr_busy = False
        self.last_chat_hash = ""
        self.last_window_rect = None
        self.drag_origin = None
        self.avatar_photo = None
        self.build_ui()
        self.refresh_chats()
        self.root.after(300, self.follow_window)
        self.root.after(900, self.monitor_tick)
        self.root.after(100, self.poll_events)

    def build_ui(self) -> None:
        self.top = tk.Frame(self.root, bg="#f7f5f3", height=50)
        self.top.pack(fill="x")
        self.top.bind("<ButtonPress-1>", self.begin_drag)
        self.top.bind("<B1-Motion>", self.drag_window)
        top = self.top
        top.pack_propagate(False)
        tk.Label(top, text="◉  WhatsApp 翻译", bg="#f7f5f3", fg="#111b21", font=("Microsoft YaHei UI", 11, "bold")).pack(side="left", padx=12)
        tk.Button(top, text="×", command=self.exit_app, bg="#f7f5f3", fg="#111b21", activebackground="#e25555", activeforeground="white", relief="flat", font=("Arial", 15), width=3).pack(side="right", fill="y")
        tk.Checkbutton(top, text="自动监听", variable=self.monitoring, bg="#f7f5f3", fg="#111b21", selectcolor="#ffffff", activebackground="#f7f5f3", activeforeground="#111b21").pack(side="right", padx=8)

        body = tk.PanedWindow(self.root, orient="horizontal", sashwidth=4, bg="#111b21", bd=0)
        body.pack(fill="both", expand=True)
        self.chat_list = tk.Frame(body, bg="#111b21", width=165)
        body.add(self.chat_list, minsize=150, width=175)
        self.chat_list_content = tk.Frame(self.chat_list, bg="#111b21")
        self.chat_list_content.pack(fill="both", expand=True)
        self.cache_settings = tk.Frame(self.chat_list, bg="#0b141a", padx=8, pady=9)
        self.cache_settings.pack(fill="x", side="bottom")
        self.follow_check = tk.Checkbutton(self.cache_settings, text="跟随当前对话", variable=self.follow_chat, command=self.toggle_follow, bg="#0b141a", fg="#e9edef", selectcolor="#202c33", activebackground="#0b141a", activeforeground="white")
        self.follow_check.grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,6))
        tk.Label(self.cache_settings, text="对方语言", bg="#0b141a", fg="#8696a0", font=("Microsoft YaHei UI", 8)).grid(row=1,column=0,sticky="w",pady=2)
        tk.Label(self.cache_settings, text="我的语言", bg="#0b141a", fg="#8696a0", font=("Microsoft YaHei UI", 8)).grid(row=2,column=0,sticky="w",pady=2)
        self.peer_language_name = tk.StringVar(value="自动识别")
        self.my_language_name = tk.StringVar(value="简体中文")
        self.peer_language_combo = ttk.Combobox(self.cache_settings, textvariable=self.peer_language_name, values=list(LANGUAGES), state="readonly", width=8)
        self.my_language_combo = ttk.Combobox(self.cache_settings, textvariable=self.my_language_name, values=list(TARGETS), state="readonly", width=8)
        self.peer_language_combo.grid(row=1,column=1,sticky="e",pady=2)
        self.my_language_combo.grid(row=2,column=1,sticky="e",pady=2)
        self.peer_language_combo.bind("<<ComboboxSelected>>", self.change_languages)
        self.my_language_combo.bind("<<ComboboxSelected>>", self.change_languages)
        conversation = tk.Frame(body, bg="#efeae2")
        body.add(conversation, minsize=360)

        chat_header = tk.Frame(conversation, bg="#f0f2f5", height=82)
        chat_header.pack(fill="x")
        chat_header.pack_propagate(False)
        self.avatar = tk.Label(chat_header, text="?", bg="#00a884", fg="white", width=3, font=("Microsoft YaHei UI", 14, "bold"))
        self.avatar.pack(side="left", padx=10, pady=10)
        self.chat_title = tk.StringVar(value="等待打开 WhatsApp 对话")
        tk.Label(chat_header, textvariable=self.chat_title, bg="#f0f2f5", fg="#111b21", font=("Microsoft YaHei UI", 11, "bold"), anchor="w").pack(side="left", fill="x", expand=True)

        self.canvas = tk.Canvas(conversation, bg="#efeae2", highlightthickness=0)
        scroll = ttk.Scrollbar(conversation, orient="vertical", command=self.canvas.yview)
        self.message_frame = tk.Frame(self.canvas, bg="#efeae2")
        self.message_window = self.canvas.create_window((0, 0), window=self.message_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="top", fill="both", expand=True)
        scroll.place(relx=1, rely=.09, relheight=.72, anchor="ne")
        self.message_frame.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.message_window, width=e.width))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-e.delta / 120), "units"))

        composer = tk.Frame(conversation, bg="#f0f2f5", padx=8, pady=8)
        composer.pack(fill="x", side="bottom")
        self.input = tk.Text(composer, height=3, wrap="word", relief="flat", padx=8, pady=6, font=("Microsoft YaHei UI", 10))
        self.input.pack(fill="x")
        self.input.bind("<Control-Return>", lambda _e: self.translate_and_add())
        row = tk.Frame(composer, bg="#f0f2f5")
        row.pack(fill="x", pady=(6, 0))
        self.status = tk.StringVar(value="等待 WhatsApp 窗口")
        tk.Label(row, textvariable=self.status, bg="#f0f2f5", fg="#667781", anchor="w").pack(side="left", fill="x", expand=True)
        tk.Button(row, text="翻译并加入", command=self.translate_and_add, bg="#00a884", fg="white", relief="flat", padx=12, pady=5).pack(side="right")

    def refresh_chats(self) -> None:
        for child in self.chat_list_content.winfo_children(): child.destroy()
        tk.Label(self.chat_list_content, text="聊天缓存", bg="#111b21", fg="#8696a0", anchor="w", padx=10, pady=10).pack(fill="x")
        for chat_id, name, target, _seen in self.store.chats():
            label = (name[:16] + "…") if len(name) > 16 else name
            button = tk.Button(self.chat_list_content, text=f"  {label}", anchor="w", relief="flat", bg="#202c33" if chat_id == self.current_chat else "#111b21", fg="#e9edef", activebackground="#2a3942", activeforeground="white", disabledforeground="#667781", state="disabled" if self.follow_chat.get() else "normal", command=lambda cid=chat_id, n=name: self.select_chat(cid, n, manual=True))
            button.pack(fill="x", pady=1, ipady=8)

    def select_chat(self, chat_id: str, name: str, manual: bool = False) -> None:
        if manual and self.follow_chat.get():
            return
        self.current_chat, self.current_name = chat_id, name
        self.chat_title.set(name)
        self.show_avatar(chat_id, name)
        peer_lang, my_lang = self.store.languages(chat_id)
        self.peer_language_name.set(next((n for n, code in LANGUAGES.items() if code == peer_lang), "自动识别"))
        self.my_language_name.set(next((n for n, code in TARGETS.items() if code == my_lang), "简体中文"))
        self.render_messages()
        self.refresh_chats()

    def toggle_follow(self) -> None:
        if self.follow_chat.get() and self.observed_chat:
            self.select_chat(self.observed_chat, self.observed_name)
        else:
            self.refresh_chats()

    def show_avatar(self, chat_id: str, name: str) -> None:
        path = AVATAR_DIR / f"{chat_id}.png"
        try:
            image = Image.open(path).convert("RGB")
            image.thumbnail((48,48), Image.Resampling.LANCZOS)
            self.avatar_photo = ImageTk.PhotoImage(image)
            self.avatar.config(image=self.avatar_photo, text="", width=48, height=48)
        except Exception:
            self.avatar_photo = None
            self.avatar.config(image="", text=(name.strip()[:1] or "?"), width=3, height=2)

    def change_languages(self, _event=None) -> None:
        if self.current_chat:
            self.store.set_languages(self.current_chat, LANGUAGES[self.peer_language_name.get()], TARGETS[self.my_language_name.get()])

    def begin_drag(self, event: tk.Event) -> None:
        self.drag_origin = (event.x_root, event.y_root, self.root.winfo_x(), self.root.winfo_y())

    def drag_window(self, event: tk.Event) -> None:
        if self.drag_origin:
            sx, sy, wx, wy = self.drag_origin
            self.root.geometry(f"+{wx + event.x_root-sx}+{wy + event.y_root-sy}")

    def render_messages(self) -> None:
        for child in self.message_frame.winfo_children(): child.destroy()
        if not self.current_chat: return
        for mid, stamp, direction, original, translation in self.store.messages(self.current_chat):
            self.add_bubble(mid, stamp, direction, original, translation)
        self.root.after(30, lambda: self.canvas.yview_moveto(1.0))

    def add_bubble(self, mid: int, stamp: str, direction: str, original: str, translation: str) -> None:
        outgoing = direction == "out"
        holder = tk.Frame(self.message_frame, bg="#efeae2")
        holder.pack(fill="x", padx=8, pady=4)
        bubble = tk.Frame(holder, bg="#d9fdd3" if outgoing else "white", padx=9, pady=7)
        bubble.pack(side="right" if outgoing else "left", anchor="e" if outgoing else "w")
        if original == MEDIA_PLACEHOLDER:
            media = tk.Frame(bubble, width=220, height=120, bg="#d3d8db")
            media.pack_propagate(False); media.pack()
            tk.Label(media, text="▧\n图片 / 视频", bg="#d3d8db", fg="#667781", font=("Microsoft YaHei UI", 12, "bold")).pack(expand=True)
        else:
            tk.Label(bubble, text=original, wraplength=340, justify="left", bg=bubble["bg"], fg="#111b21", font=("Microsoft YaHei UI", 10)).pack(anchor="w")
        if translation:
            tk.Frame(bubble, bg="#aebac1", height=1).pack(fill="x", pady=5)
            tk.Label(bubble, text=translation, wraplength=340, justify="left", bg=bubble["bg"], fg="#008069", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w")
            tk.Button(bubble, text="复制译文", command=lambda t=translation: self.copy_text(t), relief="flat", bg="#00a884", fg="white", font=("Microsoft YaHei UI", 8)).pack(anchor="e", pady=(5, 0))
        tk.Label(bubble, text=stamp or datetime.now().strftime("%H:%M"), bg=bubble["bg"], fg="#667781", font=("Microsoft YaHei UI", 7)).pack(anchor="e")

    def copy_text(self, text: str) -> None:
        self.root.clipboard_clear(); self.root.clipboard_append(text); self.root.update()
        self.status.set("译文已复制，可粘贴到 WhatsApp")

    def follow_window(self) -> None:
        hwnd = find_whatsapp_window()
        if hwnd:
            self.whatsapp_hwnd = hwnd
            rect = get_rect(hwnd)
            if rect and rect != self.last_window_rect:
                self.last_window_rect = rect
                left, top, right, bottom = rect
                screen_right = self.root.winfo_vrootx() + self.root.winfo_screenwidth()
                available = screen_right - right
                width = min(660, max(520, available)) if available >= 520 else 520
                x = right if available >= 520 else max(0, right - width)
                height = max(300, bottom-top-1)
                self.top.configure(height=caption_height(hwnd))
                self.root.geometry(f"{width}x{height}+{x}+{top}")
            self.status.set("已绑定 WhatsApp" if self.monitoring.get() else "监听已暂停")
        else:
            self.status.set("未找到 WhatsApp 窗口")
        self.root.after(500, self.follow_window)

    def monitor_tick(self) -> None:
        if self.monitoring.get() and self.whatsapp_hwnd and foreground_belongs_to(self.whatsapp_hwnd) and not self.ocr_busy:
            rect = get_rect(self.whatsapp_hwnd)
            if rect:
                self.ocr_busy = True
                threading.Thread(target=self.capture_and_parse, args=(rect,), daemon=True).start()
        self.root.after(1200, self.monitor_tick)

    @staticmethod
    def average_hash(image: Image.Image) -> str:
        gray = np.asarray(image.convert("L").resize((8, 8)))
        bits = (gray > gray.mean()).astype(np.uint8).flatten()
        return "".join(map(str, bits.tolist()))

    def capture_and_parse(self, rect: tuple[int, int, int, int]) -> None:
        try:
            left, top, right, bottom = rect
            image = ImageGrab.grab(bbox=rect, all_screens=True)
            w, h = image.size
            cap_height = caption_height(self.whatsapp_hwnd)
            scale = cap_height / 50
            header_top, header_bottom = cap_height, min(h, cap_height + round(136*cap_height/44))
            header = image.crop((int(w*.28), header_top, int(w*.96), header_bottom))
            header_result, _ = self.ocr(np.asarray(header))
            name, name_x = self.extract_chat_name(header_result or [], header.size)
            if not name:
                self.events.put(("capture_done",)); return
            absolute_name_x = int(w*.28) + name_x
            avatar_size = max(48, round(88*scale))
            avatar_left = max(0, absolute_name_x - round(94*scale))
            avatar_top = header_top + round(20*scale)
            avatar = image.crop((avatar_left, avatar_top, avatar_left+avatar_size, avatar_top+avatar_size))
            chat_left = max(int(w*.24), avatar_left-round(18*scale))
            chat = image.crop((chat_left, header_bottom, w, max(header_bottom+1, h-round(94*scale))))
            avatar_hash = self.average_hash(avatar)
            chat_id = self.store.resolve_chat_id(name, avatar_hash)
            AVATAR_DIR.mkdir(parents=True, exist_ok=True)
            avatar.save(AVATAR_DIR / f"{chat_id}.png", "PNG")
            chat_hash = hashlib.sha1(chat.resize((64, 64)).tobytes()).hexdigest()
            payload = []
            if chat_hash != self.last_chat_hash:
                self.last_chat_hash = chat_hash
                result, _ = self.ocr(np.asarray(chat))
                payload = self.parse_messages(result or [], chat.size)
            self.events.put(("capture", chat_id, name, avatar_hash, payload))
        except Exception as exc:
            self.events.put(("capture_error", str(exc)))

    @staticmethod
    def extract_chat_name(result, size: tuple[int,int]) -> tuple[str,int]:
        width, height = size
        items = []
        for box, text, score in result:
            text = text.strip()
            if not text or float(score) < .42: continue
            x = min(p[0] for p in box)
            y = (min(p[1] for p in box) + max(p[1] for p in box)) / 2
            box_height = max(p[1] for p in box)-min(p[1] for p in box)
            if x < width*.08 or box_height < 10: continue
            items.append((y, x, text, box_height))
        if not items: return "", 0
        rows = []
        for item in sorted(items, key=lambda i:i[0]):
            row = next((r for r in rows if abs(r[0][0]-item[0]) < max(12,item[3]*.7)), None)
            if row is None:
                rows.append([item])
            else:
                row.append(item)
        candidates = [r for r in rows if .10*height <= sum(i[0] for i in r)/len(r) <= .78*height]
        if not candidates: return "", 0
        first_line = max(candidates, key=lambda r:(max(i[3] for i in r), sum(len(i[2]) for i in r)))
        name = " ".join(i[2] for i in sorted(first_line, key=lambda i:i[1])).strip()
        return name[:80], int(min(i[1] for i in first_line))

    @staticmethod
    def parse_messages(result, size: tuple[int, int]):
        width, _height = size
        items = []
        for box, text, score in result:
            text = text.strip()
            if not text or float(score) < .45: continue
            x1, x2 = min(p[0] for p in box), max(p[0] for p in box)
            y1, y2 = min(p[1] for p in box), max(p[1] for p in box)
            items.append({"text": text, "x": (x1+x2)/2, "y": (y1+y2)/2, "h": y2-y1})
        stamps = [i for i in items if re.fullmatch(r"(?:[01]?\d|2[0-3]):[0-5]\d", i["text"])]
        messages = []
        used = set()
        stamps = sorted(stamps, key=lambda item: item["y"])
        previous_y = {"in": -1e9, "out": -1e9}
        for stamp in stamps:
            outgoing = stamp["x"] > width*.53
            side = "out" if outgoing else "in"
            lower_bound = max(previous_y[side] + 8, stamp["y"] - 125)
            same = [i for i in items if i is not stamp
                    and lower_bound <= i["y"] <= stamp["y"]+8
                    and ((i["x"] > width*.43) if outgoing else (i["x"] < width*.57))
                    and not re.fullmatch(r"(?:[01]?\d|2[0-3]):[0-5]\d", i["text"])]
            text_parts = [i["text"] for i in sorted(same, key=lambda x:(x["y"],x["x"])) if i["text"] not in ("✓", "✓✓")]
            text = " ".join(text_parts).strip() or MEDIA_PLACEHOLDER
            canonical = Store.canonical_message(text)
            key = (stamp["text"], side, canonical)
            if key in used: continue
            used.add(key)
            messages.append((stamp["text"], side, text))
            previous_y[side] = stamp["y"]
        return messages

    def translate_message(self, mid: int, chat_id: str, text: str, target: str) -> None:
        try:
            translated = online_translate(text, target)
            self.store.set_translation(mid, translated)
            self.events.put(("translated", chat_id))
        except Exception as exc:
            self.events.put(("translation_error", str(exc)))

    def translate_and_add(self) -> None:
        text = self.input.get("1.0", "end").strip()
        if not text or not self.current_chat:
            self.status.set("请先选择会话并输入文字"); return
        self.input.delete("1.0", "end")
        self.status.set("正在翻译输入内容…")
        stamp = datetime.now().strftime("%H:%M")
        mid = self.store.add_message(self.current_chat, stamp, "out", text, fingerprint=hashlib.sha1(f"manual|{self.current_chat}|{time.time_ns()}".encode()).hexdigest(), deduplicate=False)
        if mid:
            self.render_messages()
            peer_lang, my_lang = self.store.languages(self.current_chat)
            if peer_lang == "auto":
                peer_lang = "en" if my_lang.startswith("zh") else "zh-CN"
            threading.Thread(target=self.translate_message, args=(mid, self.current_chat, text, peer_lang), daemon=True).start()

    def poll_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait(); kind = event[0]
                if kind == "capture":
                    _, chat_id, name, avatar_hash, messages = event
                    self.store.upsert_chat(chat_id, name, avatar_hash)
                    self.observed_chat, self.observed_name = chat_id, name
                    if self.follow_chat.get() and chat_id != self.current_chat:
                        self.select_chat(chat_id, name)
                    elif not self.follow_chat.get():
                        self.refresh_chats()
                    if chat_id == self.current_chat:
                        self.show_avatar(chat_id, name)
                    added = 0
                    detected_peer = None
                    for stamp, direction, text in messages:
                        mid = self.store.add_message(chat_id, stamp, direction, text)
                        if mid:
                            added += 1
                            peer_lang, my_lang = self.store.languages(chat_id)
                            if text != MEDIA_PLACEHOLDER and direction == "in" and peer_lang == "auto":
                                detected_peer = guess_source(text)
                                self.store.set_detected_peer_language(chat_id, detected_peer)
                            if text != MEDIA_PLACEHOLDER:
                                threading.Thread(target=self.translate_message, args=(mid, chat_id, text, my_lang), daemon=True).start()
                    if added and chat_id == self.current_chat: self.render_messages()
                    if detected_peer and chat_id == self.current_chat:
                        self.peer_language_name.set(next((n for n, code in LANGUAGES.items() if code == detected_peer), "自动识别"))
                    self.ocr_busy = False
                elif kind == "capture_done": self.ocr_busy = False
                elif kind == "capture_error": self.ocr_busy = False; self.status.set("识别失败：" + event[1])
                elif kind == "translated":
                    if event[1] == self.current_chat: self.render_messages()
                    self.status.set("翻译完成")
                elif kind == "translation_error": self.status.set("翻译失败：" + event[1])
        except queue.Empty:
            pass
        self.root.after(100, self.poll_events)

    def exit_app(self) -> None:
        if messagebox.askyesno(APP_NAME, "退出翻译侧栏？本次消息记录会立即清空，联系人和语言设置会保留。", parent=self.root):
            self.store.clear_messages()
            self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    WhatsAppSidecar().run()
