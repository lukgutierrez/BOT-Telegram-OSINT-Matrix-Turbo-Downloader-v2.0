import asyncio
from datetime import datetime, timedelta
from collections import Counter
from telethon.tl.types import (
    Channel, Chat, User,
    MessageMediaPhoto, MessageMediaDocument,
    DocumentAttributeVideo, DocumentAttributeAudio,
)
from config import OSINT_MAX_MESSAGES_ANALYZE, OSINT_MAX_PARTICIPANTS


async def info_canal(client, entity) -> str:
    if not isinstance(entity, (Channel, Chat)):
        return "La entidad no es un canal o grupo."

    lineas = [
        "═══════════════════════════",
        f"  **INFORMACION DEL CANAL**",
        "═══════════════════════════",
        f"",
        f"**Nombre:** {entity.title}",
        f"**ID:** `{entity.id}`",
    ]

    if isinstance(entity, Channel):
        lineas.append(f"**Tipo:** {'Supergupo (megagroup)' if entity.megagroup else 'Canal broadcast'}")
        if entity.username:
            lineas.append(f"**Username:** @{entity.username}")
            lineas.append(f"**Link publico:** https://t.me/{entity.username}")
        else:
            lineas.append(f"**Username:** Privado (sin username)")
        if entity.about:
            lineas.append(f"**Descripcion:** {entity.about}")
        if hasattr(entity, "participants_count") and entity.participants_count:
            lineas.append(f"**Miembros:** {entity.participants_count}")
        lineas.append(f"**Verificado:** {'Si' if entity.verified else 'No'}")
        lineas.append(f"**Restringido:** {'Si' if entity.restricted else 'No'}")
        lineas.append(f"**Scam:** {'Si' if entity.scam else 'No'}")
        lineas.append(f"**Fake:** {'Si' if entity.fake else 'No'}")
        if entity.date:
            lineas.append(f"**Fecha creacion:** {entity.date.strftime('%d/%m/%Y %H:%M')}")
        if entity.megagroup:
            lineas.append(f"**Enlace invite:** https://t.me/{entity.username}" if entity.username else "")
        lineas.append(f"**Puede ser enlazado:** {'Si' if not entity.noforward else 'No'}")

    elif isinstance(entity, Chat):
        if hasattr(entity, "participants_count") and entity.participants_count:
            lineas.append(f"**Miembros:** {entity.participants_count}")
        if entity.date:
            lineas.append(f"**Fecha creacion:** {entity.date.strftime('%d/%m/%Y %H:%M')}")

    return "\n".join(l for l in lineas if l)


async def info_usuario(client, entity) -> str:
    if not isinstance(entity, User):
        return "La entidad no es un usuario."

    nombre = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
    username_display = f"@{entity.username}" if entity.username else "No tiene"

    lineas = [
        "═══════════════════════════",
        f"  **INFORMACION DEL USUARIO**",
        "═══════════════════════════",
        f"",
        f"**Nombre:** {nombre}",
        f"**Username:** {username_display}",
        f"**ID:** `{entity.id}`",
        f"**Bot:** {'Si' if entity.bot else 'No'}",
        f"**Premium:** {'Si' if entity.premium else 'No'}",
        f"**Verificado:** {'Si' if entity.verified else 'No'}",
        f"**Scam:** {'Si' if entity.scam else 'No'}",
        f"**Fake:** {'Si' if entity.fake else 'No'}",
        f"**Restringido:** {'Si' if entity.restricted else 'No'}",
        f"**Tiene foto de perfil:** {'Si' if entity.photo else 'No'}",
    ]
    if entity.lang_code:
        lineas.append(f"**Idioma:** {entity.lang_code}")

    try:
        common = await client.get_common_chats(entity)
        if common:
            lineas.append(f"**Chats en comun:** {len(common)}")
            for c in common[:5]:
                tipo = "Canal" if isinstance(c, Channel) and not c.megagroup else "Grupo"
                lineas.append(f"  - {tipo}: {c.title}")
    except Exception:
        pass

    return "\n".join(l for l in lineas if l)


