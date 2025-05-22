import os
import logging
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from pgd_bot import PGD_Person_Mod, PGD_Pair

# ───────────────────────────────
# CONFIG
# ───────────────────────────────

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не найден в .env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния
PERSON_INPUT, PAIR_NAME1, PAIR_DOB1, PAIR_NAME2, PAIR_DOB2 = range(5)


# ───────────────────────────────
# VALIDATION
# ───────────────────────────────

def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%d.%m.%Y")
        return True
    except ValueError:
        return False


# ───────────────────────────────
# HANDLERS
# ───────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🧬 Личная диагностика", callback_data="person")],
        [InlineKeyboardButton("❤️ Парная диагностика", callback_data="pair")]
    ])
    await update.message.reply_text("Выберите тип диагностики:", reply_markup=keyboard)


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "person":
        await query.edit_message_text("Введите данные в формате: `Имя;ДД.ММ.ГГГГ;М/Ж`", parse_mode="MarkdownV2")
        return PERSON_INPUT

    elif query.data == "pair":
        await query.edit_message_text("👤 Введите имя первого человека:")
        return PAIR_NAME1


async def handle_person(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        name, date, gender = map(str.strip, update.message.text.split(";"))
        if not validate_date(date):
            raise ValueError("Неверный формат даты.")
        if gender.upper() not in {"М", "Ж"}:
            raise ValueError("Пол должен быть М или Ж")

        p = PGD_Person_Mod(name, date, gender.upper())
        points = p.calculate_points()
        tasks = p.tasks()
        periods = p.periods_person()

        msg = f"🧬 <b>Диагностика для {name}</b>\n\n"

        msg += "🔹 <b>Точки личности</b>\n"
        for group, values in points.items():
            msg += f"\n<b>{group}</b>\n"
        for key, val in values.items():
            msg += f"• <i>{key}</i>: <code>{val}</code>\n"

        msg += "\n🌟 <b>Сверхзадачи</b>\n"
        for key, val in tasks.items():
            msg += f"• <i>{key}</i>: <code>{val}</code>\n"

        msg += "\n🧭 <b>Бизнес-периоды</b>\n"
        for key, val in periods["Бизнес периоды"].items():
            msg += f"• <i>{key}</i>: <code>{val}</code>\n"

        await update.message.reply_text(msg, parse_mode="HTML")

        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка: {e}\nПопробуйте снова.")
        return PERSON_INPUT


# ───── ПАРНАЯ ─────

async def pair_name1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name1"] = update.message.text
    await update.message.reply_text("📅 Дата рождения первого (ДД.ММ.ГГГГ):")
    return PAIR_DOB1


async def pair_dob1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not validate_date(update.message.text):
        await update.message.reply_text("⛔ Формат даты: ДД.ММ.ГГГГ")
        return PAIR_DOB1

    context.user_data["dob1"] = update.message.text
    await update.message.reply_text("👤 Введите имя второго:")
    return PAIR_NAME2


async def pair_name2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name2"] = update.message.text
    await update.message.reply_text("📅 Дата рождения второго (ДД.ММ.ГГГГ):")
    return PAIR_DOB2


async def pair_dob2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not validate_date(update.message.text):
        await update.message.reply_text("⛔ Формат даты: ДД.ММ.ГГГГ")
        return PAIR_DOB2

    name1 = context.user_data["name1"]
    dob1 = context.user_data["dob1"]
    name2 = context.user_data["name2"]
    dob2 = update.message.text

    try:
        pair = PGD_Pair(name1, dob1, name2, dob2)
        points = pair.main_pair()
        tasks = pair.tasks()
        periods = pair.periods_pair()
        business = pair.tasks_business()

        msg = f"👫 <b>Диагностика пары: {name1} и {name2}</b>\n\n"

        msg += "🔹 <b>Точки пары</b>\n"
        for section, data in points.items():
            msg += f"\n<b>{section}</b>\n"
            for k, v in data.items():
                msg += f"• <i>{k}</i>: <code>{v}</code>\n"

        msg += "\n🌟 <b>Сверхзадачи</b>\n"
        for k, v in tasks["Сверхзадачи"].items():
            msg += f"• <i>{k}</i>: <code>{v}</code>\n"

        msg += "\n🧭 <b>Бизнес-периоды</b>\n"
        for k, v in periods["Бизнес периоды"].items():
            msg += f"• <i>{k}</i>: <code>{v}</code>\n"

        msg += "\n🔧 <b>Задачи партнёров</b>\n"
        for k, v in business.items():
            msg += f"• <i>{k}</i>: <code>{v}</code>\n"

        await update.message.reply_text(msg, parse_mode="HTML")
        return ConversationHandler.END

    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка: {e}")
        return PAIR_DOB2


# ───────────────────────────────
# BOT RUNNER
# ───────────────────────────────

import asyncio
# другие импорты...

async def run_bot():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(button_click)],
        states={
            PERSON_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_person)],
            PAIR_NAME1: [MessageHandler(filters.TEXT & ~filters.COMMAND, pair_name1)],
            PAIR_DOB1: [MessageHandler(filters.TEXT & ~filters.COMMAND, pair_dob1)],
            PAIR_NAME2: [MessageHandler(filters.TEXT & ~filters.COMMAND, pair_name2)],
            PAIR_DOB2: [MessageHandler(filters.TEXT & ~filters.COMMAND, pair_dob2)],
        },
        fallbacks=[],
        allow_reentry=True
    ))

    logger.info("📡 Бот запущен.")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.wait_for_stop()
    await app.stop()
    await app.shutdown()

# ───────────────────────────────
# ЗАПУСК
# ───────────────────────────────

if __name__ == "__main__":
    asyncio.run(run_bot())

