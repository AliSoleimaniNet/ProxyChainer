import flet as ft
import json
import re
import threading
import time

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def measure_ping(count=3):
    """HTTP ping via Google generate_204 endpoint, returns avg ms or None."""
    url = "https://www.google.com/generate_204"
    times = []
    for _ in range(count):
        try:
            start = time.perf_counter()
            r = requests.get(url, timeout=5)
            elapsed = (time.perf_counter() - start) * 1000
            # generate_204 returns HTTP 204 No Content — that's a success
            if r.status_code in (200, 204):
                times.append(elapsed)
        except Exception:
            pass
    if not times:
        return None
    return round(sum(times) / len(times), 1)


def get_ip_info():
    if not HAS_REQUESTS:
        return {
            "ip": "N/A (web)", "city": "—",
            "country": "—", "org": "Not supported in browser",
            "ping": None,
        }

    # Each provider is tried in order until one succeeds
    providers = [
        _from_ipapi_co,
        _from_ip_api_com,
        _from_ipinfo_io,
        _from_freeipapi,
    ]

    for provider in providers:
        try:
            info = provider()
            if info:
                info["ping"] = measure_ping()
                return info
        except Exception:
            continue

    return None


def _from_ipapi_co():
    r = requests.get("https://ipapi.co/json/", timeout=5)
    d = r.json()
    if d.get("error"):
        return None
    return {
        "ip":      d.get("ip", "N/A"),
        "city":    d.get("city", "N/A"),
        "country": d.get("country_name", "N/A"),
        "org":     d.get("org", "N/A"),
    }


def _from_ip_api_com():
    # 45 req/min free, no key needed
    r = requests.get("http://ip-api.com/json/?fields=status,message,country,city,org,query", timeout=5)
    d = r.json()
    if d.get("status") != "success":
        return None
    return {
        "ip":      d.get("query", "N/A"),
        "city":    d.get("city", "N/A"),
        "country": d.get("country", "N/A"),
        "org":     d.get("org", "N/A"),
    }


def _from_ipinfo_io():
    # 50k req/month free, no key needed
    r = requests.get("https://ipinfo.io/json", timeout=5)
    d = r.json()
    if "ip" not in d:
        return None
    city, country = d.get("city", "N/A"), d.get("country", "N/A")
    return {
        "ip":      d.get("ip", "N/A"),
        "city":    city,
        "country": country,
        "org":     d.get("org", "N/A"),
    }


def _from_freeipapi():
    # Completely free, no key needed
    r = requests.get("https://freeipapi.com/api/json", timeout=5)
    d = r.json()
    if "ipAddress" not in d:
        return None
    return {
        "ip":      d.get("ipAddress", "N/A"),
        "city":    d.get("cityName", "N/A"),
        "country": d.get("countryName", "N/A"),
        "org":     d.get("ipVersion", "N/A"),
    }


