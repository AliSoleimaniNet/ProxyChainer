"""
ui.py — ProxyChainer UI
Two tabs: SINGLE (one chain) and GROUP (batch all-to-all).
"""

import flet as ft
import threading
import json

from network import get_ip_info
from config  import build_config_json, build_config, get_protocol, get_filename
from save    import save_config, save_batch

# ── Colors ────────────────────────────────────────────────────────────────────
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
WARN     = "#FFD700"

# ── Helpers ───────────────────────────────────────────────────────────────────
def ping_color(ms):
    if ms is None:  return "#888888"
    if ms < 300:    return ACCENT
    if ms < 1000:   return WARN
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
        multiline=True, min_lines=3, max_lines=5, expand=True,
        bgcolor=BG, border_color=BORDER,
        focused_border_color=ACCENT, cursor_color=ACCENT,
        label_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=10),
        hint_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=10),
        content_padding=ft.Padding(10, 10, 10, 10), border_radius=8,
    )
    base.update(kw)
    return ft.TextField(**base)

def tab_btn(label_text, is_active, on_click):
    return ft.Container(
        content=ft.Text(label_text, font_family="Syne-Bold", size=11,
                        color=BG if is_active else TEXT_DIM,
                        weight=ft.FontWeight.W_700,
                        style=ft.TextStyle(letter_spacing=1)),
        padding=ft.Padding(16, 8, 16, 8),
        bgcolor=ACCENT if is_active else CARD,
        border_radius=8,
        border=bdr(ACCENT if is_active else BORDER),
        on_click=on_click,
    )

