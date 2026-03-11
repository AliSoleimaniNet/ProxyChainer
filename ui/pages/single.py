"""
ui/pages/single.py
SINGLE tab — generate a chained config from two proxy URLs.
"""

import flet as ft

from ui.theme import BG, CARD, BORDER, ACCENT, ACCENT2, MUTED, TEXT
from ui.components.primitives import (
    border, section_label, glow_divider, icon_button,
    proxy_input, generate_button,
)


class SinglePage:
    def __init__(self, mobile_switch: ft.Switch, on_generate, on_copy,
                 on_paste_hop1, on_paste_hop2, on_export, on_clear):
        self.hop1_input = proxy_input(
            label="HOP 1  —  socks:// · vless:// · vmess:// · trojan:// · ss://",
            hint="socks://host:port#Name  or  vless://...#Name",
        )
        self.hop2_input = proxy_input(
            label="HOP 2  —  socks:// · vless:// · vmess:// · trojan:// · ss://",
            hint="vless://...#Name  or  vmess://...  or  trojan://...",
        )
        self.output_field = ft.TextField(
            multiline=True, min_lines=10, max_lines=28,
            read_only=True, expand=True, filled=True,
            text_style=ft.TextStyle(font_family="JetBrains", size=10, color=ACCENT2),
            bgcolor=BG, border_color=BORDER,
            focused_border_color=ACCENT2, cursor_color=ACCENT2,
            content_padding=ft.Padding(10, 10, 10, 10), border_radius=8,
            hint_text="Generated config appears here…",
            hint_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=10),
        )
        self.saved_path_text = ft.Text(
            "", font_family="JetBrains", size=9, color=ACCENT, selectable=True)

        self._gen_btn, self._gen_icon, self._gen_label = generate_button(
            "GENERATE CONFIG", on_generate,
        )

        self._mobile_switch = mobile_switch
        self._on_paste_hop1 = on_paste_hop1
        self._on_paste_hop2 = on_paste_hop2
        self._on_copy       = on_copy
        self._on_export     = on_export
        self._on_clear      = on_clear

    def set_busy(self, busy: bool, page: ft.Page) -> None:
        if busy:
            self._gen_icon.name    = ft.Icons.HOURGLASS_TOP
            self._gen_label.value  = "WORKING…"
            self._gen_btn.bgcolor  = MUTED
            self._gen_btn.opacity  = 0.55
        else:
            self._gen_icon.name    = ft.Icons.BOLT
            self._gen_label.value  = "GENERATE CONFIG"
            self._gen_btn.bgcolor  = ACCENT
            self._gen_btn.opacity  = 1.0
        page.update()

    def build(self, width: int, toggle_card: ft.Container) -> ft.Column:
        hop1_card = self._input_card("01  //  HOP 1", self.hop1_input, self._on_paste_hop1)
        hop2_card = self._input_card("02  //  HOP 2", self.hop2_input, self._on_paste_hop2)

        if width < 600:
            hop1_card.expand = hop2_card.expand = False
            input_row = ft.Column([hop1_card, hop2_card], spacing=10)
        else:
            hop1_card.expand = hop2_card.expand = True
            input_row = ft.Row([hop1_card, hop2_card], spacing=12,
                               vertical_alignment=ft.CrossAxisAlignment.START)

        gen_row = ft.Row(
            [toggle_card, self._gen_btn], spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        output_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    section_label("03  //  JSON OUTPUT"),
                    ft.Row([
                        icon_button(ft.Icons.COPY_ALL,        "Copy",     self._on_copy,   ACCENT2),
                        icon_button(ft.Icons.DOWNLOAD_ROUNDED,"Download", self._on_export, ACCENT),
                        icon_button(ft.Icons.DELETE_OUTLINE,  "Clear",    self._on_clear,  MUTED),
                    ], spacing=0),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=6),
                ft.Row([self.output_field]),
                ft.Text("Auto-copied · re-copy or download with buttons above",
                        font_family="JetBrains", size=9, color=MUTED),
                self.saved_path_text,
            ], spacing=4),
            padding=ft.Padding(12, 12, 12, 12),
            bgcolor=CARD, border_radius=10, border=border(),
        )

        return ft.Column(
            [input_row, glow_divider(), gen_row, glow_divider(), output_card],
            spacing=10,
        )

    def _input_card(self, label: str, field: ft.TextField, on_paste) -> ft.Container:
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
