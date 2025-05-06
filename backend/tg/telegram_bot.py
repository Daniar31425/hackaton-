from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
import requests
import datetime
import os
from dotenv import load_dotenv

SELECT_ACTION, TOPIC, TEXT, PHOTO, LOCATION = range(5)

TOPIC_TO_DEPARTMENT = {
    "мусор": "ЖКХ",
    "вода": "Коммунальные службы",
    "интернет": "Цифровизация",
    "дорога": "Отдел транспорта",
    "освещение": "Энергетика",
    "экология": "Экология"
}

BASE_URL = "http://localhost:8000"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["📨 Оставить анонимно жалобу"], ["💡 Предложить идею"], ["📋 Узнать статус жалобы"]]
    await update.message.reply_text(
        "Здравствуйте! Я — бот обратной связи FutureMakers.\n\nВыберите действие:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return SELECT_ACTION
    
async def select_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "жалоб" in text:
        return await ask_topic(update, context)
    elif "иде" in text:
        await update.message.reply_text("🔧 Раздел с идеями в разработке.")
        return ConversationHandler.END
    elif "статус" in text:
        await update.message.reply_text("✍️ Отправьте код обращения (например: FM-2025-0001)")
        return SELECT_ACTION
    elif text.upper().startswith("FM-"):
        return await handle_status(update, context)
    else:
        await update.message.reply_text("Пожалуйста, выберите действие с помощью кнопок.")
        return SELECT_ACTION

async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    try:
        res = requests.get(f"{BASE_URL}/tasks/code/{code}")
        if res.status_code == 200:
            task = res.json()
            msg = f"📋 Статус обращения {code}:\n\n🗂 Отдел: {task['department']}\n📄 Статус: {task['status']}\n📆 Срок: {task['deadline']}"
            if task.get("reply"):
                msg += f"\n💬 Ответ: {task['reply']}"
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("❌ Обращение не найдено.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка при запросе: {e}")
    return ConversationHandler.END

async def ask_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[t] for t in TOPIC_TO_DEPARTMENT]
    await update.message.reply_text(
        "Выберите тему обращения:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return TOPIC

async def set_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = update.message.text.lower()
    if topic not in TOPIC_TO_DEPARTMENT:
        await update.message.reply_text("Пожалуйста, выберите тему из списка.")
        return TOPIC
    context.user_data["topic"] = topic
    context.user_data["department"] = TOPIC_TO_DEPARTMENT[topic]
    await update.message.reply_text("✍️ Введите текст жалобы:")
    return TEXT

async def set_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["text"] = update.message.text
    await update.message.reply_text(
        "📷 Прикрепите фото или нажмите 'Пропустить':",
        reply_markup=ReplyKeyboardMarkup([["Пропустить"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return PHOTO

async def set_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text.lower() == "пропустить":
        context.user_data["photo_url"] = None
    elif update.message.photo:
        file = await update.message.photo[-1].get_file()
        context.user_data["photo_url"] = file.file_path
    else:
        await update.message.reply_text("Пожалуйста, отправьте фото или нажмите 'Пропустить'")
        return PHOTO

    await update.message.reply_text(
        "📍 Отправьте геолокацию или нажмите 'Пропустить':",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("Пропустить")],
            [KeyboardButton("Отправить геолокацию", request_location=True)]
        ], resize_keyboard=True, one_time_keyboard=True)
    )
    return LOCATION

async def set_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if update.message.location:
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        location = f"{lat}, {lon}"
    elif update.message.text and update.message.text.lower() == "пропустить":
        location = None
    else:
        await update.message.reply_text("Пожалуйста, отправьте геолокацию или нажмите 'Пропустить'")
        return LOCATION

    topic = context.user_data["topic"]
    dept = context.user_data["department"]
    text = context.user_data["text"]
    photo_url = context.user_data.get("photo_url")

    content = f"[{topic.upper()}] {text}"
    if photo_url:
        content += f"\n📷 Фото: <a href='{photo_url}'>Открыть</a>"
    if location:
        content += f"\n📍 Геолокация: {location}"

    payload = {
        "content": content,
        "department": dept,
        "deadline": (datetime.datetime.utcnow() + datetime.timedelta(days=3)).isoformat(),
        "telegram_id": str(user.id),
    }

    try:
        res = requests.post(f"{BASE_URL}/tasks", json=payload)
        if res.status_code == 200:
            task = res.json()
            code = f"FM-2025-{str(task['id']).zfill(4)}"
            await update.message.reply_text(
                f"✅ Жалоба зарегистрирована.\nНомер: {code}",
                reply_markup=ReplyKeyboardMarkup([
                    ["📨 Оставить жалобу", "📋 Узнать статус"]
                ], resize_keyboard=True, one_time_keyboard=True),
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(f"❌ Ошибка: {res.status_code} - {res.text}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка сервера: {e}")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог завершён.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start(update, context)

if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("BOT_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_action)],
            TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_topic)],
            TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_text)],
            PHOTO: [MessageHandler(filters.PHOTO | filters.TEXT, set_photo)],
            LOCATION: [MessageHandler(filters.LOCATION | filters.TEXT, set_location)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^❌ Завершить$"), cancel),
        ],
    )

    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Regex("^📋 Узнать статус$"), select_action))
    app.add_handler(MessageHandler(filters.Regex("^📨 Оставить жалобу$"), restart))
    app.add_handler(MessageHandler(filters.Regex("^FM-2025-[0-9]+$"), handle_status))

    print("🚀 Бот запущен")
    app.run_polling()
