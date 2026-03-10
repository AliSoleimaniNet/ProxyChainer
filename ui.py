"""
ui.py  —  ProxyChainer UI
All business logic lives in config.py / save.py / network.py / parser.py
"""

import flet as ft
import threading

from network import get_ip_info
from config  import build_config_json, get_protocol, get_filename
from save    import save_config

BG       = "#0A0C10"
SURFACE  = "#111318"
CARD     = "#161A22"
BORDER   = "#1E2330"
ACCENT   = "#00FFA3"
ACCENT2  = "#00FFFF"
MUTED    = "#4A5368"
TEXT     = "#E2E8F0"
TEXT_DIM = "#7A8499"
DANGER   = "#FF4757"

def ping_color(ms):
    if ms is None:  return "#888888"
    if ms < 300:    return ACCENT
    if ms < 1000:   return "#FFD700"
    if ms < 5000:   return "#FF8C00"
    if ms < 10000:  return DANGER
    return "#888888"

def bdr(color=BORDER):
    s = ft.BorderSide(1, color)
    return ft.Border(s, s, s, s)

def mono(text, size=10, color=TEXT_DIM):
    return ft.Text(text, font_family="JetBrains", size=size, color=color)

def lbl(text):
    return ft.Row([
        ft.Container(width=3, height=12, bgcolor=ACCENT, border_radius=2),
        ft.Text(text, font_family="Syne-Bold", size=10, color=ACCENT,
                weight=ft.FontWeight.W_600,
                style=ft.TextStyle(letter_spacing=1.5)),
    ], spacing=6)

def glow():
    return ft.Container(
        height=1,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, 0), end=ft.Alignment(1, 0),
            colors=["#00000000", ACCENT+"55", ACCENT2+"33", "#00000000"],
        ),
        margin=ft.Margin(0, 2, 0, 2),
    )

def ibtn(icon, tip, fn, color=MUTED):
    return ft.IconButton(
        icon=icon, icon_color=color, icon_size=15,
        tooltip=tip, on_click=fn,
        style=ft.ButtonStyle(
            overlay_color={ft.ControlState.DEFAULT: "#00000000",
                           ft.ControlState.HOVERED: ACCENT+"18"},
            shape=ft.RoundedRectangleBorder(radius=6),
            padding=ft.Padding(5, 5, 5, 5),
        ),
    )

def tfield(**kw):
    base = dict(
        text_style=ft.TextStyle(font_family="JetBrains", size=11, color=TEXT),
        multiline=True, min_lines=3, max_lines=5,
        expand=True,
        bgcolor=BG, border_color=BORDER,
        focused_border_color=ACCENT, cursor_color=ACCENT,
        label_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=10),
        hint_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=10),
        content_padding=ft.Padding(10, 10, 10, 10),
        border_radius=8,
    )
    base.update(kw)
    return ft.TextField(**base)

