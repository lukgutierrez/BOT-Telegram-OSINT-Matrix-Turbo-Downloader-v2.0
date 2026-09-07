import os
import sys
import time
import shutil

# Forzar UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def detectar_google_drive_local():
    """Detecta automáticamente la letra de unidad donde Google Drive está montado en Windows."""
    posibles_letras = ["G", "H", "I", "F", "D", "E"]
    for l in posibles_letras:
        drive_path = f"{l}:\\"
        if os.path.exists(drive_path):
            for sub in ["My Drive", "Mi unidad", "Other computers"]:
                full = os.path.join(drive_path, sub)
                if os.path.exists(full):
                    return full
            # Si existe la unidad directamente
            if l == "G":
                return drive_path
                
    user_drive = os.path.expanduser(r"~\Google Drive")
    if os.path.exists(user_drive):
        return user_drive
        
    return None

def abrir_app_google_drive():
    """Lanza la aplicación Google Drive de Windows."""
    try:
        launch_bat = r"C:\Program Files\Google\Drive File Stream\launch.bat"
        if os.path.exists(launch_bat):
            os.startfile(launch_bat)
            return True, "Abriendo Google Drive..."
    except Exception as e:
        return False, str(e)
    return False, "No se encontró launch.bat de Google Drive."

def copiar_archivo_con_progreso(src, dst, chunk_size=8*1024*1024, on_chunk=None):
    """Copia un archivo por bloques midiendo bytes transferidos."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
        while True:
            buf = fsrc.read(chunk_size)
            if not buf:
                break
            fdst.write(buf)
            if on_chunk:
                on_chunk(len(buf))
    try:
        shutil.copystat(src, dst)
    except Exception:
        pass

def copiar_a_google_drive_local(origen_path: str, carpeta_destino_nombre: str = None, destino_custom: str = None, callback_progress=None):
    """Copia una carpeta o archivo a Google Drive local reportando progreso, velocidad y ETA en vivo."""
    gdrive_root = destino_custom.strip() if destino_custom and destino_custom.strip() else detectar_google_drive_local()
    
    if not gdrive_root or not os.path.exists(gdrive_root):
        return False, f"La ruta de destino '{gdrive_root}' no existe. Asegúrate de abrir la app de Google Drive o especificar una carpeta válida."
    
    if not os.path.exists(origen_path):
        return False, f"La ruta de origen '{origen_path}' no existe."
        
    nombre = carpeta_destino_nombre or os.path.basename(origen_path.rstrip("\\/"))
    destino_final = os.path.join(gdrive_root, nombre)
    
    archivos_a_copiar = []
    if os.path.isdir(origen_path):
        for root, dirs, files in os.walk(origen_path):
            for file in files:
                full_src = os.path.join(root, file)
                rel_path = os.path.relpath(full_src, origen_path)
                full_dst = os.path.join(destino_final, rel_path)
                archivos_a_copiar.append((full_src, full_dst))
    else:
        dest_file = os.path.join(destino_final if os.path.isdir(destino_final) else gdrive_root, os.path.basename(origen_path))
        archivos_a_copiar.append((origen_path, dest_file))
        destino_final = dest_file
        
    if not archivos_a_copiar:
        return True, destino_final
        
    total_bytes_global = sum(os.path.getsize(src) for src, _ in archivos_a_copiar if os.path.exists(src))
    bytes_copiados_global = 0
    
    t_start = time.time()
    t_last = t_start
    bytes_last = 0
    smooth_speed = 0.0
    
    total_files = len(archivos_a_copiar)
    
    for idx, (src, dst) in enumerate(archivos_a_copiar, 1):
        fname = os.path.basename(src)
        bytes_file_done = 0
        
        def on_chunk(bytes_chunk):
            nonlocal bytes_copiados_global, bytes_file_done, t_last, bytes_last, smooth_speed
            bytes_copiados_global += bytes_chunk
            bytes_file_done += bytes_chunk
            
            t_now = time.time()
            dt = t_now - t_last
            if dt >= 0.2:
                d_bytes = bytes_copiados_global - bytes_last
                inst_speed = (d_bytes / (1024 * 1024)) / dt if dt > 0 else 0
                if smooth_speed == 0:
                    smooth_speed = inst_speed
                else:
                    smooth_speed = 0.7 * smooth_speed + 0.3 * inst_speed
                t_last = t_now
                bytes_last = bytes_copiados_global
                
            rem_bytes = max(0, total_bytes_global - bytes_copiados_global)
            eta = rem_bytes / (smooth_speed * 1024 * 1024) if smooth_speed > 0 else 0
            
            if callback_progress:
                try:
                    callback_progress(
                        fname,
                        idx,
                        total_files,
                        bytes_copiados_global,
                        total_bytes_global,
                        smooth_speed,
                        eta
                    )
                except Exception:
                    pass
                    
        copiar_archivo_con_progreso(src, dst, chunk_size=8*1024*1024, on_chunk=on_chunk)
        
    return True, destino_final
