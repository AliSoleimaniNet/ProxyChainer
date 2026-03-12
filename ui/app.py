"""
ui/app.py
ProxyChainer app controller — N-hop edition.
"""

import asyncio
import json
import pathlib
import platform
import sys

import flet as ft

from core.config  import build_config, build_config_json, build_config_list_json, get_protocol, get_filename
from core.network import get_ip_info
from utils.save   import save_config, save_batch
from utils.log    import Logger

from ui.theme   import ACCENT, ACCENT2, MUTED, DANGER, BG, CARD, BORDER, TEXT
from ui.theme   import ping_color, FONTS

from ui.layouts.header  import build_header
from ui.layouts.footer  import Footer
from ui.layouts.tab_bar import build_tab_bar

from ui.pages.single import SinglePage
from ui.pages.group  import GroupPage
from ui.pages.log    import build_log_page

from ui.components.primitives import border


def _resolve_log_file(is_web: bool, is_android: bool) -> pathlib.Path | None:
    if is_web:
        return None
    candidates = (
        [pathlib.Path("/sdcard/Download"),
         pathlib.Path("/storage/emulated/0/Download"),
         pathlib.Path.home()]
        if is_android else
        [pathlib.Path.home() / "Desktop",
         pathlib.Path.home() / "Downloads",
         pathlib.Path.home(),
         pathlib.Path.cwd()]
    )
    for p in candidates:
        try:
            if p.exists():
                return p / "proxychainer.log"
        except Exception:
            pass
    return None


def _parse_lines(text: str) -> list[str]:
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]


def _cartesian(lists: list[list[str]]) -> list[list[str]]:
    """Return the cartesian product of N lists as a list of N-tuples (as lists)."""
    if not lists:
        return []
    result = [[]]
    for lst in lists:
        result = [prev + [item] for prev in result for item in lst]
    return result


