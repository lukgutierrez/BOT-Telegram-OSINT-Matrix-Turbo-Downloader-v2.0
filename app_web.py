import os
import sys
import asyncio
import time
import sqlite3
import pandas as pd
import streamlit as st

# Configurar timeout largo en SQLite para evitar "database is locked"
def configurar_sqlite():
    try:
        session_file = os.path.join(os.path.dirname(__file__), "user_session.session")
        if os.path.exists(session_file):
            conn = sqlite3.connect(session_file, timeout=30)
            conn.execute("PRAGMA busy_timeout=30000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=OFF")
            conn.commit()
            conn.close()
    except Exception:
        pass

configurar_sqlite()

# Asegurar path
sys.path.insert(0, os.path.dirname(__file__))

from telethon import TelegramClient
from config import API_ID, API_HASH, DOWNLOAD_FOLDER, MAX_CONCURRENT_DOWNLOADS
from link_parser import parsear_enlace, resolver_entidad
from downloader import descargar_un_archivo, descargar_multiples, formatear_estado_descarga, obtener_tipo_media, establecer_concurrencia
from osint import info_canal, info_usuario, stats_canal, listar_participantes, buscar_usuarios, mensajes_recientes, listar_mis_chats, buscar_palabras_clave
from hash_dedup import obtener_stats_dedup
from proxy_manager import obtener_config_proxy
from gdrive_uploader import obtener_servicio_gdrive, subir_archivo_drive, crear_carpeta_drive, generar_url_autorizacion, guardar_token_desde_codigo
from gdrive_desktop_sync import detectar_google_drive_local, copiar_a_google_drive_local, abrir_app_google_drive

