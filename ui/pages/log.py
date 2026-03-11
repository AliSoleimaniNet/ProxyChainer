"""
ui/pages/log.py
LOG tab — scrollable in-memory log viewer with copy and clear actions.
"""

import flet as ft

from ui.theme import BG, CARD, BORDER, ACCENT2, MUTED
from ui.components.primitives import border, section_label, icon_button


def build_log_page(
    log_controls: list[ft.Control],
    log_info: str,
    on_copy,
    on_clear,
) -> ft.Column:
    log_list = ft.Column(
        controls=log_controls,
        spacing=3,
        scroll=ft.ScrollMode.AUTO,
    )
    log_card = ft.Container(
        content=ft.Column([
            ft.Row([
                section_label("📋  LOGS"),
                ft.Row([
                    ft.Text(log_info, font_family="JetBrains", size=8, color=MUTED),
                    icon_button(ft.Icons.COPY_ALL,       "Copy",  on_copy,  ACCENT2),
                    icon_button(ft.Icons.DELETE_OUTLINE, "Clear", on_clear, MUTED),
                ], spacing=0),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=6),
            ft.Container(
                content=log_list, bgcolor=BG, border_radius=8,
                padding=ft.Padding(10, 10, 10, 10), border=border(),
                height=420, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            ),
        ], spacing=4),
        padding=ft.Padding(12, 12, 12, 12),
        bgcolor=CARD, border_radius=10, border=border(),
    )

    return ft.Column([log_card], spacing=10)