# ── Page ──────────────────────────────────────────────────────────────────────
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

    # ── Shared state ──────────────────────────────────────────────────────────
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

    current_tab = {"value": "single"}   # mutable dict to avoid nonlocal

    def set_status(msg, color=ACCENT, dot=ACCENT):
        status_text.value  = msg
        status_text.color  = color
        status_dot.bgcolor = dot
        page.update()

    # ── IP refresh ────────────────────────────────────────────────────────────
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

    # ── SINGLE TAB widgets ────────────────────────────────────────────────────
    hop1_input = tfield(
        label="HOP 1  —  socks:// · vless:// · vmess:// · trojan:// · ss://",
        hint_text="socks://host:port#Name  or  vless://...#Name",
    )
    hop2_input = tfield(
        label="HOP 2  —  socks:// · vless:// · vmess:// · trojan:// · ss://",
        hint_text="vless://...#Name  or  vmess://...  or  trojan://...",
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
    saved_path_text = ft.Text("", font_family="JetBrains", size=9,
                               color=ACCENT, selectable=True)

    async def process_chain(e):
        set_status("PROCESSING…", ACCENT2, ACCENT2)
        try:
            json_text = build_config_json(hop1_input.value, hop2_input.value,
                                          mobile_switch.value)
            p1   = get_protocol(hop1_input.value)
            p2   = get_protocol(hop2_input.value)
            mode = "MOB" if mobile_switch.value else "PC"
            output_field.value = json_text
            await ft.Clipboard().set(json_text)
            set_status(f"✓ {mode} · {p1.upper()}→{p2.upper()} — COPIED",
                       ACCENT, ACCENT)
            page.update()
        except Exception as ex:
            set_status(f"ERROR: {ex}", DANGER, DANGER)
            page.update()

    async def copy_output(e):
        if output_field.value:
            await ft.Clipboard().set(output_field.value)
            set_status("COPIED ✓", ACCENT, ACCENT)

    async def paste_hop1(e):
        hop1_input.value = await ft.Clipboard().get() or ""
        page.update()

    async def paste_hop2(e):
        hop2_input.value = await ft.Clipboard().get() or ""
        page.update()

    def clear_single(e):
        hop1_input.value = hop2_input.value = output_field.value = ""
        saved_path_text.value = ""
        set_status("CLEARED", MUTED, MUTED)
        page.update()

    async def export_single(e):
        if not output_field.value:
            set_status("GENERATE FIRST", DANGER, DANGER)
            return
        try:
            name = get_filename(hop1_input.value, hop2_input.value)
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

    # ── GROUP TAB widgets ─────────────────────────────────────────────────────
    # User pastes multiple hop1 URLs (one per line) and multiple hop2 URLs
    # (one per line). We generate all N×M combinations.

    group_hop1 = ft.TextField(
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
    group_hop2 = ft.TextField(
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
    group_folder_name = ft.TextField(
        label="FOLDER NAME  (optional)",
        hint_text="MyConfigs",
        multiline=False, expand=True,
        text_style=ft.TextStyle(font_family="JetBrains", size=11, color=TEXT),
        bgcolor=BG, border_color=BORDER,
        focused_border_color=ACCENT, cursor_color=ACCENT,
        label_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=10),
        hint_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=10),
        content_padding=ft.Padding(10, 10, 10, 10), border_radius=8,
    )
    group_preview   = ft.Text("", font_family="JetBrains", size=10, color=TEXT_DIM)
    group_result    = ft.Text("", font_family="JetBrains", size=9,
                               color=ACCENT, selectable=True)
    group_progress  = ft.ProgressBar(value=0, bgcolor=BORDER, color=ACCENT,
                                      height=4, border_radius=2, visible=False)

    def _parse_lines(text: str) -> list[str]:
        return [l.strip() for l in text.splitlines() if l.strip()]

    def _update_preview(e=None):
        h1 = _parse_lines(group_hop1.value or "")
        h2 = _parse_lines(group_hop2.value or "")
        n  = len(h1) * len(h2)
        if n == 0:
            group_preview.value = "Enter URLs above to see combination count"
            group_preview.color = TEXT_DIM
        else:
            group_preview.value = (
                f"⚡  {len(h1)} HOP-1  ×  {len(h2)} HOP-2  =  {n} configs"
                f"  ·  {'MOBILE' if mobile_switch.value else 'DESKTOP'} mode"
            )
            group_preview.color = ACCENT
        page.update()

    group_hop1.on_change = _update_preview
    group_hop2.on_change = _update_preview

    async def paste_group_hop1(e):
        group_hop1.value = await ft.Clipboard().get() or ""
        _update_preview()
        page.update()

    async def paste_group_hop2(e):
        group_hop2.value = await ft.Clipboard().get() or ""
        _update_preview()
        page.update()

    def clear_group(e):
        group_hop1.value = group_hop2.value = group_folder_name.value = ""
        group_preview.value = ""
        group_result.value  = ""
        group_progress.visible = False
        group_progress.value   = 0
        set_status("CLEARED", MUTED, MUTED)
        page.update()

    async def generate_group(e):
        h1_list = _parse_lines(group_hop1.value or "")
        h2_list = _parse_lines(group_hop2.value or "")

        if not h1_list or not h2_list:
            set_status("ADD URLS TO BOTH LISTS", DANGER, DANGER)
            return

        total   = len(h1_list) * len(h2_list)
        mobile  = mobile_switch.value
        folder  = group_folder_name.value.strip() or "ProxyChainer_Group"

        set_status(f"BUILDING {total} CONFIGS…", ACCENT2, ACCENT2)
        group_progress.visible = True
        group_progress.value   = 0
        group_result.value     = ""
        page.update()

        configs: list[tuple[str, str]] = []
        errors  = 0
        idx     = 0

        for u1 in h1_list:
            for u2 in h2_list:
                idx += 1
                try:
                    json_text = build_config_json(u1, u2, mobile)
                    name      = get_filename(u1, u2)
                    configs.append((json_text, name))
                except Exception as ex:
                    errors += 1
                    set_status(f"SKIP {idx}/{total}: {ex}", WARN, WARN)
                group_progress.value = idx / total
                page.update()

        if not configs:
            set_status("ALL CONFIGS FAILED — check your URLs", DANGER, DANGER)
            group_progress.visible = False
            page.update()
            return

        set_status(f"SAVING {len(configs)} CONFIGS…", ACCENT2, ACCENT2)
        page.update()

        saved, tot, path = await save_batch(configs, folder_name=folder, page=page)

        group_progress.visible = False
        mode_label = "MOBILE" if mobile else "DESKTOP"

        if saved > 0:
            set_status(f"✓ SAVED {saved}/{tot} · {mode_label}", ACCENT, ACCENT)
            err_txt = f"  ({errors} skipped)" if errors else ""
            group_result.value = f"📁  {path}{err_txt}"
            group_result.color = ACCENT
        else:
            set_status("SAVE FAILED", DANGER, DANGER)
            group_result.value = f"✗  {path}"
            group_result.color = DANGER

        page.update()

    # ── Layout skeleton ───────────────────────────────────────────────────────
    header_container = ft.Container(
        bgcolor=SURFACE,
        border=ft.Border(bottom=ft.BorderSide(1, BORDER)),
    )
    body_col = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)
    footer_container = ft.Container(
        bgcolor=SURFACE,
        border=ft.Border(top=ft.BorderSide(1, BORDER)),
    )

    # ── Rebuild (responsive, called on init + resize) ─────────────────────────
    def rebuild(e=None):
        w   = page.width or 400
        pad = 10 if w < 400 else 14

        # ── Header ────────────────────────────────────────────────────────────
        if w < 360:
            status_pill = ft.Container(
                content=status_dot,
                padding=ft.Padding(6, 6, 6, 6),
                bgcolor=CARD, border_radius=5, border=bdr(),
            )
        elif w < 540:
            status_text.max_lines = 1
            status_text.overflow  = ft.TextOverflow.ELLIPSIS
            status_text.size      = 9
            status_pill = ft.Container(
                content=ft.Row([status_dot, status_text], spacing=4, tight=True),
                padding=ft.Padding(6, 4, 6, 4),
                bgcolor=CARD, border_radius=5, border=bdr(),
                width=min(w * 0.42, 160),
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
                ft.Text("ANY → ANY  ·  VLESS · VMess · Trojan · SS · SOCKS",
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
                        ft.Text("ANY → ANY  ·  VLESS · VMess · Trojan · SS · SOCKS",
                                font_family="JetBrains", size=9, color=TEXT_DIM),
                    ], spacing=1, tight=True),
                ], spacing=8),
                status_pill,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
               vertical_alignment=ft.CrossAxisAlignment.CENTER)

        header_container.content = ft.Container(
            content=hbody, padding=ft.Padding(pad, 10, pad, 10),
        )

        # ── Tab bar ───────────────────────────────────────────────────────────
        is_single = current_tab["value"] == "single"

        def switch_single(e):
            current_tab["value"] = "single"
            rebuild()

        def switch_group(e):
            current_tab["value"] = "group"
            _update_preview()
            rebuild()

        tab_bar = ft.Container(
            content=ft.Row([
                tab_btn("⚡  SINGLE", is_single,  switch_single),
                tab_btn("⚡⚡  GROUP", not is_single, switch_group),
            ], spacing=8),
            padding=ft.Padding(pad, 8, pad, 8),
            bgcolor=SURFACE,
            border=ft.Border(bottom=ft.BorderSide(1, BORDER)),
        )

        # ── Mode toggle ───────────────────────────────────────────────────────
        mob_label = ft.Text("MOB", font_family="JetBrains", size=9,
                            color=TEXT if mobile_switch.value else MUTED)
        pc_label  = ft.Text("PC",  font_family="JetBrains", size=9,
                            color=TEXT if not mobile_switch.value else MUTED)

        def _on_switch(e):
            mob_label.color = TEXT if mobile_switch.value else MUTED
            pc_label.color  = TEXT if not mobile_switch.value else MUTED
            _update_preview()
            page.update()
        mobile_switch.on_change = _on_switch

        toggle_card = ft.Container(
            content=ft.Column([
                ft.Text("MODE", font_family="JetBrains", size=8, color=ACCENT),
                ft.Row([mob_label, mobile_switch, pc_label],
                       spacing=2, tight=True,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], spacing=2, tight=True,
               horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(14, 8, 14, 8),
            bgcolor=CARD, border_radius=10, border=bdr(),
        )

        # ── SINGLE tab content ────────────────────────────────────────────────
        if is_single:
            hop1_card = ft.Container(
                content=ft.Column([
                    ft.Row([lbl("01  //  HOP 1"),
                            ibtn(ft.Icons.CONTENT_PASTE, "Paste", paste_hop1)],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=6),
                    ft.Row([hop1_input]),
                ], spacing=0),
                padding=ft.Padding(12, 12, 12, 12),
                bgcolor=CARD, border_radius=10, border=bdr(),
            )
            hop2_card = ft.Container(
                content=ft.Column([
                    ft.Row([lbl("02  //  HOP 2"),
                            ibtn(ft.Icons.CONTENT_PASTE, "Paste", paste_hop2)],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=6),
                    ft.Row([hop2_input]),
                ], spacing=0),
                padding=ft.Padding(12, 12, 12, 12),
                bgcolor=CARD, border_radius=10, border=bdr(),
            )
            if w < 600:
                hop1_card.expand = False
                hop2_card.expand = False
                cards = ft.Column([hop1_card, hop2_card], spacing=10)
            else:
                hop1_card.expand = True
                hop2_card.expand = True
                cards = ft.Row([hop1_card, hop2_card], spacing=12,
                               vertical_alignment=ft.CrossAxisAlignment.START)

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
                            ibtn(ft.Icons.COPY_ALL,         "Copy",     copy_output,   ACCENT2),
                            ibtn(ft.Icons.DOWNLOAD_ROUNDED, "Download", export_single, ACCENT),
                            ibtn(ft.Icons.DELETE_OUTLINE,   "Clear",    clear_single,  MUTED),
                        ], spacing=0),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=6),
                    ft.Row([output_field]),
                    ft.Text("Auto-copied on generate · re-copy or download above",
                            font_family="JetBrains", size=9, color=MUTED),
                    saved_path_text,
                ], spacing=4),
                padding=ft.Padding(12, 12, 12, 12),
                bgcolor=CARD, border_radius=10, border=bdr(),
            )

            tab_content = ft.Column([
                cards, glow(), gen_row, glow(), output_card,
            ], spacing=10)

        # ── GROUP tab content ─────────────────────────────────────────────────
        else:
            g_hop1_card = ft.Container(
                content=ft.Column([
                    ft.Row([lbl("HOP 1  LIST"),
                            ibtn(ft.Icons.CONTENT_PASTE, "Paste all", paste_group_hop1)],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=6),
                    ft.Row([group_hop1]),
                ], spacing=0),
                padding=ft.Padding(12, 12, 12, 12),
                bgcolor=CARD, border_radius=10, border=bdr(),
            )
            g_hop2_card = ft.Container(
                content=ft.Column([
                    ft.Row([lbl("HOP 2  LIST"),
                            ibtn(ft.Icons.CONTENT_PASTE, "Paste all", paste_group_hop2)],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=6),
                    ft.Row([group_hop2]),
                ], spacing=0),
                padding=ft.Padding(12, 12, 12, 12),
                bgcolor=CARD, border_radius=10, border=bdr(),
            )

            if w < 600:
                g_hop1_card.expand = False
                g_hop2_card.expand = False
                g_cards = ft.Column([g_hop1_card, g_hop2_card], spacing=10)
            else:
                g_hop1_card.expand = True
                g_hop2_card.expand = True
                g_cards = ft.Row([g_hop1_card, g_hop2_card], spacing=12,
                                  vertical_alignment=ft.CrossAxisAlignment.START)

            folder_row = ft.Row([
                ft.Container(
                    content=ft.Row([group_folder_name], expand=True),
                    expand=True,
                    padding=ft.Padding(0, 0, 0, 0),
                ),
            ])

            # Preview counter
            preview_card = ft.Container(
                content=ft.Column([
                    group_preview,
                    group_progress,
                ], spacing=6, tight=True),
                padding=ft.Padding(12, 10, 12, 10),
                bgcolor=CARD, border_radius=8, border=bdr(),
            )

            gen_all_btn = ft.Container(
                content=ft.GestureDetector(
                    content=ft.Row([
                        ft.Icon(ft.Icons.BOLT, color=BG, size=16),
                        ft.Text("GENERATE ALL & SAVE", font_family="Syne-Bold",
                                size=13, color=BG, weight=ft.FontWeight.W_700,
                                style=ft.TextStyle(letter_spacing=0.8)),
                    ], spacing=8, tight=True,
                       alignment=ft.MainAxisAlignment.CENTER),
                    on_tap=lambda e: page.run_task(generate_group, e),
                ),
                expand=True, height=56,
                bgcolor=ACCENT, border_radius=10,
                alignment=ft.Alignment(0, 0),
            )
            gen_all_row = ft.Row([toggle_card, gen_all_btn], spacing=10,
                                  vertical_alignment=ft.CrossAxisAlignment.CENTER)

            result_card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        lbl("RESULT"),
                        ibtn(ft.Icons.DELETE_OUTLINE, "Clear", clear_group, MUTED),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=4),
                    group_result,
                ], spacing=4),
                padding=ft.Padding(12, 12, 12, 12),
                bgcolor=CARD, border_radius=10, border=bdr(),
                visible=True,
            )

            tab_content = ft.Column([
                g_cards,
                glow(),
                ft.Container(
                    content=ft.Column([
                        mono("FOLDER NAME  (leave empty for auto)", 9),
                        ft.Container(height=4),
                        folder_row,
                    ], spacing=0),
                    padding=ft.Padding(12, 12, 12, 12),
                    bgcolor=CARD, border_radius=10, border=bdr(),
                ),
                preview_card,
                glow(),
                gen_all_row,
                glow(),
                result_card,
            ], spacing=10)

        # ── Assemble body ─────────────────────────────────────────────────────
        body_col.controls = [
            tab_bar,
            ft.Container(
                content=tab_content,
                padding=ft.Padding(pad, pad, pad, pad),
            ),
        ]

        # ── Footer ────────────────────────────────────────────────────────────
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