def main(page: ft.Page):
    page.title = "ProxyChainer — SOCKS → VLESS"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = "#0A0C10"

    # ── Local fonts ───────────────────────────────────────────────
    page.fonts = {
        "JetBrains":          "fonts/JetBrainsMono-Regular.ttf",
        "JetBrains-SemiBold": "fonts/JetBrainsMono-SemiBold.ttf",
        "JetBrains-Bold":     "fonts/JetBrainsMono-Bold.ttf",
        "Syne":               "fonts/Syne-Regular.ttf",
        "Syne-SemiBold":      "fonts/Syne-SemiBold.ttf",
        "Syne-Bold":          "fonts/Syne-Bold.ttf",
        "Syne-ExtraBold":     "fonts/Syne-ExtraBold.ttf",
    }

    # ── Colors ────────────────────────────────────────────────────
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

    # ── Helpers ───────────────────────────────────────────────────
    def mono(text, size=13, color=TEXT, weight=ft.FontWeight.NORMAL):
        return ft.Text(text, font_family="JetBrains", size=size,
                       color=color, weight=weight)

    def label(text):
        return ft.Row([
            ft.Container(width=3, height=14, bgcolor=ACCENT, border_radius=2),
            ft.Text(
                text,
                font_family="Syne-Bold",
                size=11,
                color=ACCENT,
                weight=ft.FontWeight.W_600,
                style=ft.TextStyle(letter_spacing=2),
            ),
        ], spacing=8)

    def glowing_divider():
        return ft.Container(
            height=1,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, 0),
                end=ft.Alignment(1, 0),
                colors=["#00000000", ACCENT + "55", ACCENT2 + "33", "#00000000"],
            ),
            margin=ft.Margin(0, 4, 0, 4),
        )

    # ── Fields ────────────────────────────────────────────────────
    field_style = dict(
        text_style=ft.TextStyle(font_family="JetBrains", size=12, color=TEXT),
        multiline=True,
        min_lines=3,
        max_lines=5,
        expand=True,
        bgcolor=BG,
        border_color=BORDER,
        focused_border_color=ACCENT,
        cursor_color=ACCENT,
        label_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=11),
        hint_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=12),
        content_padding=ft.Padding(14, 14, 14, 14),
        border_radius=8,
    )

    socks_input = ft.TextField(
        label="SOCKS PROXY  //  socks://user:pass@host:port",
        hint_text="socks://...",
        **field_style,
    )
    vless_input = ft.TextField(
        label="VLESS CONFIG  //  vless://uuid@host:port?params",
        hint_text="vless://...",
        **field_style,
    )
    final_output = ft.TextField(
        label="GENERATED CONFIG  //  JSON OUTPUT",
        multiline=True,
        min_lines=12,
        expand=True,
        read_only=True,
        text_style=ft.TextStyle(font_family="JetBrains", size=11, color=ACCENT2),
        bgcolor=BG,
        border_color=BORDER,
        focused_border_color=ACCENT2,
        cursor_color=ACCENT2,
        label_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=11),
        content_padding=ft.Padding(14, 14, 14, 14),
        border_radius=8,
    )

    # ── Status bar ────────────────────────────────────────────────
    status_text = ft.Text(
        "READY",
        font_family="JetBrains",
        size=11,
        color=ACCENT,
        weight=ft.FontWeight.W_600,
    )
    status_dot = ft.Container(
        width=7, height=7,
        bgcolor=ACCENT,
        border_radius=50,
        animate=ft.Animation(800, ft.AnimationCurve.EASE_IN_OUT),
    )

    # ── IP panel ──────────────────────────────────────────────────
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

    def ping_color(ms):
        """good <300, acceptable <1000, bad <5000, worst <10000, unreachable >=10000"""
        if ms is None:      return "#888888"   # grey  — unreachable
        if ms < 300:        return ACCENT       # green — good
        if ms < 1000:       return "#FFD700"    # yellow — acceptable
        if ms < 5000:       return "#FF8C00"    # orange — bad
        if ms < 10000:      return DANGER       # red   — worst
        return "#888888"                        # grey  — effectively unreachable

    def ping_label(ms):
        if ms is None:   return "PING ── N/A"
        return f"PING ── {ms} ms"

    def refresh_ip(e):
        set_status("FETCHING IP + PING...", ACCENT2, ACCENT2)
        def _fetch():
            info = get_ip_info()
            if info:
                pc = ping_color(info["ping"])
                ip_row.controls = [
                    mono("IP ──", 11, TEXT_DIM),
                    mono(info["ip"], 11, ACCENT),
                    ft.Container(width=12),
                    mono("CITY ──", 11, TEXT_DIM),
                    mono(f"{info['city']}, {info['country']}", 11, TEXT),
                    ft.Container(width=12),
                    mono("ORG ──", 11, TEXT_DIM),
                    mono(info["org"], 11, TEXT_DIM),
                    ft.Container(width=12),
                    mono("PING ──", 11, TEXT_DIM),
                    mono(
                        f"{info['ping']} ms" if info["ping"] is not None else "N/A",
                        11, pc, ft.FontWeight.W_600
                    ),
                    # small colored dot to visualise quality
                    ft.Container(
                        width=7, height=7,
                        bgcolor=pc,
                        border_radius=50,
                        margin=ft.Margin(2, 0, 0, 0),
                    ),
                ]
                set_status("IP INFO LOADED", ACCENT, ACCENT)
            else:
                ip_row.controls = [mono("UNABLE TO FETCH IP — CHECK CONNECTION", 11, DANGER)]
                set_status("CONNECTION ERROR", DANGER, DANGER)
            page.update()
        threading.Thread(target=_fetch, daemon=True).start()

    # ── Core logic ────────────────────────────────────────────────
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

    # ── Icon button ───────────────────────────────────────────────
    def icon_btn(icon_name: str, tooltip: str, handler, color=MUTED):
        return ft.IconButton(
            icon=icon_name,
            icon_color=color,
            icon_size=16,
            tooltip=tooltip,
            on_click=handler,
            style=ft.ButtonStyle(
                overlay_color={
                    ft.ControlState.DEFAULT: "#00000000",
                    ft.ControlState.HOVERED: ACCENT + "18",
                },
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.Padding(6, 6, 6, 6),
            ),
        )

    # ── Header ────────────────────────────────────────────────────
    header = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Container(width=4, height=28, bgcolor=ACCENT, border_radius=2),
                ft.Column([
                    ft.Text(
                        "PROXY CHAINER",
                        font_family="Syne-ExtraBold",
                        size=20,
                        color=TEXT,
                        weight=ft.FontWeight.W_800,
                        style=ft.TextStyle(letter_spacing=3),
                    ),
                    ft.Text(
                        "SOCKS  →  VLESS  //  dialerProxy tunnel builder",
                        font_family="JetBrains",
                        size=10,
                        color=TEXT_DIM,
                        style=ft.TextStyle(letter_spacing=1),
                    ),
                ], spacing=1, tight=True),
            ], spacing=12),
            ft.Container(
                content=ft.Row([status_dot, status_text], spacing=8),
                padding=ft.Padding(14, 8, 14, 8),
                bgcolor=SURFACE,
                border_radius=6,
                border=ft.Border(
                    ft.BorderSide(1, BORDER),
                    ft.BorderSide(1, BORDER),
                    ft.BorderSide(1, BORDER),
                    ft.BorderSide(1, BORDER),
                ),
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.Padding(20, 16, 20, 16),
        bgcolor=SURFACE,
        border=ft.Border(
            bottom=ft.BorderSide(1, BORDER),
        ),
    )

    # ── Input cards ───────────────────────────────────────────────
    def input_card(title, step, field, paste_fn):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    label(f"STEP {step}  //  {title}"),
                    icon_btn(ft.Icons.CONTENT_PASTE, "Paste", paste_fn, MUTED),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=8),
                ft.Row([field], expand=True),
            ], spacing=0, expand=True),
            padding=ft.Padding(16, 16, 16, 16),
            expand=True,
            bgcolor=CARD,
            border_radius=10,
            border=ft.Border(
                ft.BorderSide(1, BORDER),
                ft.BorderSide(1, BORDER),
                ft.BorderSide(1, BORDER),
                ft.BorderSide(1, BORDER),
            ),
        )

    socks_card = input_card("SOCKS PROXY",  "01", socks_input, paste_socks)
    vless_card = input_card("VLESS CONFIG", "02", vless_input, paste_vless)

    # ── Generate button ───────────────────────────────────────────
    generate_btn = ft.Container(
        content=ft.Button(
            content=ft.Row([
                ft.Icon(ft.Icons.BOLT, color=BG, size=18),
                ft.Text(
                    "GENERATE CHAIN CONFIG",
                    font_family="Syne-Bold",
                    size=13,
                    color=BG,
                    weight=ft.FontWeight.W_700,
                    style=ft.TextStyle(letter_spacing=1.5),
                ),
            ], spacing=10, tight=True),
            on_click=process_chain,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.DEFAULT: ACCENT,
                    ft.ControlState.HOVERED: "#00FFBF",
                },
                overlay_color="#00000000",
                elevation={ft.ControlState.DEFAULT: 0, ft.ControlState.HOVERED: 8},
                shadow_color=ACCENT + "55",
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding(32, 16, 32, 16),
                animation_duration=200,
            ),
        ),
        alignment=ft.Alignment(0, 0),
    )

    # ── Output card ───────────────────────────────────────────────
    output_card = ft.Container(
        content=ft.Column([
            ft.Row([
                label("STEP 03  //  JSON OUTPUT"),
                ft.Row([
                    icon_btn(ft.Icons.COPY_ALL, "Copy Output", copy_output, ACCENT2),
                    icon_btn(ft.Icons.DELETE_OUTLINE, "Clear All", clear_all, MUTED),
                ], spacing=0),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=8),
            ft.Row([final_output], expand=True),
        ], spacing=0, expand=True),
        padding=ft.Padding(16, 16, 16, 16),
        expand=True,
        bgcolor=CARD,
        border_radius=10,
        border=ft.Border(
            ft.BorderSide(1, BORDER),
            ft.BorderSide(1, BORDER),
            ft.BorderSide(1, BORDER),
            ft.BorderSide(1, BORDER),
        ),
    )

    # ── IP footer ─────────────────────────────────────────────────
    ip_footer = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.LANGUAGE, color=MUTED, size=14),
            ip_row,
            ft.Container(expand=True),
            icon_btn(ft.Icons.REFRESH, "Refresh IP", refresh_ip, ACCENT),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding(20, 12, 20, 12),
        bgcolor=SURFACE,
        border=ft.Border(top=ft.BorderSide(1, BORDER)),
    )

    # ── Responsive layout ─────────────────────────────────────────
    inputs_container = ft.Container()

    def build_inputs():
        w = page.width or 800
        if w < 600:
            return ft.Column([socks_card, vless_card], spacing=12)
        return ft.Row([
            ft.Column([socks_card], expand=1),
            ft.Column([vless_card], expand=1),
        ], spacing=16)

    def on_resize(e):
        inputs_container.content = build_inputs()
        page.update()

    page.on_resized = on_resize
    inputs_container.content = build_inputs()

    body = ft.Container(
        content=ft.Column([
            inputs_container,
            glowing_divider(),
            generate_btn,
            glowing_divider(),
            output_card,
        ], spacing=16),
        padding=ft.Padding(20, 20, 20, 20),
    )

    # ── Assemble ──────────────────────────────────────────────────
    page.add(
        ft.Column(
            controls=[
                header,
                ft.ListView(controls=[body], expand=True, padding=0),
                ip_footer,
            ],
            spacing=0,
            expand=True,
        )
    )

    # ── Auto-fetch IP + ping immediately on open ───────────────────
    threading.Thread(target=lambda: refresh_ip(None), daemon=True).start()


ft.run(main, assets_dir="assets")