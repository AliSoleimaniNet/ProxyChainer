"""
utils/log.py
In-memory log buffer with optional file persistence.
Never calls page.update() — callers handle UI refresh.
"""

import datetime
import pathlib
import threading
from typing import Callable

import flet as ft

from ui.theme import MUTED, TEXT_DIM, ACCENT, WARN, DANGER, BG


MAX_ENTRIES = 300

LEVEL_COLORS = {
    "INFO":  TEXT_DIM,
    "OK":    ACCENT,
    "WARN":  WARN,
    "ERROR": DANGER,
}


class Logger:
    def __init__(self, log_file: pathlib.Path | None = None):
        self.entries: list[dict]      = []
        self.controls: list[ft.Control] = []
        self._log_file                = log_file
        self._on_entry: Callable | None = None

    def set_on_entry(self, cb: Callable) -> None:
        """Optional callback fired after each new entry (e.g. to refresh UI)."""
        self._on_entry = cb

    def add(self, msg: str, level: str = "INFO") -> ft.Row:
        ts    = datetime.datetime.now().strftime("%H:%M:%S")
        color = LEVEL_COLORS.get(level, TEXT_DIM)

        row = ft.Row([
            ft.Text(f"[{ts}]", font_family="JetBrains", size=9, color=MUTED),
            ft.Container(
                content=ft.Text(level, font_family="JetBrains", size=9,
                                color=BG, weight=ft.FontWeight.W_700),
                bgcolor=color, border_radius=3,
                padding=ft.Padding(4, 1, 4, 1),
            ),
            ft.Text(msg, font_family="JetBrains", size=9, color=color,
                    selectable=True, expand=True),
        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.START)

        self.entries.append({"ts": ts, "level": level, "msg": msg})
        self.controls.append(row)

        if len(self.controls) > MAX_ENTRIES:
            self.controls[:] = self.controls[-MAX_ENTRIES:]
            self.entries[:]  = self.entries[-MAX_ENTRIES:]

        if self._log_file:
            threading.Thread(target=self._write_file,
                             args=(ts, level, msg), daemon=True).start()

        return row

    def clear(self) -> None:
        self.entries.clear()
        self.controls.clear()

    def to_text(self) -> str:
        return "\n".join(
            f"[{e['ts']}] [{e['level']}] {e['msg']}" for e in self.entries
        )

    def _write_file(self, ts: str, level: str, msg: str) -> None:
        try:
            with open(self._log_file, "a", encoding="utf-8") as fh:
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                fh.write(f"[{now}] [{level}] {msg}\n")
        except Exception:
            pass
