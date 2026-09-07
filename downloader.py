import os
import asyncio
from datetime import datetime
from telethon.tl.types import (
    MessageMediaPhoto, MessageMediaDocument,
    DocumentAttributeVideo, DocumentAttributeAudio,
    DocumentAttributeAnimated, DocumentAttributeSticker,
    DocumentAttributeFilename,
)
from config import DOWNLOAD_FOLDER, MAX_CONCURRENT_DOWNLOADS, MAX_FLOOD_WAIT


TIPOS_MEDIA = {
    "video": "videos",
    "photo": "fotos",
    "document": "documentos",
    "audio": "audio",
    "sticker": "stickers",
    "voice": "voice",
    "video_note": "video_notes",
    "animation": "animaciones",
    "gif": "animaciones",
}

semaforo = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

def establecer_concurrencia(concurrencia: int):
    global semaforo
    concurrencia_val = max(1, min(50, concurrencia))
    semaforo = asyncio.Semaphore(concurrencia_val)


def obtener_tipo_media(message) -> str:
    if not message.media:
        return "texto"
    if isinstance(message.media, MessageMediaPhoto):
        return "photo"
    if isinstance(message.media, MessageMediaDocument):
        doc = message.media.document
        if doc is None:
            return "documento"
        for attr in doc.attributes:
            if isinstance(attr, DocumentAttributeSticker):
                return "sticker"
            if isinstance(attr, DocumentAttributeVideo):
                if getattr(attr, "round_message", False):
                    return "video_note"
                if getattr(attr, "supports_streaming", False):
                    return "video"
                return "video"
            if isinstance(attr, DocumentAttributeAudio):
                if getattr(attr, "voice", False):
                    return "voice"
                return "audio"
            if isinstance(attr, DocumentAttributeAnimated):
                return "animation"
        return "document"
    return "documento"


import time

def sanitizar_nombre(nombre: str) -> str:
    if not nombre:
        return ""
    # Reemplazar caracteres invalidos en Windows/Linux
    caracteres_invalidos = r'[\/:*?"<>|]'
    import re
    nombre_limpio = re.sub(caracteres_invalidos, "_", nombre).strip()
    return nombre_limpio or "archivo_sin_nombre"


def obtener_nombre_archivo(message) -> str:
    if message.file and message.file.name:
        return sanitizar_nombre(message.file.name)
    tipo = obtener_tipo_media(message)
    if getattr(message, "date", None):
        ts = message.date.strftime("%Y%m%d_%H%M%S")
    else:
        ts = "archivo"
    ext_map = {
        "video": ".mp4", "photo": ".jpg", "document": ".bin",
        "audio": ".mp3", "sticker": ".webp", "voice": ".ogg",
        "video_note": ".mp4", "animation": ".gif",
    }
    ext = ext_map.get(tipo, ".bin")
    if message.file and getattr(message.file, "ext", None):
        ext = message.file.ext
    return f"{tipo}_{ts}_{message.id}{ext}"


def obtener_subcarpeta(message, topic_nombre: str = None) -> str:
    if message.chat:
        chat_nombre = getattr(message.chat, "title", None) or str(getattr(message, "chat_id", "desconocido"))
        chat_nombre = "".join(c if c.isalnum() or c in " _-" else "_" for c in chat_nombre).strip()
    else:
        chat_nombre = "desconocido"
    tipo = obtener_tipo_media(message)
    sub = TIPOS_MEDIA.get(tipo, "otros")
    if topic_nombre:
        topic_clean = "".join(c if c.isalnum() or c in " _-" else "_" for c in topic_nombre).strip()
        return os.path.join(DOWNLOAD_FOLDER, chat_nombre or "desconocido", topic_clean or "general", sub)
    return os.path.join(DOWNLOAD_FOLDER, chat_nombre or "desconocido", sub)


_ULTIMA_ACTUALIZACION_PROGRESO = {}

async def progress_callback(current, total, message, status_msg):
    if not total or total <= 0 or not status_msg:
        return

    msg_key = id(status_msg)
    ahora = time.time()

    # Throttling: solo actualizar cada 2 segundos o cuando termina (100%)
    ultimo_tiempo = _ULTIMA_ACTUALIZACION_PROGRESO.get(msg_key, 0)
    pct = current * 100 / total
    if pct < 100 and (ahora - ultimo_tiempo) < 2.0:
        return

    _ULTIMA_ACTUALIZACION_PROGRESO[msg_key] = ahora

    bar_len = 20
    filled = int(bar_len * pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)
    mb_current = current / (1024 * 1024)
    mb_total = total / (1024 * 1024)
    texto = (
        f"⬇️ Descargando...\n"
        f"[{bar}] {pct:.1f}%\n"
        f"{mb_current:.1f}MB / {mb_total:.1f}MB"
    )
    try:
        await status_msg.edit(texto)
    except Exception:
        pass


