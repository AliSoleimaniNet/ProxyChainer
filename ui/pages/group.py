"""
ui/pages/group.py
GROUP tab — batch-generate configs from two lists of proxy URLs.
"""

import flet as ft

from ui.theme import BG, CARD, BORDER, ACCENT, ACCENT2, MUTED, TEXT, TEXT_DIM
from ui.components.primitives import (
    border, section_label, glow_divider, icon_button, generate_button,
)


class GroupPage:
    def __init__(self, mobile_switch: ft.Switch, on_generate,
                 on_paste_hop1, on_paste_hop2, on_clear):
        self.hop1_input = ft.TextField(
            label="HOP 1 LIST  —  one URL per line",
            hint_text="socks://1.1.1.1:1080#Server1\nvless://...#Server2",
            multiline=True, min_lines=4, max_lines=8, expand=True,
            text_style=ft.TextStyle(font_family="JetBrains", size=10, color=TEXT),
            bgcolor=BG, border_color=BORDER,
            focused_border_color=ACCENT, cursor_color=ACCENT,
            label_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=10),
            hint_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=10),
            content_padding=ft.Padding(10, 10, 10, 10), border_radius=8,
        )
        self.hop2_input = ft.TextField(
            label="HOP 2 LIST  —  one URL per line",
            hint_text="vless://...#Proxy1\nvmess://...#Proxy2",
            multiline=True, min_lines=4, max_lines=8, expand=True,
            text_style=ft.TextStyle(font_family="JetBrains", size=10, color=TEXT),
            bgcolor=BG, border_color=BORDER,
            focused_border_color=ACCENT2, cursor_color=ACCENT2,
            label_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=10),
            hint_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=10),
            content_padding=ft.Padding(10, 10, 10, 10), border_radius=8,
        )
        self.folder_input = ft.TextField(
            label="FOLDER NAME  (optional)", hint_text="MyConfigs",
            multiline=False, expand=True,
            text_style=ft.TextStyle(font_family="JetBrains", size=11, color=TEXT),
            bgcolor=BG, border_color=BORDER,
            focused_border_color=ACCENT, cursor_color=ACCENT,
            label_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=10),
            hint_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=10),
            content_padding=ft.Padding(10, 10, 10, 10), border_radius=8,
        )
        self.preview_text  = ft.Text("Enter URLs above", font_family="JetBrains",
                                     size=10, color=TEXT_DIM)
        self.result_text   = ft.Text("", font_family="JetBrains", size=9,
                                     color=ACCENT, selectable=True)
        self.progress_bar  = ft.ProgressBar(
            value=0, bgcolor=BORDER, color=ACCENT,
            height=4, border_radius=2, visible=False,
        )

        self._gen_btn, self._gen_icon, self._gen_label = generate_button(
            "GENERATE ALL & SAVE", on_generate,
        )

        self._mobile_switch  = mobile_switch
        self._on_paste_hop1  = on_paste_hop1
        self._on_paste_hop2  = on_paste_hop2
        self._on_clear       = on_clear

    def set_busy(self, busy: bool, page: ft.Page) -> None:
        if busy:
            self._gen_icon.name   = ft.Icons.HOURGLASS_TOP
            self._gen_label.value = "WORKING…"
            self._gen_btn.bgcolor = MUTED
            self._gen_btn.opacity = 0.55
        else:
            self._gen_icon.name   = ft.Icons.BOLT
            self._gen_label.value = "GENERATE ALL & SAVE"
            self._gen_btn.bgcolor = ACCENT
            self._gen_btn.opacity = 1.0
        page.update()

    def update_preview(self, mobile: bool) -> None:
        h1 = self._parse_lines(self.hop1_input.value)
        h2 = self._parse_lines(self.hop2_input.value)
        n  = len(h1) * len(h2)
        if n == 0:
            self.preview_text.value = "Enter URLs above to see combination count"
            self.preview_text.color = TEXT_DIM
        else:
            mode = "MOBILE" if mobile else "DESKTOP"
            self.preview_text.value = f"⚡  {len(h1)} × {len(h2)} = {n} configs  ·  {mode}"
            self.preview_text.color = ACCENT

    @staticmethod
    def _parse_lines(text: str) -> list[str]:
        return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]

    def build(self, width: int, toggle_card: ft.Container) -> ft.Column:
        g1_card = self._list_card("HOP 1  LIST", self.hop1_input, self._on_paste_hop1)
        g2_card = self._list_card("HOP 2  LIST", self.hop2_input, self._on_paste_hop2)

        if width < 600:
            g1_card.expand = g2_card.expand = False
            lists = ft.Column([g1_card, g2_card], spacing=10)
        else:
            g1_card.expand = g2_card.expand = True
            lists = ft.Row([g1_card, g2_card], spacing=12,
                           vertical_alignment=ft.CrossAxisAlignment.START)

        folder_card = ft.Container(
            content=ft.Column([
                section_label("FOLDER NAME"),
                ft.Container(height=6),
                ft.Row([self.folder_input]),
            ], spacing=0),
            padding=ft.Padding(12, 12, 12, 12),
            bgcolor=CARD, border_radius=10, border=border(),
        )
        preview_card = ft.Container(
            content=ft.Column([self.preview_text, self.progress_bar], spacing=6, tight=True),
            padding=ft.Padding(12, 10, 12, 10),
            bgcolor=CARD, border_radius=8, border=border(),
        )
        gen_row = ft.Row(
            [toggle_card, self._gen_btn], spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        result_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    section_label("RESULT"),
                    icon_button(ft.Icons.DELETE_OUTLINE, "Clear", self._on_clear, MUTED),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=4),
                self.result_text,
            ], spacing=4),
            padding=ft.Padding(12, 12, 12, 12),
            bgcolor=CARD, border_radius=10, border=border(),
        )

        return ft.Column([
            lists, glow_divider(), folder_card,
            preview_card, glow_divider(), gen_row,
            glow_divider(), result_card,
        ], spacing=10)

    def _list_card(self, label: str, field: ft.TextField, on_paste) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    section_label(label),
                    icon_button(ft.Icons.CONTENT_PASTE, "Paste", on_paste),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=6),
                ft.Row([field]),
            ], spacing=0),
            padding=ft.Padding(12, 12, 12, 12),
            bgcolor=CARD, border_radius=10, border=border(),
        )
