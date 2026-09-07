import http.server
import socketserver
import urllib.parse
import os
import sys

# Forzar UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from gdrive_uploader import guardar_token_desde_codigo

PORT = 8080

class OAuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        if "code" in qs:
            code = qs["code"][0]
            ok, msg = guardar_token_desde_codigo(code)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            if ok:
                html = """
                <html>
                <body style="font-family: sans-serif; background-color: #050505; color: #00FF41; text-align: center; padding-top: 50px;">
                    <h1>🎉 ¡CONEXIÓN EXITOSA CON GOOGLE DRIVE!</h1>
                    <p style="color: #FFFFFF; font-size: 1.2rem;">Tu cuenta ha sido vinculada correctamente. Ya puedes cerrar esta pestaña y volver al Bot.</p>
                </body>
                </html>
                """
                self.wfile.write(html.encode("utf-8"))
                # Salir del servidor despues de recibir el token
                sys.exit(0)
            else:
                html = f"<html><body><h1>Error: {msg}</h1></body></html>"
                self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()

if __name__ == "__main__":
    try:
        with socketserver.TCPServer(("", PORT), OAuthHandler) as httpd:
            print(f"Escuchando en http://localhost:{PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Error en listener: {e}")
