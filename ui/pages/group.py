"""
ui/pages/group.py
GROUP tab — batch-generate configs from N lists of proxy URLs.
Each column = one hop position. Min 2 hops, unlimited max.
Output is a single JSON array file containing all configs.
"""

import flet as ft

from ui.theme import BG, CARD, BORDER, ACCENT, ACCENT2, MUTED, TEXT, TEXT_DIM, DANGER
from ui.components.primitives import (
    border, section_label, glow_divider, icon_button, generate_button,
)


class GroupPage:
    def __init__(self, mobile_switch: ft.Switch, on_generate,
                 on_paste, on_clear):
        """
        on_paste(index)  — called with hop-list index when paste clicked
        """
        # Start with 2 hop lists
        self._hop_inputs: list[ft.TextField] = []
        self._add_hop_input()
        self._add_hop_input()

        self.file_name_input = ft.TextField(
            label="FILE NAME  (optional)", hint_text="MyConfigs",
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

        self._mobile_switch = mobile_switch
        self._on_paste      = on_paste   # callable(index)
        self._on_clear      = on_clear
        self._page: ft.Page | None = None

    # ── Hop input management ──────────────────────────────────────────────────

    def _add_hop_input(self) -> ft.TextField:
        n = len(self._hop_inputs) + 1
        field = ft.TextField(
            label=f"HOP {n} LIST  —  one URL per line",
            hint_text="socks://1.1.1.1:1080#Server1\nvless://...#Server2",
            multiline=True, min_lines=4, max_lines=8, expand=True,
            text_style=ft.TextStyle(font_family="JetBrains", size=10, color=TEXT),
            bgcolor=BG, border_color=BORDER,
            focused_border_color=ACCENT if n % 2 == 1 else ACCENT2,
            cursor_color=ACCENT if n % 2 == 1 else ACCENT2,
            label_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=10),
            hint_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=10),
            content_padding=ft.Padding(10, 10, 10, 10), border_radius=8,
        )
        self._hop_inputs.append(field)
        return field

    def _relabel_inputs(self) -> None:
        for i, f in enumerate(self._hop_inputs):
            f.label = f"HOP {i + 1} LIST  —  one URL per line"
            f.focused_border_color = ACCENT if i % 2 == 0 else ACCENT2
            f.cursor_color         = ACCENT if i % 2 == 0 else ACCENT2

    @property
    def hop_lists(self) -> list[list[str]]:
        """Returns a list-of-lists, one inner list per hop position."""
        return [self._parse_lines(f.value) for f in self._hop_inputs]

    # ── Busy state ────────────────────────────────────────────────────────────

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
        lists = self.hop_lists
        counts = [len(lst) for lst in lists]
        if any(c == 0 for c in counts):
            self.preview_text.value = "Enter URLs in all hop columns to see count"
            self.preview_text.color = TEXT_DIM
            return
        total = 1
        for c in counts:
            total *= c
        mode = "MOBILE" if mobile else "DESKTOP"
        sizes = " × ".join(str(c) for c in counts)
        self.preview_text.value = f"⚡  {sizes} = {total} configs  ·  {mode}"
        self.preview_text.color = ACCENT

    @staticmethod
    def _parse_lines(text: str) -> list[str]:
        return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self, width: int, toggle_card: ft.Container, page: ft.Page) -> ft.Column:
        self._page = page

        # Register on_change for all hop inputs
        for f in self._hop_inputs:
            f.on_change = lambda e: (self.update_preview(self._mobile_switch.value),
                                     page.update())

        hop_cards = [self._list_card(i) for i in range(len(self._hop_inputs))]
        can_remove = len(self._hop_inputs) > 2

        # Responsive: stack vertically when narrow or >2 hops
        if width < 600 or len(self._hop_inputs) > 2:
            for c in hop_cards:
                c.expand = False
            lists_widget: ft.Control = ft.Column(hop_cards, spacing=10)
        else:
            for c in hop_cards:
                c.expand = True
            lists_widget = ft.Row(hop_cards, spacing=12,
                                  vertical_alignment=ft.CrossAxisAlignment.START)

        # Add hop button
        add_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=ACCENT2, size=14),
                ft.Text("ADD HOP COLUMN", font_family="Syne-Bold", size=10,
                        color=ACCENT2, weight=ft.FontWeight.W_700,
                        style=ft.TextStyle(letter_spacing=0.8)),
            ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
            on_click=self._on_add_hop,
            bgcolor=CARD, border_radius=8,
            border=border(ACCENT2 + "55"),
            padding=ft.Padding(14, 8, 14, 8),
            height=36,
        )

        file_name_card = ft.Container(
            content=ft.Column([
                section_label("OUTPUT FILE NAME"),
                ft.Container(height=6),
                ft.Row([self.file_name_input]),
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
            lists_widget, add_btn, glow_divider(),
            file_name_card, preview_card,
            glow_divider(), gen_row,
            glow_divider(), result_card,
        ], spacing=10)

    def _list_card(self, index: int) -> ft.Container:
        field      = self._hop_inputs[index]
        hop_num    = index + 1
        can_remove = len(self._hop_inputs) > 2

        actions = ft.Row([
            section_label(f"HOP {hop_num}  LIST"),
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
        self._add_hop_input()
        self._relabel_inputs()
        if self._page:
            self._page.run_task(self._rebuild_page)

    def _on_remove_hop(self, index: int, e=None) -> None:
        if len(self._hop_inputs) <= 2:
            return
        self._hop_inputs.pop(index)
        self._relabel_inputs()
        if self._page:
            self._page.run_task(self._rebuild_page)

    async def _rebuild_page(self) -> None:
        if self._page:
            self._page.on_resized and self._page.on_resized(None)