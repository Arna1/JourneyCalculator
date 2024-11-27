import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
from datetime import datetime, timedelta
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Estados del flujo de conversación
ENTRADA, PAUSA, REGRESO = range(3)

# Servidor web simple para Render
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("El bot está corriendo y escuchando en Render.".encode("utf-8"))


def run_server():
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Función para iniciar el bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu asistente de jornada laboral. Por favor, ingresa la hora de entrada al trabajo en formato HH:MM."
    )
    return ENTRADA

# Recibe la hora de entrada
async def entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hora_entrada'] = update.message.text
    await update.message.reply_text("Gracias. Ahora ingresa la hora de pausa para comer (HH:MM).")
    return PAUSA

# Recibe la hora de pausa
async def pausa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hora_pausa'] = update.message.text
    await update.message.reply_text("Perfecto. Ahora ingresa la hora de regreso de la pausa (HH:MM).")
    return REGRESO

# Recibe la hora de regreso y calcula la salida
async def regreso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hora_regreso'] = update.message.text

    # Extraer las horas ingresadas
    hora_entrada = context.user_data['hora_entrada']
    hora_pausa = context.user_data['hora_pausa']
    hora_regreso = context.user_data['hora_regreso']

    # Calcular la hora de salida
    try:
        formato = "%H:%M"
        entrada = datetime.strptime(hora_entrada, formato)
        pausa = datetime.strptime(hora_pausa, formato)
        regreso = datetime.strptime(hora_regreso, formato)
        duracion_pausa = regreso - pausa
        jornada_timedelta = timedelta(hours=8)
        hora_salida = entrada + jornada_timedelta + duracion_pausa
        hora_salida_str = hora_salida.strftime(formato)

        await update.message.reply_text(f"Debes salir a las: {hora_salida_str}")
    except Exception as e:
        await update.message.reply_text("Hubo un error en los datos ingresados. Por favor, intenta de nuevo.")

    return ConversationHandler.END

# Cancela la interacción
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operación cancelada. ¡Hasta la próxima!")
    return ConversationHandler.END

# Configuración principal del bot
def main():
    # Coloca aquí el token de tu bot
    TOKEN = os.getenv("TOKEN_API")

    # Crear la aplicación
    application = Application.builder().token(TOKEN).build()

    # Conversación
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ENTRADA: [MessageHandler(filters.TEXT & ~filters.COMMAND, entrada)],
            PAUSA: [MessageHandler(filters.TEXT & ~filters.COMMAND, pausa)],
            REGRESO: [MessageHandler(filters.TEXT & ~filters.COMMAND, regreso)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    # Ejecutar el servidor web en un hilo separado
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    # Iniciar el bot (Polling)
    application.run_polling()

if __name__ == '__main__':
    main()
