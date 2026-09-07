import re
from urllib.parse import urlparse
from dataclasses import dataclass
from typing import Optional
from telethon.tl.types import Channel, Chat, User


@dataclass
class ParsedLink:
    tipo: str  # "publico", "privado", "invite", "mensaje_directo"
    chat_id: Optional[int] = None
    chat_username: Optional[str] = None
    invite_hash: Optional[str] = None
    msg_id: Optional[int] = None
    raw_url: str = ""


def parsear_enlace(url: str) -> ParsedLink:
    url = url.strip()
    if url.lstrip("-").isdigit():
        num_id = int(url)
        return ParsedLink(tipo="privado", chat_id=num_id, raw_url=url)

    if "t.me/" not in url:
        if url.startswith("@"):
            return ParsedLink(tipo="publico", chat_username=url[1:], raw_url=url)
        raise ValueError(f"Enlace no valido: {url}")

    # Limpiar parametros de consulta
    url_clean = url.split("?")[0].split("#")[0]
    p = urlparse(url_clean if url_clean.startswith("http") else f"https://{url_clean}")
    parts = [s for s in p.path.split("/") if s]

    if not parts:
        raise ValueError("Enlace vacio")

    # Manejar prefijo /s/ (preview publico de canal)
    if parts[0] == "s" and len(parts) > 1:
        parts = parts[1:]

    if parts[0] == "c" and len(parts) >= 2:
        num_id = int(parts[1])
        # Asegurar formato -100 para supergrupos/canales si no lo tiene
        if num_id > 0:
            chat_id = int(f"-100{num_id}")
        else:
            chat_id = num_id
        msg_id = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
        return ParsedLink(
            tipo="privado",
            chat_id=chat_id,
            msg_id=msg_id,
            raw_url=url,
        )
    elif parts[0].startswith("+") or parts[0] == "joinchat":
        invite_hash = parts[0][1:] if parts[0].startswith("+") else (parts[1] if len(parts) > 1 else None)
        return ParsedLink(
            tipo="invite",
            invite_hash=invite_hash,
            raw_url=url,
        )
    else:
        username = parts[0]
        msg_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
        return ParsedLink(
            tipo="publico",
            chat_username=username,
            msg_id=msg_id,
            raw_url=url,
        )


async def resolver_entidad(client, parsed: ParsedLink):
    if parsed.chat_id:
        try:
            return await client.get_entity(parsed.chat_id)
        except Exception:
            pass

    if parsed.chat_username:
        try:
            return await client.get_entity(parsed.chat_username)
        except Exception:
            pass

    if parsed.invite_hash:
        try:
            from telethon.tl.functions.messages import ImportChatInviteRequest
            updates = await client(ImportChatInviteRequest(parsed.invite_hash))
            if updates.chats:
                return updates.chats[0]
        except Exception:
            pass

    return None


def formatear_entidad(entity) -> str:
    if isinstance(entity, Channel):
        tipo = "Canal" if entity.megagroup else "Grupo"
        lineas = [
            f"**{tipo}:** {entity.title}",
            f"**Username:** @{entity.username}" if entity.username else "**Username:** Privado",
            f"**ID:** `{entity.id}`",
            f"**Descripcion:** {entity.about}" if entity.about else "",
            f"**Miembros:** {entity.participants_count}" if hasattr(entity, "participants_count") and entity.participants_count else "",
            f"**Verificado:** Si" if entity.verified else "",
            f"**Restringido:** Si" if entity.restricted else "",
            f"**Scam:** Si" if entity.scam else "",
            f"**Fake:** Si" if entity.fake else "",
            f"**Fecha creacion:** {entity.date.strftime('%d/%m/%Y')}" if entity.date else "",
        ]
        return "\n".join(l for l in lineas if l)
    elif isinstance(entity, User):
        nombre = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
        lineas = [
            f"**Usuario:** {nombre}",
            f"**Username:** @{entity.username}" if entity.username else "**Username:** No tiene",
            f"**ID:** `{entity.id}`",
            f"**Bot:** Si" if entity.bot else "**Bot:** No",
            f"**Verificado:** Si" if entity.verified else "",
            f"**Premium:** Si" if entity.premium else "",
            f"**Scam:** Si" if entity.scam else "",
            f"**Fake:** Si" if entity.fake else "",
            f"**Restringido:** Si" if entity.restricted else "",
            f"**Foto de perfil:** Si" if entity.photo else "**Foto de perfil:** No",
        ]
        return "\n".join(l for l in lineas if l)
    elif isinstance(entity, Chat):
        lineas = [
            f"**Grupo:** {entity.title}",
            f"**ID:** `{entity.id}`",
            f"**Miembros:** {entity.participants_count}" if hasattr(entity, "participants_count") else "",
            f"**Fecha creacion:** {entity.date.strftime('%d/%m/%Y')}" if entity.date else "",
        ]
        return "\n".join(l for l in lineas if l)
    return str(entity)
