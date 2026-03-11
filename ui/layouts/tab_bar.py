"""
ui/layouts/tab_bar.py
Tab bar with SINGLE / GROUP / LOG tabs.
"""

import flet as ft

from ui.theme import SURFACE, BORDER, ACCENT, CARD, BG, TEXT_DIM
from ui.components.primitives import border


def build_tab_bar(current: str, pad: int, on_switch) -> ft.Container:
    def _tab(label: str, key: str) -> ft.Container:
        active = current == key
        return ft.Container(
            content=ft.Text(
                label,
                font_family="Syne-Bold", size=10,
                color=BG if active else TEXT_DIM,
                weight=ft.FontWeight.W_700,
                style=ft.TextStyle(letter_spacing=0.8),
            ),
            padding=ft.Padding(14, 8, 14, 8),
            bgcolor=ACCENT if active else CARD,
            border_radius=7,
            border=border(ACCENT if active else BORDER),
            on_click=lambda e, k=key: on_switch(k),
        )

    return ft.Container(
        content=ft.Row([
            _tab("⚡ SINGLE",  "single"),
            _tab("⚡⚡ GROUP",  "group"),
            _tab("📋 LOG",     "log"),
        ], spacing=6),
        padding=ft.Padding(pad, 6, pad, 6),
        bgcolor=SURFACE,
        border=ft.Border(bottom=ft.BorderSide(1, BORDER)),
    )