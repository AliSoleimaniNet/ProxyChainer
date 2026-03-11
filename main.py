"""
main.py
Entry point — launches the Flet app.
"""

import flet as ft
from ui.app import build_page

ft.run(build_page, assets_dir="assets")