def build_page(page: ft.Page) -> None:
    page.title      = "ProxyChainer"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding    = 0
    page.bgcolor    = BG

    page.fonts = {
        "JetBrains":      "fonts/JetBrainsMono-Regular.ttf",
        "JetBrains-Bold": "fonts/JetBrainsMono-Bold.ttf",
        "Syne-Bold":      "fonts/Syne-Bold.ttf",
        "Syne-ExtraBold": "fonts/Syne-ExtraBold.ttf",
    }

    socks_input = tfield(label="SOCKS PROXY", hint_text="socks://user:pass@host:port")
    proxy_input = tfield(
        label="PROXY CONFIG (vless / vmess / trojan / ss)",
        hint_text="vless:// or vmess:// or trojan:// or ss://",
    )
    output_field = ft.TextField(
        multiline=True, min_lines=12, max_lines=30,
        read_only=True, expand=True, filled=True,
        text_style=ft.TextStyle(font_family="JetBrains", size=10, color=ACCENT2),
        bgcolor=BG, border_color=BORDER,
        focused_border_color=ACCENT2, cursor_color=ACCENT2,
        content_padding=ft.Padding(10, 10, 10, 10), border_radius=8,
        hint_text="Generated config appears here…",
        hint_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=10),
    )
    mobile_switch = ft.Switch(active_color=ACCENT2, value=False)
    status_dot    = ft.Container(width=6, height=6, bgcolor=ACCENT, border_radius=50)
    status_text   = ft.Text("READY", font_family="JetBrains", size=10,
                            color=ACCENT, weight=ft.FontWeight.W_600)
    ip_val    = ft.Text("—", font_family="JetBrains", size=10, color=ACCENT)
    city_val  = ft.Text("—", font_family="JetBrains", size=10, color=TEXT)
    ping_val  = ft.Text("—", font_family="JetBrains", size=10, color=MUTED,
                        weight=ft.FontWeight.W_600)
    ping_dot  = ft.Container(width=6, height=6, bgcolor="#888888", border_radius=50)
    fetch_lbl = ft.Text("", font_family="JetBrains", size=9, color=ACCENT2)

    def set_status(msg, color=ACCENT, dot=ACCENT):
        status_text.value  = msg
        status_text.color  = color
        status_dot.bgcolor = dot
        page.update()

    def refresh_ip(e):
        fetch_lbl.value = "…"
        page.update()
        def _run():
            info = get_ip_info()
            if info:
                pc = ping_color(info["ping"])
                ip_val.value     = info["ip"]
                city_val.value   = f"{info['city']}, {info['country']}"
                ping_val.value   = f"{info['ping']} ms" if info["ping"] else "N/A"
                ping_val.color   = pc
                ping_dot.bgcolor = pc
                fetch_lbl.value  = ""
                set_status("IP INFO LOADED", ACCENT, ACCENT)
            else:
                ip_val.value    = "ERROR"
                fetch_lbl.value = ""
                set_status("CONNECTION ERROR", DANGER, DANGER)
            page.update()
        threading.Thread(target=_run, daemon=True).start()

    async def process_chain(e):
        set_status("PROCESSING…", ACCENT2, ACCENT2)
        try:
            json_text = build_config_json(
                socks_input.value,
                proxy_input.value,
                mobile_switch.value,
            )
            proto = get_protocol(proxy_input.value)
            output_field.value = json_text
            await ft.Clipboard().set(json_text)
            mode = "MOBILE" if mobile_switch.value else "DESKTOP"
            set_status(f"✓ {mode} · {proto.upper()} — COPIED", ACCENT, ACCENT)
            page.update()
        except Exception as ex:
            set_status(f"ERROR: {ex}", DANGER, DANGER)
            page.update()

    async def copy_output(e):
        if output_field.value:
            await ft.Clipboard().set(output_field.value)
            set_status("COPIED  ✓", ACCENT, ACCENT)

    async def paste_socks(e):
        socks_input.value = await ft.Clipboard().get() or ""
        page.update()

    async def paste_proxy(e):
        proxy_input.value = await ft.Clipboard().get() or ""
        page.update()

    def clear_all(e):
        socks_input.value = proxy_input.value = output_field.value = ""
        set_status("CLEARED", MUTED, MUTED)
        page.update()

    # saved_path holds the last saved path so we can show it under output card
    saved_path_text = ft.Text("", font_family="JetBrains", size=9, color=ACCENT,
                               selectable=True)   # selectable so user can copy it

    async def export_json(e):
        if not output_field.value:
            set_status("GENERATE FIRST", DANGER, DANGER)
            return
        try:
            name = get_filename(socks_input.value, proxy_input.value) + "-" + ("mobile" if mobile_switch.value else "desktop")
        except Exception:
            name = ""
        ok, msg = await save_config(output_field.value, page=page, name=name)
        if ok:
            set_status("SAVED ✓  (see path below)", ACCENT, ACCENT)
            saved_path_text.value = f"📁  {msg}"
            saved_path_text.color = ACCENT
        else:
            set_status(msg, DANGER, DANGER)
            saved_path_text.value = f"✗  {msg}"
            saved_path_text.color = DANGER
        page.update()

    header_container = ft.Container(
        bgcolor=SURFACE,
        border=ft.Border(bottom=ft.BorderSide(1, BORDER)),
    )
    body_col = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)
    footer_container = ft.Container(
        bgcolor=SURFACE,
        border=ft.Border(top=ft.BorderSide(1, BORDER)),
    )

    def rebuild(e=None):
        w   = page.width or 400
        pad = 10 if w < 400 else 14

        # On very narrow screens: only show the dot, hide the text label
        # On medium screens: show dot + short text (no overflow)
        # On wide screens: full pill with full text
        if w < 360:
            # Just the dot — absolute minimum
            status_pill = ft.Container(
                content=status_dot,
                padding=ft.Padding(6, 6, 6, 6),
                bgcolor=CARD, border_radius=5, border=bdr(),
            )
        elif w < 540:
            # Dot + text but max_width capped so it never pushes title off
            status_text.max_lines = 1
            status_text.overflow  = ft.TextOverflow.ELLIPSIS
            status_text.size      = 9
            status_pill = ft.Container(
                content=ft.Row([status_dot, status_text], spacing=4, tight=True),
                padding=ft.Padding(6, 4, 6, 4),
                bgcolor=CARD, border_radius=5, border=bdr(),
                width=min(w * 0.42, 160),   # max 42% of screen width
            )
        else:
            status_text.max_lines = 1
            status_text.overflow  = ft.TextOverflow.ELLIPSIS
            status_text.size      = 10
            status_pill = ft.Container(
                content=ft.Row([status_dot, status_text], spacing=4, tight=True),
                padding=ft.Padding(7, 4, 7, 4),
                bgcolor=CARD, border_radius=5, border=bdr(),
            )

        if w < 480:
            hbody = ft.Column([
                ft.Row([
                    ft.Container(width=3, height=18, bgcolor=ACCENT, border_radius=2),
                    ft.Text("PROXY CHAINER", font_family="Syne-ExtraBold",
                            size=13, color=TEXT, weight=ft.FontWeight.W_800),
                    ft.Container(expand=True),
                    status_pill,
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Text("SOCKS → VLESS / VMess / Trojan / SS",
                        font_family="JetBrains", size=8, color=TEXT_DIM),
            ], spacing=2, tight=True)
        else:
            hbody = ft.Row([
                ft.Row([
                    ft.Container(width=4, height=22, bgcolor=ACCENT, border_radius=2),
                    ft.Column([
                        ft.Text("PROXY CHAINER", font_family="Syne-ExtraBold",
                                size=16, color=TEXT, weight=ft.FontWeight.W_800,
                                style=ft.TextStyle(letter_spacing=2)),
                        ft.Text("SOCKS → VLESS / VMess / Trojan / SS",
                                font_family="JetBrains", size=9, color=TEXT_DIM),
                    ], spacing=1, tight=True),
                ], spacing=8),
                status_pill,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
               vertical_alignment=ft.CrossAxisAlignment.CENTER)

        header_container.content = ft.Container(
            content=hbody, padding=ft.Padding(pad, 10, pad, 10),
        )

        socks_card = ft.Container(
            content=ft.Column([
                ft.Row([lbl("01  //  SOCKS"),
                        ibtn(ft.Icons.CONTENT_PASTE, "Paste", paste_socks)],
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=6),
                ft.Row([socks_input]),
            ], spacing=0),
            padding=ft.Padding(12, 12, 12, 12),
            bgcolor=CARD, border_radius=10, border=bdr(),
        )
        proxy_card = ft.Container(
            content=ft.Column([
                ft.Row([lbl("02  //  CONFIG"),
                        ibtn(ft.Icons.CONTENT_PASTE, "Paste", paste_proxy)],
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=6),
                ft.Row([proxy_input]),
            ], spacing=0),
            padding=ft.Padding(12, 12, 12, 12),
            bgcolor=CARD, border_radius=10, border=bdr(),
        )

        if w < 600:
            socks_card.expand = False
            proxy_card.expand = False
            cards = ft.Column([socks_card, proxy_card], spacing=10)
        else:
            socks_card.expand = True
            proxy_card.expand = True
            cards = ft.Row([socks_card, proxy_card], spacing=12,
                           vertical_alignment=ft.CrossAxisAlignment.START)

        mob_label = ft.Text("MOB", font_family="JetBrains", size=9,
                            color=TEXT if mobile_switch.value else MUTED)
        pc_label  = ft.Text("PC",  font_family="JetBrains", size=9,
                            color=TEXT if not mobile_switch.value else MUTED)

        def _on_switch(e):
            mob_label.color = TEXT if mobile_switch.value else MUTED
            pc_label.color  = TEXT if not mobile_switch.value else MUTED
            page.update()
        mobile_switch.on_change = _on_switch

        toggle_card = ft.Container(
            content=ft.Column([
                ft.Text("MODE", font_family="JetBrains", size=8, color=ACCENT),
                ft.Row([pc_label, mobile_switch, mob_label],
                       spacing=2, tight=True,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], spacing=2, tight=True,
               horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(14, 8, 14, 8),
            bgcolor=CARD, border_radius=10, border=bdr(),
        )

        gen_btn = ft.Container(
            content=ft.GestureDetector(
                content=ft.Row([
                    ft.Icon(ft.Icons.BOLT, color=BG, size=16),
                    ft.Text("GENERATE CONFIG", font_family="Syne-Bold", size=13,
                            color=BG, weight=ft.FontWeight.W_700,
                            style=ft.TextStyle(letter_spacing=0.8)),
                ], spacing=8, tight=True,
                   alignment=ft.MainAxisAlignment.CENTER),
                on_tap=lambda e: page.run_task(process_chain, e),
            ),
            expand=True, height=56,
            bgcolor=ACCENT, border_radius=10,
            alignment=ft.Alignment(0, 0),
        )

        gen_row = ft.Row([toggle_card, gen_btn], spacing=10,
                         vertical_alignment=ft.CrossAxisAlignment.CENTER)

        output_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    lbl("03  //  JSON OUTPUT"),
                    ft.Row([
                        ibtn(ft.Icons.COPY_ALL,         "Copy",     copy_output, ACCENT2),
                        ibtn(ft.Icons.DOWNLOAD_ROUNDED, "Download", export_json, ACCENT),
                        ibtn(ft.Icons.DELETE_OUTLINE,   "Clear",    clear_all,   MUTED),
                    ], spacing=0),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=6),
                ft.Row([output_field]),
                ft.Text(
                    "Auto-copied on generate · re-copy or download with buttons above",
                    font_family="JetBrains", size=9, color=MUTED,
                ),
                saved_path_text,
            ], spacing=4),
            padding=ft.Padding(12, 12, 12, 12),
            bgcolor=CARD, border_radius=10, border=bdr(),
        )

        body_col.controls = [
            ft.Container(
                content=ft.Column([
                    cards, glow(), gen_row, glow(), output_card,
                ], spacing=10),
                padding=ft.Padding(pad, pad, pad, pad),
            )
        ]

        footer_container.content = ft.GestureDetector(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.LANGUAGE, color=MUTED, size=11),
                        mono("IP", 9), ip_val,
                        ft.Container(width=1, height=8, bgcolor=BORDER,
                                     margin=ft.Margin(4, 0, 4, 0)),
                        mono("CITY", 9), city_val,
                        ft.Container(width=1, height=8, bgcolor=BORDER,
                                     margin=ft.Margin(4, 0, 4, 0)),
                        mono("PING", 9), ping_val, ping_dot,
                        fetch_lbl,
                    ], spacing=3, wrap=True,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Row([
                        ft.Icon(ft.Icons.REFRESH, color=MUTED, size=10),
                        mono("Tap to refresh", 9, MUTED),
                    ], spacing=3),
                ], spacing=3, tight=True),
                padding=ft.Padding(pad, 8, pad, 8),
            ),
            on_tap=refresh_ip,
        )

        page.update()

    page.on_resized = rebuild
    page.add(
        ft.Column([header_container, body_col, footer_container],
                  spacing=0, expand=True)
    )
    rebuild()
    threading.Thread(target=lambda: refresh_ip(None), daemon=True).start()