import os
import logging
import json
import threading
import random
import requests
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

TOKEN = "8991788772:AAEy4xMXBTlhr4odaVXN1DaSX1CbfMtlxEU"
CHANNEL_ID = "-1003948185788"
CHANNEL_URL = "https://t.me/CodigoOcultoTech"
CHANNEL_USERNAME = "@CodigoOcultoTech"
HORAS_PUBLICACION = 2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
ARCHIVO_ESTADO = "estado_posts.json"
ENLACES_USADOS = "enlaces_usados.json"
ARCHIVO_STATS = "stats.json"

FUENTES_RSS = {
    "Inteligencia Artificial": "https://www.artificialintelligence-news.com/feed/",
    "Tecnología": "https://www.xataka.com/feed",
    "Ciencia": "https://www.bbc.com/mundo/ciencia/tecnologia/index.xml",
    "Hacks": "https://lifehacker.com/rss",
    "Android": "https://www.androidpolice.com/feed",
    "Apps MOD": "https://www.reddit.com/r/ApksApps/.rss",
    "ChatGPT": "https://www.reddit.com/r/ChatGPT/.rss",
    "Lifehacks": "https://www.reddit.com/r/lifehacks/.rss",
    "Deep Web": "https://www.reddit.com/r/deepweb/.rss",
    "Privacidad": "https://www.reddit.com/r/privacidad/.rss",
}

PALABRAS_CLAVE = [
    "jailbreak", "chatgpt", "uncensored", "mod", "premium", "gratis",
    "secreto", "truco", "oculto", "deepweb", "darkweb", "hack", "gratuito",
    "desbloqueado", "viral", "nadie sabe", "filtrado", "android", "whatsapp",
    "youtube", "spotify", "apk", "modded", "crack", "tutorial", "como"
]

def cargar_json(archivo):
    try:
        with open(archivo, 'r') as f:
            return json.load(f)
    except:
        if archivo == ARCHIVO_STATS:
            return {"posts_publicados": 0, "reacciones_totales": 0, "inicio": datetime.now().isoformat()}
        return {} if archivo == ENLACES_USADOS else {"ultimo_post_id": 0, "reacciones_actuales": 0}

def guardar_json(archivo, datos):
    with open(archivo, 'w') as f:
        json.dump(datos, f)

def enlace_ya_usado(url):
    usados = cargar_json(ENLACES_USADOS)
    if url in usados:
        return True
    usados[url] = datetime.now().isoformat()
    guardar_json(ENLACES_USADOS, usados)
    return False

def buscar_noticias():
    resultados = []
    for fuente, url in FUENTES_RSS.items():
        try:
            feed = feedparser.parse(url)
            for entrada in feed.entries[:3]:
                texto = (entrada.title + " " + entrada.get("description", "")).lower()
                if any(palabra in texto for palabra in PALABRAS_CLAVE):
                    if not enlace_ya_usado(entrada.link):
                        resultados.append({
                            "tipo": "📰 NOTICIA",
                            "fuente": fuente,
                            "titulo": entrada.title,
                            "texto": entrada.get("description", "")[:300],
                            "link": entrada.link,
                        })
        except:
            continue
    return resultados[:3]

def buscar_videos_youtube():
    resultados = []
    try:
        from youtubesearchpython import VideosSearch
        busquedas = ["trucos android", "apps mod", "ia jailbreak", "whatsapp secreto", "deepweb tutorial"]
        busqueda = random.choice(busquedas)
        videosSearch = VideosSearch(busqueda, limit=2)
        resultados_busqueda = videosSearch.result()
        for video in resultados_busqueda.get('result', []):
            if not enlace_ya_usado(video['link']):
                resultados.append({
                    "tipo": "🎬 VIDEO",
                    "titulo": video['title'],
                    "texto": video.get('description', '')[:200],
                    "link": video['link'],
                    "duracion": video.get('duration', 'N/A')
                })
    except:
        pass
    return resultados[:1]

def buscar_imagenes():
    resultados = []
    busquedas = ["tecnologia secreta", "hack android", "ia future", "deepweb", "mod apk"]
    busqueda = random.choice(busquedas)
    try:
        url = f"https://www.bing.com/images/search?q={busqueda.replace(' ', '+')}&first=1"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        imagenes = soup.find_all('img', limit=3)
        for img in imagenes:
            img_url = img.get('src')
            if img_url and img_url.startswith('http') and not enlace_ya_usado(img_url):
                resultados.append({
                    "tipo": "🖼️ IMAGEN",
                    "titulo": f"Imagen sobre {busqueda}",
                    "link": img_url,
                    "texto": f"**{busqueda.title()}**"
                })
                break
    except:
        pass
    return resultados[:1]

