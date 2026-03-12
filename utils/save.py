"""
utils/save.py
Cross-platform file saving for single configs and batch exports.

Single config  →  saves a JSON array file:  [config]
Batch export   →  saves ONE JSON array file: [cfg1, cfg2, …]
                  (no more folder creation)

  Windows / Linux / macOS  →  Desktop → Downloads → home
  Android                  →  /sdcard/Download
  Web                      →  data: URI browser download
"""

import base64
import datetime
import json
import pathlib
import platform
import re
import sys


def _timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe(name: str) -> str:
    name = re.sub(r'[\/:*?"<>|\\]', "_", name.strip())
    return name[:60] or "proxychainer"


def make_filename(base_name: str = "") -> str:
    ts = _timestamp()
    return f"{_safe(base_name)}_{ts}.json" if base_name else f"proxy_chain_{ts}.json"


def _is_android() -> bool:
    return hasattr(sys, "getandroidapilevel") or (
        platform.system() == "Linux"
        and (pathlib.Path("/sdcard").exists() or pathlib.Path("/data/data").exists())
    )


def _is_web(page=None) -> bool:
    if page is not None:
        return getattr(page, "web", False)
    return "pyodide" in sys.modules or "flet_web" in sys.modules


def _get_save_folder() -> pathlib.Path | None:
    candidates = (
        [
            pathlib.Path("/sdcard/Download"),
            pathlib.Path("/storage/emulated/0/Download"),
            pathlib.Path.home(),
        ]
        if _is_android()
        else [
            pathlib.Path.home() / "Desktop",
            pathlib.Path.home() / "Downloads",
            pathlib.Path.home(),
            pathlib.Path.cwd(),
        ]
    )

    for folder in candidates:
        if folder.exists():
            try:
                test = folder / ".pc_write_test"
                test.touch()
                test.unlink()
                return folder
            except Exception:
                continue

    return None


async def _web_download(json_text: str, filename: str, page) -> tuple[bool, str]:
    """Trigger a browser download via data URI."""
    try:
        import flet as ft
        b64      = base64.b64encode(json_text.encode("utf-8")).decode("ascii")
        data_uri = f"data:application/json;base64,{b64}"
        launcher = ft.UrlLauncher()
        page.overlay.append(launcher)
        page.update()
        await launcher.launch_url(data_uri)
        return True, f"DOWNLOAD ✓  {filename}"
    except Exception as ex:
        return False, f"WEB DOWNLOAD ERROR: {ex}"


async def save_config(json_text: str, page=None, name: str = "") -> tuple[bool, str]:
    """
    Save a single config file (already a JSON array string).
    Returns (ok, message).
    """
    filename = make_filename(name)

    if _is_web(page) and page is not None:
        return await _web_download(json_text, filename, page)

    folder = _get_save_folder()
    if folder is None:
        return False, "SAVE FAILED: no writable folder found"

    try:
        path = folder / filename
        path.write_text(json_text, encoding="utf-8")
        return True, str(path)
    except Exception as ex:
        return False, f"SAVE ERROR: {ex}"


async def save_batch(
    configs: list[dict],
    file_name: str,
    page=None,
) -> tuple[bool, str]:
    """
    Save all configs as ONE JSON array file.

    configs   : list of config dicts (already built, not serialized)
    file_name : base name for the output file (without extension)
    Returns (ok, path_or_message)
    """
    filename = make_filename(file_name)
    json_text = json.dumps(configs, indent=2)

    if _is_web(page) and page is not None:
        return await _web_download(json_text, filename, page)

    folder = _get_save_folder()
    if folder is None:
        return False, "SAVE FAILED: no writable folder"

    try:
        path = folder / filename
        path.write_text(json_text, encoding="utf-8")
        return True, str(path)
    except Exception as ex:
        return False, f"SAVE ERROR: {ex}"