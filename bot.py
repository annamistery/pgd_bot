# Файл: telegram_bot.py

import logging
import os
import re
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
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

# Импортируем ваши рабочие классы
from pgd_bot import PGD_Person_Mod
from cashka_preprocessor import PersonalityProcessor

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv("TOKEN_BOT")

if not BOT_TOKEN:
    print("--- ОШИБКА ---")
    print("Не найден токен для Telegram бота! Убедитесь, что у вас есть файл .env")
    print("И в нем есть строка вида: TOKEN_BOT=12345:ABC-DEF...")
    exit()

GET_NAME, GET_DOB, GET_GENDER, SHOW_DESCRIPTION = range(4)


def escape_markdown(text: str) -> str:
    """Экранирует специальные символы для Telegram MarkdownV2."""
    if not isinstance(text, str):
        text = str(text)
    escape_chars = r'_*[]()~`>#+-.=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def format_results_for_download(name: str, dob: datetime, results: dict, tasks: dict, periods: dict) -> str:
    """Форматирует все результаты в красивую строку для .txt файла."""
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

# --- Функции диалога ---

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
    logger.info(f"Имя пользователя: {context.user_data['name']}")
    await update.message.reply_text(
        rf"Отлично, {escape_markdown(context.user_data['name'])}\! Теперь введите Вашу дату рождения в формате *ДД\.ММ\.ГГГГ*\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return GET_DOB

async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['dob'] = datetime.strptime(update.message.text, '%d.%m.%Y')
        logger.info(f"Дата рождения: {update.message.text}")
        keyboard = [[InlineKeyboardButton("Женский", callback_data="Ж"), InlineKeyboardButton("Мужской", callback_data="М")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(r"Спасибо\! Пожалуйста, выберите Ваш пол:", reply_markup=reply_markup)
        return GET_GENDER
    except ValueError:
        await update.message.reply_text(
            r"❌ *Ошибка формата даты*\."
            r"\n\nПожалуйста, введите дату строго в формате *ДД\.ММ\.ГГГГ* \(например, 09\.10\.1988\)\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return GET_DOB

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    gender_char = query.data
    gender_full = "Женский" if gender_char == "Ж" else "Мужской"
    logger.info(f"Пол: {gender_full}")

    await query.edit_message_text(text=rf"Вы выбрали пол: *{escape_markdown(gender_full)}*\.\n\n⏳ Начинаю расчет\.\.\.", parse_mode=ParseMode.MARKDOWN_V2)

    user_data = context.user_data
    name = user_data['name']
    date_str = user_data['dob'].strftime('%d.%m.%Y')

    try:
        person_mod = PGD_Person_Mod(name, date_str, gender_char)
        main_cup_data = person_mod.calculate_points()
        tasks_data = person_mod.tasks()
        periods_data = person_mod.periods_person()
        
        if not isinstance(main_cup_data, dict):
            raise ValueError(f"Ошибка при расчете основной матрицы: {main_cup_data}")

        processor = PersonalityProcessor(main_cup_data)
        full_descriptions = processor.get_full_description()
        
        context.user_data['full_descriptions'] = full_descriptions
        context.user_data['tasks_data'] = tasks_data
        context.user_data['periods_data'] = periods_data
        
        description_keys = list(full_descriptions.keys())
        context.user_data['description_keys'] = description_keys

        # --- ИСПРАВЛЕНО: Этот блок теперь НАХОДИТСЯ ВНУТРИ TRY ---
        header = f"*Результаты анализа для {escape_markdown(name)} \\({escape_markdown(date_str)}\\)*\n\n"
        summary_text = ""
        if tasks_data:
            summary_text += "*Задачи по Матрице:*\n"
            for key, val in tasks_data.items():
                summary_text += f"_{escape_markdown(key)}_ `{escape_markdown(val) if val is not None else '-'}`\n"
        if periods_data and "Бизнес периоды" in periods_data:
            summary_text += "\n*Бизнес Периоды:*\n"
            for key, val in periods_data["Бизнес периоды"].items():
                summary_text += f"_{escape_markdown(key)}_: `{escape_markdown(val) if val is not None else '-'}`\n"
        
        if summary_text:
            await context.bot.send_message(chat_id=query.message.chat_id, text=header + summary_text, parse_mode=ParseMode.MARKDOWN_V2)
        # --- КОНЕЦ ИСПРАВЛЕННОГО БЛОКА ---

        if full_descriptions:
            keyboard = [
                [InlineKeyboardButton(text=key, callback_data=f"desc_{i}")]
                for i, key in enumerate(description_keys)
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

# Вставьте этот код в telegram_bot.py, заменив старую функцию show_description

async def show_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # Максимальная длина сообщения в Telegram
    MAX_MESSAGE_LENGTH = 4096

    try:
        key_index = int(query.data.split('_')[1])
    except (IndexError, ValueError):
        await query.edit_message_text(text="❌ Ошибка данных кнопки.")
        return SHOW_DESCRIPTION

    description_keys = context.user_data.get('description_keys', [])
    full_descriptions = context.user_data.get('full_descriptions', {})

    if not description_keys or key_index >= len(description_keys):
        await query.edit_message_text(text="❌ Описание не найдено. Возможно, сессия устарела.")
        return SHOW_DESCRIPTION

    selected_key = description_keys[key_index]
    # Используем .get() для большей безопасности
    description_text = full_descriptions.get(selected_key, "Описание для этой точки не было найдено.")
    
    formatted_value = description_text.replace('**', '*').replace('\n\n', '\n')
    message_text = f"*{escape_markdown(selected_key)}*\n\n{escape_markdown(formatted_value)}"
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад к списку", callback_data="BACK_TO_LIST")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        # Проверяем, не превышает ли итоговый текст лимит Telegram
        if len(message_text) > MAX_MESSAGE_LENGTH:
            # Если да, обрезаем его, оставляя место для предупреждения
            cutoff_point = MAX_MESSAGE_LENGTH - 200  # Запас для текста и Markdown-разметки
            message_text = message_text[:cutoff_point] + (
                r"\n\n\.\.\."
                r"\n\n*\[Внимание: Текст был сокращен из\-за ограничений Telegram\. "
                r"Полная версия доступна в файле для скачивания\]*"
            )

        await query.edit_message_text(
            text=message_text, 
            reply_markup=reply_markup, 
            parse_mode=ParseMode.MARKDOWN_V2
        )
    except Exception as e:
        # Логируем ошибку, если что-то пошло не так при отправке
        logger.error(f"Не удалось отправить описание для ключа '{selected_key}': {e}", exc_info=True)
        # Сообщаем пользователю о проблеме
        await query.edit_message_text(
            text=r"❌ Произошла ошибка при отображении этого пункта\. "
                r"Возможно, описание слишком длинное\. Пожалуйста, скачайте полный отчет в виде файла\.",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    return SHOW_DESCRIPTION

async def back_to_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    full_descriptions = context.user_data.get('full_descriptions', {})
    
    if full_descriptions:
        description_keys = context.user_data.get('description_keys', [])
        keyboard = [
            [InlineKeyboardButton(text=key, callback_data=f"desc_{i}")]
            for i, key in enumerate(description_keys)
        ]
        keyboard.append([InlineKeyboardButton("📥 Скачать результат в .txt", callback_data="DOWNLOAD_FILE")])
        keyboard.append([InlineKeyboardButton("✅ Завершить", callback_data="END_CONVERSATION")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="Выберите точку для получения подробного описания или скачайте полный отчет:",
            reply_markup=reply_markup
        )
    else:
        await query.edit_message_text("Список описаний пуст.")

    return SHOW_DESCRIPTION

async def send_results_as_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer(text="Готовлю файл...")

    user_data = context.user_data
    
    if not all(k in user_data for k in ['name', 'dob', 'full_descriptions', 'tasks_data', 'periods_data']):
        await context.bot.send_message(chat_id=query.message.chat_id, text="❌ Недостаточно данных для формирования файла. Попробуйте начать заново /start")
        return SHOW_DESCRIPTION

    file_content = format_results_for_download(
        name=user_data['name'],
        dob=user_data['dob'],
        results=user_data['full_descriptions'],
        tasks=user_data['tasks_data'],
        periods=user_data['periods_data']
    )
    
    file_name = f"analysis_{user_data['name']}_{user_data['dob'].strftime('%Y%m%d')}.txt"
    
    try:
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=bytes(file_content, 'utf-8'),
            filename=file_name
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке файла: {e}", exc_info=True)
        await context.bot.send_message(chat_id=query.message.chat_id, text="❌ Не удалось отправить файл.")
    
    return SHOW_DESCRIPTION

async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(text=r"✅ Анализ завершен\. Чтобы начать новый, отправьте команду /start\.", parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text(r"✅ Анализ завершен\. Чтобы начать новый, отправьте команду /start\.", parse_mode=ParseMode.MARKDOWN_V2)

    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"Пользователь {update.effective_user.first_name} отменил диалог.")
    await update.message.reply_text(
        r"Действие отменено\. Чтобы начать новый анализ, введите /start\.", 
        parse_mode=ParseMode.MARKDOWN_V2
    )
    context.user_data.clear()
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
                CallbackQueryHandler(show_description, pattern=r"^desc_\d+$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__": 
    main()