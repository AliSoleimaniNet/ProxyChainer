"""
ui/layouts/footer.py
Persistent footer — status row + IP/ping row, no wrap, no phantom height.
"""

import flet as ft

from ui.theme import SURFACE, BORDER, ACCENT, MUTED, TEXT
from ui.components.primitives import mono


class Footer:
    def __init__(self, on_log_tap, on_ip_refresh):
        # ── Leaf widget refs ──────────────────────────────────────────────────
        self.status_dot  = ft.Container(width=8, height=8, bgcolor=ACCENT, border_radius=50)
        self.status_text = ft.Text(
            "READY", font_family="JetBrains", size=10,
            color=ACCENT, weight=ft.FontWeight.W_600,
            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, expand=True,
        )
        self.ip_val   = ft.Text("—", font_family="JetBrains", size=10, color=ACCENT)
        self.city_val = ft.Text("—", font_family="JetBrains", size=10, color=TEXT)
        self.ping_val = ft.Text("—", font_family="JetBrains", size=10, color=MUTED,
                                weight=ft.FontWeight.W_600)
        self.ping_dot     = ft.Container(width=7, height=7, bgcolor="#888888", border_radius=50)
        self.refresh_icon = ft.Icon(ft.Icons.REFRESH, color=MUTED, size=14)

        # ── Status row ────────────────────────────────────────────────────────
        self._status_inner = ft.Container(
            content=ft.Row([
                self.status_dot,
                self.status_text,
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=MUTED, size=13),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=SURFACE,
        )

        # ── IP row — wrap=True so items wrap on narrow screens ─────────────────
        self._ip_inner = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.LANGUAGE, color=MUTED, size=13),
                mono("IP", 9),
                self.ip_val,
                ft.Container(width=1, height=12, bgcolor=BORDER, margin=ft.Margin(3, 0, 3, 0)),
                mono("CITY", 9),
                self.city_val,
                ft.Container(width=1, height=12, bgcolor=BORDER, margin=ft.Margin(3, 0, 3, 0)),
                mono("PING", 9),
                self.ping_val,
                self.ping_dot,
                self.refresh_icon,
            ], spacing=4, wrap=True,
               run_spacing=4,
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=SURFACE,
        )

        # ── Separator — no margin, full width, zero height ────────────────────
        self._sep = ft.Divider(height=1, thickness=1, color=BORDER)

        # ── Root container ────────────────────────────────────────────────────
        self.container = ft.Container(
            content=ft.Column([
                ft.GestureDetector(on_tap=on_log_tap,    content=self._status_inner),
                self._sep,
                ft.GestureDetector(on_tap=on_ip_refresh, content=self._ip_inner),
            ], spacing=0, tight=True),
            bgcolor=SURFACE,
            border=ft.Border(top=ft.BorderSide(1, BORDER)),
        )

    def set_status(self, msg: str, color: str) -> None:
        self.status_text.value  = msg
        self.status_text.color  = color
        self.status_dot.bgcolor = color

    def set_ip(self, ip: str, city: str, country: str,
               ping_label: str, ping_color: str) -> None:
        self.ip_val.value     = ip
        self.city_val.value   = f"{city}, {country}"
        self.ping_val.value   = ping_label
        self.ping_val.color   = ping_color
        self.ping_dot.bgcolor = ping_color

    def update_padding(self, pad: int) -> None:
        p = ft.Padding(pad, 10, pad, 10)
        self._status_inner.padding = p
        self._ip_inner.padding     = p