def buscar_apps_mod():
    resultados = []
    mods_conocidos = [
        {"titulo": "YouTube ReVanced", "desc": "Sin anuncios, background play, SponsorBlock", "link": "https://revanced.net"},
        {"titulo": "Spotify Premium Mod", "desc": "Todas las canciones gratis, sin anuncios", "link": "https://spotifypremiummod.com"},
        {"titulo": "CapCut PRO", "desc": "Todos los efectos y filtros premium gratis", "link": "https://capcutmod.com"},
        {"titulo": "TikTok MOD", "desc": "Sin publicidad, descarga de videos sin marca", "link": "https://tiktokmod.com"},
        {"titulo": "WhatsApp Plus", "desc": "Funciones ocultas de privacidad", "link": "https://whatsappplus.com"},
    ]
    for mod in random.sample(mods_conocidos, 2):
        if not enlace_ya_usado(mod['link']):
            resultados.append({
                "tipo": "📱 APP MOD",
                "titulo": mod['titulo'],
                "texto": mod['desc'],
                "link": mod['link']
            })
    return resultados

def buscar_trucos():
    trucos = [
        "**WhatsApp:** Escribe *texto* para negritas, _texto_ para cursiva, ~texto~ para tachado",
        "**Android:** Marca `*#*#4636#*#*` para menú de prueba oculto",
        "**YouTube:** Escribe `?v=` y borra todo para ver solo el video",
        "**Google:** Usa `site:dominio.com` para buscar en un sitio específico",
        "**Windows:** `Ctrl + Shift + V` pega sin formato",
        "**iPhone:** Desliza el dedo por la barra espaciadora para mover el cursor",
        "**Gmail:** Añade `+palabra` a tu correo para crear filtros automáticos",
        "**Instagram:** Guarda borradores ilimitados sin publicar",
        "**Netflix:** Usa códigos secretos en la URL (ej: 1365 para Acción)",
        "**Spotify:** Crea playlists colaborativas con cualquier usuario",
    ]
    truco_elegido = random.choice(trucos)
    if not enlace_ya_usado(truco_elegido[:50]):
        return [{"tipo": "💡 TRUCO", "titulo": "Truco que nadie sabe", "texto": truco_elegido}]
    return []

def buscar_deepweb():
    enlaces = [
        {"titulo": "Yandex", "desc": "Buscador ruso que NO filtra resultados políticos", "link": "https://yandex.com"},
        {"titulo": "Searx", "desc": "Agrega 100+ motores de búsqueda, sin rastreo de IP", "link": "https://searx.space"},
        {"titulo": "Wayback Machine", "desc": "Recupera páginas web BORRADAS de Internet", "link": "https://archive.org"},
        {"titulo": "DuckDuckGo", "desc": "Buscador que NO guarda tu historial", "link": "https://duckduckgo.com"},
        {"titulo": "Startpage", "desc": "Resultados de Google sin ser rastreado", "link": "https://startpage.com"},
        {"titulo": "Tor Project", "desc": "Navegador para acceso a la deep web (uso educativo)", "link": "https://torproject.org"},
    ]
    deep = random.choice(enlaces)
    if not enlace_ya_usado(deep['link']):
        return [{"tipo": "🌐 DEEP WEB", "titulo": deep['titulo'], "texto": deep['desc'], "link": deep['link']}]
    return []

def generar_contenido_completo():
    contenido = []
    contenido.extend(buscar_noticias())
    contenido.extend(buscar_videos_youtube())
    contenido.extend(buscar_imagenes())
    contenido.extend(buscar_apps_mod())
    contenido.extend(buscar_trucos())
    contenido.extend(buscar_deepweb())
    if not contenido:
        contenido = [{"tipo": "📡 INFO", "titulo": "Buscando contenido...", "texto": "El bot está buscando nuevo contenido.", "link": CHANNEL_URL}]
    random.shuffle(contenido)
    return contenido[:10]

CADENA_CONTENIDO = generar_contenido_completo()
indice_actual = 0

def formatear_post(item):
    pie = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ **REACCIONA CON CUALQUIER EMOJI**
📢 **MÁS CONTENIDO CADA {HORAS_PUBLICACION} HORAS**

👥 **ÚNETE A NUESTRA COMUNIDAD**
🔗 {CHANNEL_URL}

📢 **FIN EDUCATIVO** - Contenido informativo"""
    
    titulo_tipo = item.get('tipo', '📡 NOVEDAD')
    
    if item['tipo'] == "🎬 VIDEO":
        return f"""{titulo_tipo}

**🎬 {item['titulo']}**

{item['texto']}

▶️ **Ver video:** {item['link']}

{pie}"""
    
    elif item['tipo'] == "🖼️ IMAGEN" and item.get('link'):
        return f"""{titulo_tipo}

{item['texto']}

{pie}"""
    
    elif item['tipo'] == "📱 APP MOD":
        return f"""{titulo_tipo}

**🔥 {item['titulo']}**

✅ {item['texto']}

📥 **Descarga:** {item['link']}

{pie}

⚠️ **FIN EDUCATIVO** - Instala bajo tu responsabilidad"""
    
    elif item['tipo'] == "🌐 DEEP WEB":
        return f"""{titulo_tipo} - USO EDUCATIVO

**🌐 {item['titulo']}**

{item['texto']}

