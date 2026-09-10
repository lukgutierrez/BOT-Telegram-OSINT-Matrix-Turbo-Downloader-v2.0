# 🏗️ 03 — Arquitectura del Sistema (v2.0 Desktop)

> **Proyecto:** BOT-Telegram-OSINT-Matrix-Turbo-Downloader-v2.0  
> **Versión:** 2.0.0 Desktop

---

## 📐 Diagrama de Arquitectura de Módulos

```mermaid
graph TD
    User["👤 Operador / Analista"] -->|Interactúa con| WebGUI["🌐 Streamlit Cyber GUI (app_web.py)"]
    User -->|Envía Comandos| TelegramBot["🤖 Bot de Telegram (bot.py)"]

    subgraph "Core Engines"
        LP["🔗 Link Parser (link_parser.py)"]
        OSINT["🕵️ OSINT Recon Engine (osint.py)"]
        DL["⚡ Concurrency Downloader (downloader.py)"]
        DEDUP["🔐 SHA-256 Deduplicator (hash_dedup.py)"]
    end

    subgraph "Storage & Cloud Sync"
        GDESK["💻 Google Drive Desktop Sync (gdrive_desktop_sync.py)"]
        GAPI["☁️ Google Drive API v3 (gdrive_uploader.py)"]
        LOCALFS["📁 Local Storage (downloads/)"]
        SQLITEDB["🗄️ SQLite Database (downloads_hashes.db)"]
    end

    WebGUI --> LP
    WebGUI --> OSINT
    WebGUI --> DL
    WebGUI --> GDESK
    WebGUI --> GAPI

    TelegramBot --> LP
    TelegramBot --> OSINT
    TelegramBot --> DL

    DL --> DEDUP
    DEDUP --> SQLITEDB
    DL --> LOCALFS
    GDESK --> LOCALFS
    GDESK -->|Stream 8MB| GDriveFS["💾 Google Drive Virtual FS (G:\Mi unidad)"]
    GDriveFS -->|Background Daemon| CloudDrive["☁️ Google Drive Cloud"]
```

---

## 🧩 Especificación de Módulos

| Módulo | Responsabilidad |
| :--- | :--- |
| `app_web.py` | Consola Web Streamlit interactiva con 6 pestañas, métricas en vivo, gráficos y gestión de descargas. |
| `bot.py` | Servidor de comandos de Telegram (`/dl`, `/batch`, `/topics`, `/info`, `/stats`, `/sync`). |
| `downloader.py` | Motor de descarga con `asyncio.Semaphore`, aceleración `cryptg` y reintentos automáticos. |
| `osint.py` | Inspección forense de canales/grupos, conteo de fotos/videos/docs, horarios pico y búsqueda de palabras clave. |
| `gdrive_desktop_sync.py` | Copia de alta velocidad por bloques (8MB) hacia `G:\Mi unidad` con telemetría en vivo. |
| `hash_dedup.py` | Deduplicación SQLite con cálculo de hashes SHA-256 en bloques de 64KB. |
