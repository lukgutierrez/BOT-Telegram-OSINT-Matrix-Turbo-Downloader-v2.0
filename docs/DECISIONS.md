# 📜 Registro de Decisiones de Arquitectura (ADR) — v2.0 Desktop

> **Proyecto:** BOT-Telegram-OSINT-Matrix-Turbo-Downloader-v2.0  
> **Reglas:** Nunca se borra una entrada; se marca como "Reemplazada por ADR-00Y".

---

## ADR-001 — Desacoplamiento de Sesiones SQLite en Streamlit (`MemorySession`)
**Fecha:** 2026-09-08  
**Estado:** Vigente  
**Decisión:** Abrir temporalmente el archivo de sesión para leer la clave de autenticación (`auth_key`), `dc_id` y puerto, transfiriéndolos a una instancia de `MemorySession()` en memoria.  
**Motivo:** Telethon bloquea el archivo `.session` en disco por defecto. Al ejecutar scripts en Streamlit con múltiples hilos, SQLite lanzaba `sqlite3.OperationalError: database is locked`.  
**Alternativas descartadas:** Usar un único archivo `.session` compartido (bloqueos continuos).

---

## ADR-002 — Bucle de Eventos Asíncrono en Hilo Dedicado
**Fecha:** 2026-09-08  
**Estado:** Vigente  
**Decisión:** Crear un singleton de loop asíncrono (`get_background_loop()`) en un `threading.Thread(daemon=True)` y despachar tareas con `asyncio.run_coroutine_threadsafe()`.  
**Motivo:** Streamlit destruye y crea bucles de asyncio por cada ciclo de ejecución, provocando `RuntimeError: Event loop is closed`.  
**Alternativas descartadas:** Iniciar `asyncio.run()` en cada evento de la interfaz (congelaba la interfaz gráfica).

---

## ADR-003 — Deduplicación Doble-Capa (Identificador + Hash SHA-256)
**Fecha:** 2026-09-09  
**Estado:** Vigente  
**Decisión:** Capa 1 por nombre determinista en disco `YYYYMMDD_HHMMSS_{msg_id}_{filename}` (O(1)), y Capa 2 criptográfica con hash SHA-256 en bloques de 64KB en SQLite (`downloads_hashes.db`).  
**Motivo:** Evitar redundancia y ahorrar ancho de banda al descargar canales con miles de mensajes duplicados.  
**Alternativas descartadas:** Chequear solo tamaño de archivo (falsos positivos).

---

## ADR-004 — Sincronización Google Drive Desktop Sync por Chunks de 8MB
**Fecha:** 2026-09-09  
**Estado:** Vigente  
**Decisión:** Aprovechar la unidad virtual montada por Google Drive para Escritorio (`G:\Mi unidad`) y transferir archivos por bloques de 8MB calculando velocidad en tiempo real y ETA.  
**Motivo:** Permite transferir más de 100GB con 0% de uso de RAM y delega la subida a la nube al daemon oficial de Google, evitando timeouts de socket en Python.  
**Alternativas descartadas:** Cargar archivos en memoria antes de subirlos por API REST (causaba Out Of Memory).