🔗 {item['link']}

{pie}"""
    
    elif item['tipo'] == "💡 TRUCO":
        return f"""{titulo_tipo}

{item['texto']}

{pie}"""
    
    else:
        fuente = item.get('fuente', '')
        return f"""{titulo_tipo} {('de ' + fuente) if fuente else ''}

**📌 {item.get('titulo', 'NOVEDAD')}**

{item.get('texto', '')}

🔗 **Fuente:** {item.get('link', CHANNEL_URL)}

{pie}"""

def publicar_con_media(context, item):
    try:
        if item['tipo'] == "🖼️ IMAGEN" and item.get('link'):
            return context.bot.send_photo(
                chat_id=CHANNEL_ID, 
                photo=item['link'], 
                caption=formatear_post(item), 
                parse_mode='Markdown'
            )
        else:
            return context.bot.send_message(
                chat_id=CHANNEL_ID, 
                text=formatear_post(item), 
                parse_mode='Markdown'
            )
    except Exception as e:
        logging.error(f"Error publicando: {e}")
        return context.bot.send_message(
            chat_id=CHANNEL_ID, 
            text=formatear_post(item), 
            parse_mode='Markdown'
        )

def publicar_siguiente(context):
    global CADENA_CONTENIDO, indice_actual
    if indice_actual >= len(CADENA_CONTENIDO):
        logging.info("🔄 Generando nuevo contenido...")
        CADENA_CONTENIDO = generar_contenido_completo()
        indice_actual = 0
    
    item = CADENA_CONTENIDO[indice_actual]
    publicar_con_media(context, item)
    
    stats = cargar_json(ARCHIVO_STATS)
    stats["posts_publicados"] = stats.get("posts_publicados", 0) + 1
    guardar_json(ARCHIVO_STATS, stats)
    
    logging.info(f"✅ Publicado Post {indice_actual + 1} - Tipo: {item['tipo']}")
    indice_actual += 1

def publicacion_programada(context):
    publicar_siguiente(context)

def start(update, context):
    stats = cargar_json(ARCHIVO_STATS)
    update.message.reply_text(
        f"""🔓 **CÓDIGO OCULTO - BOT PROFESIONAL**

📡 **{CHANNEL_USERNAME}** - Contenido exclusivo

📊 **ESTADÍSTICAS:**
• Posts publicados: {stats.get('posts_publicados', 0)}
• Reacciones totales: {stats.get('reacciones_totales', 0)}
• Desde: {stats.get('inicio', 'hoy')}

⚙️ **CONFIGURACIÓN:**
• Publicación automática: cada {HORAS_PUBLICACION} horas
• Búsqueda de contenido: continua

📂 **CATEGORÍAS:**
• 🤖 IA sin filtros
• 📱 Apps MOD actualizadas
• 💡 Trucos que NADIE sabe
• 🌐 Deep web ligera
• 🎬 Videos e imágenes

⭐ **REACCIONA EN CUALQUIER POST**

👥 **COMPARTE:** {CHANNEL_URL}"""
    )

def stats_command(update, context):
    stats = cargar_json(ARCHIVO_STATS)
    update.message.reply_text(
        f"""📊 **ESTADÍSTICAS DE {CHANNEL_USERNAME}**

📝 Posts publicados: {stats.get('posts_publicados', 0)}
⭐ Reacciones totales: {stats.get('reacciones_totales', 0)}
📅 Activo desde: {stats.get('inicio', 'hoy')}
⏱️ Frecuencia: cada {HORAS_PUBLICACION} horas

🔗 {CHANNEL_URL}"""
    )

def manejar_reacciones(update, context):
    update_obj = update.message_reaction
    if not update_obj:
        return
    
    stats = cargar_json(ARCHIVO_STATS)
    stats["reacciones_totales"] = stats.get("reacciones_totales", 0) + 1
    guardar_json(ARCHIVO_STATS, stats)
    logging.info(f"⭐ Reacción detectada - Total: {stats['reacciones_totales']}")

def actualizar_contenido(context):
    global CADENA_CONTENIDO, indice_actual
    logging.info("🔄 Buscando nuevo contenido en la web...")
    CADENA_CONTENIDO = generar_contenido_completo()
    indice_actual = 0

web_app = Flask('')

@web_app.route('/')
def home():
    return f"""Bot Código Oculto - Profesional
    Canal: {CHANNEL_URL}
    Publica cada {HORAS_PUBLICACION} horas
    Estado: Activo 24/7"""

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
    dp.add_handler(CommandHandler("stats", stats_command))
    dp.add_handler(MessageHandler(Filters.all, manejar_reacciones))
    
    segundos = HORAS_PUBLICACION * 3600
    updater.job_queue.run_repeating(publicacion_programada, interval=segundos, first=10)
    updater.job_queue.run_repeating(actualizar_contenido, interval=86400, first=10)
    
    logging.info(f"🚀 Bot Código Oculto iniciado - Publica cada {HORAS_PUBLICACION} horas - {CHANNEL_URL}")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