async def stats_canal(client, channel) -> str:
    if not isinstance(channel, Channel):
        return "La entidad no es un canal."

    nombre = channel.title
    lineas = [
        "═══════════════════════════",
        f"  **ESTADISTICAS: {nombre}**",
        "═══════════════════════════",
        f"",
    ]

    counter_tipos = Counter()
    counter_usuarios = Counter()
    counter_dias = Counter()
    counter_horas = Counter()
    total_msg = 0
    total_con_media = 0
    tam_total = 0

    status_msg = None

    try:
        async for message in client.iter_messages(channel, limit=OSINT_MAX_MESSAGES_ANALYZE):
            total_msg += 1

            if message.media:
                total_con_media += 1
                if isinstance(message.media, MessageMediaPhoto):
                    counter_tipos["Fotos"] += 1
                elif isinstance(message.media, MessageMediaDocument):
                    doc = message.media.document
                    if doc:
                        has_video = any(
                            isinstance(a, DocumentAttributeVideo) for a in doc.attributes
                        )
                        has_audio = any(
                            isinstance(a, DocumentAttributeAudio) for a in doc.attributes
                        )
                        if has_video:
                            counter_tipos["Videos"] += 1
                        elif has_audio:
                            counter_tipos["Audio"] += 1
                        else:
                            counter_tipos["Documentos"] += 1

            if message.sender_id:
                try:
                    user = await client.get_entity(message.sender_id)
                    nombre_u = user.first_name or f"User_{user.id}"
                    counter_usuarios[nombre_u] += 1
                except Exception:
                    counter_usuarios[f"ID_{message.sender_id}"] += 1

            if message.date:
                counter_dias[message.date.strftime("%A")] += 1
                counter_horas[message.date.hour] += 1

            if total_msg % 20 == 0:
                pass

    except Exception as e:
        lineas.append(f"Error al analizar: {str(e)[:100]}")
        return "\n".join(lineas)

    lineas.append(f"**Mensajes analizados:** {total_msg}")
    lineas.append(f"**Mensajes con media:** {total_con_media}")
    lineas.append(f"**Ratio media:** {(total_con_media/total_msg*100):.1f}%" if total_msg > 0 else "")

    if counter_tipos:
        lineas.append(f"\n**Tipos de media:**")
        for tipo, cant in counter_tipos.most_common():
            lineas.append(f"  - {tipo}: {cant}")

    if counter_usuarios:
        lineas.append(f"\n**Top usuarios mas activos:**")
        for user, cant in counter_usuarios.most_common(10):
            lineas.append(f"  - {user}: {cant} mensajes")

    if counter_horas:
        hora_pico = counter_horas.most_common(1)[0]
        lineas.append(f"\n**Hora pico:** {hora_pico[0]}:00 ({hora_pico[1]} mensajes)")

    if counter_dias:
        dia_pico = counter_dias.most_common(1)[0]
        lineas.append(f"**Dia mas activo:** {dia_pico[0]} ({dia_pico[1]} mensajes)")

    return "\n".join(l for l in lineas if l)


async def listar_participantes(client, channel, limit=None) -> str:
    if not isinstance(channel, (Channel, Chat)):
        return "La entidad no es un canal o grupo."

    limit = limit or OSINT_MAX_PARTICIPANTS
    lineas = [
        "═══════════════════════════",
        f"  **PARTICIPANTES: {channel.title}**",
        "═══════════════════════════",
        f"",
    ]

    admins = []
    bots = []
    usuarios = []
    total = 0

    try:
        async for user in client.iter_participants(channel, limit=limit):
            total += 1
            nombre = f"{user.first_name or ''} {user.last_name or ''}".strip()
            uname = f"@{user.username}" if user.username else "sin_username"

            info = f"{nombre} ({uname}) [ID: {user.id}]"

            if user.admin:
                admins.append(info)
            elif user.bot:
                bots.append(info)
            else:
                usuarios.append(info)

    except Exception as e:
        lineas.append(f"Error: {str(e)[:100]}")
        return "\n".join(lineas)

    lineas.append(f"**Total obtenidos:** {total}")

    if admins:
        lineas.append(f"\n**Administradores ({len(admins)}):**")
        for a in admins[:20]:
            lineas.append(f"  👑 {a}")

    if bots:
        lineas.append(f"\n**Bots ({len(bots)}):**")
        for b in bots[:10]:
            lineas.append(f"  🤖 {b}")

    if usuarios:
        lineas.append(f"\n**Usuarios ({len(usuarios)}):**")
        for u in usuarios[:30]:
            lineas.append(f"  👤 {u}")
        if len(usuarios) > 30:
            lineas.append(f"  ... y {len(usuarios) - 30} mas")

    return "\n".join(l for l in lineas if l)


