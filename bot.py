# Файл: telegram_bot.py (ПОЛНАЯ ПРАВИЛЬНАЯ ВЕРСИЯ)

import logging
import os
import re
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from pgd_bot import PGD_Person_Mod
from cashka_preprocessor import PersonalityProcessor

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv("TOKEN_BOT")

if not BOT_TOKEN:
    print("ОШИБКА: Не найден токен для Telegram бота в .env файле.")
    exit()

GET_NAME, GET_DOB, GET_GENDER, SHOW_DESCRIPTION = range(4)


def escape_markdown(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    escape_chars = r'_*[]()~`>#+-.=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def format_results_for_download(name: str, dob: datetime, results: dict, tasks: dict, periods: dict) -> str:
    header = (
        f"Анализ личности\n{'='*20}\n"
        f"Имя: {name}\nДата рождения: {dob.strftime('%d.%m.%Y')}\n{'='*20}\n"
    )
    tasks_content = "\n--- Задачи по Матрице ---\n"
    if tasks:
        for key, value in tasks.items():
            tasks_content += f"{key}: {value if value is not None else '-'}\n"
    periods_content = "\n--- Бизнес Периоды ---\n"
    if periods and "Бизнес периоды" in periods:
        for key, value in periods["Бизнес периоды"].items():
            periods_content += f"{key}: {value if value is not None else '-'}\n"
    main_content = "\n--- Подробное описание ---\n"
    for key, value in results.items():
        clean_value = value.replace('**', '').replace('*', '').replace('\n\n', '\n')
        main_content += f"\n--- {key} ---\n{clean_value}\n"
    return header + tasks_content + periods_content + main_content


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        r"👋 Здравствуйте\! Я бот для психологической диагностики\."
        r"\n\nЧтобы начать, пожалуйста, введите Ваше имя\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return GET_NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text(
        rf"Отлично, {escape_markdown(context.user_data['name'])}\! Теперь введите Вашу дату рождения в формате *ДД\.ММ\.ГГГГ*\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return GET_DOB


async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['dob'] = datetime.strptime(update.message.text, '%d.%m.%Y')
        keyboard = [[InlineKeyboardButton("Женский", callback_data="Ж"), InlineKeyboardButton("Мужской", callback_data="М")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(r"Спасибо\! Пожалуйста, выберите Ваш пол:", reply_markup=reply_markup)
        return GET_GENDER
    except ValueError:
        await update.message.reply_text(
            r"❌ *Ошибка формата даты*\."
            r"\n\nПожалуйста, введите дату строго в формате *ДД\.ММ\.ГГГГ*\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return GET_DOB


# Файл: telegram_bot.py
# Замените только эту функцию

# Файл: telegram_bot.py
# Замените старую функцию get_gender на эту:

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    gender_char = query.data
    gender_full = "Женский" if gender_char == "Ж" else "Мужской"
    await query.edit_message_text(text=rf"Вы выбрали пол: *{escape_markdown(gender_full)}*\.\n\n⏳ Начинаю расчет\.\.\.", parse_mode=ParseMode.MARKDOWN_V2)

    user_data = context.user_data
    name = user_data['name']
    date_str = user_data['dob'].strftime('%d.%m.%Y')

    try:
        # Шаг 1: Выполняем расчеты
        person_mod = PGD_Person_Mod(name, date_str, gender_char)
        main_cup_data = person_mod.calculate_points()
        tasks_data = person_mod.tasks()
        periods_data = person_mod.periods_person()

        # Шаг 2: Оборачиваем и передаем в процессор
        wrapped_cup_data = {'Основная чашка': main_cup_data}
        processor = PersonalityProcessor(wrapped_cup_data)
        full_descriptions = processor.get_full_description()
        
        # Шаг 3: Сохраняем данные в сессию
        context.user_data['full_descriptions'] = full_descriptions
        context.user_data['tasks_data'] = tasks_data
        context.user_data['periods_data'] = periods_data
        
        # --- ВОТ ВОССТАНОВЛЕННЫЙ БЛОК ---
        header = f"*Результаты анализа для {escape_markdown(name)} \\({escape_markdown(date_str)}\\)*\n\n"
        
        # 1. Определяем переменную summary_text
        summary_text = ""
        
        # 2. Наполняем ее данными
        if tasks_data:
            summary_text += "*Задачи по Матрице:*\n"
            for key, val in tasks_data.items():
                summary_text += f"_{escape_markdown(key)}_ `{escape_markdown(val) if val is not None else '-'}`\n"
        if periods_data and "Бизнес периоды" in periods_data:
            summary_text += "\n*Бизнес Периоды:*\n"
            for key, val in periods_data["Бизнес периоды"].items():
                summary_text += f"_{escape_markdown(key)}_: `{escape_markdown(val) if val is not None else '-'}`\n"
        # --- КОНЕЦ ВОССТАНОВЛЕННОГО БЛОКА ---
        
        # 3. Теперь эта проверка корректна
        if summary_text:
            await context.bot.send_message(chat_id=query.message.chat_id, text=header + summary_text, parse_mode=ParseMode.MARKDOWN_V2)
        
        # Отправка кнопок с подробными описаниями
        if full_descriptions:
            description_keys = list(full_descriptions.keys())
            keyboard = [
                [InlineKeyboardButton(text=key, callback_data=f"key_{key}")]
                for key in description_keys
            ]
            keyboard.append([InlineKeyboardButton("📥 Скачать результат в .txt", callback_data="DOWNLOAD_FILE")])
            keyboard.append([InlineKeyboardButton("✅ Завершить", callback_data="END_CONVERSATION")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Выберите точку для получения подробного описания или скачайте полный отчет:",
                reply_markup=reply_markup
            )
            return SHOW_DESCRIPTION
        else:
            await context.bot.send_message(chat_id=query.message.chat_id, text="❌ Подробные описания не были сформированы.")
            return await end_conversation(update, context)

    except Exception as e:
        logger.error(f"Ошибка при расчете или отправке: {e}", exc_info=True)
        await context.bot.send_message(chat_id=query.message.chat_id, text=r"❌ Произошла внутренняя ошибка\. Попробуйте позже\.")
        return ConversationHandler.END

async def show_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    MAX_MESSAGE_LENGTH = 4096

    try:
        # ПРАВИЛЬНАЯ ЛОГИКА: извлекаем ключ из callback_data
        selected_key = query.data.split('_', 1)[1]
    except IndexError:
        await query.edit_message_text(text="❌ Ошибка данных кнопки.")
        return SHOW_DESCRIPTION

    full_descriptions = context.user_data.get('full_descriptions', {})
    description_text = full_descriptions.get(selected_key, "Описание для этой точки не было найдено.")
    
    formatted_value = description_text.replace('**', '*').replace('\n\n', '\n')
    message_text = f"*{escape_markdown(selected_key)}*\n\n{escape_markdown(formatted_value)}"
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад к списку", callback_data="BACK_TO_LIST")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        if len(message_text) > MAX_MESSAGE_LENGTH:
            cutoff_point = MAX_MESSAGE_LENGTH - 200
            message_text = message_text[:cutoff_point] + (r"\n\n\.\.\." r"\n\n*\[Полная версия в файле для скачивания\]*")
        await query.edit_message_text(text=message_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.error(f"Не удалось отправить описание для ключа '{selected_key}': {e}", exc_info=True)
        await query.edit_message_text(text=r"❌ Ошибка отображения\. Скачайте полный отчет в виде файла\.", reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    
    return SHOW_DESCRIPTION


async def back_to_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    full_descriptions = context.user_data.get('full_descriptions', {})
    
    if full_descriptions:
        # ПРАВИЛЬНАЯ ЛОГИКА: создаем кнопки так же, как в get_gender
        keyboard = [
            [InlineKeyboardButton(text=key, callback_data=f"key_{key}")]
            for key in full_descriptions.keys()
        ]
        keyboard.append([InlineKeyboardButton("📥 Скачать результат в .txt", callback_data="DOWNLOAD_FILE")])
        keyboard.append([InlineKeyboardButton("✅ Завершить", callback_data="END_CONVERSATION")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Выберите точку для получения подробного описания:", reply_markup=reply_markup)
    else:
        await query.edit_message_text("Список описаний пуст.")
    return SHOW_DESCRIPTION


# Функции send_results_as_file, end_conversation, cancel остаются без изменений...
async def send_results_as_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # ...
    return SHOW_DESCRIPTION
async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # ...
    return ConversationHandler.END
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # ...
    return ConversationHandler.END


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GET_DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dob)],
            GET_GENDER: [CallbackQueryHandler(get_gender, pattern="^Ж$|^М$")],
            SHOW_DESCRIPTION: [
                CallbackQueryHandler(back_to_list, pattern="^BACK_TO_LIST$"),
                CallbackQueryHandler(end_conversation, pattern="^END_CONVERSATION$"),
                CallbackQueryHandler(send_results_as_file, pattern="^DOWNLOAD_FILE$"),
                # ПРАВИЛЬНАЯ ЛОГИКА: паттерн для распознавания кнопок
                CallbackQueryHandler(show_description, pattern=r"^key_")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    print("Бот запущен...")
    application.run_polling()


if __name__ == "__main__": 
    main()