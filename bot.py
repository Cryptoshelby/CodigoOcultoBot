import os
import logging
import json
import threading
import requests
import random
import feedparser
from bs4 import BeautifulSoup
from flask import Flask
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from datetime import datetime, timedelta

TOKEN = "8991788772:AAEy4xMXBTlhr4odaVXN1DaSX1CbfMtlxEU"
CHANNEL_ID = "-1003948185788"

logging.basicConfig(level=logging.INFO)
ARCHIVO_ESTADO = "estado_posts.json"
ARCHIVO_REPORTADOS = "links_reportados.json"

# ========== CONFIGURACIÓN DE BÚSQUEDA ==========
LIMITE_REACCIONES = 10  # Cambia a 50 después

# Fuentes RSS de contenido
FUENTES = {
    "ia_noticias": "https://www.artificialintelligence-news.com/feed/",
    "tech_noticias": "https://www.xataka.com/feed",
    "reddit_ia": "https://www.reddit.com/r/ChatGPT/.rss",
    "reddit_trucos": "https://www.reddit.com/r/AndroidTips/.rss",
    "youtube_ia": "https://www.youtube.com/feeds/videos.xml?channel_id=UCfJgKxSJKvKQ8q9yX5ZG0JA",  # IA channel
    "github_trending": "https://github.com/trending/python.rss",
}

# Palabras clave para filtrar
PALABRAS_CLAVE = [
    "jailbreak", "chatgpt", "uncensored", "mod", "premium", "gratis",
    "secreto", "truco", "oculto", "deepweb", "darkweb", "hack",
    "gratuito", "desbloqueado", "viral", "nadie sabe", "filtrado",
    "android", "whatsapp", "youtube premium", "spotify mod"
]

# URLs de scraping para apps mod
MOD_SITES = [
    "https://modyolo.com/",
    "https://rexdl.com/",
    "https://apkdone.com/mod-apk/"
]

# URLs de deep web
DEEP_WEB_LINKS = [
    "Buscador Yandex (no rastrea tu IP): https://yandex.com",
    "Searx (100+ motores, sin logs): https://searx.space",
    "Wayback Machine (páginas borradas): https://archive.org",
    "Tor Metrics: https://metrics.torproject.org",
]

def cargar_json(archivo):
    try:
        with open(archivo, 'r') as f:
            return json.load(f)
    except:
        return {}

def guardar_json(archivo, datos):
    with open(archivo, 'w') as f:
        json.dump(datos, f)

def buscar_noticias_rss():
    """Busca noticias de las fuentes RSS"""
    resultados = []
    for nombre, url in FUENTES.items():
        try:
            feed = feedparser.parse(url)
            for entrada in feed.entries[:3]:
                for palabra in PALABRAS_CLAVE:
                    if palabra.lower() in (entrada.title + entrada.description).lower():
                        resultados.append({
                            "titulo": entrada.title,
                            "descripcion": entrada.description[:200],
                            "link": entrada.link,
                            "fuente": nombre,
                            "tipo": "noticia"
                        })
                        break
        except:
            continue
    return resultados[:5]

def buscar_apps_mod():
    """Busca apps mod de sitios de APK (simulado)"""
    mods = [
        "YouTube ReVanced - Sin anuncios y background play",
        "Spotify Premium MOD - Todas las canciones gratis",
        "CapCut PRO - Todos los efectos desbloqueados",
        "TikTok MOD - Sin publicidad y descarga de videos",
        "WhatsApp Plus - Funciones ocultas de privacidad"
    ]
    return [{"titulo": m, "tipo": "mod", "link": "Busca en Telegram @CodigoOculto"} for m in mods]

def buscar_trucos():
    """Busca trucos de tecnología"""
    trucos = [
        "WhatsApp: Activa el modo 'escritura invisible' poniendo `*texto*`",
        "Android: Código `*#*#4636#*#*` para menú de prueba oculto",
        "YouTube: Escribe `?v=` y borra todo para ver solo el video",
        "Google: `site:codigooculto.com` para buscar en específico",
        "Windows: `Ctrl + Shift + V` pega sin formato"
    ]
    return [{"titulo": t, "tipo": "truco"} for t in trucos]

def buscar_contenido():
    """Junta todo el contenido de todas las fuentes"""
    todo = []
    todo.extend(buscar_noticias_rss())
    todo.extend(buscar_apps_mod())
    todo.extend(buscar_trucos())
    
    # Mezclar para que no sea siempre el mismo orden
    random.shuffle(todo)
    return todo[:5]  # Máximo 5 posts en la cadena

