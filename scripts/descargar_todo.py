import asyncio
import os
import sqlite3
import time
from telethon import TelegramClient
from config import API_ID, API_HASH, DOWNLOAD_FOLDER
from downloader import obtener_subcarpeta, obtener_nombre_archivo
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, DocumentAttributeVideo

# Configurar timeout largo en la base de datos de la sesion para evitar "database is locked"
def configurar_sqlite():
    try:
        conn = sqlite3.connect("user_session.session", timeout=30)
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=OFF")
        conn.commit()
        conn.close()
        print("SQLite configurado con timeout")
    except Exception as e:
        print(f"SQLite no configurable: {e}")

configurar_sqlite()

client = TelegramClient("user_session", API_ID, API_HASH)

GROUP_ID = -1004340179079
CANTIDAD = 1000


async def main():
    await client.start()
    entity = await client.get_entity(GROUP_ID)
    print(f"Conectado: {entity.title}")
    print(f"Descargando multimedia (ultimos {CANTIDAD} mensajes)")
    print(f"Ya descargados: {len([f for f in os.listdir(DOWNLOAD_FOLDER) if os.path.isdir(os.path.join(DOWNLOAD_FOLDER, f))])}")
    print("=" * 50)

    total_ok = 0
    total_fail = 0
    ya_existentes = 0

    async for msg in client.iter_messages(entity, limit=CANTIDAD):
        if not msg.media:
            continue

        tipo = "otro"
        if isinstance(msg.media, MessageMediaPhoto):
            tipo = "foto"
        elif isinstance(msg.media, MessageMediaDocument):
            doc = msg.media.document
            if doc:
                if any(isinstance(a, DocumentAttributeVideo) for a in doc.attributes):
                    tipo = "video"
                else:
                    tipo = "doc"

        carpeta = obtener_subcarpeta(msg)
        nombre = obtener_nombre_archivo(msg)
        ruta = os.path.join(carpeta, nombre)

        if os.path.exists(ruta) and os.path.getsize(ruta) > 0:
            ya_existentes += 1
            continue

        try:
            os.makedirs(carpeta, exist_ok=True)

            # Intentar con reintentos por database locked
            for intento in range(5):
                try:
                    ruta = await client.download_media(msg, ruta)
                    break
                except Exception as e:
                    if "database is locked" in str(e) or "SQLITE" in str(e):
                        await asyncio.sleep(2)
                        continue
                    raise

            if ruta:
                total_ok += 1
                tam = os.path.getsize(ruta) / (1024 * 1024)
                print(f"OK [{tipo}] {os.path.basename(ruta)} ({tam:.1f}MB)")
            else:
                total_fail += 1
        except Exception as e:
            total_fail += 1
            print(f"FAIL [{tipo}] {os.path.basename(ruta)}: {str(e)[:60]}")
            if "FloodWait" in str(e):
                await asyncio.sleep(10)

        # Pequeña pausa para no saturar la db
        if total_ok % 5 == 0 and total_ok > 0:
            await asyncio.sleep(1)

    print("=" * 50)
    print(f"DESCARGA COMPLETADA: {total_ok} ok / {total_fail} fail / {ya_existentes} ya estaban")
    print(f"Archivos en: {DOWNLOAD_FOLDER}")


asyncio.run(main())
