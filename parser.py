"""
parser.py
Parse vless / vmess / trojan / ss URLs into normalized dicts,
then build Xray-compatible outbound objects.
"""

import base64
import json
from urllib.parse import urlparse, parse_qs, unquote


# ── URL parser ────────────────────────────────────────────────────────────────

def parse_proxy_url(url: str) -> dict:
    """
    Parse any of: vless, vmess, trojan, ss / shadowsocks

    Returns a normalized dict:
        protocol  str       — vless | vmess | trojan | ss
        addr      str       — server hostname / IP
        port      int       — server port
        uuid      str       — user ID / password  (vless / vmess / trojan)
        method    str       — cipher method       (ss only)
        password  str       — password            (ss only)
        params    dict[str] — transport / security query params

    Raises ValueError on unsupported or malformed input.
    """
    url = url.strip()

    # Extract fragment as remark before stripping
    remark = ""
    if "#" in url:
        remark = url[url.index("#") + 1:]
        url    = url[: url.index("#")]

    if "://" not in url:
        raise ValueError("Not a valid proxy URL (missing '://')")

    protocol = url.split("://")[0].lower()

    # ── VMess  (Base64-encoded JSON) ──────────────────────────────
    if protocol == "vmess":
        return _parse_vmess(url, remark)

    # ── Shadowsocks ───────────────────────────────────────────────
    if protocol in ("ss", "shadowsocks"):
        return _parse_ss(url, remark)

    # ── VLESS / Trojan  (standard URI) ────────────────────────────
    if protocol in ("vless", "trojan"):
        return _parse_uri(url, protocol, remark)

    raise ValueError(f"Unsupported protocol: '{protocol}'")


def _parse_vmess(url: str, remark: str = "") -> dict:
    b64 = url[len("vmess://"):]
    b64 += "=" * (-len(b64) % 4)          # fix padding
    try:
        d = json.loads(base64.b64decode(b64).decode("utf-8"))
    except Exception as ex:
        raise ValueError(f"Invalid VMess base64: {ex}") from ex

    return {
        "protocol": "vmess",
        "remark":   remark,
        "addr":     d.get("add", ""),
        "port":     int(d.get("port", 443)),
        "uuid":     d.get("id", ""),
        "params": {
            "type":     d.get("net",  "tcp"),
            "security": d.get("tls",  ""),
            "path":     d.get("path", ""),
            "host":     d.get("host", ""),
            "sni":      d.get("sni",  ""),
            "aid":      str(d.get("aid", "0")),
        },
    }


def _parse_ss(url: str, remark: str = "") -> dict:
    parsed   = urlparse(url)
    userinfo = parsed.username or ""

    # userinfo may be  base64(method:password)  OR plain  method:password
    method   = "aes-256-gcm"
    password = ""
    try:
        decoded = base64.b64decode(
            userinfo + "=" * (-len(userinfo) % 4)
        ).decode("utf-8")
        if ":" in decoded:
            method, password = decoded.split(":", 1)
        else:
            password = decoded
    except Exception:
        if ":" in userinfo:
            method, password = userinfo.split(":", 1)
        else:
            password = userinfo

    return {
        "protocol": "ss",
        "remark":   remark,
        "addr":     parsed.hostname or "",
        "port":     parsed.port or 443,
        "method":   method,
        "password": password,
        "params":   {},
    }


def _parse_uri(url: str, protocol: str, remark: str = "") -> dict:
    parsed = urlparse(url)
    query  = parse_qs(parsed.query)
    params = {k: unquote(v[0]) for k, v in query.items()}
    return {
        "protocol": protocol,
        "remark":   remark,
        "addr":     parsed.hostname or "",
        "port":     parsed.port or 443,
        "uuid":     unquote(parsed.username or ""),
        "params":   params,
    }


# ── Outbound builder ──────────────────────────────────────────────────────────

def build_outbound(info: dict, dialer_tag: str | None, tag: str = "proxy-chain") -> dict:
    """
    Convert a parsed proxy dict (from parse_proxy_url) into an
    Xray-compatible outbound object.
    If dialer_tag is given, sets sockopt.dialerProxy so this outbound
    tunnels through the named outbound (used for chaining).
    """
    protocol = info["protocol"]
    addr     = info["addr"]
    port     = info["port"]
    params   = info.get("params", {})

    sockopt = {}
    if dialer_tag:
        sockopt["dialerProxy"] = dialer_tag

    outbound: dict = {
        "tag":      tag,
        "protocol": protocol,
        "settings": {},
        "streamSettings": {
            "network":  params.get("type", "tcp"),
            "security": params.get("security", "none") or "none",
            "sockopt":  sockopt,
        },
    }

    # ── Protocol-level settings ───────────────────────────────────
    if protocol == "vless":
        outbound["settings"] = {
            "vnext": [{"address": addr, "port": port, "users": [{
                "id":         info["uuid"],
                "encryption": "none",
                "flow":       params.get("flow", ""),
            }]}]
        }

    elif protocol == "vmess":
        outbound["settings"] = {
            "vnext": [{"address": addr, "port": port, "users": [{
                "id":       info["uuid"],
                "alterId":  int(params.get("aid", 0)),
                "security": "auto",
            }]}]
        }

    elif protocol == "trojan":
        outbound["settings"] = {
            "servers": [{"address": addr, "port": port, "password": info["uuid"]}]
        }

    elif protocol == "ss":
        outbound["settings"] = {
            "servers": [{"address": addr, "port": port,
                         "method":  info["method"],
                         "password": info["password"]}]
        }

    # ── Security settings ─────────────────────────────────────────
    sec = params.get("security", "").lower()

    if sec == "tls":
        outbound["streamSettings"]["tlsSettings"] = {
            "serverName":    params.get("sni", ""),
            "allowInsecure": params.get("allowInsecure", "0") == "1",
            "alpn":          [a for a in params.get("alpn", "").split(",") if a],
            "fingerprint":   params.get("fp", ""),
        }

    elif sec == "reality":
        outbound["streamSettings"]["realitySettings"] = {
            "serverName":  params.get("sni",  ""),
            "fingerprint": params.get("fp",   "chrome"),
            "publicKey":   params.get("pbk",  ""),
            "shortId":     params.get("sid",  ""),
            "spiderX":     params.get("spx",  "/"),
        }

    # ── Transport settings ────────────────────────────────────────
    net = params.get("type", "tcp").lower()

    if net == "ws":
        outbound["streamSettings"]["wsSettings"] = {
            "path":    unquote(params.get("path", "/")),
            "headers": {"Host": params.get("host", "")},
        }

    elif net == "grpc":
        outbound["streamSettings"]["grpcSettings"] = {
            "serviceName": params.get("serviceName", params.get("path", "")),
        }

    elif net == "h2":
        outbound["streamSettings"]["httpSettings"] = {
            "host": [params.get("host", "")],
            "path": params.get("path", "/"),
        }

    return outbound