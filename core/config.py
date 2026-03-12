"""
core/config.py
Xray/V2Ray config builder for N-hop proxy chaining.

Chaining is done via V2Ray's dialerProxy sockopt:
    hop[n]_outbound.streamSettings.sockopt.dialerProxy = "hop[n-1]"

Traffic flow: local → [inbound] → hopN → hopN-1 → … → hop1 → internet
              (and responses travel back: internet → hop1 → … → hopN → local)

Mobile (V2rayNG):  no inbounds, dns + routing only
Desktop (v2rayN):  socks:10808 + http:10809 inbounds

Output is always a JSON array: [config]  (single) or [cfg1, cfg2, …] (group)
Each config carries a top-level "remarks" field with a human-readable name.
"""

import json
import re
from urllib.parse import urlparse, unquote

from core.parser import parse_proxy_url, build_outbound


def _is_socks(url: str) -> bool:
    return url.strip().lower().startswith("socks")


def _get_remark(url: str) -> str:
    url = url.strip()
    return unquote(url[url.index("#") + 1:]) if "#" in url else ""


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


def _build_hop_outbound(url: str, tag: str) -> dict:
    """Parse a single hop URL into an outbound dict with the given tag."""
    u = url.strip()
    if _is_socks(u):
        return _build_socks_outbound(u, tag)
    return build_outbound(parse_proxy_url(u), tag=tag)


def _make_remarks(hop_urls: list[str]) -> str:
    """Build a readable remarks string from N hop URLs."""
    parts = []
    for url in hop_urls:
        r = _get_remark(url)
        if r:
            parts.append(r)
        else:
            u = _strip_fragment(url.strip())
            if _is_socks(u):
                try:
                    parts.append(urlparse(u).hostname or "socks")
                except Exception:
                    parts.append("socks")
            else:
                try:
                    info = parse_proxy_url(u)
                    parts.append(info.get("remark") or info.get("addr") or "proxy")
                except Exception:
                    parts.append("proxy")
    return " → ".join(parts)


def build_config(hop_urls: list[str], mobile: bool) -> dict:
    """
    Build a complete N-hop Xray/V2Ray config.

    hop_urls: list of proxy URLs, index 0 = first hop (closest to internet),
              last index = last hop (closest to user / inbound).

    Chain is built so that:
        last_hop → … → hop[1] → hop[0] → internet

    dialerProxy chain:
        outbound[n].sockopt.dialerProxy = "hop[n-1]"

    The outbound that traffic enters first is the LAST hop outbound
    (it proxies via the one before it, which proxies via the one before it…)
    """
    if len(hop_urls) < 2:
        raise ValueError("At least 2 hops are required")

    hops = [url.strip() for url in hop_urls if url.strip()]
    if len(hops) < 2:
        raise ValueError("At least 2 non-empty hop URLs are required")

    # Build outbounds: hop0, hop1, …, hopN-1
    outbounds: list[dict] = []
    for i, url in enumerate(hops):
        tag = f"hop{i}"
        ob  = _build_hop_outbound(url, tag)
        outbounds.append(ob)

    # Apply dialerProxy chain: hop[i] routes through hop[i-1]
    for i in range(1, len(outbounds)):
        if "streamSettings" not in outbounds[i]:
            outbounds[i]["streamSettings"] = {}
        outbounds[i]["streamSettings"]["sockopt"] = {
            "dialerProxy": f"hop{i - 1}"
        }

    # The "entry" outbound (what routing points to) is the last hop
    entry_tag = f"hop{len(hops) - 1}"

    config: dict = {
        "remarks": _make_remarks(hops),
        "log":     {"loglevel": "warning"},
        "outbounds": [
            *outbounds,
            {"tag": "direct", "protocol": "freedom",  "settings": {"domainStrategy": "UseIP"}},
            {"tag": "block",  "protocol": "blackhole", "settings": {}},
        ],
    }

    if mobile:
        _apply_mobile_routing(config, entry_tag)
    else:
        _apply_desktop_routing(config, entry_tag)

    return config


def build_config_json(hop_urls: list[str], mobile: bool) -> str:
    """Return a JSON array string containing the single config object."""
    cfg = build_config(hop_urls, mobile)
    return json.dumps([cfg], indent=2)


def build_config_list_json(configs: list[dict]) -> str:
    """Serialize a list of config dicts as a JSON array."""
    return json.dumps(configs, indent=2)


def get_protocol(url: str) -> str:
    u = url.strip()
    return "socks" if _is_socks(u) else parse_proxy_url(u)["protocol"]


def get_filename(hop_urls: list[str], index: int = 0) -> str:
    """Build a safe filename from N hop names. index appended when non-zero."""
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

    parts = [_safe(_name(u)) for u in hop_urls]
    base  = "-".join(parts)
    return f"{base}_{index:03d}" if index > 0 else base


# ── Routing profiles ──────────────────────────────────────────────────────────

def _apply_mobile_routing(config: dict, entry_tag: str) -> None:
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
            {"type": "field", "outboundTag": entry_tag, "port": "0-65535"},
        ],
    }


def _apply_desktop_routing(config: dict, entry_tag: str) -> None:
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
            {"type": "field", "outboundTag": entry_tag, "port": "0-65535"},
        ],
    }