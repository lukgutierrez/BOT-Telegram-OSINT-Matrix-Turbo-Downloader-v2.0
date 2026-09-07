import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# Forzar UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "gdrive_credentials.json")
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "gdrive_token.json")

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    flow_obj = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        
        if "code" in qs:
            code = qs["code"][0]
            try:
                # Canjear token usando el codigo directamente (sin CSRF state error)
                OAuthCallbackHandler.flow_obj.fetch_token(code=code)
                creds = OAuthCallbackHandler.flow_obj.credentials
                with open(TOKEN_PATH, 'w', encoding='utf-8') as token:
                    token.write(creds.to_json())
                    
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                html = """
                <html>
                <body style="font-family: Arial, sans-serif; background-color: #050505; color: #00FF41; text-align: center; padding-top: 50px;">
                    <h1>🎉 ¡CONEXIÓN EXITOSA CON GOOGLE DRIVE!</h1>
                    <p style="color: #FFFFFF; font-size: 1.2rem;">Tu token ha sido guardado correctamente. Ya puedes cerrar esta ventana.</p>
                </body>
                </html>
                """
                self.wfile.write(html.encode("utf-8"))
                print("\n=======================================================")
                print("✅ ¡AUTORIZADO EXITOSAMENTE! Token guardado en gdrive_token.json")
                print("=======================================================\n")
                
                # Probar subida de inmediato
                try:
                    from gdrive_auto_test import test_upload
                    test_upload()
                except Exception as e:
                    print(f"Error en prueba automatica: {e}")
                    
                sys.exit(0)
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                err_html = f"<html><body><h1>Error al canjear token: {e}</h1></body></html>"
                self.wfile.write(err_html.encode("utf-8"))
                print(f"❌ Error al canjear token: {e}")
        else:
            self.send_response(400)
            self.end_headers()

def main():
    if not os.path.exists(CREDENTIALS_PATH):
        print("ERROR: No se encuentra gdrive_credentials.json")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_PATH,
        SCOPES,
        redirect_uri="http://localhost:8080/"
    )
    OAuthCallbackHandler.flow_obj = flow
    
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    
    print("\n=======================================================")
    print("INICIANDO SERVIDOR DE AUTORIZACION DE GOOGLE DRIVE")
    print("=======================================================")
    print(f"Haz clic o abre este enlace en tu navegador:\n{auth_url}\n")
    
    # Abrir navegador automaticamente
    import webbrowser
    webbrowser.open(auth_url)
    
    server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
    server.serve_forever()

if __name__ == "__main__":
    main()
