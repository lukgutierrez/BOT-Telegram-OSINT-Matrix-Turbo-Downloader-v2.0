import socks
from config import PROXY_ENABLED, PROXY_TYPE, PROXY_HOST, PROXY_PORT, PROXY_USERNAME, PROXY_PASSWORD, PROXY_SECRET

def obtener_config_proxy():
    """Retorna la tupla/configuracion de proxy compatible con Telethon."""
    if not PROXY_ENABLED or not PROXY_HOST or not PROXY_PORT:
        return None
    
    tipo_proxy = (PROXY_TYPE or "SOCKS5").upper()
    
    if tipo_proxy == "SOCKS5":
        return (
            socks.SOCKS5,
            PROXY_HOST,
            int(PROXY_PORT),
            True,  # rdns (Remote DNS)
            PROXY_USERNAME or None,
            PROXY_PASSWORD or None
        )
    elif tipo_proxy == "SOCKS4":
        return (
            socks.SOCKS4,
            PROXY_HOST,
            int(PROXY_PORT),
            True,
            PROXY_USERNAME or None,
            PROXY_PASSWORD or None
        )
    elif tipo_proxy == "HTTP":
        return (
            socks.HTTP,
            PROXY_HOST,
            int(PROXY_PORT),
            True,
            PROXY_USERNAME or None,
            PROXY_PASSWORD or None
        )
    elif tipo_proxy == "MTPROTO":
        # Telethon MTProto proxy dict format
        proxy_dict = {
            "proxy_type": "mtproxy",
            "addr": PROXY_HOST,
            "port": int(PROXY_PORT),
            "secret": PROXY_SECRET or "00000000000000000000000000000000"
        }
        return proxy_dict

    return None
