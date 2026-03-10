"""
config.py — Xray/v2ray config builder.

Supports ANY two-hop chain:  hop1 → hop2
Each hop can be: socks:// vless:// vmess:// trojan:// ss://

Mobile config is V2rayNG-compatible (no inbounds — V2rayNG provides its own).
Desktop config adds socks:10808 + http:10809 inbounds.
"""

import json
from urllib.parse import urlparse

from parser import parse_proxy_url, build_outbound


def _is_socks(url: str) -> bool:
    return url.strip().lower().startswith("socks")


def _get_remark(url: str) -> str:
    url = url.strip()
    if "#" in url:
        return url[url.index("#") + 1:]
    return ""


def _build_socks_outbound(url: str, tag: str) -> dict:
    raw = url.strip()
    if "#" in raw:
        raw = raw[: raw.index("#")]
    parsed = urlparse(raw)
    addr, port = parsed.hostname, parsed.port
    if not addr or not port:
        raise ValueError(f"Invalid SOCKS URL: {url!r}  (expected socks://host:port)")
    out: dict = {
        "tag":      tag,
        "protocol": "socks",
        "settings": {"servers": [{"address": addr, "port": port}]},
    }
    if parsed.username and parsed.password:
        out["settings"]["servers"][0]["users"] = [
            {"user": parsed.username, "pass": parsed.password}
        ]
    return out


def build_config(hop1_url: str, hop2_url: str, mobile: bool) -> dict:
    """
    Build a complete Xray config chaining hop1 → hop2.

    Mobile mode (V2rayNG):
      - NO inbounds (V2rayNG injects its own tproxy/VPN inbound)
      - dns block with Iranian bypass
      - routing: ir/private → direct, else → hop2

    Desktop mode (v2rayN / CLI):
      - socks:10808 + http:10809 inbounds
      - simple routing: all → hop2
    """
    u1 = hop1_url.strip()
    u2 = hop2_url.strip()

    if not u1 or not u2:
        raise ValueError("Both hop fields are required")

    # hop1: connects directly to internet (the carrier)
    if _is_socks(u1):
        hop1_out = _build_socks_outbound(u1, tag="hop1")
    else:
        info1    = parse_proxy_url(u1)
        hop1_out = build_outbound(info1, dialer_tag=None, tag="hop1")

    # hop2: connects through hop1 via dialerProxy
    if _is_socks(u2):
        hop2_out = _build_socks_outbound(u2, tag="hop2")
        hop2_out.setdefault("streamSettings", {})
        hop2_out["streamSettings"].setdefault("sockopt", {})
        hop2_out["streamSettings"]["sockopt"]["dialerProxy"] = "hop1"
    else:
        info2    = parse_proxy_url(u2)
        hop2_out = build_outbound(info2, dialer_tag="hop1", tag="hop2")

    config: dict = {
        "log": {"loglevel": "warning"},
        "outbounds": [
            hop2_out,
            hop1_out,
            {"tag": "direct",  "protocol": "freedom",   "settings": {"domainStrategy": "UseIP"}},
            {"tag": "block",   "protocol": "blackhole",  "settings": {}},
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
    if _is_socks(u):
        return "socks"
    return parse_proxy_url(u)["protocol"]


def get_filename(hop1_url: str, hop2_url: str) -> str:
    import re

    def _safe(name: str) -> str:
        name = name.strip()
        name = re.sub(r'[\/:*?"<>|\\]', "_", name)
        return name[:48] or "unnamed"

    def _name(url: str) -> str:
        remark = _get_remark(url)
        if remark:
            return remark
        u = url.strip()
        if "#" in u:
            u = u[: u.index("#")]
        if _is_socks(u):
            return urlparse(u).hostname or "socks"
        try:
            info = parse_proxy_url(u)
            return info.get("remark") or info.get("addr") or "proxy"
        except Exception:
            return "proxy"

    return f"{_safe(_name(hop1_url))}-{_safe(_name(hop2_url))}"


# ── Mobile routing — V2rayNG compatible ──────────────────────────────────────
# V2rayNG docs / latest behaviour:
#   • Do NOT add inbounds — V2rayNG manages its own VPN/tproxy inbound
#   • outboundTag names must match exactly what's in outbounds[]
#   • dns.servers list: first entry = main, rest = fallback
#   • fakedns is optional; skip it to keep config minimal
#   • routeOnly in dns is NOT needed for basic usage
#   • "freedom" outbound domainStrategy="UseIP" ensures direct domains resolve locally

def _apply_mobile_routing(config: dict) -> None:
    config["dns"] = {
        "servers": [
            {
                "address": "223.5.5.5",       # Alibaba DNS — fast inside Iran for .ir
                "domains": ["geosite:ir"],
                "expectIPs": ["geoip:ir"],
            },
            "1.1.1.1",                         # Cloudflare — for everything else
            "8.8.8.8",                         # Google fallback
        ]
    }
    config["routing"] = {
        "domainStrategy": "IPIfNonMatch",
        "rules": [
            # Iranian domains and IPs → go direct (bypass proxy)
            {
                "type": "field",
                "outboundTag": "direct",
                "domain": ["geosite:ir"],
            },
            {
                "type": "field",
                "outboundTag": "direct",
                "ip": ["geoip:ir", "geoip:private"],
            },
            # Everything else → through the chain
            {
                "type": "field",
                "outboundTag": "hop2",
                "port": "0-65535",
            },
        ],
    }


# ── Desktop routing — v2rayN / CLI ────────────────────────────────────────────

def _apply_desktop_routing(config: dict) -> None:
    config["inbounds"] = [
        {
            "tag": "socks-in", "port": 10808, "listen": "127.0.0.1",
            "protocol": "socks",
            "settings": {"auth": "noauth", "udp": True},
            "sniffing": {"enabled": True, "destOverride": ["http", "tls"]},
        },
        {
            "tag": "http-in", "port": 10809, "listen": "127.0.0.1",
            "protocol": "http", "settings": {},
            "sniffing": {"enabled": True, "destOverride": ["http", "tls"]},
        },
    ]
    config["routing"] = {
        "domainStrategy": "IPIfNonMatch",
        "rules": [
            {"type": "field", "outboundTag": "hop2", "port": "0-65535"},
        ],
    }