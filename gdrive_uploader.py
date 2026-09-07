import os
import sys
import time
import asyncio

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']

TOKEN_PATH = os.path.join(os.path.dirname(__file__), "gdrive_token.json")
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "gdrive_credentials.json")


from urllib.parse import urlparse, parse_qs


def generar_url_autorizacion():
    """Genera la URL de autorización para que el usuario ingrese desde su navegador."""
    if not os.path.exists(CREDENTIALS_PATH):
        return None, "Falta el archivo gdrive_credentials.json"
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_PATH,
            SCOPES,
            redirect_uri="http://localhost:8080/"
        )
        auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
        return auth_url, "OK"
    except Exception as e:
        return None, str(e)


def guardar_token_desde_codigo(input_str: str):
    """Procesa el código de autorización o la URL de redirección y guarda gdrive_token.json."""
    if not input_str or not input_str.strip():
        return False, "Ingresa un código válido"
    
    clean_input = input_str.strip()
    code = clean_input
    
    if "code=" in clean_input:
        try:
            parsed = urlparse(clean_input)
            qs = parse_qs(parsed.query)
            if "code" in qs:
                code = qs["code"][0]
        except Exception:
            pass
            
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_PATH,
            SCOPES,
            redirect_uri="http://localhost:8080/"
        )
        flow.fetch_token(code=code)
        creds = flow.credentials
        with open(TOKEN_PATH, 'w', encoding='utf-8') as token:
            token.write(creds.to_json())
        return True, "OK"
    except Exception as e:
        return False, f"Error al validar código: {e}"


def obtener_servicio_gdrive(interactive: bool = False):
    """Obtiene el servicio autenticado de Google Drive API v3."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_PATH, 'w', encoding='utf-8') as token:
                    token.write(creds.to_json())
            except Exception:
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_PATH):
                return None, "Falta el archivo 'gdrive_credentials.json'."
            
            if not interactive:
                return None, "NO_TOKEN"

            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=8080, open_browser=True)
                with open(TOKEN_PATH, 'w', encoding='utf-8') as token:
                    token.write(creds.to_json())
            except Exception as e:
                return None, f"Error al autorizar: {e}"

    try:
        service = build('drive', 'v3', credentials=creds)
        return service, "OK"
    except Exception as e:
        return None, f"Error en servicio: {e}"


def crear_carpeta_drive(service, nombre_carpeta: str, parent_id: str = None) -> str:
    """Crea una carpeta en Google Drive y retorna su ID."""
    metadata = {
        'name': nombre_carpeta,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        metadata['parents'] = [parent_id]

    try:
        folder = service.files().create(body=metadata, fields='id').execute()
        return folder.get('id')
    except Exception:
        return None


def subir_archivo_drive(service, filepath: str, parent_id: str = None, callback_st=None):
    """Subes un archivo pesado a Google Drive usando subida por bloques (64MB/128MB Chunked Upload) a máxima velocidad."""
    if not os.path.exists(filepath):
        return None, "El archivo no existe"

    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)

    metadata = {'name': filename}
    if parent_id:
        metadata['parents'] = [parent_id]

    # Tamaño de bloque de 64MB / 128MB para hiper-velocidad
    chunk_size = 64 * 1024 * 1024
    if file_size > 1 * 1024 * 1024 * 1024:
        chunk_size = 128 * 1024 * 1024

    media = MediaFileUpload(
        filepath,
        mimetype='application/octet-stream',
        chunksize=chunk_size,
        resumable=True
    )

    request = service.files().create(body=metadata, media_body=media, fields='id, name, webViewLink')
    response = None

    t_start = time.time()
    t_last = t_start
    bytes_last = 0
    smooth_speed = 0.0

    while response is None:
        status, response = request.next_chunk()
        if status:
            current = status.progress()
            t_now = time.time()
            dt = t_now - t_last
            if dt > 0.3:
                d_bytes = current - bytes_last
                inst_speed = (d_bytes / (1024 * 1024)) / dt if dt > 0 else 0
                if smooth_speed == 0:
                    smooth_speed = inst_speed
                else:
                    smooth_speed = 0.7 * smooth_speed + 0.3 * inst_speed
                t_last = t_now
                bytes_last = current

            if callback_st:
                try:
                    callback_st(filename, current, file_size, smooth_speed)
                except Exception:
                    pass

    return response, "OK"
