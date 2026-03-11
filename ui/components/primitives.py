"""
ui/components/primitives.py
Reusable low-level UI primitives.
"""

import flet as ft

from ui.theme import (
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT2, MUTED, TEXT, TEXT_DIM
)


def border(color: str = BORDER) -> ft.Border:
    s = ft.BorderSide(1, color)
    return ft.Border(s, s, s, s)


def mono(text: str, size: int = 10, color: str = TEXT_DIM) -> ft.Text:
    return ft.Text(text, font_family="JetBrains", size=size, color=color)


def section_label(text: str) -> ft.Row:
    return ft.Row([
        ft.Container(width=3, height=12, bgcolor=ACCENT, border_radius=2),
        ft.Text(
            text,
            font_family="Syne-Bold", size=10, color=ACCENT,
            weight=ft.FontWeight.W_600,
            style=ft.TextStyle(letter_spacing=1.5),
        ),
    ], spacing=6)


def glow_divider() -> ft.Container:
    return ft.Container(
        height=1,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, 0), end=ft.Alignment(1, 0),
            colors=["#00000000", ACCENT + "55", ACCENT2 + "33", "#00000000"],
        ),
        margin=ft.Margin(0, 2, 0, 2),
    )


def icon_button(icon: str, tooltip: str, on_click, color: str = MUTED) -> ft.IconButton:
    return ft.IconButton(
        icon=icon, icon_color=color, icon_size=15,
        tooltip=tooltip, on_click=on_click,
        style=ft.ButtonStyle(
            overlay_color={
                ft.ControlState.DEFAULT: "#00000000",
                ft.ControlState.HOVERED: ACCENT + "18",
            },
            shape=ft.RoundedRectangleBorder(radius=6),
            padding=ft.Padding(5, 5, 5, 5),
        ),
    )


def proxy_input(label: str, hint: str) -> ft.TextField:
    return ft.TextField(
        label=label, hint_text=hint,
        text_style=ft.TextStyle(font_family="JetBrains", size=11, color=TEXT),
        multiline=True, min_lines=3, max_lines=5, expand=True,
        bgcolor=BG, border_color=BORDER,
        focused_border_color=ACCENT, cursor_color=ACCENT,
        label_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=10),
        hint_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=10),
        content_padding=ft.Padding(10, 10, 10, 10), border_radius=8,
    )


def generate_button(label: str, on_tap) -> tuple[ft.Container, ft.Icon, ft.Text]:
    icon_widget  = ft.Icon(ft.Icons.BOLT, color=BG, size=15)
    label_widget = ft.Text(
        label, font_family="Syne-Bold", size=12,
        color=BG, weight=ft.FontWeight.W_700,
        style=ft.TextStyle(letter_spacing=0.8),
    )

    # ۱. Row برای چیدمان محتوا
    inner = ft.Row(
        [icon_widget, label_widget], 
        spacing=6, 
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # ۲. استفاده از رشته "transparent" به جای ft.colors برای حذف خطا
    # و ft.Alignment(0, 0) برای مرکز کردن دقیق
    click_box = ft.Container(
        content=inner,
        alignment=ft.Alignment(0, 0), 
        expand=True,
        bgcolor="transparent", # <-- اصلاح شد
    )

    gesture_layer = ft.GestureDetector(
        content=click_box,
        on_tap=on_tap,
        mouse_cursor=ft.MouseCursor.CLICK,
    )

    # ۳. کانتینر اصلی دکمه
    btn = ft.Container(
        content=gesture_layer,
        bgcolor=ACCENT, 
        border_radius=10, 
        height=44,
        expand=True, # پر کردن کل عرض والد
        padding=0,
        animate=ft.Animation(300, "decelerate"),
    )
    
    return btn, icon_widget, label_widget