"""
network.py
Ping measurement and IP info fetching with multiple provider fallbacks.
Works on desktop (requests), gracefully degrades on web (httpx / no ping).
"""

import time

# Try requests first (desktop/mobile builds), then httpx (web-compatible)
try:
    import requests as _req
    def _get(url, timeout=5):
        r = _req.get(url, timeout=timeout)
        return r.status_code, r.json()
    def _get_raw(url, timeout=5):
        r = _req.get(url, timeout=timeout)
        return r.status_code
    HAS_HTTP = True
except ImportError:
    try:
        import httpx as _httpx
        def _get(url, timeout=5):
            r = _httpx.get(url, timeout=timeout, follow_redirects=True)
            return r.status_code, r.json()
        def _get_raw(url, timeout=5):
            r = _httpx.get(url, timeout=timeout, follow_redirects=True)
            return r.status_code
        HAS_HTTP = True
    except ImportError:
        HAS_HTTP = False


# ── Ping ──────────────────────────────────────────────────────────────────────

def measure_ping(count: int = 3) -> float | None:
    """HTTP ping via Google generate_204. Returns avg ms or None on failure."""
    if not HAS_HTTP:
        return None
    url   = "https://www.google.com/generate_204"
    times = []
    for _ in range(count):
        try:
            start   = time.perf_counter()
            status  = _get_raw(url, timeout=5)
            elapsed = (time.perf_counter() - start) * 1000
            if status in (200, 204):
                times.append(elapsed)
        except Exception:
            pass
    if not times:
        return None
    return round(sum(times) / len(times), 1)


# ── IP providers ──────────────────────────────────────────────────────────────

def get_ip_info() -> dict | None:
    """
    Try each provider in order. Returns dict with keys:
        ip, city, country, org, ping
    Returns None if all providers fail.
    """
    if not HAS_HTTP:
        return {
            "ip":      "N/A",
            "city":    "—",
            "country": "—",
            "org":     "HTTP library unavailable",
            "ping":    None,
        }

    for provider in [_from_ip_api_com, _from_ipinfo_io, _from_ipapi_co, _from_freeipapi]:
        try:
            info = provider()
            if info:
                info["ping"] = measure_ping()
                return info
        except Exception:
            continue

    return None


def _from_ip_api_com() -> dict | None:
    # 45 req/min, no key needed, HTTP (not HTTPS) — works through proxies too
    status, d = _get("http://ip-api.com/json/?fields=status,country,city,org,query")
    if d.get("status") != "success":
        return None
    return {
        "ip":      d.get("query",   "N/A"),
        "city":    d.get("city",    "N/A"),
        "country": d.get("country", "N/A"),
        "org":     d.get("org",     "N/A"),
    }


def _from_ipinfo_io() -> dict | None:
    # 50k req/month, no key needed
    status, d = _get("https://ipinfo.io/json")
    if "ip" not in d:
        return None
    return {
        "ip":      d.get("ip",      "N/A"),
        "city":    d.get("city",    "N/A"),
        "country": d.get("country", "N/A"),
        "org":     d.get("org",     "N/A"),
    }


def _from_ipapi_co() -> dict | None:
    # 1k req/day, no key needed
    status, d = _get("https://ipapi.co/json/")
    if d.get("error"):
        return None
    return {
        "ip":      d.get("ip",           "N/A"),
        "city":    d.get("city",         "N/A"),
        "country": d.get("country_name", "N/A"),
        "org":     d.get("org",          "N/A"),
    }


def _from_freeipapi() -> dict | None:
    # Unlimited, no key needed
    status, d = _get("https://freeipapi.com/api/json")
    if "ipAddress" not in d:
        return None
    return {
        "ip":      d.get("ipAddress",   "N/A"),
        "city":    d.get("cityName",    "N/A"),
        "country": d.get("countryName", "N/A"),
        "org":     "N/A",
    }