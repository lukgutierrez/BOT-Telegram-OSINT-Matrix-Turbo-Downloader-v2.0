import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============================================================
# CREDENCIALES DE TELEGRAM
# ============================================================
# Consigue tu API_ID y API_HASH en: https://my.telegram.org
# Consigue tu BOT_TOKEN creando un bot con @BotFather en Telegram

API_ID = int(os.getenv("TELEGRAM_API_ID", "37975206"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "05c1d0668fb608e464154f3030b055af")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8406820290:AAFlStLnD9tEyChkGr7ybRWbrDtgf0hM44I")

# ============================================================
# CONFIGURACION DEL BOT
# ============================================================

# Maximo de descargas simultaneas (no subir mucho para evitar FloodWait)
MAX_CONCURRENT_DOWNLOADS = 5

# Carpeta donde se guardan los archivos descargados
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "downloads")

# Tamano maximo de archivo a enviar por Telegram (50MB limite bot API)
MAX_FILE_SIZE_MB = 50

# Tiempo maximo de espera por FloodWait (en segundos)
MAX_FLOOD_WAIT = 300

# ============================================================
# CONFIGURACION OSINT
# ============================================================

# Limite de mensajes a analizar en stats de canal
OSINT_MAX_MESSAGES_ANALYZE = 100

# Limite de participantes a obtener
OSINT_MAX_PARTICIPANTS = 200

# ============================================================
# CONFIGURACION DE DEDUPLICACION Y HASH
# ============================================================
DEDUP_ENABLE = True
HASH_ALGORITHM = "sha256"  # sha256 o md5

# ============================================================
# CONFIGURACION DE PROXIES (SOCKS5 / MTPROTO)
# ============================================================
PROXY_ENABLED = os.getenv("PROXY_ENABLED", "false").lower() in ("true", "1", "yes")
PROXY_TYPE = os.getenv("PROXY_TYPE", "SOCKS5")  # SOCKS5, SOCKS4, HTTP, MTPROTO
PROXY_HOST = os.getenv("PROXY_HOST", "127.0.0.1")
PROXY_PORT = int(os.getenv("PROXY_PORT", "1080"))
PROXY_USERNAME = os.getenv("PROXY_USERNAME", "")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD", "")
PROXY_SECRET = os.getenv("PROXY_SECRET", "")  # Para MTProto Proxy

