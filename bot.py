
import logging
import os
import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен Telegram-бота
BOT_TOKEN = "вставь_сюда_свой_токен"

# Подключение к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# ID или URL таблицы
SPREADSHEET_ID = "вставь_сюда_ID_таблицы"

bot = telebot.TeleBot(BOT_TOKEN)

# Словарь для временного хранения данных по пользователю
user_data = {}

# Команда /start
@bot.message_handler(commands=["start"])
def handle_start(message):
    bot.reply_to(message, "Привет! Пришли фото чека, затем сумму и описание.
В конце напиши своё имя (например: Ирина)")

# Обработка фото
@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

    user_data[message.chat.id] = {
        "photo_url": file_url
    }
    bot.reply_to(message, "Фото получено. Теперь пришли сумму и описание (например: 2000 Маникюр)")

# Обработка текста с суммой и описанием
@bot.message_handler(func=lambda msg: msg.text and msg.chat.id in user_data and "sum" not in user_data[msg.chat.id])
def handle_sum_description(message):
    try:
        parts = message.text.strip().split(" ", 1)
        amount = float(parts[0])
        description = parts[1] if len(parts) > 1 else "Без описания"

        user_data[message.chat.id]["sum"] = amount
        user_data[message.chat.id]["description"] = description

        bot.reply_to(message, "Отлично! Теперь напиши своё имя (например: Ирина)")

    except:
        bot.reply_to(message, "Нужно ввести сумму и описание в формате: 4500 Перевод за прививки")

# Обработка имени
@bot.message_handler(func=lambda msg: msg.text and msg.chat.id in user_data and "sum" in user_data[msg.chat.id] and "employee" not in user_data[msg.chat.id])
def handle_employee_name(message):
    name = message.text.strip()

    data = user_data[message.chat.id]
    date = datetime.now().strftime("%d.%m.%y")
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(name)

    row = [date, -data["sum"], data["description"], data["photo_url"], name]
    sheet.append_row(row)

    bot.reply_to(message, "Супер! Всё записал.")
    del user_data[message.chat.id]

bot.infinity_polling()
