import os
import sys
import time

# Forzar UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from gdrive_uploader import obtener_servicio_gdrive, crear_carpeta_drive, subir_archivo_drive

def test_upload():
    print("==================================================")
    print("🧪 PRUEBA DE SUBIDA A GOOGLE DRIVE")
    print("==================================================")
    
    service, status = obtener_servicio_gdrive(interactive=False)
    if not service:
        print(f"❌ No se encontró token válido ({status}). Por favor completa la autorización.")
        return False
        
    print("✅ Servicio de Google Drive conectado correctamente!")
    
    # Crear archivo de prueba local
    test_file_path = os.path.join(os.path.dirname(__file__), "test_drive_upload.txt")
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(f"Archivo de prueba creado por Bot Telegram a las {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("Verificacion de subida automatica 100% exitosa!")
        
    print(f"📄 Archivo de prueba creado: {test_file_path}")
    print("⏳ Creando carpeta 'BOT_TELEGRAM_TEST' en Google Drive...")
    
    folder_id = crear_carpeta_drive(service, "BOT_TELEGRAM_TEST")
    if not folder_id:
        print("❌ Error al crear carpeta en Google Drive.")
        return False
        
    print(f"✅ Carpeta creada en Google Drive (ID: {folder_id})")
    print("🚀 Subiendo archivo de prueba...")
    
    res, msg = subir_archivo_drive(service, test_file_path, parent_id=folder_id)
    if res:
        link = res.get('webViewLink', 'N/A')
        print("\n==================================================")
        print("🎉 ¡SUBIDA 100% EXITOSA Y VERIFICADA!")
        print(f"🔗 Link en Google Drive: {link}")
        print("==================================================\n")
        return True
    else:
        print(f"❌ Error en subida: {msg}")
        return False

if __name__ == "__main__":
    test_upload()
