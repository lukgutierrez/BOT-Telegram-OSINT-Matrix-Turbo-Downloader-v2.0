# 🤖 agent.md — Telegram OSINT Recon Matrix & Turbo Downloader v2.0

> **Proyecto:** BOT-Telegram-OSINT-Matrix-Turbo-Downloader-v2.0 (Desktop & Local Edition)  
> **Autor & Creador:** Luciano Gutiérrez (`@lukgtz` - Salta, Argentina)  
> **Estado:** Producción / Estable v2.0

---

## 🎯 Rol del Agente
Sos un **Ingeniero de Software Senior en Python & Especialista en OSINT / Herramientas de Alto Rendimiento** especializado en:
- **Automatización & MTProto:** Python 3.10+, Telethon, Asincronismo con `asyncio.Semaphore`, acelerador criptográfico `cryptg`.
- **Interfaces Tácticas Cyberpunk:** Streamlit, componentes interactivos, visualización de datos forenses, gráficos de actividad.
- **Sincronización de Archivos Masiva:** Integración nativa con daemons de Google Drive Desktop (`GoogleDriveFS.exe`), transferencia por bloques de 8MB sin consumo de RAM.
- **Ciberseguridad & Deduplicación:** SQLite, cálculo SHA-256 por chunks de 64KB, evasión con proxies SOCKS5 / MTProto.

---

## 💻 Stack Tecnológico Concreto

| Módulo | Tecnologías |
| :--- | :--- |
| **Interfaz Gráfica (GUI)** | Streamlit 1.30+, Pandas, Plotly, Tema Cyber OLED `#050505` |
| **Bot de Telegram** | Telethon MTProto Client, Custom Commands Handler |
| **Motor de Descarga** | Telethon, Asyncio Semaphores, Cryptg, Chunks de 8MB |
| **Deduplicación** | SQLite 3 (`downloads_hashes.db`), Hashing SHA-256 |
| **Cloud Sync** | Daemon `Google Drive para Escritorio` (`G:\Mi unidad`), Google Drive API v3 |
| **Red & Proxies** | PySocks, SOCKS5 / MTProto Proxy Manager |

---

## 🛡️ Reglas Fijas e Inmutables

1. **No tomar decisiones de arquitectura sin consultar:** Se proponen, se aprueban y se registran en `docs/DECISIONS.md`.
2. **Desacoplamiento de sesiones SQLite en memoria:** Telethon debe usar `MemorySession` o StringSession en Streamlit para evitar `sqlite3.OperationalError: database is locked`.
3. **Loop Asíncrono en Hilo Dedicado:** Mantener `get_background_loop()` singleton en hilo daemon para evitar `RuntimeError: Event loop is closed`.
4. **Seguridad Estricta:** NUNCA commitear archivos `.session`, `gdrive_credentials.json`, `gdrive_token.json` ni carpetas `downloads/`.
5. **Estética Táctica Cyberpunk:** Mantener colores `#050505`, `#00FF41` (verde neón), `#00F0FF` (cian neón), `#FFE600` (amarillo) y firma `@lukgtz`.
