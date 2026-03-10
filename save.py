"""
save.py — Cross-platform file saving (single + batch).

  Windows / Linux / macOS  →  Desktop → Downloads → home
  Android                  →  /sdcard/Download
  Web                      →  data: URI browser download (single files only)
"""

import base64
import datetime
import pathlib
import platform
import re
import sys


def _timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe(name: str) -> str:
    name = name.strip()
    name = re.sub(r'[\/:*?"<>|\\]', "_", name)
    return name[:60] or "proxychainer"


def make_filename(base_name: str = "") -> str:
    ts = _timestamp()
    return f"{_safe(base_name)}_{ts}.json" if base_name else f"proxy_chain_{ts}.json"


def _is_android() -> bool:
    return hasattr(sys, "getandroidapilevel") or (
        platform.system() == "Linux" and (
            pathlib.Path("/sdcard").exists() or
            pathlib.Path("/data/data").exists()
        )
    )


def _is_web(page=None) -> bool:
    if page is not None:
        return getattr(page, "web", False)
    return "pyodide" in sys.modules or "flet_web" in sys.modules


def _get_base_folder() -> pathlib.Path | None:
    """Return the first writable candidate folder."""
    candidates = [
        pathlib.Path.home() / "Desktop",
        pathlib.Path.home() / "Downloads",
        pathlib.Path.home(),
        pathlib.Path.cwd(),
    ]
    if _is_android():
        candidates = [
            pathlib.Path("/sdcard/Download"),
            pathlib.Path("/storage/emulated/0/Download"),
            pathlib.Path.home(),
        ]
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


async def save_config(json_text: str, page=None, name: str = "") -> tuple[bool, str]:
    """Save a single config. Returns (ok, message)."""
    filename = make_filename(name)

    if _is_web(page) and page is not None:
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

    folder = _get_base_folder()
    if folder is None:
        return False, "SAVE FAILED: no writable folder found"

    try:
        path = folder / filename
        path.write_text(json_text, encoding="utf-8")
        return True, str(path)
    except Exception as ex:
        return False, f"SAVE ERROR: {ex}"


async def save_batch(
    configs: list[tuple[str, str]],   # [(json_text, base_name), ...]
    folder_name: str,
    page=None,
) -> tuple[int, int, str]:
    """
    Save multiple configs into a named subfolder.
    Web: downloads them one by one as data URIs.
    Desktop/Android: creates folder_name/ inside the base folder.

    Returns (saved_count, total_count, folder_path_or_message)
    """
    total  = len(configs)
    saved  = 0

    if _is_web(page) and page is not None:
        # Web: no folder concept — download each file
        for json_text, name in configs:
            ok, _ = await save_config(json_text, page=page, name=name)
            if ok:
                saved += 1
        return saved, total, f"DOWNLOADED {saved}/{total} files"

    base = _get_base_folder()
    if base is None:
        return 0, total, "SAVE FAILED: no writable folder"

    ts     = _timestamp()
    folder = base / _safe(f"{folder_name}_{ts}")
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except Exception as ex:
        return 0, total, f"FOLDER CREATE ERROR: {ex}"

    for json_text, name in configs:
        try:
            filename = f"{_safe(name)}.json" if name else f"config_{saved+1}.json"
            (folder / filename).write_text(json_text, encoding="utf-8")
            saved += 1
        except Exception:
            continue

    return saved, total, str(folder)