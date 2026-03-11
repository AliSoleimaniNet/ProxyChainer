"""
ui/layouts/header.py
App header — responsive single-line (mobile) vs full (desktop).
Returns the header content directly (not a wrapper Container).
"""

import flet as ft

from ui.theme import SURFACE, BORDER, ACCENT, TEXT, TEXT_DIM


def build_header(width: int, pad: int) -> ft.Container:
    if width < 480:
        body = ft.Column([
            ft.Row([
                ft.Container(width=3, height=18, bgcolor=ACCENT, border_radius=2),
                ft.Text("PROXY CHAINER", font_family="Syne-ExtraBold",
                        size=13, color=TEXT, weight=ft.FontWeight.W_800),
            ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Text("ANY→ANY · VLESS · VMess · Trojan · SS · SOCKS",
                    font_family="JetBrains", size=8, color=TEXT_DIM),
        ], spacing=2, tight=True)
    else:
        body = ft.Row([
            ft.Container(width=4, height=22, bgcolor=ACCENT, border_radius=2),
            ft.Column([
                ft.Text("PROXY CHAINER", font_family="Syne-ExtraBold",
                        size=16, color=TEXT, weight=ft.FontWeight.W_800,
                        style=ft.TextStyle(letter_spacing=2)),
                ft.Text("ANY → ANY  ·  VLESS · VMess · Trojan · SS · SOCKS",
                        font_family="JetBrains", size=9, color=TEXT_DIM),
            ], spacing=1, tight=True),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    # Returns a single Container — used directly as header_container.content
    return ft.Container(
        content=body,
        padding=ft.Padding(pad, 10, pad, 10),
        bgcolor=SURFACE,
        border=ft.Border(bottom=ft.BorderSide(1, BORDER)),
    )