import os
import sys
import asyncio
from fpdf import FPDF
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)
from pgd_bot import PGD_Person_Mod, PGD_Pair

# === Загрузка токена ===
with open("token.txt", "r") as f:
    TOKEN = f.read().strip()

# === Состояния
MENU, NAME, DATE, SEX = range(4)
P_NAME1, P_DATE1, P_NAME2, P_DATE2 = range(10, 14)

# === Клавиатуры
def main_menu_keyboard():
    return ReplyKeyboardMarkup([["👤 Личная диагностика"], ["❤️ Диагностика пары"]], resize_keyboard=True)

def cancel_keyboard():
    return ReplyKeyboardMarkup([["❌ Отмена"]], resize_keyboard=True)

def result_keyboard():
    return ReplyKeyboardMarkup([["📄 Скачать описание"], ["🔙 В главное меню"]], resize_keyboard=True)

# === PDF генерация
def generate_pdf(text: str, filename: str) -> str:
    os.makedirs("output", exist_ok=True)
    path = os.path.join("output", filename)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.multi_cell(0, 10, line)
    pdf.output(path)
    return path

# === Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Выберите тип диагностики:", reply_markup=main_menu_keyboard())
    return MENU

# === Главное меню
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "👤 Личная диагностика":
        await update.message.reply_text("Введите имя:", reply_markup=cancel_keyboard())
        return NAME
    elif text == "❤️ Диагностика пары":
        await update.message.reply_text("Введите имя первого партнёра:", reply_markup=cancel_keyboard())
        return P_NAME1
    else:
        await update.message.reply_text("Пожалуйста, выберите действие с клавиатуры.")
        return MENU

# === Личная диагностика
async def personal_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Введите дату рождения (ДД.ММ.ГГГГ):", reply_markup=cancel_keyboard())
    return DATE

async def personal_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["date"] = update.message.text
    await update.message.reply_text("Укажите пол:", reply_markup=ReplyKeyboardMarkup([["М", "Ж"]], resize_keyboard=True))
    return SEX

async def personal_sex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sex = update.message.text.strip().upper()
    if sex not in ["М", "Ж"]:
        await update.message.reply_text("Пожалуйста, выберите пол из предложенных вариантов: М или Ж.")
        return SEX
    context.user_data["sex"] = sex

    try:
        person = PGD_Person_Mod(context.user_data["name"], context.user_data["date"], context.user_data["sex"])
        points = person.calculate_points()
        tasks = person.tasks()
        periods = person.periods_person()

        msg = f"📌 *Результаты для {context.user_data['name']}*\n\n"
        msg += "🔹 *Точки личности:*\n"
        for group, values in points.items():
            msg += f"_{group}_\n"
            for key, val in values.items():
                msg += f"• *{key}*: `{val}`\n"
        msg += "\n🌟 *Сверхзадачи:*\n"
        for k, v in tasks.items():
            msg += f"• *{k}*: `{v}`\n"
        msg += "\n🧭 *Бизнес-периоды:*\n"
        for k, v in periods["Бизнес периоды"].items():
            msg += f"• *{k}*: `{v}`\n"

        context.user_data["last_result"] = msg
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=result_keyboard())
        return MENU
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")
        return MENU

# === Парная диагностика
async def pair_name1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name1"] = update.message.text
    await update.message.reply_text("Дата рождения первого партнёра (ДД.ММ.ГГГГ):")
    return P_DATE1

async def pair_date1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["date1"] = update.message.text
    await update.message.reply_text("Введите имя второго партнёра:")
    return P_NAME2

async def pair_name2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name2"] = update.message.text
    await update.message.reply_text("Дата рождения второго партнёра (ДД.ММ.ГГГГ):")
    return P_DATE2

async def pair_date2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["date2"] = update.message.text
    try:
        pair = PGD_Pair(context.user_data["name1"], context.user_data["date1"],
                        context.user_data["name2"], context.user_data["date2"])
        points = pair.main_pair()
        tasks = pair.tasks()
        periods = pair.periods_pair()
        partner_tasks = pair.tasks_business()

        msg = f"📌 *Пара: {context.user_data['name1']} и {context.user_data['name2']}*\n\n"
        msg += "🔹 *Точки пары:*\n"
        for group, values in points.items():
            msg += f"_{group}_\n"
            for key, val in values.items():
                msg += f"• *{key}*: `{val}`\n"
        msg += "\n🌟 *Сверхзадачи:*\n"
        for key, val in tasks["Сверхзадачи"].items():
            msg += f"• *{key}*: `{val}`\n"
        msg += "\n🧭 *Бизнес-периоды:*\n"
        for key, val in periods["Бизнес периоды"].items():
            msg += f"• *{key}*: `{val}`\n"
        msg += "\n🔧 *Задачи партнёров:*\n"
        for k, v in partner_tasks.items():
            msg += f"• *{k}*: `{v}`\n"

        context.user_data["last_result"] = msg
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=result_keyboard())
        return MENU
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")
        return MENU

# === Обработка кнопок
async def handle_result_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📄 Скачать описание":
        try:
            content = context.user_data.get("last_result", "Нет данных.")
            filename = f"diagnostic_{update.message.from_user.id}.pdf"
            path = generate_pdf(content, filename)
            await update.message.reply_document(document=open(path, "rb"), filename=filename)
        except Exception as e:
            await update.message.reply_text(f"Ошибка при генерации PDF: {e}")
        return MENU
    elif text == "🔙 В главное меню":
        return await start(update, context)

# === Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.", reply_markup=main_menu_keyboard())
    return MENU

# === Основной асинхронный запуск
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, personal_name)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, personal_date)],
            SEX: [MessageHandler(filters.TEXT & ~filters.COMMAND, personal_sex)],
            P_NAME1: [MessageHandler(filters.TEXT & ~filters.COMMAND, pair_name1)],
            P_DATE1: [MessageHandler(filters.TEXT & ~filters.COMMAND, pair_date1)],
            P_NAME2: [MessageHandler(filters.TEXT & ~filters.COMMAND, pair_name2)],
            P_DATE2: [MessageHandler(filters.TEXT & ~filters.COMMAND, pair_date2)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Отмена$"), cancel)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_result_buttons))

    print("✅ Бот запущен.")
    await app.run_polling()

# === Запуск
import sys
import asyncio

if __name__ == "__main__":
    # Для Windows Python 3.8+
    if sys.platform.startswith("win") and sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        print("Установи nest_asyncio: pip install nest_asyncio")
        sys.exit(1)

    import contextlib

    async def runner():
        try:
            await main()
        except KeyboardInterrupt:
            print("⛔ Остановка по Ctrl+C")

    with contextlib.suppress(RuntimeError):
        asyncio.get_event_loop().run_until_complete(runner())


