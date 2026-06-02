import os
import logging
import json
import threading
import random
import requests
import feedparser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from flask import Flask
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

TOKEN = "8991788772:AAEy4xMXBTlhr4odaVXN1DaSX1CbfMtlxEU"
CHANNEL_ID = "-1003948185788"
LIMITE_REACCIONES = 10

logging.basicConfig(level=logging.INFO)
ARCHIVO_ESTADO = "estado_posts.json"

# URLs para buscar contenido automático
FUENTES_RSS = {
    "ia_noticias": "https://www.artificialintelligence-news.com/feed/",
    "tecnologia": "https://www.xataka.com/feed",
    "reddit_ia": "https://www.reddit.com/r/ChatGPT/.rss",
    "reddit_trucos": "https://www.reddit.com/r/lifehacks/.rss",
    "reddit_mods": "https://www.reddit.com/r/ApksApps/.rss",
}

PALABRAS_CLAVE = ["jailbreak", "chatgpt", "mod", "premium", "gratis", "secreto", "truco", "oculto", "deepweb", "hack", "desbloqueado", "gratuito"]

def buscar_noticias():
    resultados = []
    for nombre, url in FUENTES_RSS.items():
        try:
            feed = feedparser.parse(url)
            for entrada in feed.entries[:5]:
                texto_completo = (entrada.title + " " + entrada.get("description", "")).lower()
                for palabra in PALABRAS_CLAVE:
                    if palabra in texto_completo:
                        resultados.append({
                            "titulo": entrada.title,
                            "descripcion": entrada.get("description", "")[:250],
                            "link": entrada.link,
                            "fuente": nombre
                        })
                        break
        except:
            continue
    return resultados[:5]

def buscar_apps_mod():
    mods_conocidos = [
        {"titulo": "YouTube ReVanced v19.47.53", "desc": "Sin anuncios, background play, SponsorBlock", "link": "https://revanced.net"},
        {"titulo": "Spotify Premium Mod", "desc": "Todas las canciones gratis, sin anuncios", "link": "https://spotifypremiummod.com"},
        {"titulo": "CapCut PRO Desbloqueado", "desc": "Todos los efectos y filtros premium gratis", "link": "https://capcutmod.com"},
        {"titulo": "TikTok MOD", "desc": "Sin publicidad, descarga de videos sin marca", "link": "https://tiktokmod.com"},
        {"titulo": "WhatsApp Plus", "desc": "Funciones ocultas de privacidad y personalización", "link": "https://whatsappplus.com"},
    ]
    return random.sample(mods_conocidos, 3)

def buscar_trucos_web():
    trucos = [
        "WhatsApp: Escribe *texto* para negritas, _texto_ para cursiva, ~texto~ para tachado",
        "Android: Marca *#*#4636#*#* para menú de prueba oculto",
        "YouTube: Escribe ?v= y borra todo para ver solo el video",
        "Google: Usa 'site:dominio.com' para buscar en un sitio específico",
        "Windows: Ctrl + Shift + V pega sin formato",
        "iPhone: Desliza el dedo por la barra espaciadora para mover el cursor",
        "Gmail: Añade +palabra a tu correo para crear filtros automáticos",
        "Instagram: Guarda borradores ilimitados sin publicar",
    ]
    return random.sample(trucos, 3)

def buscar_deepweb():
    enlaces = [
        "🌐 Yandex.com - Buscador ruso que NO filtra resultados políticos",
        "🌐 Searx.space - Agrega 100+ motores de búsqueda, sin rastreo de IP",
        "🌐 Archive.org - Recupera páginas web BORRADAS de Internet",
        "🌐 DuckDuckGo - Buscador que NO guarda tu historial",
        "🌐 Startpage.com - Resultados de Google sin ser rastreado",
    ]
    return random.sample(enlaces, 2)

