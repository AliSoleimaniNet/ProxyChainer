# ⚡ ProxyChainer
> **SOCKS → VLESS // Modern dialerProxy Tunnel Builder**

**ProxyChainer** is a specialized utility designed to create chained configurations for **Xray-core** based clients. It leverages the `dialerProxy` feature to tunnel your VLESS traffic through a local or remote SOCKS proxy, helping to bypass restrictive network environments.

---

## 🌐 Live Demo (Web Version)
You can use the application directly in your browser without installation:
👉 **[https://AliSoleimaniNet.github.io/ProxyChainer/](https://AliSoleimaniNet.github.io/ProxyChainer/)**

---

## 🚀 How to Use

1.  **Input SOCKS:** Paste your intermediate SOCKS proxy URL (e.g., `socks://127.0.0.1:1080`).
2.  **Input VLESS:** Paste your destination VLESS configuration link.
3.  **Generate:** Click the **GENERATE CHAIN CONFIG** button.
4.  **Get Results:** * The app instantly generates a structured **Xray-compatible JSON**.
    * The result is **automatically copied** to your clipboard.
    * Use this JSON in clients like **v2rayN**, **Nekoray**, or **v2rayNG**.



---

## 📦 Download Desktop & Mobile

Our CI/CD pipeline automatically builds the latest versions for all platforms. You can find them in the **[Releases](https://github.com/AliSoleimaniNet/ProxyChainer/releases)** section:

* **Windows:** Download `ProxyChainer-Windows.zip` (Extract and run the `.exe`).
* **Android:** Download `ProxyChainer-Android.apk` for mobile usage.
* **Web:** Always synced with the `main` branch.



---

## 🛠 Technical Stack
* **UI Framework:** [Flet](https://flet.dev) (Flutter for Python).
* **Package Management:** [uv](https://github.com/astral-sh/uv) for ultra-fast dependency resolution.
* **Environment:** Python 3.12.
* **CI/CD:** GitHub Actions for multi-platform automated deployment.

---
*Built for performance and privacy by AliSoleimaniNet.*
