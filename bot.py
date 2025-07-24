# Файл: telegram_bot.py

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

# --- Определяем состояния для нашего диалога ---
# GET_... - для сбора данных, SHOW_... - для показа результатов
GET_NAME, GET_DOB, GET_GENDER, SHOW_DESCRIPTION = range(4)


def escape_markdown(text: str) -> str:
    """Экранирует специальные символы для Telegram MarkdownV2."""
    if not isinstance(text, str):
        text = str(text)
    escape_chars = r'_*[]()~`>#+-.=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает диалог и запрашивает имя."""
    # Очищаем данные от предыдущих сессий на всякий случай
    context.user_data.clear()
    await update.message.reply_text(
        r"👋 Здравствуйте\! Я бот для психологической диагностики\."
        r"\n\nЧтобы начать, пожалуйста, введите Ваше имя\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return GET_NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет имя и запрашивает дату рождения."""
    context.user_data['name'] = update.message.text
    logger.info(f"Имя пользователя: {context.user_data['name']}")
    await update.message.reply_text(
        rf"Отлично, {escape_markdown(context.user_data['name'])}\! Теперь введите Вашу дату рождения в формате *ДД\.ММ\.ГГГГ*\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return GET_DOB


async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет дату рождения и запрашивает пол."""
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
    """Сохраняет пол, запускает расчет и отправляет кнопки с результатами."""
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
        # 1. Расчеты
        person_mod = PGD_Person_Mod(name, date_str, gender_char)
        main_cup_data = person_mod.calculate_points()
        tasks_data = person_mod.tasks()
        periods_data = person_mod.periods_person()
        
        if not isinstance(main_cup_data, dict):
            raise ValueError(f"Ошибка при расчете основной матрицы: {main_cup_data}")

        # 2. Обработка текста
        processor = PersonalityProcessor(main_cup_data)
        full_descriptions = processor.get_full_description()
        
        # --- СОХРАНЯЕМ РЕЗУЛЬТАТЫ В ПАМЯТИ ДИАЛОГА ---
        context.user_data['full_descriptions'] = full_descriptions

        # 3. Отправка сводных данных
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
        
        await context.bot.send_message(chat_id=query.message.chat_id, text=header + summary_text, parse_mode=ParseMode.MARKDOWN_V2)
        
        # 4. Формирование и отправка кнопок
        if full_descriptions:
            keyboard = [[InlineKeyboardButton(text=key, callback_data=key)] for key in full_descriptions.keys()]
            # Добавляем кнопку для завершения
            keyboard.append([InlineKeyboardButton("✅ Завершить", callback_data="END_CONVERSATION")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Выберите точку для получения подробного описания:",
                reply_markup=reply_markup
            )
            # ПЕРЕХОДИМ В СОСТОЯНИЕ ОЖИДАНИЯ НАЖАТИЯ КНОПКИ
            return SHOW_DESCRIPTION
        else:
            await context.bot.send_message(chat_id=query.message.chat_id, text="❌ Подробные описания не были сформированы.")
            return await end_conversation(update, context) # Завершаем, если нет описаний

    except Exception as e:
        logger.error(f"Ошибка при расчете или отправке: {e}", exc_info=True)
        await context.bot.send_message(chat_id=query.message.chat_id, text=r"❌ Произошла внутренняя ошибка\. Попробуйте позже\.")
        return ConversationHandler.END


async def show_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает описание для выбранной точки."""
    query = update.callback_query
    await query.answer()

    # Получаем ключ из callback_data
    selected_key = query.data
    
    # Достаем сохраненные описания
    full_descriptions = context.user_data.get('full_descriptions', {})

    if not full_descriptions or selected_key not in full_descriptions:
        await query.edit_message_text(text="❌ Описание не найдено. Возможно, сессия устарела.")
        return SHOW_DESCRIPTION

    description_text = full_descriptions[selected_key]
    formatted_value = description_text.replace('**', '*').replace('\n\n', '\n')
    
    # Формируем новое сообщение с описанием и кнопкой "назад"
    message_text = f"*{escape_markdown(selected_key)}*\n\n{escape_markdown(formatted_value)}"
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад к списку", callback_data="BACK_TO_LIST")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Редактируем исходное сообщение, показывая текст
    await query.edit_message_text(text=message_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    
    return SHOW_DESCRIPTION


async def back_to_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Возвращает пользователя к списку кнопок."""
    query = update.callback_query
    await query.answer()
    
    full_descriptions = context.user_data.get('full_descriptions', {})
    
    if full_descriptions:
        keyboard = [[InlineKeyboardButton(text=key, callback_data=key)] for key in full_descriptions.keys()]
        keyboard.append([InlineKeyboardButton("✅ Завершить", callback_data="END_CONVERSATION")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Редактируем сообщение, снова показывая список
        await query.edit_message_text(
            text="Выберите точку для получения подробного описания:",
            reply_markup=reply_markup
        )
    else:
        await query.edit_message_text("Список описаний пуст.")

    return SHOW_DESCRIPTION


async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Корректно завершает диалог."""
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(text="✅ Анализ завершен\. Чтобы начать новый, отправьте команду /start\.", parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text("✅ Анализ завершен\. Чтобы начать новый, отправьте команду /start\.", parse_mode=ParseMode.MARKDOWN_V2)

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет текущий диалог."""
    await update.message.reply_text(r"Действие отменено\. Чтобы начать заново, введите /start\.")
    context.user_data.clear()
    return ConversationHandler.END


def main() -> None:
    """Запускает бота."""
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GET_DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dob)],
            GET_GENDER: [CallbackQueryHandler(get_gender, pattern="^Ж$|^М$")], # Ловит только 'М' или 'Ж'
            SHOW_DESCRIPTION: [
                CallbackQueryHandler(back_to_list, pattern="^BACK_TO_LIST$"),
                CallbackQueryHandler(end_conversation, pattern="^END_CONVERSATION$"),
                # Этот обработчик ловит все остальные нажатия
                CallbackQueryHandler(show_description) 
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    print("Бот запущен...")
    application.run_polling()


if __name__ == "__main__": 
    main()