def generar_contenido_automatico():
    contenido = []
    
    # Noticias IA
    for noticia in buscar_noticias():
        contenido.append({
            "tipo": "🤖 NOVEDAD IA",
            "texto": f"""🤖 **IA SIN FILTROS** - {noticia['titulo']}

📌 {noticia['descripcion']}

🔗 Fuente: {noticia['link']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ **REACCIONA CON CUALQUIER EMOJI**

🎁 **AL LLEGAR A {LIMITE_REACCIONES} REACCIONES:**
- MÁS contenido como este

👥 **INVITA AMIGOS** a @CodigoOculto"""
        })
    
    # Apps MOD
    for mod in buscar_apps_mod():
        contenido.append({
            "tipo": "📱 APP MOD",
            "texto": f"""📱 **APP MOD ACTUALIZADA** - {mod['titulo']}

✅ {mod['desc']}

🔗 Descarga: {mod['link']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ **REACCIONA PARA MÁS MODS**

👥 @CodigoOculto"""
        })
    
    # Trucos
    for truco in buscar_trucos_web():
        contenido.append({
            "tipo": "💀 TRUCO QUE NADIE SABE",
            "texto": f"""💀 **TRUCO OCULTO**

{truco}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ **REACCIONA PARA MÁS TRUCOS**

👥 @CodigoOculto"""
        })
    
    # Deep web
    for deep in buscar_deepweb():
        contenido.append({
            "tipo": "🕳️ DEEP WEB",
            "texto": f"""🕳️ **DEEP WEB LIGERA**

{deep}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ **REACCIONA PARA MÁS ENLACES**

👥 @CodigoOculto"""
        })
    
    random.shuffle(contenido)
    return contenido[:8]

CADENA_CONTENIDO = generar_contenido_automatico()

def cargar_estado():
    try:
        with open(ARCHIVO_ESTADO, 'r') as f:
            return json.load(f)
    except:
        return {"ultimo_post_id": 0, "message_id_actual": None, "reacciones_actuales": 0}

def guardar_estado(estado):
    with open(ARCHIVO_ESTADO, 'w') as f:
        json.dump(estado, f)

def publicar_siguiente(context):
    global CADENA_CONTENIDO
    estado = cargar_estado()
    siguiente_id = estado["ultimo_post_id"] + 1
    
    if siguiente_id > len(CADENA_CONTENIDO):
        CADENA_CONTENIDO = generar_contenido_automatico()
        estado = cargar_estado()
        estado["ultimo_post_id"] = 0
        estado["message_id_actual"] = None
        estado["reacciones_actuales"] = 0
        guardar_estado(estado)
        siguiente_id = 1
    
    contenido = CADENA_CONTENIDO[siguiente_id - 1]
    mensaje = context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=contenido["texto"],
        parse_mode='Markdown'
    )
    estado["ultimo_post_id"] = siguiente_id
    estado["message_id_actual"] = mensaje.message_id
    estado["reacciones_actuales"] = 0
    guardar_estado(estado)
    logging.info(f"✅ Publicado Post {siguiente_id} - {contenido['tipo']}")

def start(update, context):
    update.message.reply_text(
        "🔓 **BOT ACTIVO**\n\n"
        "📡 @CodigoOculto busca y publica contenido AUTOMÁTICO\n\n"
        "✅ IA sin filtros (noticias y Reddit)\n"
        "✅ Apps MOD actualizadas\n"
        "✅ Trucos que NADIE sabe\n"
        "✅ Deep web ligera\n\n"
        "⭐ **REACCIONA EN CUALQUIER POST**\n\n"
        "👥 **INVITA AMIGOS** a @CodigoOculto"
    )

def manejar_reacciones(update, context):
    update_obj = update.message_reaction
    if not update_obj:
        return
    
    message_id = update_obj.message_id
    chat_id = str(update_obj.chat.id)
    
    if chat_id != CHANNEL_ID:
        return
    
    estado = cargar_estado()
    
    if message_id == estado.get("message_id_actual"):
        nueva_cuenta = update_obj.reaction_count
        estado["reacciones_actuales"] = nueva_cuenta
        guardar_estado(estado)
        logging.info(f"⭐ Reacciones en Post {estado['ultimo_post_id']}: {nueva_cuenta}")
        
        if nueva_cuenta >= LIMITE_REACCIONES:
            logging.info("🎉 Límite alcanzado! Publicando siguiente contenido...")
            publicar_siguiente(context)

def actualizar_contenido(context):
    global CADENA_CONTENIDO
    logging.info("🔄 Actualizando contenido desde la web...")
    CADENA_CONTENIDO = generar_contenido_automatico()
    estado = cargar_estado()
    estado["ultimo_post_id"] = 0
    estado["message_id_actual"] = None
    estado["reacciones_actuales"] = 0
    guardar_estado(estado)

web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot @CodigoOculto funcionando 24/7"

@web_app.route('/health')
def health():
    return "OK", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

def main():
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()
    logging.info("🌐 Servidor web iniciado")
    
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.all, manejar_reacciones))
    
    updater.job_queue.run_repeating(actualizar_contenido, interval=86400, first=10)
    
    estado = cargar_estado()
    if estado["ultimo_post_id"] == 0:
        updater.job_queue.run_once(publicar_siguiente, 5, context=updater)
    
    logging.info("🚀 Bot iniciado con búsqueda automática de contenido")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
