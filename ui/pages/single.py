"""
ui/pages/single.py
SINGLE tab — generate a chained config from N proxy URLs (min 2, unlimited max).
"""

import flet as ft

from ui.theme import BG, CARD, BORDER, ACCENT, ACCENT2, MUTED, TEXT, DANGER
from ui.components.primitives import (
    border, section_label, glow_divider, icon_button,
    proxy_input, generate_button,
)


class SinglePage:
    def __init__(self, mobile_switch: ft.Switch, on_generate, on_copy,
                 on_paste, on_export, on_clear):
        """
        on_paste(index)  — called with hop index when paste button clicked
        """
        # Start with 2 hops
        self._hop_fields: list[ft.TextField] = []
        self._add_hop_field()
        self._add_hop_field()

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
        self._on_paste      = on_paste   # callable(index)
        self._on_copy       = on_copy
        self._on_export     = on_export
        self._on_clear      = on_clear

        # We hold a ref to page so hop add/remove can call page.update()
        self._page: ft.Page | None = None

    # ── Hop field management ──────────────────────────────────────────────────

    def _add_hop_field(self) -> ft.TextField:
        field = proxy_input(
            label=f"HOP {len(self._hop_fields) + 1}  —  socks:// · vless:// · vmess:// · trojan:// · ss://",
            hint="socks://host:port#Name  or  vless://...#Name",
        )
        self._hop_fields.append(field)
        return field

    def _relabel_fields(self) -> None:
        for i, f in enumerate(self._hop_fields):
            f.label = f"HOP {i + 1}  —  socks:// · vless:// · vmess:// · trojan:// · ss://"

    @property
    def hop_values(self) -> list[str]:
        return [f.value.strip() for f in self._hop_fields]

    def set_hop_value(self, index: int, value: str) -> None:
        if 0 <= index < len(self._hop_fields):
            self._hop_fields[index].value = value

    # ── Busy state ────────────────────────────────────────────────────────────

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

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self, width: int, toggle_card: ft.Container, page: ft.Page) -> ft.Column:
        self._page = page
        hop_cards  = self._build_hop_cards(width)

        # Add hop button
        add_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=ACCENT2, size=14),
                ft.Text("ADD HOP", font_family="Syne-Bold", size=10,
                        color=ACCENT2, weight=ft.FontWeight.W_700,
                        style=ft.TextStyle(letter_spacing=0.8)),
            ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
            on_click=self._on_add_hop,
            bgcolor=CARD, border_radius=8,
            border=border(ACCENT2 + "55"),
            padding=ft.Padding(14, 8, 14, 8),
            height=36,
        )

        gen_row = ft.Row(
            [toggle_card, self._gen_btn], spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        output_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    section_label(f"{'02' if len(self._hop_fields) == 2 else str(len(self._hop_fields) + 1).zfill(2)}  //  JSON OUTPUT"),
                    ft.Row([
                        icon_button(ft.Icons.COPY_ALL,         "Copy",     self._on_copy,   ACCENT2),
                        icon_button(ft.Icons.DOWNLOAD_ROUNDED, "Download", self._on_export, ACCENT),
                        icon_button(ft.Icons.DELETE_OUTLINE,   "Clear",    self._on_clear,  MUTED),
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
            [hop_cards, add_btn, glow_divider(), gen_row, glow_divider(), output_card],
            spacing=10,
        )

    def _build_hop_cards(self, width: int) -> ft.Control:
        """Build all hop input cards, responsive layout."""
        cards = [self._hop_card(i, width) for i in range(len(self._hop_fields))]

        if width < 600 or len(self._hop_fields) > 2:
            # Stack vertically when narrow or more than 2 hops
            for c in cards:
                c.expand = False
            return ft.Column(cards, spacing=10)
        else:
            for c in cards:
                c.expand = True
            return ft.Row(cards, spacing=12,
                          vertical_alignment=ft.CrossAxisAlignment.START)

    def _hop_card(self, index: int, width: int = 800) -> ft.Container:
        field      = self._hop_fields[index]
        hop_num    = index + 1
        can_remove = len(self._hop_fields) > 2

        label_text = f"{str(hop_num).zfill(2)}  //  HOP {hop_num}"

        actions = ft.Row([
            section_label(label_text),
            ft.Row([
                icon_button(ft.Icons.CONTENT_PASTE, "Paste",
                            lambda e, i=index: self._on_paste(i)),
                *(
                    [icon_button(ft.Icons.REMOVE_CIRCLE_OUTLINE, "Remove hop",
                                 lambda e, i=index: self._on_remove_hop(i), DANGER)]
                    if can_remove else []
                ),
            ], spacing=0),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        return ft.Container(
            content=ft.Column([
                actions,
                ft.Container(height=6),
                ft.Row([field]),
            ], spacing=0),
            padding=ft.Padding(12, 12, 12, 12),
            bgcolor=CARD, border_radius=10, border=border(),
        )

    # ── Hop add / remove ──────────────────────────────────────────────────────

    def _on_add_hop(self, e=None) -> None:
        self._add_hop_field()
        self._relabel_fields()
        if self._page:
            self._page.run_task(self._rebuild_page)

    def _on_remove_hop(self, index: int, e=None) -> None:
        if len(self._hop_fields) <= 2:
            return
        self._hop_fields.pop(index)
        self._relabel_fields()
        if self._page:
            self._page.run_task(self._rebuild_page)

    async def _rebuild_page(self) -> None:
        """Ask the app-level rebuild to re-render (via page resize trick)."""
        if self._page:
            self._page.on_resized and self._page.on_resized(None)