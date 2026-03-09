import flet as ft
import json
import requests
import re


def get_ip_info():
    try:
        response = requests.get("https://ipapi.co/json/", timeout=5)
        data = response.json()
        return {
            "ip": data.get("ip", "N/A"),
            "city": data.get("city", "N/A"),
            "country": data.get("country_name", "N/A"),
            "org": data.get("org", "N/A"),
        }
    except:
        return None


def main(page: ft.Page):
    page.title = "ProxyChain — SOCKS → VLESS"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.scroll = "adaptive"
    page.bgcolor = "#0A0C10"
    page.fonts = {
        "JetBrains": "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&display=swap",
        "Syne": "https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&display=swap",
    }

    # ── Color tokens ──────────────────────────────────────────────
    BG       = "#0A0C10"
    SURFACE  = "#111318"
    CARD     = "#161A22"
    BORDER   = "#1E2330"
    ACCENT   = "#00FFA3"       # neon green
    ACCENT2  = "#0FF"           # cyan
    MUTED    = "#4A5368"
    TEXT     = "#E2E8F0"
    TEXT_DIM = "#7A8499"
    DANGER   = "#FF4757"

    # ── Reusable style helpers ─────────────────────────────────────
    def mono(text, size=13, color=TEXT, weight="normal"):
        return ft.Text(text, font_family="JetBrains", size=size, color=color, weight=weight)

    def label(text):
        return ft.Row([
            ft.Container(width=3, height=14, bgcolor=ACCENT, border_radius=2),
            ft.Text(text, font_family="Syne", size=11, color=ACCENT,
                    weight="w600", letter_spacing=2),
        ], spacing=8)

    def glowing_divider():
        return ft.Container(
            height=1,
            gradient=ft.LinearGradient(
                begin=ft.alignment.center_left,
                end=ft.alignment.center_right,
                colors=["#00000000", ACCENT + "55", ACCENT2 + "33", "#00000000"],
            ),
            margin=ft.margin.symmetric(vertical=4),
        )

    # ── Input fields ───────────────────────────────────────────────
    field_style = dict(
        font_family="JetBrains",
        text_size=12,
        multiline=True,
        min_lines=3,
        max_lines=5,
        bgcolor=BG,
        border_color=BORDER,
        focused_border_color=ACCENT,
        cursor_color=ACCENT,
        color=TEXT,
        label_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=11),
        content_padding=ft.padding.all(14),
        border_radius=8,
    )

    socks_input = ft.TextField(
        label="SOCKS PROXY  //  socks://user:pass@host:port",
        hint_text="socks://...",
        hint_style=ft.TextStyle(color=MUTED, font_family="JetBrains"),
        **field_style,
    )
    vless_input = ft.TextField(
        label="VLESS CONFIG  //  vless://uuid@host:port?params",
        hint_text="vless://...",
        hint_style=ft.TextStyle(color=MUTED, font_family="JetBrains"),
        **field_style,
    )
    final_output = ft.TextField(
        label="GENERATED CONFIG  //  JSON OUTPUT",
        multiline=True,
        min_lines=12,
        read_only=True,
        font_family="JetBrains",
        text_size=11,
        bgcolor=BG,
        border_color=BORDER,
        focused_border_color=ACCENT2,
        cursor_color=ACCENT2,
        color=ACCENT2,
        label_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=11),
        content_padding=ft.padding.all(14),
        border_radius=8,
    )

    # ── Status bar state ───────────────────────────────────────────
    status_text  = ft.Text("READY", font_family="JetBrains", size=11,
                           color=ACCENT, weight="w600")
    status_dot   = ft.Container(width=7, height=7, bgcolor=ACCENT,
                                border_radius=50,
                                animate=ft.animation.Animation(800, "easeInOut"))

    # ── IP info panel ──────────────────────────────────────────────
    ip_row = ft.Row([
        mono("IP ──", 11, TEXT_DIM),
        mono("—", 11, MUTED),
        ft.Container(width=8),
        mono("CITY ──", 11, TEXT_DIM),
        mono("—", 11, MUTED),
        ft.Container(width=8),
        mono("ORG ──", 11, TEXT_DIM),
        mono("—", 11, MUTED),
    ], spacing=4, wrap=True)

    def set_status(msg, color=ACCENT, dot_color=ACCENT):
        status_text.value = msg
        status_text.color = color
        status_dot.bgcolor = dot_color
        page.update()

    def refresh_ip(e):
        set_status("FETCHING IP INFO...", ACCENT2, ACCENT2)
        info = get_ip_info()
        if info:
            ip_row.controls = [
                mono("IP ──", 11, TEXT_DIM),
                mono(info["ip"], 11, ACCENT),
                ft.Container(width=12),
                mono("CITY ──", 11, TEXT_DIM),
                mono(f"{info['city']}, {info['country']}", 11, TEXT),
                ft.Container(width=12),
                mono("ORG ──", 11, TEXT_DIM),
                mono(info["org"], 11, TEXT_DIM),
            ]
            set_status("IP INFO LOADED", ACCENT, ACCENT)
        else:
            ip_row.controls = [mono("UNABLE TO FETCH IP — CHECK CONNECTION", 11, DANGER)]
            set_status("CONNECTION ERROR", DANGER, DANGER)
        page.update()

    # ── Core logic ─────────────────────────────────────────────────
    def process_chain(e):
        set_status("PROCESSING...", ACCENT2, ACCENT2)
        try:
            v_url = vless_input.value.strip()
            s_url = socks_input.value.strip()

            if not v_url or not s_url:
                raise ValueError("Both SOCKS and VLESS configs are required")

            s_addr = re.search(r"@(.*?):", s_url).group(1)
            s_port = int(re.search(r":(\d+)", s_url).group(1).split('#')[0])

            v_id   = re.search(r"vless://(.*?)@", v_url).group(1)
            v_addr = re.search(r"@(.*?):", v_url).group(1)
            v_port = int(re.search(r":(\d+)\?", v_url).group(1))

            query_str = v_url.split('?')[1].split('#')[0]
            params    = dict(x.split('=') for x in query_str.split('&'))

            config = {
                "outbounds": [
                    {
                        "tag": "proxy-chain",
                        "protocol": "vless",
                        "settings": {
                            "vnext": [{
                                "address": v_addr,
                                "port": v_port,
                                "users": [{
                                    "id": v_id,
                                    "encryption": "none",
                                    "flow": params.get("flow", ""),
                                }],
                            }]
                        },
                        "streamSettings": {
                            "network":  params.get("type", "tcp"),
                            "security": params.get("security", ""),
                            "realitySettings": {
                                "serverName":  params.get("sni", ""),
                                "fingerprint": params.get("fp", "chrome"),
                                "publicKey":   params.get("pbk", ""),
                                "shortId":     params.get("sid", ""),
                                "spiderX":     params.get("spx", "").replace("%2F", "/"),
                            },
                            "sockopt": {"dialerProxy": "iran-socks"},
                        },
                    },
                    {
                        "tag": "iran-socks",
                        "protocol": "socks",
                        "settings": {"servers": [{"address": s_addr, "port": s_port}]},
                    },
                    {"tag": "direct", "protocol": "freedom"},
                ],
                "routing": {
                    "rules": [{
                        "type": "field",
                        "outboundTag": "proxy-chain",
                        "network": "tcp,udp",
                    }]
                },
            }

            final_output.value = json.dumps(config, indent=2)
            page.set_clipboard(final_output.value)
            set_status("CONFIG GENERATED & COPIED  ✓", ACCENT, ACCENT)
            page.update()

        except Exception as ex:
            set_status(f"ERROR: {str(ex)}", DANGER, DANGER)
            page.update()

    def copy_output(e):
        if final_output.value:
            page.set_clipboard(final_output.value)
            set_status("COPIED TO CLIPBOARD  ✓", ACCENT, ACCENT)

    def paste_socks(e):
        socks_input.value = page.get_clipboard() or ""
        page.update()

    def paste_vless(e):
        vless_input.value = page.get_clipboard() or ""
        page.update()

    def clear_all(e):
        socks_input.value = ""
        vless_input.value = ""
        final_output.value = ""
        set_status("CLEARED", MUTED, MUTED)

    # ── Icon button helper ─────────────────────────────────────────
    def icon_btn(icon, tooltip, handler, color=MUTED):
        return ft.IconButton(
            icon=icon,
            icon_color=color,
            icon_size=16,
            tooltip=tooltip,
            on_click=handler,
            style=ft.ButtonStyle(
                overlay_color={"": "#00000000", "hovered": ACCENT + "18"},
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.all(6),
            ),
        )

    # ── Header ─────────────────────────────────────────────────────
    header = ft.Container(
        content=ft.Row([
            ft.Column([
                ft.Row([
                    ft.Container(width=4, height=28, bgcolor=ACCENT, border_radius=2),
                    ft.Column([
                        ft.Text("PROXY CHAINER", font_family="Syne", size=22,
                                color=TEXT, weight="w800", letter_spacing=3),
                        ft.Text("SOCKS  →  VLESS  //  dialerProxy tunnel builder",
                                font_family="JetBrains", size=10,
                                color=TEXT_DIM, letter_spacing=1),
                    ], spacing=1),
                ], spacing=12),
            ], expand=True),
            ft.Column([
                ft.Container(
                    content=ft.Row([
                        status_dot,
                        status_text,
                    ], spacing=8, alignment=ft.MainAxisAlignment.END),
                    padding=ft.padding.symmetric(horizontal=14, vertical=8),
                    bgcolor=SURFACE,
                    border_radius=6,
                    border=ft.border.all(1, BORDER),
                ),
            ]),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.padding.symmetric(horizontal=28, vertical=20),
        bgcolor=SURFACE,
        border=ft.border.only(bottom=ft.border.BorderSide(1, BORDER)),
    )

    # ── Input section ──────────────────────────────────────────────
    def input_card(title, step, field, paste_fn):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    label(f"STEP {step}  //  {title}"),
                    icon_btn(ft.icons.CONTENT_PASTE_ROUNDED, "Paste", paste_fn, MUTED),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=8),
                field,
            ], spacing=0),
            padding=ft.padding.all(18),
            bgcolor=CARD,
            border_radius=10,
            border=ft.border.all(1, BORDER),
        )

    socks_card = input_card("SOCKS PROXY", "01", socks_input, paste_socks)
    vless_card = input_card("VLESS CONFIG", "02", vless_input, paste_vless)

    # ── Generate button ────────────────────────────────────────────
    generate_btn = ft.Container(
        content=ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.icons.BOLT, color=BG, size=18),
                ft.Text("GENERATE CHAIN CONFIG", font_family="Syne", size=13,
                        color=BG, weight="w700", letter_spacing=1.5),
            ], spacing=10, tight=True),
            on_click=process_chain,
            style=ft.ButtonStyle(
                bgcolor={"": ACCENT, "hovered": "#00FFBF"},
                overlay_color="#00000000",
                elevation={"": 0, "hovered": 8},
                shadow_color=ACCENT + "55",
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=32, vertical=16),
                animation_duration=200,
            ),
        ),
        alignment=ft.alignment.center,
    )

    # ── Output card ────────────────────────────────────────────────
    output_card = ft.Container(
        content=ft.Column([
            ft.Row([
                label("STEP 03  //  JSON OUTPUT"),
                ft.Row([
                    icon_btn(ft.icons.COPY_ALL_ROUNDED, "Copy Output", copy_output, ACCENT2),
                    icon_btn(ft.icons.DELETE_OUTLINE_ROUNDED, "Clear All", clear_all, MUTED),
                ], spacing=0),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=8),
            final_output,
        ], spacing=0),
        padding=ft.padding.all(18),
        bgcolor=CARD,
        border_radius=10,
        border=ft.border.all(1, BORDER),
    )

    # ── IP footer ──────────────────────────────────────────────────
    ip_footer = ft.Container(
        content=ft.Row([
            ft.Icon(ft.icons.LANGUAGE_ROUNDED, color=MUTED, size=14),
            ip_row,
            ft.Container(expand=True),
            icon_btn(ft.icons.REFRESH_ROUNDED, "Refresh IP", refresh_ip, ACCENT),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.symmetric(horizontal=28, vertical=14),
        bgcolor=SURFACE,
        border=ft.border.only(top=ft.border.BorderSide(1, BORDER)),
    )

    # ── Corner decoration ──────────────────────────────────────────
    def corner_accent():
        return ft.Container(
            width=40, height=40,
            border=ft.border.only(
                top=ft.border.BorderSide(1, ACCENT + "44"),
                left=ft.border.BorderSide(1, ACCENT + "44"),
            ),
            border_radius=ft.border_radius.only(top_left=4),
        )

    # ── Assemble page ──────────────────────────────────────────────
    body = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Column([socks_card], expand=1),
                ft.Column([vless_card], expand=1),
            ], spacing=16),
            glowing_divider(),
            generate_btn,
            glowing_divider(),
            output_card,
        ], spacing=16),
        padding=ft.padding.all(24),
        expand=True,
    )

    page.add(
        ft.Column([
            header,
            body,
            ip_footer,
        ], spacing=0, expand=True)
    )


ft.app(target=main)