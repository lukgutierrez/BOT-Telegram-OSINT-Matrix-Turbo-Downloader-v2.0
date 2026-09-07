import asyncio
import os
import sqlite3
import re
import sys
from telethon import TelegramClient
from telethon.tl.functions.messages import GetForumTopicsRequest
from config import API_ID, API_HASH, DOWNLOAD_FOLDER
from downloader import (
    obtener_subcarpeta, obtener_nombre_archivo,
    descargar_un_archivo, sanitizar_nombre
)

# Configurar timeout largo en SQLite para la sesion
def configurar_sqlite():
    try:
        conn = sqlite3.connect("user_session.session", timeout=30)
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=OFF")
        conn.commit()
        conn.close()
    except Exception:
        pass

configurar_sqlite()

client = TelegramClient("user_session", API_ID, API_HASH)

# ============================================================
# CONFIGURACION DE DESCARGA
# ============================================================
GROUP_ID = -1004340179079  # Realeza Salta 🇦🇷

# ¿Invertir el orden de los topics? 
# True  = Empieza por los ultimos topics (de abajo hacia arriba)
# False = Empieza por los primeros topics (de arriba hacia abajo)
INVERTIR_ORDEN_TOPICS = True

# ¿Invertir el orden de los mensajes dentro de cada topic?
# False = De los mas recientes a los mas antiguos (de abajo hacia arriba en el chat)
# True  = De los mas antiguos a los mas recientes
REVERSAR_MENSAJES = False

# Cantidad maxima de mensajes a revisar por topic (None = TODO sin limite)
MESSAGES_PER_TOPIC = None
# ============================================================


async def main():
    await client.start()
    
    try:
        entity = await client.get_entity(GROUP_ID)
    except Exception as e:
        print(f"❌ Error resolviendo el grupo ID {GROUP_ID}: {e}")
        return

    print("=" * 60)
    print(f"  DESCARGADOR DE FORO POR TOPICS")
    print("=" * 60)
    print(f"  Grupo: {entity.title} (ID: {entity.id})")
    print(f"  Carpeta destino: {DOWNLOAD_FOLDER}")
    orden_str = "De ABAJO hacia ARRIBA (Últimos topics primero)" if INVERTIR_ORDEN_TOPICS else "De ARRIBA hacia ABAJO (Primeros topics primero)"
    print(f"  Orden de Topics: {orden_str}")
    print("=" * 60)

    # 1. Obtener todos los topics del foro
    try:
        topics_result = await client(GetForumTopicsRequest(
            peer=entity.id,
            offset_date=None,
            offset_id=0,
            offset_topic=0,
            limit=500
        ))
    except Exception as e:
        print(f"❌ Error obteniendo los topics del grupo: {e}")
        return

    topics_lista = list(topics_result.topics)
    
    # Invertir orden si esta configurado
    if INVERTIR_ORDEN_TOPICS:
        topics_lista.reverse()

    print(f"Se encontraron {len(topics_lista)} topics en el foro.")
    print("-" * 60)

    total_descargados = 0
    total_omitidos = 0
    total_fallidos = 0

    # 2. Descargar contenido topic por topic
    for idx, t in enumerate(topics_lista, start=1):
        topic_id = t.id
        topic_title = t.title
        print(f"\n📂 [{idx}/{len(topics_lista)}] Procesando Topic ID {topic_id}: '{topic_title}'")

        archivos_ok = 0
        archivos_existian = 0
        archivos_fail = 0

        async def procesar_msg(message):
            nonlocal archivos_ok, archivos_existian, archivos_fail, total_descargados, total_omitidos, total_fallidos
            if not message.media:
                return
            try:
                carpeta = obtener_subcarpeta(message, topic_nombre=topic_title)
                nombre = obtener_nombre_archivo(message)
                ruta = os.path.join(carpeta, nombre)

                if os.path.exists(ruta) and os.path.getsize(ruta) > 0:
                    archivos_existian += 1
                    total_omitidos += 1
                    return

                ruta_descargada = await descargar_un_archivo(client, message, topic_nombre=topic_title)
                if ruta_descargada:
                    archivos_ok += 1
                    total_descargados += 1
                    tam_mb = os.path.getsize(ruta_descargada) / (1024 * 1024)
                    print(f"  ✅ [{topic_title[:20]}] {os.path.basename(ruta_descargada)} ({tam_mb:.1f} MB)")
            except Exception as e:
                archivos_fail += 1
                total_fallidos += 1
                print(f"  ❌ Error msg {message.id}: {str(e)[:50]}")
                if "FloodWait" in str(e):
                    await asyncio.sleep(5)

        try:
            try:
                async for message in client.iter_messages(entity, reply_to=topic_id, reverse=REVERSAR_MENSAJES):
                    await procesar_msg(message)
            except Exception:
                async for message in client.iter_messages(entity, limit=MESSAGES_PER_TOPIC, reverse=REVERSAR_MENSAJES):
                    reply = message.reply_to
                    top_id = (getattr(reply, "reply_to_top_id", None) or getattr(reply, "reply_to_msg_id", None)) if reply else None
                    if top_id == topic_id or message.id == topic_id:
                        await procesar_msg(message)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"  ⚠️ Error en topic '{topic_title}': {e}")

        print(f"  📊 Resumen '{topic_title}': {archivos_ok} nuevos | {archivos_existian} omitidos (ya existían) | {archivos_fail} fallidos")

    print("\n" + "=" * 60)
    print("  🎉 DESCARGA DE FORO COMPLETADA")
    print(f"  ✅ Nuevos descargados: {total_descargados}")
    print(f"  📁 Ya existían (omitidos): {total_omitidos}")
    print(f"  ❌ Fallidos: {total_fallidos}")
    print(f"  Archivos guardados en: {DOWNLOAD_FOLDER}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n" + "=" * 60)
        print(" ⏹️ DESCARGA PAUSADA POR EL USUARIO (Ctrl + C)")
        print(" Todos los archivos descargados hasta ahora están guardados.")
        print(" Cuando vuelvas a ejecutar 'python descargar_foro.py',")
        print(" continuará automáticamente desde donde quedó.")
        print("=" * 60)
