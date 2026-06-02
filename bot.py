import os
import logging
import json
import threading
from flask import Flask
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

TOKEN = "8991788772:AAEy4xMXBTlhr4odaVXN1DaSX1CbfMtlxEU"
CHANNEL_ID = "-1003948185788"
LIMITE_REACCIONES = 50

logging.basicConfig(level=logging.INFO)

ARCHIVO_ESTADO = "estado_posts.json"

CADENA_CONTENIDO = [
    "🤖 **IA SIN FILTROS - Parte 1**\n\nNuevo jailbreak para ChatGPT.\n\n⭐ Reacciona con CUALQUIER REACCIÓN. Al llegar a 50, publico la Parte 2.",
    "💀 **TRUCO QUE NADIE SABÍA - Parte 2**\n\nEn WhatsApp, escribe `*texto*` para **negritas**.\n\n⭐ Siguiente parte en 50 reacciones.",
    "📱 **APP MOD ACTUALIZADA - Parte 3**\n\nYouTube ReVanced v19.09.37\n✅ Sin anuncios\n\n⭐ Parte 4 al llegar a 50 reacciones.",
]

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
    estado = cargar_estado()
    siguiente_id = estado["ultimo_post_id"] + 1
    
    if siguiente_id <= len(CADENA_CONTENIDO):
        texto = CADENA_CONTENIDO[siguiente_id - 1]
        mensaje = context.bot.send_message(
            chat_id=CHANNEL_ID, 
            text=texto, 
            parse_mode='Markdown'
        )
        estado["ultimo_post_id"] = siguiente_id
        estado["message_id_actual"] = mensaje.message_id
        estado["reacciones_actuales"] = 0
        guardar_estado(estado)
        logging.info(f"✅ Publicado Post {siguiente_id}")

def start(update, context):
    update.message.reply_text("🔓 Bot activo. Reacciona en el canal para desbloquear contenido.")

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
            logging.info("🎉 Límite alcanzado! Publicando siguiente...")
            publicar_siguiente(context)

web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot funcionando"

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
    
    estado = cargar_estado()
    if estado["ultimo_post_id"] == 0:
        updater.job_queue.run_once(publicar_siguiente, 5, context=updater)
    
    logging.info("🚀 Bot iniciado")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