# Configuración de la página Streamlit
st.set_page_config(
    page_title="TELEGRAM OSINT MATRIX - @lukgtz",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS con estética Cyber OLED Terminal Hacker (@lukgtz)
CSS_CYBER = """
<style>
    /* Estilo OLED Ultra Oscuro */
    .stApp {
        background-color: #050505 !important;
        color: #E0E6ED;
        font-family: 'Consolas', 'Courier New', monospace;
    }
    
    /* Container Cyber Terminal */
    .cyber-terminal-container {
        background-color: #080B10;
        border: 1px solid #1F2937;
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 25px;
        box-shadow: 0 0 25px rgba(0, 240, 255, 0.08);
        position: relative;
        font-family: 'Consolas', 'Courier New', monospace;
    }
    
    .terminal-meta-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 15px;
        font-size: 0.82rem;
        color: #9CA3AF;
        margin-bottom: 15px;
    }
    
    .terminal-meta-left {
        text-align: left;
    }
    
    .terminal-meta-center {
        text-align: center;
    }
    
    .terminal-meta-right {
        text-align: right;
    }
    
    .cyber-title-main {
        color: #FFFFFF;
        font-size: 3.5rem;
        font-weight: 900;
        letter-spacing: 4px;
        text-shadow: 0 0 20px rgba(255, 255, 255, 0.9), 0 0 40px rgba(0, 240, 255, 0.4);
        margin: 10px 0 5px 0;
        text-align: center;
    }
    
    .cyber-title-sub {
        color: #00F0FF;
        font-size: 1.4rem;
        font-weight: bold;
        text-align: center;
        letter-spacing: 2px;
    }
    
    .blinking-cursor {
        display: inline-block;
        width: 12px;
        height: 1.3rem;
        background-color: #00FF41;
        margin-left: 6px;
        animation: blink 1s infinite;
        vertical-align: middle;
    }
    
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
    }
    
    .quote-box {
        border-top: 1px dashed #374151;
        border-bottom: 1px dashed #374151;
        padding: 8px;
        margin-top: 15px;
        text-align: center;
        color: #F3F4F6;
        font-weight: bold;
        font-size: 0.85rem;
        letter-spacing: 2px;
    }
    
    /* Tarjetas de comando */
    .command-card {
        background-color: #0F172A;
        border-left: 4px solid #00FF41;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 12px;
    }
    
    .command-name {
        color: #00F0FF;
        font-weight: bold;
        font-size: 1.1rem;
    }
    
    .command-desc {
        color: #94A3B8;
        font-size: 0.95rem;
    }
    
    /* Botones estilo hacker */
    .stButton>button {
        background-color: #1E293B !important;
        color: #00FF41 !important;
        border: 1px solid #00FF41 !important;
        font-weight: bold !important;
        letter-spacing: 1px !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        background-color: #00FF41 !important;
        color: #050505 !important;
        box-shadow: 0 0 14px rgba(0, 255, 65, 0.8) !important;
    }

    /* Pestañas (Tabs) Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #0B0F17;
        border-radius: 6px;
        padding: 6px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 4px;
        color: #9CA3AF;
        font-family: 'Consolas', 'Courier New', monospace;
        font-weight: bold;
    }

    .stTabs [aria-selected="true"] {
        background-color: #1F2937 !important;
        color: #00FF41 !important;
        border: 1px solid #00FF41 !important;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.3);
    }
</style>
"""

st.markdown(CSS_CYBER, unsafe_allow_html=True)

# Banner Principal OLED Terminal Hacker (@lukgtz)
st.markdown("""<div class="cyber-terminal-container">
<div class="terminal-meta-grid">
<div class="terminal-meta-left">
<div>&gt; user: <b>lukgtz</b></div>
<div>&gt; location: <b>Salta, Argentina</b></div>
<div>&gt; focus: <b>OSINT &amp; Cyber Investigations</b></div>
<div>&gt; status: <span style="color:#00FF41;">always learning</span></div>
</div>
<div class="terminal-meta-center">
<div style="color: #6B7280;">// scanning...</div>
<div style="color: #4B5563;">-----------------------------</div>
<div>&gt; assets_found: <b>12</b></div>
<div>&gt; investigations: <span style="color:#00F0FF;">active</span></div>
<div>&gt; mindset: <b>discipline &gt; motivation</b></div>
</div>
<div class="terminal-meta-right">
<div style="color:#00F0FF; font-family: monospace; line-height: 1.1;">
01001100 ┐<br>
01110101 │<br>
01101811 │<br>
01100111 │<br>
01110100 │<br>
01111012 ┘
</div>
</div>
</div>
<div class="cyber-title-main">@lukgtz</div>
<div class="cyber-title-sub">&gt; I'm Luciano<span class="blinking-cursor"></span></div>
<div class="quote-box">
INFORMATION IS POWER &bull; DISCRETION IS SURVIVAL
</div>
</div>""", unsafe_allow_html=True)

import threading
from telethon.sessions import SQLiteSession, MemorySession

_BG_LOOP = None
_BG_THREAD = None

def _start_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

@st.cache_resource
def get_background_loop():
    global _BG_LOOP, _BG_THREAD
    if _BG_LOOP is None or _BG_LOOP.is_closed():
        _BG_LOOP = asyncio.new_event_loop()
        _BG_THREAD = threading.Thread(target=_start_background_loop, args=(_BG_LOOP,), daemon=True)
        _BG_THREAD.start()
    return _BG_LOOP

@st.cache_resource
def get_telegram_client():
    loop = get_background_loop()
    proxy = obtener_config_proxy()
    
    # Cargar datos de autenticacion de la sesion en memoria para desacoplar SQLite
    memory_session = MemorySession()
    try:
        sql_session = SQLiteSession("user_session")
        memory_session.set_dc(sql_session.dc_id, sql_session.server_address, sql_session.port)
        memory_session.auth_key = sql_session.auth_key
        sql_session.close()
    except Exception:
        pass

    client = TelegramClient(memory_session, API_ID, API_HASH, loop=loop, proxy=proxy)
    return client

from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

def run_async(coro):
    ctx = get_script_run_ctx()
    loop = get_background_loop()

    async def _wrapped():
        if ctx:
            try:
                add_script_run_ctx(threading.current_thread(), ctx)
            except Exception:
                pass
        try:
            await client.start()
        except Exception:
            pass
        return await coro

    future = asyncio.run_coroutine_threadsafe(_wrapped(), loop)
    return future.result()

client = get_telegram_client()

async def obtener_entidad_segura(client, target_str: str):
    if not target_str or not target_str.strip():
        return None
    target_clean = target_str.strip()
    parsed = parsear_enlace(target_clean)
    ent = await resolver_entidad(client, parsed)
    if ent:
        return ent

    num_str = target_clean.lstrip("-")
    if num_str.isdigit():
        try:
            val = int(target_clean)
            return await client.get_entity(val)
        except Exception:
            pass

    try:
        return await client.get_entity(target_clean)
    except Exception:
        pass

    try:
        async for dialog in client.iter_dialogs():
            d_id = str(dialog.entity.id)
            if target_clean == d_id or target_clean == f"-100{d_id}" or target_clean.lstrip("-100") == d_id:
                return dialog.entity
    except Exception:
        pass

    return None

# Pestañas Principales
tab_dl, tab_forum, tab_gdrive, tab_osint, tab_guide, tab_settings = st.tabs([
    "🚀 DESCARGADOR RÁPIDO",
    "📂 DESCARGADOR DE FOROS (TOPICS)",
    "☁️ DRIVE TURBO UPLOADER (10GB+)",
    "🕵️ CENTRO OSINT",
    "📖 MANUAL DE COMANDOS",
    "⚙️ CONFIGURACIÓN & PROXIES"
])

# ============================================================
# PESTAÑA 1: DESCARGADOR RÁPIDO
# ============================================================
with tab_dl:
    st.subheader("📥 Extracción de Multimedia (Individual o por Lote)")
    st.write("Ingresa un enlace público/privado de Telegram o el ID de un chat.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        link_input = st.text_input("🔗 Enlace o ID de Telegram:", placeholder="https://t.me/canal/123  o  @username  o  -100123456789")
    with col2:
        modo_descarga = st.radio("Modo:", ["Mensaje Único", "Lote Reciente (Batch)"])
    
    cant_batch = 20
    if modo_descarga == "Lote Reciente (Batch)":
        cant_batch = st.slider("Cantidad de mensajes a revisar:", 5, 100, 20)

    if st.button("⚡ INICIAR EXTRACCIÓN", key="btn_dl"):
        if not link_input.strip():
            st.warning("⚠️ Por favor ingresa un enlace o ID válido.")
        else:
            with st.spinner("🔍 Conectando con los servidores de Telegram..."):
                async def ejecutar_descarga():
                    await client.start()
                    parsed = parsear_enlace(link_input.strip())
                    entidad = await resolver_entidad(client, parsed)
                    if not entidad:
                        # Intento con get_entity directo
                        try:
                            entidad = await client.get_entity(int(link_input.strip()) if link_input.strip().lstrip("-").isdigit() else link_input.strip())
                        except Exception:
                            pass
                    return parsed, entidad

                try:
                    parsed, entidad = run_async(ejecutar_descarga())
                    if not entidad:
                        st.error("❌ No se pudo encontrar el canal, grupo o usuario. Verifica las credenciales o el enlace.")
                    else:
                        st.success(f"✅ Entidad Encontrada: **{getattr(entidad, 'title', getattr(entidad, 'first_name', 'Chat'))}**")
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        async def procesar_archivos():
                            exitosos = []
                            fallidos = []

                            if modo_descarga == "Mensaje Único":
                                msg_id = parsed.msg_id
                                if not msg_id:
                                    status_text.warning("⚠️ Para mensaje único necesitas un enlace con número de mensaje (ej. t.me/canal/123). Se descargarán los recientes.")
                                    mensajes = [m async for m in client.iter_messages(entidad, limit=1) if m.media]
                                else:
                                    msg = await client.get_messages(entidad, ids=msg_id)
                                    mensajes = [msg] if msg and msg.media else []
                            else:
                                mensajes = [m async for m in client.iter_messages(entidad, limit=cant_batch) if m.media]

                            if not mensajes:
                                return [], [("No se encontraron archivos multimedia", "Sin medios")]

                            total = len(mensajes)
                            for idx, msg in enumerate(mensajes, start=1):
                                status_text.info(f"⏳ Descargando archivo {idx}/{total}...")
                                try:
                                    ruta = await descargar_un_archivo(client, msg)
                                    if ruta:
                                        exitosos.append(ruta)
                                except Exception as e:
                                    fallidos.append((msg, str(e)))
                                progress_bar.progress(int(idx * 100 / total))

                            return exitosos, fallidos

                        exitosos, fallidos = run_async(procesar_archivos())
                        progress_bar.progress(100)
                        status_text.empty()

                        st.markdown(f"### 📊 Resultado de la Extracción:")
                        st.success(f"✅ Archivos descargados con éxito: **{len(exitosos)}**")
                        if fallidos:
                            st.error(f"❌ Fallidos: **{len(fallidos)}**")

                        if exitosos:
                            st.write("📁 **Archivos guardados en disco:**")
                            for r in exitosos:
                                tam_mb = os.path.getsize(r) / (1024 * 1024)
                                st.code(f"{r} ({tam_mb:.1f} MB)")

                except Exception as e:
                    st.error(f"❌ Error durante el procesamiento: {e}")

# ============================================================
# PESTAÑA 2: DESCARGADOR DE FOROS (TOPICS)
# ============================================================
with tab_forum:
    st.subheader("📂 Extracción Organizada de Foros por Topics")
    st.write("Carga los topics del foro, selecciona cuáles quieres descargar o descarga todos automáticamente.")
    
    col_f1, col_f2 = st.columns([3, 1])
    with col_f1:
        forum_id_input = st.text_input("🆔 ID del Grupo Foro:", value="-1004340179079", help="Ejemplo: -1004340179079 para Realeza Salta")
    with col_f2:
        st.write("")
        st.write("")
        btn_cargar_topics = st.button("📋 CARGAR LISTA DE TOPICS", key="btn_load_topics")
    
    # Session state para almacenar los topics leidos
    if "topics_disponibles" not in st.session_state:
        st.session_state.topics_disponibles = []
        st.session_state.entidad_foro = None

    if btn_cargar_topics:
        if not forum_id_input.strip():
            st.warning("⚠️ Ingresa un ID de grupo válido.")
        else:
            with st.spinner("⏳ Conectando y leyendo estructura de Topics del Foro..."):
                async def leer_topics():
                    await client.start()
                    entidad = await obtener_entidad_segura(client, forum_id_input)
                    if not entidad:
                        raise ValueError(f"No se encontró el grupo/foro '{forum_id_input}'. Asegúrate de haber ingresado un ID o enlace válido y de estar unido al grupo.")

                    from telethon.tl.functions.messages import GetForumTopicsRequest
                    topics_res = await client(GetForumTopicsRequest(
                        peer=entidad, offset_date=None, offset_id=0, offset_topic=0, limit=500
                    ))
                    return entidad, list(topics_res.topics)

                try:
                    entidad, t_list = run_async(leer_topics())
                    st.session_state.entidad_foro = entidad
                    st.session_state.topics_disponibles = t_list
                    st.success(f"✅ Conectado a: **{entidad.title}** | **{len(t_list)} Topics Encontrados**")
                except Exception as e:
                    st.error(f"❌ Error leyendo topics del foro: {e}")

    # Si hay topics cargados en sesión
    if st.session_state.topics_disponibles:
        st.markdown("---")
        st.markdown("### 🎯 Selección de Topics a Descargar")
        
        opciones_topics = {f"[{t.id}] {t.title}": t for t in st.session_state.topics_disponibles}
        
        col_s1, col_s2, col_s3 = st.columns([3, 1.5, 1.5])
        with col_s1:
            topics_seleccionados = st.multiselect(
                "Selecciona uno o varios Topics específicos (o déjalo vacío para procesar TODOS):",
                options=list(opciones_topics.keys()),
                placeholder="Elige los topics que te interesan..."
            )
        with col_s2:
            invertir_topics = st.checkbox("🔄 Invertir Orden (Últimos primero)", value=True)
        with col_s3:
            concurrencia_sel = st.select_slider(
                "⚡ Velocidad / Hilos:",
                options=[5, 10, 15, 20],
                value=10,
                help="Número de descargas simultáneas. Subir a 15-20 acelera la descarga."
            )

        if "cancelar_descarga" not in st.session_state:
            st.session_state.cancelar_descarga = False

        col_b1, col_b2, col_b3, col_b4 = st.columns(4)
        with col_b1:
            btn_analizar = st.button("🔍 PRE-ANÁLISIS Y TIEMPO", key="btn_analizar_topics")
        with col_b2:
            btn_descargar_sel = st.button("🎯 DESCARGAR SELECCIONADOS", key="btn_dl_sel")
        with col_b3:
            btn_descargar_todos = st.button("⚡ DESCARGAR TODOS", key="btn_dl_all")
        with col_b4:
            if st.session_state.cancelar_descarga:
                btn_reanudar = st.button("▶️ REANUDAR DESCARGA", key="btn_resume_dl")
                btn_pausar = False
            else:
                btn_pausar = st.button("🛑 PAUSAR DESCARGA", key="btn_stop_dl")
                btn_reanudar = False

        if btn_pausar:
            st.session_state.cancelar_descarga = True
            st.warning("🛑 Solicitud de pausa enviada. La descarga se detendrá en el próximo paso.")

        if btn_reanudar:
            st.session_state.cancelar_descarga = False
            st.success("▶️ Reanudando descarga...")

        # ----------------------------------------------------
        # OPCION: PRE-ANÁLISIS DE MULTIMEDIA & TIEMPO ESTIMADO
        # ----------------------------------------------------
        if btn_analizar:
            if topics_seleccionados:
                lista_target = [opciones_topics[k] for k in topics_seleccionados]
            else:
                lista_target = list(st.session_state.topics_disponibles)
            
            st.info(f"🔎 Ejecutando Pre-Análisis rápido de **{len(lista_target)}** Topic(s)... Por favor espera unos segundos.")
            
            entidad = st.session_state.entidad_foro or run_async(client.get_entity(int(forum_id_input.strip())))

            async def realizar_pre_analisis():
                detalles = []
                t_fotos, t_videos, t_otros, t_bytes = 0, 0, 0, 0

                for t in lista_target:
                    topic_id = t.id
                    topic_title = t.title
                    fotos, videos, otros, bytes_t = 0, 0, 0, 0

                    try:
                        async for msg in client.iter_messages(entidad, reply_to=topic_id):
                            if not msg.media:
                                continue
                            tipo = obtener_tipo_media(msg)
                            sz = getattr(msg.file, "size", 0) or 0
                            bytes_t += sz
                            if tipo == "photo":
                                fotos += 1
                            elif tipo == "video":
                                videos += 1
                            else:
                                otros += 1
                    except Exception:
                        pass

                    t_fotos += fotos
                    t_videos += videos
                    t_otros += otros
                    t_bytes += bytes_t

                    detalles.append({
                        "Topic": topic_title,
                        "Fotos 📷": fotos,
                        "Videos 🎥": videos,
                        "Otros 📄": otros,
                        "Total Archivos": fotos + videos + otros,
                        "Tamaño (MB)": round(bytes_t / (1024 * 1024), 2)
                    })

                return detalles, t_fotos, t_videos, t_otros, t_bytes

            try:
                detalles, t_fotos, t_videos, t_otros, t_bytes = run_async(realizar_pre_analisis())
                
                total_files = t_fotos + t_videos + t_otros
                total_mb = t_bytes / (1024 * 1024)
                total_gb = total_mb / 1024
                
                velocidad_est_mbs = max(3.0, concurrencia_sel * 1.2)
                tiempo_seg_est = total_mb / velocidad_est_mbs if velocidad_est_mbs > 0 else 0
                mins_est, segs_est = divmod(int(tiempo_seg_est), 60)
                
                with st.container():
                    st.markdown("### 📊 Resultado del Pre-Análisis Multimedia:")
                    st.info(f"📷 **Fotos**: {t_fotos} &nbsp;|&nbsp; 🎥 **Videos**: {t_videos} &nbsp;|&nbsp; 📄 **Otros**: {t_otros} &nbsp;|&nbsp; 💾 **Peso Total**: `{total_mb:.1f} MB` &nbsp;|&nbsp; ⏱️ **Tiempo Est.**: `{mins_est:02d}:{segs_est:02d} min` (@ {velocidad_est_mbs:.1f} MB/s)")
                    st.dataframe(pd.DataFrame(detalles), use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error durante el pre-análisis: {e}")

        # ----------------------------------------------------
        # EJECUCIÓN DE DESCARGA
        # ----------------------------------------------------
        if btn_descargar_todos or btn_descargar_sel or btn_reanudar:
            if btn_descargar_sel and not topics_seleccionados:
                st.warning("⚠️ No has seleccionado ningún topic en la lista. Selecciona al menos uno o usa 'DESCARGAR ABSOLUTAMENTE TODOS LOS TOPICS'.")
            else:
                establecer_concurrencia(concurrencia_sel)

                if btn_descargar_sel and topics_seleccionados:
                    lista_target = [opciones_topics[k] for k in topics_seleccionados]
                else:
                    lista_target = list(st.session_state.topics_disponibles)
                
                if invertir_topics:
                    lista_target.reverse()

                st.info(f"🚀 Iniciando descarga en paralelo de **{len(lista_target)}** Topic(s) con **{concurrencia_sel} Descargas Simultáneas**...")
            
                pbar_topics = st.progress(0)
                status_topic_box = st.empty()
                status_file_box = st.empty()
                
                entidad = st.session_state.entidad_foro or run_async(client.get_entity(int(forum_id_input.strip())))

                async def ejecutar_descarga_interactiva():
                    total_t = len(lista_target)
                    resumen = []

                    for idx, t in enumerate(lista_target, start=1):
                        if getattr(st.session_state, "cancelar_descarga", False):
                            try:
                                status_topic_box.warning("⏸️ Descarga pausada por el usuario. Puedes reanudar en cualquier momento.")
                            except Exception:
                                pass
                            st.session_state.cancelar_descarga = False
                            break

                        topic_title = t.title
                        topic_id = t.id
                        try:
                            status_topic_box.markdown(f"📂 **[{idx}/{total_t}] Procesando Topic:** `{topic_title}` (ID: {topic_id})")
                        except Exception:
                            pass

                        ok_count = 0
                        
                        last_upd = [0]
                        track_speed = {"t_last": time.time(), "bytes_last": 0, "smooth_spd": 0.0}

                        def callback_st(nombre_arch, current, total, ya_existia):
                            try:
                                t_now = time.time()
                                if ya_existia:
                                    status_file_box.caption(f"⚡ `[OMITIDO - YA EXISTÍA]` {nombre_arch}")
                                elif total and total > 0:
                                    dt = t_now - track_speed["t_last"]
                                    if dt > 0.3:
                                        d_bytes = current - track_speed["bytes_last"]
                                        inst_spd = (d_bytes / (1024 * 1024)) / dt if dt > 0 else 0
                                        if track_speed["smooth_spd"] == 0:
                                            track_speed["smooth_spd"] = inst_spd
                                        else:
                                            track_speed["smooth_spd"] = 0.7 * track_speed["smooth_spd"] + 0.3 * inst_spd
                                        track_speed["t_last"] = t_now
                                        track_speed["bytes_last"] = current

                                    if t_now - last_upd[0] > 0.4 or current == total:
                                        last_upd[0] = t_now
                                        pct = current * 100 / total
                                        mb_curr = current / (1024 * 1024)
                                        mb_tot = total / (1024 * 1024)
                                        spd = track_speed["smooth_spd"]
                                        
                                        rem_mb = mb_tot - mb_curr
                                        eta_str = "--:--"
                                        if spd > 0.1 and rem_mb > 0:
                                            eta_sec = int(rem_mb / spd)
                                            m_eta, s_eta = divmod(eta_sec, 60)
                                            eta_str = f"{m_eta:02d}:{s_eta:02d} seg"

                                        status_file_box.markdown(
                                            f"⬇️ **Descargando:** `{nombre_arch}` &nbsp;|&nbsp; **{pct:.1f}%** ({mb_curr:.1f} MB / {mb_tot:.1f} MB) &nbsp;|&nbsp; ⚡ **{spd:.1f} MB/s** &nbsp;|&nbsp; ⏱️ **Quedan:** `{eta_str}`"
                                        )
                            except Exception:
                                pass

                        mensajes_media = []
                        try:
                            async for msg in client.iter_messages(entidad, reply_to=topic_id):
                                if msg.media:
                                    mensajes_media.append(msg)
                        except Exception:
                            try:
                                async for msg in client.iter_messages(entidad, limit=200):
                                    if msg.media:
                                        reply = msg.reply_to
                                        top_id = (getattr(reply, "reply_to_top_id", None) or getattr(reply, "reply_to_msg_id", None)) if reply else None
                                        if top_id == topic_id or msg.id == topic_id:
                                            mensajes_media.append(msg)
                            except Exception:
                                pass

                        if mensajes_media:
                            tareas = [descargar_un_archivo(client, msg, topic_nombre=topic_title, callback_st=callback_st) for msg in mensajes_media]
                            resultados = await asyncio.gather(*tareas, return_exceptions=True)
                            for res in resultados:
                                if res and not isinstance(res, Exception):
                                    ok_count += 1
                        
                        resumen.append({"Topic": topic_title, "Archivos Descargados": ok_count})
                        try:
                            pbar_topics.progress(int(idx * 100 / total_t))
                        except Exception:
                            pass

                    return resumen

                try:
                    resumen = run_async(ejecutar_descarga_interactiva())
                    pbar_topics.progress(100)
                    status_topic_box.success("🎉 ¡Descarga de Topics seleccionados completada!")
                    status_file_box.empty()
                    st.dataframe(pd.DataFrame(resumen))
                except Exception as e:
                    import traceback
                    err_msg = str(e) or repr(e) or traceback.format_exc()
                    st.error(f"❌ Error en descarga: {err_msg}")

# ============================================================
# PESTAÑA 3: GOOGLE DRIVE TURBO UPLOADER (10GB+)
# ============================================================
with tab_gdrive:
    st.subheader("☁️ Subir a Google Drive (Fácil, Rápido y Sin Errores)")
    
    # ----------------------------------------------------
    # SECCIÓN 1: GOOGLE DRIVE PARA ESCRITORIO (RECOMENDADO)
    # ----------------------------------------------------
    st.markdown("### 💻 Método 1: Google Drive de la Computadora (100% Automático - 0 Errores)")
    st.write("Copia tus carpetas y videos descargados directamente al disco de Google Drive en tu PC. Google lo subirá automáticamente en segundo plano a la máxima velocidad de tu internet.")
    
    ruta_gdrive_detectada = detectar_google_drive_local()
    
    if ruta_gdrive_detectada:
        st.success(f"✅ **Google Drive Detectado en tu PC:** `{ruta_gdrive_detectada}`")
    else:
        st.info("ℹ️ Para que Google Drive aparezca como disco en tu PC, asegúrate de tener la app abierta e iniciada la sesión.")
        if st.button("📂 ABRIR APLICACIÓN DE GOOGLE DRIVE EN TU PC", use_container_width=True):
            abrir_app_google_drive()
            st.success("Abriendo Google Drive en tu Windows... Inicia sesión y luego recarga esta página.")
        
    gdrive_dest_custom = st.text_input("Ruta de destino en Google Drive de tu PC (Disco G: o carpeta):", value=ruta_gdrive_detectada if ruta_gdrive_detectada else r"G:\Mi unidad")
    
    downloads_dir = DOWNLOAD_FOLDER
    local_folders = []
    if os.path.exists(downloads_dir):
        for item in os.listdir(downloads_dir):
            item_path = os.path.join(downloads_dir, item)
            if os.path.isdir(item_path):
                local_folders.append(item)
                
    origen_tipo = st.radio(
        "¿Qué carpeta de tu PC quieres subir a Google Drive?",
        ["🤖 Carpeta descargada por el Bot (en downloads/)", "💻 Cualquier otra carpeta de mi PC (ej: Desktop, Disco E:, etc.)"],
        horizontal=True
    )
    
    if origen_tipo == "🤖 Carpeta descargada por el Bot (en downloads/)":
        if not local_folders:
            st.info("ℹ️ Aún no hay carpetas dentro de 'downloads'. Descarga algo primero en la Pestaña 1 o 2.")
            custom_folder_path_desk = downloads_dir
        else:
            selected_folder_desk = st.selectbox("Selecciona la carpeta descargada:", local_folders, key="select_gdrive_desk")
            custom_folder_path_desk = os.path.join(downloads_dir, selected_folder_desk)
    else:
        custom_folder_path_desk = st.text_input(
            "Pega aquí la ruta completa de la carpeta de tu PC que quieres subir a Google Drive:",
            value=r"C:\Users\LukGutierrez\Desktop\APP OSINT",
            placeholder=r"C:\Users\LukGutierrez\Desktop\APP OSINT  o  E:\MisVideos"
        )
        
    # Analizar carpeta seleccionada
    if custom_folder_path_desk and os.path.exists(custom_folder_path_desk):
        files_count = 0
        total_size_bytes = 0
        for root, _, files in os.walk(custom_folder_path_desk):
            for f in files:
                fp = os.path.join(root, f)
                if os.path.exists(fp):
                    files_count += 1
                    total_size_bytes += os.path.getsize(fp)
        
        st.write(f"📂 **Carpeta de origen:** `{custom_folder_path_desk}` &nbsp;|&nbsp; 📊 **Contenido analizado:** `{files_count}` archivo(s) ({total_size_bytes/(1024*1024):.1f} MB)")
    elif custom_folder_path_desk:
        st.warning(f"⚠️ La ruta `{custom_folder_path_desk}` aún no existe o no fue encontrada en tu PC.")
        
    if st.button("🚀 SINCRONIZAR CARPETA A GOOGLE DRIVE DE LA PC", type="primary", use_container_width=True):
        if not custom_folder_path_desk or not os.path.exists(custom_folder_path_desk):
            st.error("❌ La carpeta de origen no existe.")
        elif not os.path.exists(gdrive_dest_custom):
            st.error(f"❌ La ruta de destino `{gdrive_dest_custom}` no existe en tu PC. Abre la app de Google Drive e inicia sesión para que aparezca el Disco G:\\.")
        else:
            prog_bar = st.progress(0.0)
            status_metric_box = st.empty()
            status_detail_box = st.empty()
            
            def callback_ui(fname, cur_idx, total_idx, bytes_done, bytes_total, speed, eta):
                p = bytes_done / bytes_total if bytes_total > 0 else 0.0
                prog_bar.progress(min(max(p, 0.0), 1.0))
                
                mb_done = bytes_done / (1024 * 1024)
                mb_total = bytes_total / (1024 * 1024)
                pct = p * 100
                
                if eta >= 60:
                    mins = int(eta // 60)
                    secs = int(eta % 60)
                    eta_str = f"{mins}m {secs}s"
                else:
                    eta_str = f"{int(eta)}s"
                    
                status_metric_box.markdown(f"""
                <div style="background-color: #0F172A; border: 1px solid #00F0FF; border-radius: 6px; padding: 12px; margin: 10px 0; display: flex; justify-content: space-around; text-align: center;">
                    <div><span style="color: #94A3B8; font-size: 0.85rem;">⚡ VELOCIDAD</span><br><b style="color: #00FF41; font-size: 1.3rem;">{speed:.2f} MB/s</b></div>
                    <div><span style="color: #94A3B8; font-size: 0.85rem;">⏱️ TIEMPO RESTANTE</span><br><b style="color: #FFE600; font-size: 1.3rem;">{eta_str}</b></div>
                    <div><span style="color: #94A3B8; font-size: 0.85rem;">📊 TRANSFERIDO</span><br><b style="color: #00F0FF; font-size: 1.3rem;">{mb_done:.1f} / {mb_total:.1f} MB ({pct:.1f}%)</b></div>
                </div>
                """, unsafe_allow_html=True)
                
                status_detail_box.markdown(f"📄 **Copiando archivo [{cur_idx}/{total_idx}]:** `{fname}`")

            ok, res_path = copiar_a_google_drive_local(
                custom_folder_path_desk,
                carpeta_destino_nombre=os.path.basename(custom_folder_path_desk),
                destino_custom=gdrive_dest_custom,
                callback_progress=callback_ui
            )
            
            prog_bar.progress(1.0)
            if ok:
                st.balloons()
                st.success(f"🎉 ¡CARPETA COPIADA CON ÉXITO A GOOGLE DRIVE! `{res_path}`")
                st.info("⚡ La aplicación oficial de Google Drive ya está subiendo tus archivos a la nube a máxima velocidad en segundo plano.")
            else:
                st.error(f"❌ Error: {res_path}")
                    
    st.markdown("---")
    
    # ----------------------------------------------------
    # SECCIÓN 2: GOOGLE DRIVE POR API (OPCIONAL)
    # ----------------------------------------------------
    with st.expander("☁️ Método 2: Google Drive por API Web (Opcional)", expanded=False):
        service, status_msg = obtener_servicio_gdrive(interactive=False)
        
        if not service:
            st.warning("⚠️ **Estado:** Tu cuenta de Google Drive API aún no está autorizada.")
            auth_url, auth_err = generar_url_autorizacion()
            
            if auth_url:
                st.markdown(f"""
                <div style="background-color: #1E293B; border: 2px solid #00FF41; border-radius: 8px; padding: 20px; text-align: center; margin: 15px 0;">
                    <h3 style="color: #00FF41; margin-top: 0;">🔑 INICIAR SESIÓN EN GOOGLE</h3>
                    <p style="color: #E2E8F0; font-size: 1.05rem;">Se abrirá Google en una pestaña nueva. Selecciona tu cuenta y haz clic en <b>Permitir</b>.</p>
                    <a href="{auth_url}" target="_blank" style="display: inline-block; background-color: #00FF41; color: #050505; font-weight: bold; font-size: 1.2rem; padding: 14px 28px; border-radius: 6px; text-decoration: none; margin-top: 10px; box-shadow: 0 0 15px rgba(0, 255, 65, 0.5);">
                        🚀 CLIC AQUÍ PARA INICIAR SESIÓN EN GOOGLE
                    </a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ Conectado a Google Drive API.")
            if st.button("🚀 SUBIR CARPETA DIRECTA POR API", key="btn_up_api"):
                st.info("Subida por API iniciada.")

# ============================================================
# PESTAÑA 4: CENTRO OSINT
# ============================================================
with tab_osint:
    st.subheader("🕵️ Centro de Inteligencia OSINT & Análisis de Objetivos")
    st.write("Inspecciona metadatos de canales, grupos, usuarios, busca mensajes clave y lista tus chats unidos con sus IDs numéricos.")

    # --------------------------------------------------------
    # SECCIÓN: INSPECTOR DE CHATS Y GRUPOS UNIDOS
    # --------------------------------------------------------
    with st.expander("📋 VISOR DE MIS GRUPOS Y CHATS UNIDOS (Obtener IDs Exactos)", expanded=False):
        st.write("Obtén los títulos e IDs numéricos de todos los canales y foros donde estás unido:")
        if st.button("🔄 CARGAR / REFRESCAR MIS GRUPOS", key="btn_load_my_chats"):
            with st.spinner("⏳ Leyendo diálogos y canales..."):
                try:
                    mis_chats = run_async(listar_mis_chats(client))
                    st.session_state.mis_chats_list = mis_chats
                    st.success(f"✅ Se encontraron **{len(mis_chats)}** chats/grupos en tu cuenta.")
                except Exception as e:
                    st.error(f"❌ Error leyendo chats: {e}")

        if "mis_chats_list" in st.session_state and st.session_state.mis_chats_list:
            df_chats = pd.DataFrame(st.session_state.mis_chats_list)
            st.dataframe(df_chats, use_container_width=True)

    st.markdown("---")
    
    osint_target = st.text_input("🎯 Objetivo OSINT (@username, enlace o ID):", placeholder="@usuario  o  https://t.me/canal  o  -1004340179079")
    
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        btn_info = st.button("📋 Ficha de Información (/info)")
    with col_b:
        btn_stats = st.button("📈 Estadísticas (/stats)")
    with col_c:
        btn_recent = st.button("💬 Mensajes Recientes (/recent)")
    with col_d:
        btn_members = st.button("👥 Miembros (/members)")

    if btn_info and osint_target.strip():
        with st.spinner("🔎 Consultando metadatos..."):
            async def run_info():
                await client.start()
                ent = await obtener_entidad_segura(client, osint_target)
                if not ent:
                    return f"❌ No se encontró la entidad para '{osint_target}'. Asegúrate de haber ingresado un @username válido o el ID numérico de un grupo donde estés unido."
                
                from telethon.tl.types import User
                if isinstance(ent, User):
                    return await info_usuario(client, ent)
                return await info_canal(client, ent)

            try:
                res = run_async(run_info())
                st.markdown(res)
            except Exception as e:
                st.error(f"❌ Error: {e}")

    if btn_stats and osint_target.strip():
        with st.spinner("📊 Analizando patrones del canal..."):
            async def run_stats():
                await client.start()
                ent = await obtener_entidad_segura(client, osint_target)
                if not ent:
                    return f"❌ No se encontró la entidad para '{osint_target}'."
                return await stats_canal(client, ent)

            try:
                res = run_async(run_stats())
                st.markdown(res)
            except Exception as e:
                st.error(f"❌ Error: {e}")

    if btn_recent and osint_target.strip():
        with st.spinner("💬 Leyendo historial reciente..."):
            async def run_recent():
                await client.start()
                ent = await obtener_entidad_segura(client, osint_target)
                if not ent:
                    return f"❌ No se encontró la entidad para '{osint_target}'."
                return await mensajes_recientes(client, ent, limit=15)

            try:
                res = run_async(run_recent())
                st.markdown(res)
            except Exception as e:
                st.error(f"❌ Error: {e}")

    if btn_members and osint_target.strip():
        with st.spinner("👥 Extrayendo lista de participantes..."):
            async def run_members():
                await client.start()
                ent = await obtener_entidad_segura(client, osint_target)
                if not ent:
                    return f"❌ No se encontró la entidad para '{osint_target}'."
                return await listar_participantes(client, ent, limit=100)

            try:
                res = run_async(run_members())
                st.markdown(res)
            except Exception as e:
                st.error(f"❌ Error: {e}")

    st.markdown("---")
    st.subheader("🔍 Búsqueda OSINT de Palabras Clave en Mensajes")
    kw_input = st.text_input("🔑 Término o Palabra Clave a Buscar (ej: CBU, DNI, teléfono, filtro, admin):", placeholder="Ingresa la palabra clave...")
    btn_search_kw = st.button("🔎 EJECUTAR BÚSQUEDA OSINT", key="btn_kw_search")

    if btn_search_kw and osint_target.strip() and kw_input.strip():
        with st.spinner(f"🔍 Buscando '{kw_input}' en {osint_target}..."):
            async def run_search_kw():
                await client.start()
                ent = await obtener_entidad_segura(client, osint_target)
                if not ent:
                    return None
                return await buscar_palabras_clave(client, ent, kw_input.strip(), limit=50)

            try:
                res_kw = run_async(run_search_kw())
                if res_kw is None:
                    st.error(f"❌ No se encontró el grupo/canal '{osint_target}'. Verifica el ID o @username.")
                elif not res_kw:
                    st.warning(f"⚠️ No se encontraron mensajes con el término '{kw_input}'.")
                else:
                    st.success(f"✅ Se encontraron **{len(res_kw)}** coincidencia(s).")
                    st.dataframe(pd.DataFrame(res_kw), use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error en búsqueda: {e}")

# ============================================================
# PESTAÑA 4: MANUAL DE COMANDOS
# ============================================================
with tab_guide:
    st.subheader("📖 Manual de Comandos del Bot de Telegram")
    st.write("Explicación sencilla de cada comando disponible para usar en la app de Telegram.")
    
    comandos = [
        {"Comando": "/start", "Uso": "/start", "Explicación": "Inicia el bot y muestra el mensaje de bienvenida con el menú rápido."},
        {"Comando": "/help", "Uso": "/help", "Explicación": "Muestra la guía completa de instrucciones y comandos en Telegram."},
        {"Comando": "/dl", "Uso": "/dl <enlace>", "Explicación": "Descarga un archivo multimedia específico a partir del enlace de su mensaje."},
        {"Comando": "/batch", "Uso": "/batch <enlace> [cantidad]", "Explicación": "Descarga un lote de los últimos N archivos multimedia del canal o grupo."},
        {"Comando": "/info", "Uso": "/info <enlace_o_username>", "Explicación": "Extrae la ficha de inteligencia (OSINT): ID, fecha de creación, chats en común y flags."},
        {"Comando": "/stats", "Uso": "/stats <enlace>", "Explicación": "Analiza los hábitos del canal: distribución de fotos/videos, días de mayor actividad y horas pico."},
        {"Comando": "/mygroups", "Uso": "/mygroups", "Explicación": "Lista todos los grupos y canales a los que estás unido mostrando sus IDs numéricos negativos."},
        {"Comando": "/topics", "Uso": "/topics <group_id>", "Explicación": "Lista todos los temas (topics) disponibles dentro de un grupo con formato de Foro."},
        {"Comando": "/alltopics", "Uso": "/alltopics <group_id>", "Explicación": "Descarga automáticamente todo el contenido del foro creando una carpeta organizada por Topic."},
        {"Comando": "/recent", "Uso": "/recent <enlace> [cantidad]", "Explicación": "Muestra los textos de los mensajes más recientes publicados en el chat."},
        {"Comando": "/participants", "Uso": "/participants <enlace>", "Explicación": "Extrae el listado de miembros y usuarios participantes del grupo."},
    ]
    
    for c in comandos:
        st.markdown(f"""
        <div class="command-card">
            <div class="command-name">⚡ {c['Comando']} &nbsp;&nbsp;<code style="color: #FFE600;">{c['Uso']}</code></div>
            <div class="command-desc">{c['Explicación']}</div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# PESTAÑA 5: CONFIGURACIÓN & PROXIES
# ============================================================
with tab_settings:
    st.subheader("⚙️ Panel de Control, Deduplicación & Proxies")
    
    st.markdown("### 🔐 Estado del Sistema de Deduplicación por Hash")
    stats_dedup = obtener_stats_dedup()
    col_d1, col_d2 = st.columns(2)
    col_d1.metric("Archivos Registrados por Hash", f"{stats_dedup['total_archivos']} archivos")
    col_d2.metric("Espacio Total Registrado", f"{stats_dedup['total_mb']} MB")
    
    st.markdown("---")
    st.markdown("### 🛡️ Configuración de Proxies (SOCKS5 / MTProto)")
    st.write("Si necesitas descargar terabytes de información sin exponer tu IP de red, configura un servidor proxy.")
    
    p_enabled = st.checkbox("Habilitar Proxy", value=False)
    p_type = st.selectbox("Tipo de Proxy:", ["SOCKS5", "SOCKS4", "HTTP", "MTPROTO"])
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        p_host = st.text_input("Host / IP del Proxy:", value="127.0.0.1")
    with col_p2:
        p_port = st.number_input("Puerto:", value=1080)

# Footer estético
st.markdown("""
<br><hr>
<div style="text-align: center; color: #8B949E; font-size: 0.9rem;">
    TELEGRAM OSINT RECON MATRIX &bull; SYSTEM ENGINE &bull; 
    <span style="color: #FFE600; font-weight: bold;">CREADO POR @lukgtz</span>
</div>
""", unsafe_allow_html=True)
