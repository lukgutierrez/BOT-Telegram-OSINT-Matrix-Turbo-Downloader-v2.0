import os
import asyncio
import logging
from telethon import TelegramClient, events
from telethon.tl.types import (
    Channel, Chat, User,
    MessageMediaPhoto, MessageMediaDocument,
    ChannelParticipantsRecent,
)
from telethon.tl.functions.messages import GetForumTopicsRequest
from config import API_ID, API_HASH, DOWNLOAD_FOLDER
from link_parser import parsear_enlace, resolver_entidad, formatear_entidad
from downloader import (
    descargar_un_archivo, descargar_multiples,
    formatear_estado_descarga, obtener_tipo_media,
)
from osint import (
    info_canal, info_usuario, stats_canal,
    listar_participantes, buscar_usuarios, mensajes_recientes,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

bot = TelegramClient("user_session", API_ID, API_HASH)


async def resolver_objetivo(url_o_id):
    """Resuelve un enlace, ID numerico o @username a una entidad."""
    texto = str(url_o_id).strip()

    # Si es un numero (positivo o negativo), es un ID numerico
    if texto.lstrip("-").isdigit():
        entity_id = int(texto)
        try:
            return await bot.get_entity(entity_id)
        except Exception:
            pass

    # Si es un enlace o username
    try:
        parsed = parsear_enlace(texto)
        ent = await resolver_entidad(bot, parsed)
        if ent:
            return ent
    except Exception:
        pass

    # Ultimo intento: buscar como username directo
    if texto.startswith("@"):
        try:
            return await bot.get_entity(texto[1:])
        except Exception:
            pass

    return None


async def iniciar():
    print("=" * 50)
    print("  BOT DE TELEGRAM - DESCARGA Y OSINT")
    print("=" * 50)
    print(f"  Carpeta de descargas: {DOWNLOAD_FOLDER}")
    print("  Iniciando como USUARIO (no bot)...")
    print("=" * 50)

    await bot.start()
    print("  Bot iniciado correctamente!")
    print("=" * 50)
    await bot.run_until_disconnected()


@bot.on(events.NewMessage(pattern="/start"))
async def handler_start(event):
    await event.respond(
        "**Bot de Descarga y OSINT de Telegram**\n\n"
        "**Descarga:**\n"
        "  `/dl <enlace>` - Descargar un archivo\n"
        "  `/batch <enlace> [cantidad]` - Descargar varios archivos\n\n"
        "**OSINT:**\n"
        "  `/info <enlace>` - Info de canal/usuario\n"
        "  `/stats <enlace>` - Estadisticas\n"
        "  `/recent <enlace>` - Mensajes recientes\n\n"
        "**Grupos y Topics:**\n"
        "  `/mygroups` - Ver todos tus grupos con IDs\n"
        "  `/topics <group_id>` - Ver topics de un grupo foro\n"
        "  `/batch <group_id> [topic_id] [cant]` - Descargar de topic\n\n"
        "**Formatos:**\n"
        "  `t.me/canal/123` | `t.me/c/1234567/123`\n"
        "  `-1001234567890` (ID numerico)\n"
        "  `@username`"
    )


@bot.on(events.NewMessage(pattern="/help"))
async def handler_help(event):
    await event.respond(
        "**Ayuda del Bot**\n\n"
        "**DESCARGA:**\n"
        "  `/dl <enlace>` - Descarga un archivo\n"
        "  `/batch <enlace> [cant]` - Descarga varios archivos\n\n"
        "**GRUPOS SIN ENLACE:**\n"
        "  1. Envia `/mygroups` para ver todos tus grupos\n"
        "  2. Copia el ID del grupo (numero negativo)\n"
        "  3. Usa `/dl -1001234567890`\n\n"
        "**TOPICS (FOROS):**\n"
        "  1. Envia `/topics -1001234567890` para ver topics\n"
        "  2. Copia el ID del topic\n"
        "  3. Envia `/dl <group_id> <topic_id>`\n\n"
        "**OSINT:**\n"
        "  `/info <enlace>` | `/stats <enlace>`\n"
        "  `/recent <enlace> [cant]`\n"
        "  `/participants <enlace> [busqueda]`"
    )


@bot.on(events.NewMessage(pattern="/mygroups"))
async def handler_mygroups(event):
    status_msg = await event.respond("Buscando tus grupos y canales...")

    try:
        dialogs = []
        async for dialog in bot.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                entidad = dialog.entity
                chat_id = entidad.id
                if isinstance(entidad, Channel) and entidad.megagroup:
                    chat_id = int(f"-100{entidad.id}")
                elif isinstance(entidad, Channel):
                    chat_id = int(f"-100{entidad.id}")
                elif isinstance(entidad, Chat):
                    chat_id = int(f"-{entidad.id}")

                tipo = "Canal" if dialog.is_channel and not isinstance(entidad, Channel) or (isinstance(entidad, Channel) and not entidad.megagroup) else "Grupo"
                if isinstance(entidad, Channel) and entidad.megagroup:
                    tipo = "Supergupo"
                elif isinstance(entidad, Channel):
                    tipo = "Canal"
                else:
                    tipo = "Grupo"

                tiene_foro = getattr(entidad, "forum", False)
                forum_mark = " [FORO]" if tiene_foro else ""

                dialogs.append({
                    "nombre": dialog.title,
                    "id": chat_id,
                    "tipo": tipo,
                    "miembros": getattr(entidad, "participants_count", "?"),
                    "foro": tiene_foro,
                    "forum_mark": forum_mark,
                })

        if not dialogs:
            await status_msg.edit("No perteneces a ningun grupo o canal.")
            return

        lineas = [
            "=" * 40,
            "  TUS GRUPOS Y CANALES",
            "=" * 40,
            "",
        ]

        for d in sorted(dialogs, key=lambda x: x["nombre"]):
            lineas.append(f"{d['tipo']}: {d['nombre']}{d['forum_mark']}")
            lineas.append(f"  ID: `{d['id']}`")
            lineas.append(f"  Miembros: {d['miembros']}")
            lineas.append("")

        lineas.append("=" * 40)
        lineas.append("Copia el ID y usalo con /dl o /topics")

        resultado = "\n".join(lineas)

        if len(resultado) > 4000:
            await status_msg.edit(resultado[:4000])
        else:
            await status_msg.edit(resultado)

    except Exception as e:
        await status_msg.edit(f"Error: {str(e)[:200]}")
        logger.exception("Error en /mygroups")


@bot.on(events.NewMessage(pattern=r"/topics(?:\s|$)"))
async def handler_topics(event):
    texto = event.text.strip()
    partes = texto.split(maxsplit=1)
    if len(partes) < 2:
        await event.respond("Uso: `/topics <group_id>`\nEjemplo: `/topics -1001234567890`")
        return

    group_id_str = partes[1].strip()
    status_msg = await event.respond("Buscando topics del grupo...")

    try:
        entity = await resolver_objetivo(group_id_str)
        if not entity:
            await status_msg.edit("No pude encontrar el grupo. Verifica el ID.")
            return

        if not isinstance(entity, (Channel, Chat)):
            await status_msg.edit("La entidad no es un grupo o canal.")
            return

        tiene_foro = getattr(entity, "forum", False)
        if not tiene_foro:
            await status_msg.edit(f"**{entity.title}** no tiene topics (no es grupo foro).")
            return

        # Obtener topics via API raw
        try:
            result = await bot(GetForumTopicsRequest(
                peer=entity.id,
                offset_date=None,
                offset_id=0,
                offset_topic=0,
                limit=100,
            ))
        except Exception as e:
            await status_msg.edit(f"Error obteniendo topics: {str(e)[:100]}")
            return

        lineas = [
            f"**TOPICS DE: {entity.title}**",
            f"ID del grupo: `{entity.id}`",
            "",
        ]

        topics_encontrados = 0
        for topic in result.topics:
            if topic.id == 1:
                continue
            topics_encontrados += 1
            lineas.append(f"Topic: {topic.title}")
            lineas.append(f"  Topic ID: `{topic.id}`")
            lineas.append("")

        if topics_encontrados == 0:
            await status_msg.edit(f"**{entity.title}** tiene foro pero no encontre topics.")
            return

        lineas.append(f"Total: {topics_encontrados} topics")
        lineas.append("Usa `/dl <group_id> <topic_id>` para descargar de un topic")
        resultado = "\n".join(lineas)
        await status_msg.edit(resultado)

    except Exception as e:
        await status_msg.edit(f"Error: {str(e)[:200]}")
        logger.exception("Error en /topics")


@bot.on(events.NewMessage(pattern=r"/dl(?:\s|$)"))
async def handler_dl(event):
    texto = event.text.strip()
    partes = texto.split()
    if len(partes) < 2:
        await event.respond(
            "Uso:\n"
            "  `/dl <enlace>`\n"
            "  `/dl <group_id> <msg_id>`\n"
            "  `/dl <group_id> <topic_id> <msg_id>`"
        )
        return

    status_msg = await event.respond("Procesando...")

    try:
        entity = None
        msg_id = None
        topic_id = None

        if len(partes) == 2:
            # /dl <enlace> o /dl <group_id>
            arg1 = partes[1]
            if arg1.lstrip("-").isdigit() and len(arg1) > 5:
                # Es un ID numerico grande, probablemente un grupo
                entity = await resolver_objetivo(arg1)
                if entity:
                    await status_msg.edit(
                        f"**{getattr(entity, 'title', 'Entidad')}** encontrado.\n"
                        "Ahora necesito el ID del mensaje.\n"
                        "Usa `/recent <group_id>` para ver mensajes."
                    )
                    return
            else:
                # Es un enlace
                parsed = parsear_enlace(arg1)
                entity = await resolver_entidad(bot, parsed)
                msg_id = parsed.msg_id

        elif len(partes) == 3:
            # /dl <group_id> <msg_id>
            if partes[1].lstrip("-").isdigit() and len(partes[1]) > 5:
                entity = await resolver_objetivo(partes[1])
                msg_id = int(partes[2]) if partes[2].lstrip("-").isdigit() else None
            else:
                parsed = parsear_enlace(partes[1])
                entity = await resolver_entidad(bot, parsed)
                msg_id = int(partes[2]) if partes[2].isdigit() else None

        elif len(partes) == 4:
            # /dl <group_id> <topic_id> <msg_id>
            entity = await resolver_objetivo(partes[1])
            topic_id = int(partes[2]) if partes[2].lstrip("-").isdigit() else None
            msg_id = int(partes[3]) if partes[3].lstrip("-").isdigit() else None

        if not entity:
            await status_msg.edit("No pude encontrar la entidad. Verifica el enlace o ID.")
            return

        if not msg_id:
            await status_msg.edit("Necesitas especificar un ID de mensaje.\nUsa `/recent` para ver los mensajes.")
            return

        messages = await bot.get_messages(entity, ids=msg_id)
        if not messages:
            await status_msg.edit("No se encontro ese mensaje.")
            return
        messages = [messages] if not isinstance(messages, list) else messages

        if topic_id:
            messages = [m for m in messages if m.reply_to and m.reply_to.reply_to_msg_id == topic_id or m.id == topic_id]

        media_msgs = [m for m in messages if m.media]
        if not media_msgs:
            await status_msg.edit("Ese mensaje no contiene archivos multimedia.")
            return

        await status_msg.edit(f"Descargando {len(media_msgs)} archivo(s)...")
        exitosos, fallidos = await descargar_multiples(bot, media_msgs, status_msg)
        resultado = formatear_estado_descarga(exitosos, fallidos)
        await status_msg.edit(resultado)

        for ruta in exitosos:
            try:
                tam = os.path.getsize(ruta)
                if tam > 50 * 1024 * 1024:
                    await event.respond(f"Alerta: {os.path.basename(ruta)} supera 50MB.")
                    continue
                await bot.send_file(event.chat_id, ruta)
            except Exception as e:
                await event.respond(f"Error enviando {os.path.basename(ruta)}: {str(e)[:80]}")

    except ValueError as e:
        await status_msg.edit(f"Error: {str(e)}")
    except Exception as e:
        await status_msg.edit(f"Error inesperado: {str(e)[:200]}")
        logger.exception("Error en /dl")


@bot.on(events.NewMessage(pattern=r"/batch(?:\s|$)"))
async def handler_batch(event):
    texto = event.text.strip()
    partes = texto.split()

    if len(partes) < 2:
        await event.respond(
            "Uso:\n"
            "  `/batch <enlace> [cantidad]`\n"
            "  `/batch <group_id> [topic_id] [cantidad]`"
        )
        return

    entity = None
    topic_id = None
    cantidad = 20

    if len(partes) == 2:
        entity = await resolver_objetivo(partes[1])
    elif len(partes) == 3:
        if partes[2].isdigit():
            entity = await resolver_objetivo(partes[1])
            cantidad = min(int(partes[2]), 100)
        else:
            parsed = parsear_enlace(partes[1])
            entity = await resolver_entidad(bot, parsed)
            cantidad = 20
    elif len(partes) == 4:
        entity = await resolver_objetivo(partes[1])
        topic_id = int(partes[2]) if partes[2].lstrip("-").isdigit() else None
        cantidad = min(int(partes[3]), 100) if partes[3].isdigit() else 20

    if not entity:
        await event.respond("No pude encontrar la entidad.")
        return

    status_msg = await event.respond(f"Buscando ultimos {cantidad} mensajes...")

    try:
        exitosos = []
        fallidos = []
        count = 0

        async for message in bot.iter_messages(entity, limit=cantidad):
            if message.media:
                if topic_id:
                    reply = message.reply_to
                    rt = (getattr(reply, "reply_to_top_id", None) or getattr(reply, "reply_to_msg_id", None)) if reply else None
                    if rt != topic_id and message.id != topic_id:
                        continue
                count += 1
                await status_msg.edit(f"Descargando... ({count} archivos encontrados)")
                try:
                    ruta = await descargar_un_archivo(bot, message)
                    if ruta:
                        exitosos.append(ruta)
                except Exception as e:
                    fallidos.append((message, str(e)))

        resultado = formatear_estado_descarga(exitosos, fallidos)
        await status_msg.edit(resultado)

        for ruta in exitosos:
            try:
                tam = os.path.getsize(ruta)
                if tam > 50 * 1024 * 1024:
                    continue
                await bot.send_file(event.chat_id, ruta)
            except Exception:
                pass

    except ValueError as e:
        await status_msg.edit(f"Error: {str(e)}")
    except Exception as e:
        await status_msg.edit(f"Error: {str(e)[:200]}")
        logger.exception("Error en /batch")


@bot.on(events.NewMessage(pattern=r"/info(?:\s|$)"))
async def handler_info(event):
    texto = event.text.strip()
    partes = texto.split(maxsplit=1)
    if len(partes) < 2:
        await event.respond("Uso: `/info <enlace>`")
        return

    url = partes[1].strip()
    status_msg = await event.respond("Obteniendo informacion...")

    try:
        entity = await resolver_objetivo(url)
        if not entity:
            await status_msg.edit("No pude encontrar la entidad.")
            return

        if isinstance(entity, User):
            resultado = await info_usuario(bot, entity)
        else:
            resultado = await info_canal(bot, entity)

        await status_msg.edit(resultado)

    except Exception as e:
        await status_msg.edit(f"Error: {str(e)[:200]}")
        logger.exception("Error en /info")


@bot.on(events.NewMessage(pattern=r"/stats(?:\s|$)"))
async def handler_stats(event):
    texto = event.text.strip()
    partes = texto.split(maxsplit=1)
    if len(partes) < 2:
        await event.respond("Uso: `/stats <enlace>`")
        return

    url = partes[1].strip()
    status_msg = await event.respond("Analizando canal (puede tardar)...")

    try:
        entity = await resolver_objetivo(url)
        if not entity:
            await status_msg.edit("No pude encontrar la entidad.")
            return

        resultado = await stats_canal(bot, entity)
        await status_msg.edit(resultado)

    except Exception as e:
        await status_msg.edit(f"Error: {str(e)[:200]}")
        logger.exception("Error en /stats")


@bot.on(events.NewMessage(pattern=r"/participants(?:\s|$)"))
async def handler_participants(event):
    texto = event.text.strip()
    partes = texto.split(maxsplit=2)

    if len(partes) < 2:
        await event.respond("Uso: `/participants <enlace> [busqueda]`")
        return

    url = partes[1].strip()
    query = partes[2].strip() if len(partes) > 2 else None
    status_msg = await event.respond("Obteniendo participantes...")

    try:
        entity = await resolver_objetivo(url)
        if not entity:
            await status_msg.edit("No pude encontrar la entidad.")
            return

        if query:
            resultado = await buscar_usuarios(bot, entity, query)
        else:
            resultado = await listar_participantes(bot, entity)

        await status_msg.edit(resultado)

    except Exception as e:
        await status_msg.edit(f"Error: {str(e)[:200]}")
        logger.exception("Error en /participants")


@bot.on(events.NewMessage(pattern=r"/alltopics(?:\s|$)"))
async def handler_alltopics(event):
    texto = event.text.strip()
    partes = texto.split()

    if len(partes) < 2:
        await event.respond("Uso: `/alltopics <group_id> [cantidad_por_topic]`")
        return

    group_id_str = partes[1].strip()
    cantidad = int(partes[2]) if len(partes) > 2 and partes[2].isdigit() else 50
    cantidad = min(cantidad, 200)

    status_msg = await event.respond("Buscando topics...")

    try:
        entity = await resolver_objetivo(group_id_str)
        if not entity:
            await status_msg.edit("No pude encontrar el grupo.")
            return

        if not getattr(entity, "forum", False):
            # No es foro, descarga directo del grupo
            await status_msg.edit(f"**{getattr(entity, 'title', 'Grupo')}** no es foro. Descargando directamente...")
            exitosos = []
            fallidos = []
            count = 0
            async for message in bot.iter_messages(entity, limit=cantidad):
                if message.media:
                    count += 1
                    try:
                        ruta = await descargar_un_archivo(bot, message)
                        if ruta:
                            exitosos.append(ruta)
                    except Exception as e:
                        fallidos.append((message, str(e)))
            resultado = formatear_estado_descarga(exitosos, fallidos)
            await status_msg.edit(resultado)
            for ruta in exitosos:
                try:
                    if os.path.getsize(ruta) <= 50 * 1024 * 1024:
                        await bot.send_file(event.chat_id, ruta)
                except Exception:
                    pass
            return

        # Es un foro. Obtener topics y descargar de cada uno
        from telethon.tl.functions.messages import GetForumTopicsRequest
        result = await bot(GetForumTopicsRequest(
            peer=entity.id, offset_date=None, offset_id=0, offset_topic=0, limit=100
        ))

        topics = [t for t in result.topics if t.id != 1]
        total_archivos = 0
        total_exitosos = 0
        total_fallidos = 0

        await status_msg.edit(f"Descargando de {len(topics)} topics del foro...")

        for topic in topics:
            topic_id = topic.id
            count_topic = 0
            async for message in bot.iter_messages(entity, limit=cantidad):
                if not message.media:
                    continue
                reply = message.reply_to
                rt = (getattr(reply, "reply_to_top_id", None) or getattr(reply, "reply_to_msg_id", None)) if reply else None
                if rt != topic_id:
                    continue
                count_topic += 1
                total_archivos += 1
                try:
                    ruta = await descargar_un_archivo(bot, message, topic_nombre=topic.title)
                    if ruta:
                        total_exitosos += 1
                        await bot.send_file(event.chat_id, ruta)
                except Exception as e:
                    total_fallidos += 1

            await status_msg.edit(
                f"Topic **{topic.title}**: {count_topic} archivos. "
                f"Total: {total_exitosos} ok / {total_fallidos} fail"
            )

        await status_msg.edit(
            f"**Descarga completada de todos los topics:**\n"
            f"✅ Exitosos: {total_exitosos}\n"
            f"❌ Fallidos: {total_fallidos}\n"
            f"Total archivos: {total_archivos}"
        )

    except Exception as e:
        await status_msg.edit(f"Error: {str(e)[:200]}")
        logger.exception("Error en /alltopics")


@bot.on(events.NewMessage(pattern=r"/recent(?:\s|$)"))
async def handler_recent(event):
    texto = event.text.strip()
    partes = texto.split(maxsplit=2)

    if len(partes) < 2:
        await event.respond("Uso: `/recent <enlace> [cantidad]`")
        return

    url = partes[1].strip()
    cantidad = int(partes[2]) if len(partes) > 2 and partes[2].isdigit() else 10
    cantidad = min(cantidad, 50)
    status_msg = await event.respond("Obteniendo mensajes recientes...")

    try:
        entity = await resolver_objetivo(url)
        if not entity:
            await status_msg.edit("No pude encontrar la entidad.")
            return

        resultado = await mensajes_recientes(bot, entity, limit=cantidad)
        await status_msg.edit(resultado)

    except Exception as e:
        await status_msg.edit(f"Error: {str(e)[:200]}")
        logger.exception("Error en /recent")


@bot.on(events.NewMessage(func=lambda e: e.is_private and not e.text.startswith("/")))
async def handler_enlace_directo(event):
    texto = event.text.strip()
    if "t.me/" not in texto and not texto.startswith("@") and not (texto.lstrip("-").isdigit() and len(texto) > 5):
        return

    status_msg = await event.respond("Detecte un enlace, procesando...")

    try:
        parsed = None
        try:
            parsed = parsear_enlace(texto)
        except Exception:
            pass

        # Si el enlace contiene un msg_id especifico, descargamos el archivo de ese mensaje
        if parsed and parsed.msg_id:
            entity = await resolver_entidad(bot, parsed)
            if entity:
                message = await bot.get_messages(entity, ids=parsed.msg_id)
                if message and message.media:
                    await status_msg.edit("Descargando archivo multimedia...")
                    exitosos, fallidos = await descargar_multiples(bot, [message], status_msg)
                    res = formatear_estado_descarga(exitosos, fallidos)
                    await status_msg.edit(res)
                    for ruta in exitosos:
                        try:
                            if os.path.getsize(ruta) <= 50 * 1024 * 1024:
                                await bot.send_file(event.chat_id, ruta)
                        except Exception:
                            pass
                    return

        entity = await resolver_objetivo(texto)
        if not entity:
            await status_msg.edit("No pude encontrar la entidad.")
            return

        if isinstance(entity, User):
            info = await info_usuario(bot, entity)
        else:
            info = await info_canal(bot, entity)
        await status_msg.edit(info)

    except Exception as e:
        await status_msg.edit(f"Error: {str(e)[:200]}")
        logger.exception("Error procesando enlace directo")


def main():
    asyncio.run(iniciar())


if __name__ == "__main__":
    main()
