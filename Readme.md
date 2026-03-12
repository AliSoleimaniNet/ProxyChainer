# ⚡ ProxyChainer

**Chain any number of proxies into a single Xray-core / V2Ray config — any protocol to any protocol.**

```
Your Device  →  Hop 1  →  Hop 2  →  …  →  Hop N  →  Internet
                VLESS / VMess / Trojan / SS / SOCKS
```

Available as a **Windows app**, **Android APK**, and **Web app**.

---

## 🌐 Try it now

**[→ Open Web App](https://AliSoleimaniNet.github.io/ProxyChainer/)**

---

## 📥 Download

Go to the [**Releases**](https://github.com/AliSoleimaniNet/ProxyChainer/releases) page and download:

| Platform | File |
|----------|------|
| Windows | `ProxyChainer-Windows.zip` |
| Android | `ProxyChainer-Android.apk` |

---

## What it does

Paste proxy URLs into hop fields — ProxyChainer generates a ready-to-use JSON config that chains them together using Xray's `dialerProxy`. Supports **VLESS**, **VMess**, **Trojan**, **Shadowsocks**, and **SOCKS**.

- **Unlimited hops** — start with 2 hops, add as many as you need with the **＋ ADD HOP** button; remove any hop (minimum 2 always enforced)
- **Single mode** — N hops → one config, auto-copied to clipboard, saved as a JSON array `[config]`
- **Group mode** — N lists of URLs → generates every combination across all hop columns and saves them as a single JSON array file `[config1, config2, …]`
- **Remarks** — every output config includes a `"remarks"` field with the full chain name (e.g. `Server A → Server B → 🇺🇳 @Channel`) — emoji and unicode preserved
- **PC / Mobile toggle** — desktop config uses SOCKS5 `10808` + HTTP `10809` inbounds; mobile config bypasses Iran geosite/geoip
- **IP & ping info** — shows your current exit IP, city, and latency

---

## Output format

Both Single and Group modes output a **JSON array**:

```json
[
  {
    "remarks": "Hop1Name → Hop2Name → Hop3Name",
    "log": { "loglevel": "warning" },
    "outbounds": [ ... ],
    "routing": { ... }
  }
]
```

Group mode saves **one file** containing all generated configs:

```json
[
  { "remarks": "Server A → Proxy 1", ... },
  { "remarks": "Server A → Proxy 2", ... },
  { "remarks": "Server B → Proxy 1", ... }
]
```

---

## Built with

[Flet](https://flet.dev) · [Xray-core](https://github.com/XTLS/Xray-core) · Python 3.11+