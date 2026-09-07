import os
import hashlib
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "downloads_hashes.db")

def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hashes (
            file_hash TEXT PRIMARY KEY,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            date_added TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def calcular_hash_archivo(filepath: str, algo: str = "sha256") -> str:
    """Calcula el hash binario (SHA256 o MD5) de un archivo local en bloques de 64KB."""
    if not os.path.exists(filepath):
        return ""
    
    hasher = hashlib.sha256() if algo.lower() == "sha256" else hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""

def existe_hash(file_hash: str) -> tuple[bool, str]:
    """Retorna (True, ruta_existente) si el hash ya esta registrado en la base de datos."""
    if not file_hash:
        return False, ""
    
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM hashes WHERE file_hash = ?", (file_hash,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        ruta_existente = row[0]
        if os.path.exists(ruta_existente) and os.path.getsize(ruta_existente) > 0:
            return True, ruta_existente
    return False, ""

def registrar_hash(filepath: str, algo: str = "sha256") -> str:
    """Calcula el hash de un archivo y lo registra en la base de datos."""
    if not os.path.exists(filepath):
        return ""
    
    file_hash = calcular_hash_archivo(filepath, algo)
    if not file_hash:
        return ""
    
    size = os.path.getsize(filepath)
    now = datetime.now().isoformat()
    
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO hashes (file_hash, file_path, file_size, date_added) VALUES (?, ?, ?, ?)",
            (file_hash, filepath, size, now)
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()
    
    return file_hash

def obtener_stats_dedup() -> dict:
    """Obtiene metricas del sistema de deduplicacion por hash."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(file_size) FROM hashes")
    row = cursor.fetchone()
    conn.close()
    
    total_archivos = row[0] if row and row[0] else 0
    total_bytes = row[1] if row and row[1] else 0
    total_mb = total_bytes / (1024 * 1024) if total_bytes else 0
    
    return {
        "total_archivos": total_archivos,
        "total_mb": round(total_mb, 2)
    }
