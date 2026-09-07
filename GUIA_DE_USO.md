# 📖 GUÍA DE USO COMPLETA & MANUAL DE DESPLIEGUE

> **TELEGRAM OSINT RECON MATRIX & TURBO MEDIA DOWNLOADER**  
> **Creado por:** `@lukgtz` (Luciano Gutiérrez - Salta, Argentina)

---

## 🚀 PARTE 1: CÓMO USAR EN TU COMPUTADORA ACTUAL

### 1. Iniciar la Consola Web Táctica (Recomendado)
Abre PowerShell o CMD en la carpeta del proyecto y ejecuta:
```bash
streamlit run app_web.py
```
Se abrirá automáticamente tu navegador en `http://localhost:8501`.

---

### 💻 Explicación de las 6 Pestañas de la Consola Web:

#### 🚀 Pestaña 1: DESCARGADOR RÁPIDO
- **Para qué sirve:** Descarga fotos, videos o audios de cualquier enlace público, privado o mensaje individual.
- **Cómo se usa:**
  1. Pega el enlace del mensaje (ej: `https://t.me/canal/123` o `@canal`).
  2. Elige si quieres **Mensaje Único** o **Lote Reciente (Batch)** (ej: los últimos 20 archivos).
  3. Haz clic en **⚡ INICIAR EXTRACCIÓN**.

#### 📂 Pestaña 2: DESCARGADOR DE FOROS (TOPICS)
- **Para qué sirve:** Extrae todo el contenido multimedia de grupos organizados en Temas/Topics (como foros de filtraciones, cursos o fotos) ordenado automáticamente en subcarpetas.
- **Cómo se usa:**
  1. Ingresa el ID numérico del grupo (ej: `-1004340179079`).
  2. Haz clic en **📋 CARGAR LISTA DE TOPICS**.
  3. Opcional: Haz clic en **🔍 PRE-ANÁLISIS Y TIEMPO** para saber cuántas fotos/videos hay, cuánto pesan en MB y cuántos minutos tardará.
  4. Puedes seleccionar topics específicos o hacer clic en **⚡ DESCARGAR TODOS**.
  5. Cuenta con botones de **🛑 PAUSAR** y **▶️ REANUDAR** en cualquier momento.

#### ☁️ Pestaña 3: DRIVE TURBO UPLOADER (10GB+)
- **Para qué sirve:** Sube archivos y carpetas pesadas a tu Google Drive sin límites de tamaño y sin consumir memoria RAM.
- **¿Cómo subir carpetas descargadas por el Bot?**
  1. Selecciona la opción `"🤖 Carpeta descargada por el Bot (en downloads/)"`.
  2. Elige la carpeta del menú desplegable.
- **¿Cómo subir cualquier otra carpeta de tu PC (ej: `C:\Users\LukGutierrez\Desktop\APP OSINT`)?**
  1. Selecciona la opción `"💻 Cualquier otra carpeta de mi PC"`.
  2. Escribe o pega la ruta completa de tu carpeta.
  3. El sistema analizará instantáneamente cuántos archivos hay y el peso total en MB.
  4. Haz clic en **🚀 SINCRONIZAR CARPETA A GOOGLE DRIVE DE LA PC**.
  5. Verás una barra de progreso con **Velocidad en vivo (MB/s)**, **Tiempo restante (ETA)** y **Megabytes transferidos**.
  6. Una vez copiado al disco `G:\Mi unidad`, la aplicación oficial de Google Drive se encarga de subirlo a la nube en segundo plano a la máxima velocidad de tu internet.

#### 🕵️ Pestaña 4: CENTRO OSINT
- **Para qué sirve:** Investigación y análisis de inteligencia de fuentes abiertas sobre cualquier canal, grupo o usuario de Telegram.
- **Funcionalidades:**
  - **📋 VISOR DE MIS GRUPOS Y CHATS UNIDOS:** Lista todos tus canales con sus IDs numéricos exactos (`-100...`).
  - **📋 Ficha de Información (`/info`):** Muestra si es canal verificado, scam, fake, restringido, fecha y chats en común.
  - **📈 Estadísticas (`/stats`):** Muestra el porcentaje de fotos vs videos, días de mayor actividad y horas pico de publicación.
  - **💬 Mensajes Recientes (`/recent`):** Lee el historial reciente sin tener que abrir el chat.
  - **👥 Miembros (`/members`):** Extrae la lista de participantes de grupos públicos.
  - **🔍 Búsqueda de Palabras Clave:** Busca mensajes que contengan términos como *CBU, DNI, teléfono, filtro, admin*, etc.

