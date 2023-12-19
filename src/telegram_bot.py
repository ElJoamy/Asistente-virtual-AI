import telebot
import requests
from datetime import datetime
from src.config import get_settings
from src.db.db_manage import DatabaseManager

_SETTINGS = get_settings()

API_TOKEN =_SETTINGS.telegram_token

db_manager = DatabaseManager(_SETTINGS.db_host, _SETTINGS.db_port, _SETTINGS.db_user, _SETTINGS.db_pass, _SETTINGS.db_name)
print (API_TOKEN)

bot = telebot.TeleBot(API_TOKEN)

API_URL = get_settings().api_url

def log_user_data(user_id, user_name, command_time, comando):
    data = (user_id, user_name, command_time, command_time.date(), comando)
    db_manager.insert_user_log(data)

def get_user_ids_from_log():
    try:
        user_ids = db_manager.get_user_ids()
        return user_ids
    except Exception as e:
        print(f"Error al obtener los user_ids de la base de datos: {e}")
        return set()

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    command_time = datetime.now()
    comando = message.text

    log_user_data(user_id, user_name, command_time, comando)

    bot.reply_to(message, f"Hola {user_name}, bienvenido a tu asistente virtual...")
    print(f"El {user_name} con ID {user_id} hizo el comando {comando} a las {command_time.strftime('%H:%M:%S')}")

@bot.message_handler(commands=['help'])
def handle_help(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    command_time = datetime.now()
    comando = message.text

    log_user_data(user_id, user_name, command_time, comando)

    help_message = (
        f"Hola {user_name}, aquí tienes ayuda sobre cómo utilizar el bot:\n\n"
        "Comandos disponibles:\n"
        "/start - Inicia la interacción con el bot y te da la bienvenida.\n"
        "/help - Muestra esta ayuda.\n"
        "/status - Obtiene el estado actual del servicio.\n"
        "/sentiment - Inicia el proceso para analizar el sentimiento de un texto.\n"
        "/analysis - Inicia el proceso para realizar un análisis completo de un texto (incluye POS tags, NER, y análisis de sentimiento).\n\n"
        "Si necesitas más información o asistencia, no dudes en escribir el comando correspondiente."
    )

    bot.reply_to(message, help_message)
    print(f"El {user_name} con ID {user_id} hizo el comando {comando} a las {command_time.strftime('%H:%M:%S')}")


@bot.message_handler(commands=['status'])
def handle_status(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    command_time = datetime.now()
    comando = message.text

    allowed_user_ids = get_user_ids_from_log()
    if user_id not in allowed_user_ids:
        bot.reply_to(message, "No tienes permiso para usar este comando.")
        return

    log_user_data(user_id, user_name, command_time, comando)

    status_url = API_URL + "status" 
    try:
        response = requests.get(status_url)
        if response.status_code == 200:
            status_data = response.json()
            reply_message = f"Estado del servicio: {status_data['status']}\n" \
                            f"Nombre del servicio: {status_data['service_name']}\n" \
                            f"Versión: {status_data['version']}\n" \
                            f"Nivel de log: {status_data['log_level']}\n" \
                            f"Modelos utilizados:\n" \
                            f"  - Sentiment Model: {status_data['models_info']['sentiment_model']}\n" \
                            f"  - NLP Model: {status_data['models_info']['nlp_model']}\n" \
                            f"  - GPT Model: {status_data['models_info']['gpt_model']}"
        else:
            reply_message = "Error al obtener el estado del servicio."
    except requests.exceptions.RequestException as e:
        reply_message = f"Error al conectarse con la API: {e}"

    print(f"El {user_name} con ID {user_id} hizo el comando {comando} a las {command_time.strftime('%H:%M:%S')}")
    bot.reply_to(message, reply_message)

@bot.message_handler(commands=['sentiment'])
def handle_sentiment(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    command_time = datetime.now()
    comando = message.text

    log_user_data(user_id, user_name, command_time, comando)

    bot.send_message(user_id, "Por favor, envía el texto para el análisis de sentimiento.")

    bot.register_next_step_handler(message, analyze_sentiment_step)

def analyze_sentiment_step(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    command_time = datetime.now()
    text = message.text

    sentiment_url = API_URL + "sentiment"
    payload = {"text": text}

    try:
        response = requests.post(sentiment_url, json=payload)
        if response.status_code == 200:
            sentiment_data = response.json()
            label = sentiment_data["prediction"]["label"]
            score = sentiment_data["prediction"]["score"]
            reply_message = f"Análisis de Sentimiento:\n" \
                            f"Texto: {text}\n" \
                            f"Sentimiento: {label}\n" \
                            f"Puntuación: {score}"
        else:
            reply_message = "Error al realizar el análisis de sentimiento."
    except requests.exceptions.RequestException as e:
        reply_message = f"Error al conectarse con la API: {e}"

    print (f"El {user_name} con ID {user_id} hizo el análisis de sentimiento a las {command_time.strftime('%H:%M:%S')}")
    bot.send_message(user_id, reply_message)

@bot.message_handler(commands=['analysis'])
def handle_analysis(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    command_time = datetime.now()
    comando = message.text

    log_user_data(user_id, user_name, command_time, comando)

    bot.send_message(user_id, "Por favor, envía el texto para el análisis de texto.")

    bot.register_next_step_handler(message, analyze_text_step)

def analyze_text_step(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    command_time = datetime.now()
    text = message.text

    analysis_url = API_URL + "analysis"
    payload = {"text": text}

    try:
        response = requests.post(analysis_url, json=payload)
        if response.status_code == 200:
            analysis_data = response.json()
            reply_message = "Análisis de Texto:\n"
            reply_message += f"Texto: {text}\n"
            reply_message += f"Resumen POS Tags: {analysis_data['nlp_analysis']['pos_tags_summary']}\n"
            reply_message += f"Resumen NER: {analysis_data['nlp_analysis']['ner_summary']}\n"
            reply_message += f"Sentimiento: {analysis_data['sentiment_analysis']['label']}\n"
            reply_message += f"Puntuación de Sentimiento: {analysis_data['sentiment_analysis']['score']}"
        else:
            reply_message = "Error al realizar el análisis de texto."
    except requests.exceptions.RequestException as e:
        reply_message = f"Error al conectarse con la API: {e}"

    print (f"El {user_name} con ID {user_id} hizo el análisis de texto a las {command_time.strftime('%H:%M:%S')}")
    bot.send_message(user_id, reply_message)
