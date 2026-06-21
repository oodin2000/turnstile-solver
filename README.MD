<p align="center">
  <a href="https://github.com/zkamo/turnstile-solver">
    <img src="github_assets/logo.ico" width="120" height="120" alt="Turnstile Solver Logo">
  </a>
</p>

<h1 align="center">Turnstile Solver API</h1>

<p align="center">
  <strong>Async Cloudflare Turnstile solver with a persistent browser pool</strong>
  <br />
  Powered by <a href="https://github.com/daijro/camoufox">Camoufox</a> &amp; FastAPI
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="setup.md">Setup Guide</a> •
  <a href="https://t.me/cfdevelopment">Telegram Support</a>
</p>

<p align="center">
  <a href="https://github.com/zkamo/turnstile-solver/stargazers">
    <img src="https://img.shields.io/github/stars/zkamo/turnstile-solver?style=for-the-badge&logo=github&color=darkgreen" alt="GitHub Stars">
  </a>
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Maintained%3F-yes-green?style=for-the-badge" alt="Maintained">
</p>

---

## 📸 Preview

<p align="center">
  <img src="github_assets/preview.png" alt="API Preview" width="100%" style="border-radius: 8px;">
</p>

---

## ✨ Features

* ⚡ **Asynchronous** – handles multiple solve requests concurrently without blocking.
* 🧩 **Persistent browser pool** – browsers stay alive between requests; no startup overhead.
* 🎯 **Queue‑based job processing** – tasks are distributed to available workers automatically.
* 🛡️ **Stealth** – uses Camoufox with safe Firefox prefs and WebRTC blocking.
* 📦 **Simple REST API** – submit jobs and poll for results with ease.
* ⚙️ **Configurable** – pool size, headless mode, timeouts, host/port via `config.json`.

---

## 🚀 Performance

| Metric | Value |
| :--- | :--- |
| Average solve time | 5 - 7 seconds (depends on challenge complexity) |
| Concurrent requests | Up to pool size (default: 3) |
| Token success rate | > 99% (with valid sitekey and URL) |

---

## 🤝 Integrations & Ecosystem

| Service | Role |
| :--- | :--- |
| **[Camoufox](https://github.com/daijro/camoufox)** | Stealth browser automation |
| **[FastAPI](https://fastapi.tiangolo.com/)** | High‑performance API framework |
| **[Uvicorn](https://www.uvicorn.org/)** | ASGI server |

---

## 👥 Contributors

* **`Zkamo`** — Developer

---

<p align="center">
  <sub>⚠️ <strong>Disclaimer:</strong> This project is intended for <strong>educational and legitimate automation</strong> purposes only. Respect the terms of service of the websites you interact with. Use at your own risk.</sub>
</p>