async def buscar_usuarios(client, channel, query: str, limit=50) -> str:
    lineas = [
        f"**Buscando '{query}' en {channel.title}...**",
        f"",
    ]

    encontrados = 0
    async for user in client.iter_participants(channel, search=query, limit=limit):
        encontrados += 1
        nombre = f"{user.first_name or ''} {user.last_name or ''}".strip()
        uname = f"@{user.username}" if user.username else "sin_username"
        lineas.append(f"👤 {nombre} | {uname} | ID: `{user.id}`")

    lineas.insert(2, f"**Resultados:** {encontrados}")
    return "\n".join(lineas)


async def mensajes_recientes(client, channel, limit=10) -> str:
    lineas = [
        "═══════════════════════════",
        f"  **ULTIMOS {limit} MENSAJES**",
        "═══════════════════════════",
        f"",
    ]

    async for msg in client.iter_messages(channel, limit=limit):
        fecha = msg.date.strftime("%d/%m %H:%M") if msg.date else "?"
        texto = msg.text[:80] if msg.text else ""
        media = ""
        if msg.media:
            if isinstance(msg.media, MessageMediaPhoto):
                media = " [📷 foto]"
            elif isinstance(msg.media, MessageMediaDocument):
                doc = msg.media.document
                if doc:
                    has_video = any(isinstance(a, DocumentAttributeVideo) for a in doc.attributes)
                    media = " [🎬 video]" if has_video else " [📄 doc]"
        lineas.append(f"`{fecha}`{media} {texto}")

    return "\n".join(lineas)


async def listar_mis_chats(client):
    chats = []
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        title = dialog.name or "Sin nombre"
        chat_id = entity.id
        
        # Formatear ID para canales/grupos (Telethon usa peer id)
        if isinstance(entity, (Channel, Chat)):
            if chat_id > 0:
                chat_id_fmt = f"-100{chat_id}"
            else:
                chat_id_fmt = str(chat_id)
        else:
            chat_id_fmt = str(chat_id)

        tipo = "Usuario"
        if isinstance(entity, Channel):
            if entity.forum:
                tipo = "Foro (Topics)"
            elif entity.megagroup:
                tipo = "Supergrupo"
            else:
                tipo = "Canal Broadcast"
        elif isinstance(entity, Chat):
            tipo = "Grupo Básico"

        username = f"@{entity.username}" if getattr(entity, "username", None) else "Privado"
        miembros_cnt = getattr(entity, "participants_count", None)
        miembros_str = str(miembros_cnt) if miembros_cnt is not None else "Desconocido"

        chats.append({
            "Título": title,
            "ID Numérico": chat_id_fmt,
            "Tipo": tipo,
            "Username": username,
            "Miembros": miembros_str
        })
    return chats


async def buscar_palabras_clave(client, channel, keyword: str, limit: int = 100):
    resultados = []
    async for msg in client.iter_messages(channel, search=keyword, limit=limit):
        fecha = msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else "?"
        sender = await msg.get_sender()
        autor = f"{sender.first_name or ''} {sender.last_name or ''}".strip() if sender else "Desconocido"
        if sender and getattr(sender, "username", None):
            autor += f" (@{sender.username})"
        
        texto = msg.text or "[Archivo Multimedia]"
        resultados.append({
            "ID Msg": msg.id,
            "Fecha": fecha,
            "Autor": autor,
            "Mensaje": texto[:150]
        })
    return resultados