#### 📖 Pestaña 5: MANUAL DE COMANDOS
- Contiene una guía rápida de todos los comandos disponibles si usas el Bot directamente en la app de Telegram.

#### ⚙️ Pestaña 6: CONFIGURACIÓN & PROXIES
- Muestra el estado del sistema de **Deduplicación por Hash SHA-256** (cuántos archivos únicos se han registrado y cuántos megabytes se han ahorrado al no descargar duplicados).
- Permite configurar servidores Proxy SOCKS5 / MTProto para ocultar tu dirección IP.

---

### 2. Iniciar el Bot de Telegram (Modo Mensajería)
Si prefieres interactuar con el Bot directamente desde la app de Telegram en tu celular o PC:
```bash
python bot.py
```
Abre tu Telegram y escribe `/start` a tu bot.

---

## 🌍 PARTE 2: CÓMO INSTALAR EN UNA COMPUTADORA NUEVA O VPS

Sigue estos 5 sencillos pasos para tener el sistema funcionando en cualquier máquina nueva (Windows o Linux):

### Paso 1: Clonar el Repositorio de GitHub
```bash
git clone https://github.com/TU_USUARIO/telegram-osint-matrix.git
cd telegram-osint-matrix
```

### Paso 2: Crear el Entorno Virtual e Instalar Dependencias
```bash
# Crear entorno virtual (Recomendado)
python -m venv venv

# Activar entorno virtual
# En Windows:
.\venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# Instalar todas las librerías necesarias
pip install -r requirements.txt
```

### Paso 3: Configurar las Credenciales
1. Copia el archivo de ejemplo `.env.example` y crea tu archivo `.env`:
```bash
# En Windows (PowerShell):
Copy-Item .env.example .env

# En Linux/Mac:
cp .env.example .env
```
2. Abre el archivo `.env` y coloca tus claves de [https://my.telegram.org](https://my.telegram.org):
```env
TELEGRAM_API_ID=tu_api_id
TELEGRAM_API_HASH=tu_api_hash
TELEGRAM_BOT_TOKEN=tu_bot_token
```

### Paso 4: Iniciar Sesión por Primera Vez
Ejecuta la consola web o el bot:
```bash
streamlit run app_web.py
```
- La primera vez, Telethon te pedirá en la terminal ingresar tu número de teléfono y el código de seguridad que Telegram te envía por mensaje.
- Esto creará de forma segura tu archivo de sesión local.

### Paso 5: (Opcional) Instalar Google Drive para Escritorio
Para disfrutar de la sincronización turbo en Windows:
1. Descarga e instala [Google Drive para Computadoras](https://www.google.com/intl/es/drive/download/).
2. Inicia sesión con tu cuenta de Google.
3. Se creará automáticamente la unidad `G:\Mi unidad`.

---

## ❓ PREGUNTAS FRECUENTES (FAQ)

### 1. ¿Por qué el bot dice que ya terminó de copiar pero en Google Drive Web aún se está subiendo?
El Bot utiliza la tecnología de disco virtual de Google Drive. Copia los archivos a tu disco local `G:\Mi unidad` a una velocidad de **10 a 50 MB/s** en 1 o 2 minutos. Luego, la aplicación oficial de Google Drive en segundo plano sube los archivos a la nube sin bloquear tu navegador ni saturar tu memoria RAM. Puedes ver el icono de Google Drive junto al reloj de Windows para ver el avance en la nube.

### 2. ¿Cómo cambio de cuenta en Google Drive?
1. Haz clic derecho en el icono de Google Drive junto al reloj de Windows (barra de tareas).
2. Haz clic en el engranaje de **Configuración** ⚙️ y selecciona **Preferencias**.
3. Haz clic en tu foto de perfil y selecciona **"Agregar otra cuenta"** o **"Desconectar cuenta"** para iniciar sesión con otra.

### 3. ¿Cómo comparto una carpeta con enlace público en Google Drive?
1. Abre tu Google Drive en el navegador web ([drive.google.com](https://drive.google.com)) o ve al disco `G:\Mi unidad`.
2. Haz clic derecho en la carpeta que subiste y selecciona **Compartir** -> **Compartir**.
3. En *"Acceso general"*, cambia de "Restringido" a **"Cualquier persona con el enlace"** (Lector).
4. Haz clic en **Copiar enlace**. ¡Listo!

---

<div align="center">
    <b>TELEGRAM OSINT RECON MATRIX &bull; CREADO POR @lukgtz</b>
</div>