def build_page(page: ft.Page) -> None:
    page.title      = "ProxyChainer"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor    = BG
    page.fonts      = FONTS
    page.padding    = 0
    page.spacing    = 0
    try:
        page.window.bgcolor = BG
    except Exception:
        pass

    is_web     = getattr(page, "web", False)
    is_android = (
        hasattr(sys, "getandroidapilevel")
        or (platform.system() == "Linux" and pathlib.Path("/sdcard").exists())
    )

    # ── State ─────────────────────────────────────────────────────────────────
    current_tab   = {"v": "single"}
    mobile_switch = ft.Switch(active_color=ACCENT2, value=False)
    _busy         = [False]
    _ip_busy      = [False]

    # ── Logger ────────────────────────────────────────────────────────────────
    log_file = _resolve_log_file(is_web, is_android)
    logger   = Logger(log_file)

    # ── Footer ────────────────────────────────────────────────────────────────
    def _go_log(e):
        current_tab["v"] = "log"
        rebuild()

    footer = Footer(on_log_tap=_go_log, on_ip_refresh=lambda e: page.run_task(_refresh_ip))

    def set_status(msg: str, color: str = ACCENT, level: str = "INFO") -> None:
        footer.set_status(msg, color)
        logger.add(msg, level)
        page.update()

    # ── IP refresh ────────────────────────────────────────────────────────────
    async def _refresh_ip(e=None):
        if _ip_busy[0]:
            return
        _ip_busy[0] = True
        footer.refresh_icon.color = ACCENT2
        footer.set_status("Fetching IP…", ACCENT2)
        logger.add("Fetching IP…", "INFO")
        page.update()
        try:
            info = await asyncio.to_thread(get_ip_info)
            if info:
                pc = ping_color(info["ping"])
                footer.set_ip(
                    ip=info["ip"], city=info["city"], country=info["country"],
                    ping_label=f"{info['ping']} ms" if info["ping"] else "N/A",
                    ping_color=pc,
                )
                footer.set_status("READY", ACCENT)
                logger.add(f"IP={info['ip']}  PING={info['ping']}", "OK")
            else:
                footer.ip_val.value = "ERROR"
                footer.set_status("IP fetch failed", DANGER)
                logger.add("IP fetch failed", "ERROR")
        except Exception as ex:
            footer.ip_val.value = "ERROR"
            footer.set_status(f"IP error: {ex}", DANGER)
            logger.add(f"IP error: {ex}", "ERROR")
        finally:
            _ip_busy[0] = False
            footer.refresh_icon.color = MUTED
            page.update()

    # ── Mode toggle card ──────────────────────────────────────────────────────
    def _build_toggle_card() -> ft.Container:
        mob_lbl = ft.Text("MOB", font_family="JetBrains", size=9,
                          color=TEXT if mobile_switch.value else MUTED)
        pc_lbl  = ft.Text("PC",  font_family="JetBrains", size=9,
                          color=TEXT if not mobile_switch.value else MUTED)

        def _on_switch(e):
            mob_lbl.color = TEXT if mobile_switch.value else MUTED
            pc_lbl.color  = TEXT if not mobile_switch.value else MUTED
            group_page.update_preview(mobile_switch.value)
            page.update()

        mobile_switch.on_change = _on_switch
        return ft.Container(
            content=ft.Column([
                ft.Text("MODE", font_family="JetBrains", size=8, color=ACCENT),
                ft.Row([mob_lbl, mobile_switch, pc_lbl], spacing=2, tight=True,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], spacing=2, tight=True,
               horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(12, 7, 12, 7),
            bgcolor=CARD, border_radius=10, border=border(),
        )

    # ── Single page ───────────────────────────────────────────────────────────

    async def _process_chain():
        if _busy[0]:
            return
        _busy[0] = True
        single_page.set_busy(True, page)
        set_status("PROCESSING…", ACCENT2)
        try:
            hops = single_page.hop_values
            mob  = mobile_switch.value

            # Validate
            empty = [i + 1 for i, h in enumerate(hops) if not h]
            if empty:
                raise ValueError(f"Hop {', '.join(str(i) for i in empty)} is empty")

            hop_summary = "  →  ".join(h[:40] for h in hops)
            logger.add(f"hops={len(hops)}  mobile={mob}  {hop_summary}", "INFO")

            # Build config (returns dict)
            cfg       = await asyncio.to_thread(build_config, hops, mob)
            json_text = json.dumps([cfg], indent=2)

            protocols = [get_protocol(h) for h in hops]
            chain_str = "→".join(p.upper() for p in protocols)
            mode      = "MOB" if mob else "PC"

            single_page.output_field.value = json_text
            try:
                await ft.Clipboard().set(json_text)
            except Exception:
                pass
            set_status(f"✓ {mode} · {chain_str} · {len(hops)} HOPS — COPIED", ACCENT, "OK")
        except Exception as ex:
            set_status(f"ERROR: {ex}", DANGER, "ERROR")
        finally:
            _busy[0] = False
            single_page.set_busy(False, page)
        page.update()

    async def _copy_output():
        if single_page.output_field.value:
            try:
                await ft.Clipboard().set(single_page.output_field.value)
            except Exception:
                pass
            set_status("COPIED ✓", ACCENT, "OK")

    async def _paste_single_hop(index: int):
        val = await ft.Clipboard().get() or ""
        single_page.set_hop_value(index, val)
        page.update()

    async def _export_single():
        if not single_page.output_field.value:
            set_status("GENERATE FIRST", DANGER, "WARN")
            return
        try:
            name = get_filename(single_page.hop_values)
        except Exception:
            name = ""
        ok, msg = await save_config(single_page.output_field.value, page=page, name=name)
        if ok:
            set_status("SAVED ✓", ACCENT, "OK")
            single_page.saved_path_text.value = f"📁  {msg}"
            single_page.saved_path_text.color = ACCENT
        else:
            set_status("SAVE FAILED", DANGER, "ERROR")
            single_page.saved_path_text.value = f"✗  {msg}"
            single_page.saved_path_text.color = DANGER
        page.update()

    def _clear_single(e=None):
        for f in single_page._hop_fields:
            f.value = ""
        single_page.output_field.value    = ""
        single_page.saved_path_text.value = ""
        set_status("CLEARED", MUTED)
        page.update()

    single_page = SinglePage(
        mobile_switch = mobile_switch,
        on_generate   = lambda e: page.run_task(_process_chain),
        on_copy       = lambda e: page.run_task(_copy_output),
        on_paste      = lambda i: page.run_task(_paste_single_hop, i),
        on_export     = lambda e: page.run_task(_export_single),
        on_clear      = _clear_single,
    )

    # ── Group page ────────────────────────────────────────────────────────────

    async def _generate_group():
        if _busy[0]:
            return
        _busy[0] = True
        group_page.set_busy(True, page)

        hop_lists = group_page.hop_lists
        n_hops    = len(hop_lists)

        # Validate: all columns must have at least 1 URL
        empty_cols = [i + 1 for i, lst in enumerate(hop_lists) if not lst]
        if empty_cols:
            cols_str = ", ".join(str(c) for c in empty_cols)
            set_status(f"ADD URLS TO HOP {cols_str}", DANGER, "WARN")
            _busy[0] = False
            group_page.set_busy(False, page)
            return

        mobile    = mobile_switch.value
        file_name = group_page.file_name_input.value.strip() or "ProxyChainer_Group"

        # Cartesian product of all hop lists
        combos = _cartesian(hop_lists)
        total  = len(combos)

        sizes_str = " × ".join(str(len(l)) for l in hop_lists)
        logger.add(f"Group: {n_hops} hops  {sizes_str} = {total} configs", "INFO")
        set_status(f"BUILDING {total} CONFIGS…", ACCENT2)

        group_page.progress_bar.visible = True
        group_page.progress_bar.value   = 0
        group_page.result_text.value    = ""
        page.update()

        configs: list[dict] = []
        errors = 0

        try:
            for idx, hop_combo in enumerate(combos, start=1):
                try:
                    cfg = await asyncio.to_thread(build_config, hop_combo, mobile)
                    configs.append(cfg)
                    logger.add(f"[{idx}/{total}] OK  {cfg.get('remarks', '')}", "OK")
                except Exception as ex:
                    errors += 1
                    logger.add(f"[{idx}/{total}] SKIP: {ex}", "WARN")
                group_page.progress_bar.value = idx / total
                page.update()

            if not configs:
                set_status("ALL CONFIGS FAILED", DANGER, "ERROR")
                group_page.progress_bar.visible = False
                page.update()
                return

            set_status(f"SAVING {len(configs)} CONFIGS…", ACCENT2)
            page.update()

            ok, path = await save_batch(configs, file_name=file_name, page=page)

            group_page.progress_bar.visible = False
            mode_lbl = "MOBILE" if mobile else "DESKTOP"
            err_s    = f"  ({errors} skipped)" if errors else ""

            if ok:
                set_status(f"✓ {len(configs)}/{total} SAVED · {mode_lbl}", ACCENT, "OK")
                group_page.result_text.value = f"📁  {path}{err_s}"
                group_page.result_text.color = ACCENT
                logger.add(f"Saved: {path}", "OK")
            else:
                set_status("SAVE FAILED", DANGER, "ERROR")
                group_page.result_text.value = f"✗  {path}"
                group_page.result_text.color = DANGER

        finally:
            _busy[0] = False
            group_page.set_busy(False, page)
        page.update()

    async def _paste_grp_hop(index: int):
        val = await ft.Clipboard().get() or ""
        if 0 <= index < len(group_page._hop_inputs):
            group_page._hop_inputs[index].value = val
        group_page.update_preview(mobile_switch.value)
        page.update()

    def _clear_group(e=None):
        for f in group_page._hop_inputs:
            f.value = ""
        group_page.file_name_input.value   = ""
        group_page.result_text.value       = ""
        group_page.progress_bar.visible    = False
        group_page.progress_bar.value      = 0
        group_page.update_preview(mobile_switch.value)
        set_status("CLEARED", MUTED)
        page.update()

    group_page = GroupPage(
        mobile_switch = mobile_switch,
        on_generate   = lambda e: page.run_task(_generate_group),
        on_paste      = lambda i: page.run_task(_paste_grp_hop, i),
        on_clear      = _clear_group,
    )

    # ── Log helpers ───────────────────────────────────────────────────────────
    async def _copy_log():
        try:
            await ft.Clipboard().set(logger.to_text())
        except Exception:
            pass
        set_status("LOG COPIED ✓", ACCENT, "OK")

    def _clear_log(e=None):
        logger.clear()
        logger.add("Log cleared", "INFO")
        page.update()

    # ── Stable widget refs ────────────────────────────────────────────────────
    _header_ref = ft.Container(bgcolor=BG)
    _tab_ref    = ft.Container(bgcolor=BG)
    _body_ref   = ft.Container(bgcolor=BG)

    _scroll_col = ft.Column(
        controls=[_body_ref],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=0,
    )

    _outer_col = ft.Column(
        controls=[
            _header_ref,
            _tab_ref,
            _scroll_col,
            footer.container,
        ],
        spacing=0,
        expand=True,
    )

    # ── Rebuild ───────────────────────────────────────────────────────────────
    def rebuild(e=None):
        w   = page.width or 400
        pad = 10 if w < 400 else 14

        tab         = current_tab["v"]
        toggle_card = _build_toggle_card()

        def _switch_tab(key: str):
            current_tab["v"] = key
            if key == "group":
                group_page.update_preview(mobile_switch.value)
            rebuild()

        _header_ref.content = build_header(w, pad)
        _tab_ref.content    = build_tab_bar(tab, pad, _switch_tab)

        if tab == "single":
            tab_content = single_page.build(w, toggle_card, page)
        elif tab == "group":
            tab_content = group_page.build(w, toggle_card, page)
        else:
            log_info = (
                f"→ {log_file}" if log_file else
                "Web: in-memory only" if is_web else
                "Android: Downloads/proxychainer.log"
            )
            tab_content = build_log_page(
                log_controls=logger.controls,
                log_info=log_info,
                on_copy=lambda e: page.run_task(_copy_log),
                on_clear=_clear_log,
            )

        footer.update_padding(pad)

        _body_ref.content = ft.Container(
            content=tab_content,
            padding=ft.Padding(pad, pad, pad, pad),
            bgcolor=BG,
        )

        page.update()

    # ── Resize handler ────────────────────────────────────────────────────────
    async def _on_resized(e=None):
        rebuild()

    page.on_resized = lambda e: page.run_task(_on_resized, e)

    # ── Boot ──────────────────────────────────────────────────────────────────
    page.scroll = None
    rebuild()
    page.add(_outer_col)

    logger.add(f"ProxyChainer started · log={'web/memory' if is_web else str(log_file)}", "OK")
    page.run_task(_refresh_ip)