# Generar cadena de contenido automáticamente
def generar_cadena_contenido():
    contenido_nuevo = buscar_contenido()
    cadena = []
    for idx, item in enumerate(contentido_nuevo):
        texto = f"""
{'🤖 IA' if item.get('tipo') == 'noticia' else '💀 TRUCO' if item.get('tipo') == 'truco' else '📱 APP MOD'} - Parte {idx+1}

📌 **{item.get('titulo', 'Novedad')}**

{item.get('descripcion', 'Descubre este contenido secreto')}

🔗 {item.get('link', 'Comparte y reacciona para más')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ **REACCIONA CON CUALQUIER EMOJI**

🎁 **AL LLEGAR A {LIMITE_REACCIONES} REACCIONES:**
- Publico más contenido como este
- Material exclusivo para quienes reaccionan

👥 **INVITA AMIGOS** a @CodigoOculto

📢 **CONTENIDO REAL** buscado automáticamente de la web
"""
        cadena.append({"id": idx+1, "tipo": "auto", "texto": texto})
    
    # Si no se encontró nada, usar contenido de respaldo
    if not cadena:
        cadena = [
            {"id": 1, "tipo": "auto", "texto": "🤖 **IA SIN FILTROS**\n\nNuevo jailbreak para ChatGPT encontrado en Reddit.\n\n⭐ Reacciona para más contenido automático.\n\n👥 @CodigoOculto"},
            {"id": 2, "tipo": "auto", "texto": "💀 **TRUCO OCULTO**\n\nCódigo secreto de WhatsApp que nadie conoce.\n\n⭐ Reacciona para más.\n\n👥 @CodigoOculto"},
            {"id": 3, "tipo": "auto", "texto": "📱 **APP MOD DEL DÍA**\n\nYouTube ReVanced actualizado.\n\n⭐ Reacciona para más mods.\n\n👥 @CodigoOculto"},
        ]
    
    return cadena

# ========== BOT PRINCIPAL ==========
estado = cargar_json(ARCHIVO_ESTADO)
CADENA_ACTUAL = estado.get("cadena", generar_cadena_contenido())

def cargar_estado():
    return cargar_json(ARCHIVO_ESTADO)

def guardar_estado(estado):
    guardar_json(ARCHIVO_ESTADO, estado)

def publicar_siguiente(context):
    estado = cargar_estado()
    siguiente_id = estado.get("ultimo_post_id", 0) + 1
    
    if siguiente_id <= len(CADENA_ACTUAL):
        contenido = CADENA_ACTUAL[siguiente_id - 1]
        
        mensaje = context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=contenido["texto"],
            parse_mode='Markdown'
        )
        
        estado["ultimo_post_id"] = siguiente_id
        estado["message_id_actual"] = mensaje.message_id
        estado["reacciones_actuales"] = 0
        guardar_estado(estado)
        logging.info(f"✅ Publicado Post {siguiente_id}")

def start(update, context):
    update.message.reply_text(
        "🔓 **BOT ACTIVO**\n\n"
        "📡 @CodigoOculto busca y publica contenido AUTOMÁTICAMENTE\n\n"
        "✅ IA sin filtros (de Reddit y noticias)\n"
        "✅ Trucos que NADIE sabe\n"
        "✅ Apps MOD actualizadas\n"
        "✅ Deep web ligera\n"
        "✅ Novedades de la web\n\n"
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
        logging.info(f"⭐ Reacciones en Post {estado.get('ultimo_post_id')}: {nueva_cuenta}")
        
        if nueva_cuenta >= LIMITE_REACCIONES:
            logging.info("🎉 Límite alcanzado! Publicando siguiente contenido...")
            publicar_siguiente(context)

def actualizar_contenido(context):
    """Actualiza la cadena de contenido cada 24 horas"""
    global CADENA_ACTUAL
    logging.info("🔄 Actualizando contenido desde la web...")
    CADENA_ACTUAL = generar_cadena_contenido()
    guardar_estado(cargar_estado())  # Reinicia el progreso opcionalmente

# ========== SERVIDOR WEB PARA RENDER ==========
web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot @CodigoOculto funcionando con búsqueda automática 24/7"

@web_app.route('/health')
def health():
    return "OK", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

def main():
    # Servidor web
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()
    logging.info("🌐 Servidor web iniciado")
    
    # Bot
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.all, manejar_reacciones))
    
    # Actualizar contenido cada 24 horas
    updater.job_queue.run_repeating(actualizar_contenido, interval=86400, first=10)
    
    # Publicar primer contenido
    estado_local = cargar_estado()
    if estado_local.get("ultimo_post_id", 0) == 0:
        updater.job_queue.run_once(publicar_siguiente, 5, context=updater)
    
    logging.info("🚀 Bot iniciado con búsqueda automática de contenido")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