async def descargar_un_archivo(client, message, status_msg=None, topic_nombre: str = None, callback_st=None):
    async with semaforo:
        carpeta = obtener_subcarpeta(message, topic_nombre=topic_nombre)
        os.makedirs(carpeta, exist_ok=True)
        nombre = obtener_nombre_archivo(message)
        ruta = os.path.join(carpeta, nombre)

        # Check 1: Si el archivo ya existe y tiene contenido, omitir descarga redundante
        if os.path.exists(ruta) and os.path.getsize(ruta) > 0:
            if callback_st:
                try:
                    callback_st(os.path.basename(ruta), os.path.getsize(ruta), os.path.getsize(ruta), True)
                except Exception:
                    pass
            return ruta

        # Check 2: Deduplicación Inteligente en Carpeta Destino (por ID de Mensaje o Tamaño Exacto en Bytes)
        msg_file_size = getattr(message.file, "size", 0) if message.file else 0
        if os.path.exists(carpeta):
            try:
                for f_item in os.listdir(carpeta):
                    full_item = os.path.join(carpeta, f_item)
                    if os.path.isfile(full_item):
                        sz = os.path.getsize(full_item)
                        if sz > 0:
                            # Coincidencia por ID de mensaje
                            if f"_{message.id}." in f_item or f"_{message.id}_" in f_item:
                                if callback_st:
                                    try:
                                        callback_st(f_item, sz, sz, True)
                                    except Exception:
                                        pass
                                return full_item
                            # Coincidencia por tamaño exacto en bytes en Telegram
                            if msg_file_size > 0 and sz == msg_file_size:
                                if callback_st:
                                    try:
                                        callback_st(f_item, sz, sz, True)
                                    except Exception:
                                        pass
                                return full_item
            except Exception:
                pass

        def prog_wrapper(current, total):
            if callback_st:
                try:
                    callback_st(nombre, current, total, False)
                except Exception:
                    pass
            if status_msg:
                asyncio.create_task(progress_callback(current, total, message, status_msg))

        try:
            await client.download_media(message, ruta, progress_callback=prog_wrapper)
            
            # Registrar hash binario para deduplicación futura
            try:
                from hash_dedup import registrar_hash
                registrar_hash(ruta)
            except Exception:
                pass

            return ruta
        except Exception as e:
            error_str = str(e)
            if "FloodWait" in error_str:
                import re
                match = re.search(r"A wait of (\d+) seconds", error_str)
                if match:
                    wait = min(int(match.group(1)), MAX_FLOOD_WAIT)
                    await asyncio.sleep(wait)
                    return await descargar_un_archivo(client, message, status_msg, topic_nombre=topic_nombre, callback_st=callback_st)
            raise e


async def descargar_multiples(client, messages, status_msg=None):
    tareas = []
    resultados = []
    for msg in messages:
        if msg.media:
            tareas.append(descargar_un_archivo(client, msg, status_msg))

    if not tareas:
        return []

    resultados = await asyncio.gather(*tareas, return_exceptions=True)
    exitosos = []
    fallidos = []
    for i, res in enumerate(resultados):
        if isinstance(res, Exception):
            fallidos.append((messages[i], str(res)))
        elif res:
            exitosos.append(res)

    return exitosos, fallidos


def formatear_estado_descarga(exitosos, fallidos) -> str:
    lineas = [f"**Descarga completada:**"]
    lineas.append(f"✅ Exitosos: {len(exitosos)}")
    if fallidos:
        lineas.append(f"❌ Fallidos: {len(fallidos)}")
        for msg, err in fallidos[:5]:
            lineas.append(f"  - Msg {msg.id}: {err[:50]}")
    if exitosos:
        lineas.append(f"\n**Archivos guardados en:**")
        for ruta in exitosos[:10]:
            nombre = os.path.basename(ruta)
            tam = os.path.getsize(ruta) / (1024 * 1024)
            lineas.append(f"  📁 {nombre} ({tam:.1f}MB)")
        if len(exitosos) > 10:
            lineas.append(f"  ... y {len(exitosos) - 10} mas")
    return "\n".join(lineas)
