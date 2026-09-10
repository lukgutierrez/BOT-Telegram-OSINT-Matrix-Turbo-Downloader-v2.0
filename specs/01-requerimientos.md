# 📋 01 — Requerimientos del Sistema (v2.0 Desktop)

> **Proyecto:** BOT-Telegram-OSINT-Matrix-Turbo-Downloader-v2.0  
> **Versión:** 2.0.0 Desktop  
> **Autor:** Luciano Gutiérrez (`@lukgtz`)

---

## 🎯 1. Requerimientos Funcionales

- **RF-01: Consola Web Táctica Streamlit (6 Pestañas):**
  - **Pestaña 1 (Buscador & Descarga Rápida):** Entrada para enlaces públicos, privados (`t.me/c/...`), IDs numéricos (`-100...`) y usernames con selector de concurrencia (1 a 15 hilos).
  - **Pestaña 2 (Extractor de Foros / Topics):** Pre-análisis con cálculo de fotos/videos, peso en MB, tiempo estimado y selección por casillas de verificación.
  - **Pestaña 3 (OSINT Reconnaissance):** Ficha técnica forense (`/info`), auditoría de filtraciones de datos por palabras clave y cálculo de horarios pico de publicación.
  - **Pestaña 4 (Google Drive Desktop Sync):** Sincronización de alta velocidad hacia `G:\Mi unidad` por bloques de 8MB con velocímetro en tiempo real (MB/s), ETA y barra de progreso. Permite sincronizar carpetas del bot o cualquier ruta arbitraria de la PC.
  - **Pestaña 5 (Gestor de Descargas & Deduplicación):** Visualizador de archivos descargados con búsqueda, filtros, hash SHA-256 y estadísticas de MB ahorrados.
  - **Pestaña 6 (Configuración & Proxies):** Conexión de cuenta Telegram, selección de modo Proxy (SOCKS5/MTProto) y estado de APIs.

- **RF-02: Bot Interactivo de Telegram (`bot.py`):**
  - Comandos: `/start`, `/help`, `/dl <link>`, `/batch <links>`, `/topics <link>`, `/alltopics <link>`, `/info <link>`, `/stats <link>`, `/search <palabra>`, `/sync <folder>`.

- **RF-03: Motor Criptográfico de Deduplicación SHA-256:**
  - Base de datos SQLite (`downloads_hashes.db`) que registra hashes de 64KB para evitar re-descargar archivos idénticos.

- **RF-04: Sincronización Local a Google Drive (`gdrive_desktop_sync.py`):**
  - Transferencia directa de archivos a la unidad virtual `G:\Mi unidad` usando bloques de 8MB, logrando transferencias de 100GB+ con 0% de uso de RAM y delegando la subida al daemon oficial de Google.

---

## ⚡ 2. Requerimientos No Funcionales

- **RNF-01: Rendimiento:** Capacidad de saturar el ancho de banda disponible mediante descargas concurrentes en paralelo con acelerador `cryptg`.
- **RNF-02: Estabilidad:** Cero bloqueos de bases de datos SQLite mediante el uso de sesiones en memoria en la interfaz web.
- **RNF-03: Privacidad:** Evasión y enrutamiento seguro mediante proxies SOCKS5 / MTProto configurables.
- **RNF-04: Usabilidad:** Interfaz táctica OLED (`#050505`) y scripts ejecutables en 1 clic para Windows (`.bat`).

---

## 🚫 3. Fuera de Alcance

- Modificación o borrado masivo de mensajes ajenos en canales de Telegram.
- Spameo publicitario automatizado.
