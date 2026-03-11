"""
core/config.py
Xray/V2Ray config builder for two-hop proxy chaining.

Chaining is done via V2Ray's standard outbound proxySettings:
    hop2_outbound.proxySettings = {"tag": "hop1"}

Traffic flow: local → [inbound] → hop2 (via hop1) → internet

Mobile (V2rayNG):  no inbounds, dns + routing only
Desktop (v2rayN):  socks:10808 + http:10809 inbounds
"""

import json
import re
from urllib.parse import urlparse

from core.parser import parse_proxy_url, build_outbound


def _is_socks(url: str) -> bool:
    return url.strip().lower().startswith("socks")


def _get_remark(url: str) -> str:
    url = url.strip()
    return url[url.index("#") + 1:] if "#" in url else ""


def _strip_fragment(url: str) -> str:
    return url[: url.index("#")] if "#" in url else url


def _build_socks_outbound(url: str, tag: str) -> dict:
    raw    = _strip_fragment(url.strip())
    parsed = urlparse(raw)
    addr, port = parsed.hostname, parsed.port
    if not addr or not port:
        raise ValueError(f"Invalid SOCKS URL: {url!r}  (expected socks://host:port)")

    outbound: dict = {
        "tag":      tag,
        "protocol": "socks",
        "settings": {"servers": [{"address": addr, "port": port}]},
    }

    if parsed.username and parsed.password:
        outbound["settings"]["servers"][0]["users"] = [
            {"user": parsed.username, "pass": parsed.password}
        ]

    return outbound


def build_config(hop1_url: str, hop2_url: str, mobile: bool) -> dict:
    """Build a complete two-hop Xray/V2Ray config."""
    u1 = hop1_url.strip()
    u2 = hop2_url.strip()

    if not u1 or not u2:
        raise ValueError("Both hop fields are required")

    hop1_out = (
        _build_socks_outbound(u1, tag="hop1")
        if _is_socks(u1)
        else build_outbound(parse_proxy_url(u1), tag="hop1")
    )

    hop2_out = (
        _build_socks_outbound(u2, tag="hop2")
        if _is_socks(u2)
        else build_outbound(parse_proxy_url(u2), tag="hop2")
    )

    hop2_out["proxySettings"] = {"tag": "hop1"}

    config: dict = {
        "log": {"loglevel": "warning"},
        "outbounds": [
            hop2_out,
            hop1_out,
            {"tag": "direct", "protocol": "freedom",   "settings": {"domainStrategy": "UseIP"}},
            {"tag": "block",  "protocol": "blackhole",  "settings": {}},
        ],
    }

    if mobile:
        _apply_mobile_routing(config)
    else:
        _apply_desktop_routing(config)

    return config


def build_config_json(hop1_url: str, hop2_url: str, mobile: bool) -> str:
    return json.dumps(build_config(hop1_url, hop2_url, mobile), indent=2)


def get_protocol(url: str) -> str:
    u = url.strip()
    return "socks" if _is_socks(u) else parse_proxy_url(u)["protocol"]


def get_filename(hop1_url: str, hop2_url: str, index: int = 0) -> str:
    """Build a safe filename from both hop names. index appended when non-zero."""
    def _safe(name: str) -> str:
        name = re.sub(r'[\/:*?"<>|\\]', "_", name.strip())
        return name[:40] or "unnamed"

    def _name(url: str) -> str:
        remark = _get_remark(url)
        if remark:
            return remark
        u = _strip_fragment(url.strip())
        if _is_socks(u):
            try:
                return urlparse(u).hostname or "socks"
            except Exception:
                return "socks"
        try:
            info = parse_proxy_url(u)
            return info.get("remark") or info.get("addr") or "proxy"
        except Exception:
            return "proxy"

    base = f"{_safe(_name(hop1_url))}-{_safe(_name(hop2_url))}"
    return f"{base}_{index:03d}" if index > 0 else base


# ── Routing profiles ──────────────────────────────────────────────────────────

def _apply_mobile_routing(config: dict) -> None:
    """V2rayNG-compatible routing: bypasses Iran, proxies everything else."""
    config["dns"] = {
        "servers": [
            {
                "address":   "223.5.5.5",
                "port":      53,
                "domains":   ["geosite:ir"],
                "expectIPs": ["geoip:ir"],
            },
            "1.1.1.1",
            "8.8.8.8",
        ]
    }
    config["routing"] = {
        "domainStrategy": "IPIfNonMatch",
        "rules": [
            {"type": "field", "outboundTag": "direct", "domain": ["geosite:ir"]},
            {"type": "field", "outboundTag": "direct", "ip": ["geoip:ir", "geoip:private"]},
            {"type": "field", "outboundTag": "hop2",   "port": "0-65535"},
        ],
    }


def _apply_desktop_routing(config: dict) -> None:
    """Desktop routing with socks:10808 and http:10809 inbounds."""
    config["inbounds"] = [
        {
            "tag":      "socks-in",
            "port":     10808,
            "listen":   "127.0.0.1",
            "protocol": "socks",
            "settings": {"auth": "noauth", "udp": True},
            "sniffing": {"enabled": True, "destOverride": ["http", "tls"]},
        },
        {
            "tag":      "http-in",
            "port":     10809,
            "listen":   "127.0.0.1",
            "protocol": "http",
            "settings": {},
            "sniffing": {"enabled": True, "destOverride": ["http", "tls"]},
        },
    ]
    config["routing"] = {
        "domainStrategy": "IPIfNonMatch",
        "rules": [
            {"type": "field", "outboundTag": "hop2", "port": "0-65535"},
        ],
    }
