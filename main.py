import requests
import json
import time
import telebot
from pywebio import start_server, output

# Токен вашего Telegram-бота
BOT_TOKEN = "6198657565:AAEZE2-BoCx07Krny3qgcC8mEL9S5o0T8mk"
# URL API для получения информации о воздушной тревоге
API_URL = "https://sirens.in.ua/api/v1/"

# Словарь для хранения предыдущих данных о воздушной тревоге для каждого чата/пользователя
previous_districts_by_chat = {}
previous_districts_by_user = {}
# Словарь для хранения данных о районах на первой проверке
initial_districts = {}

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "Привіт! Я інформуватиму про повітряну тривогу у вашій області.")


def get_alert_message(status):
    """Возвращает сообщение в зависимости от статуса"""
    if status == "full":
        return "Тривога! 🚨"
    elif status is None:
        return "Тривоги немає 🟢"
    elif status == "no_data":
        return "Нема інформації 🛈"
    else:
        return "Невідомий статус ❓"


def send_telegram_message(chat_id, message_text):
    """Отправить сообщение в Telegram"""
    bot.send_message(chat_id, message_text)


def send_sirens_message(chat_id, districts):
    """Отправить сообщение о воздушной тревоге"""
    previous_districts = previous_districts_by_chat.get(chat_id, {})
    for district, status in districts.items():
        if chat_id not in initial_districts:
            # Первая проверка - отправляем информацию о всех районах
            initial_districts[chat_id] = districts

        if chat_id in initial_districts and district in initial_districts[chat_id]:
            # Вторая и последующие проверки - отправляем информацию только об измененных районах
            if district in previous_districts and previous_districts[district] == status:
                continue

        message_text = f"В області {district}: {get_alert_message(status)}"
        send_telegram_message(chat_id, message_text)

        # Обновляем статус для района в текущем чате
        previous_districts[district] = status

    # Обновляем статус для текущего чата
    previous_districts_by_chat[chat_id] = previous_districts


def check_sirens_status():
    """Получить статус воздушной тревоги с сайта"""
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            districts = json.loads(response.text)
            return districts
    except requests.exceptions.RequestException as ex:
        print(ex)
    return None


def sirens_app():
    output.put_text("Привіт! Я інформуватиму про повітряну тривогу у вашій області.")

    while True:
        # Получаем статус воздушной тревоги
        districts = check_sirens_status()
        if districts:
            for update in bot.get_updates():
                chat_id = update.message.chat.id
                send_sirens_message(chat_id, districts)
        # Пауза в 30 секунд перед следующей проверкой
        time.sleep(30)


if __name__ == "__main__":
    # Запустить веб-приложение на локальном сервере
    start_server(sirens_app, port=80, host='0.0.0.0')
