"""
ui/theme.py
Color palette and shared style constants.
"""

# ── Palette ───────────────────────────────────────────────────────────────────
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

FONTS = {
    "JetBrains":      "fonts/JetBrainsMono-Regular.ttf",
    "JetBrains-Bold": "fonts/JetBrainsMono-Bold.ttf",
    "Syne-Bold":      "fonts/Syne-Bold.ttf",
    "Syne-ExtraBold": "fonts/Syne-ExtraBold.ttf",
}


def ping_color(ms: float | None) -> str:
    if ms is None:  return "#888888"
    if ms < 300:    return ACCENT
    if ms < 1000:   return WARN
    if ms < 5000:   return "#FF8C00"
    return DANGER
