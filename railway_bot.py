import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from bot_core import BetboomBot

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальный экземпляр бота
bot = BetboomBot()

# Токен бота из переменных окружения
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        return

    await update.message.reply_text(
        "🎰 *Betboom Bot 24/7* 🎰\n\n"
        "Доступные команды:\n"
        "/promo CODE - Активировать промокод\n"
        "/status - Статус бота\n"
        "/history - История операций\n\n"
        "Или просто присылай промокоды сообщениями!",
        parse_mode='Markdown'
    )


async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Активация промокода"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        return

    if not context.args:
        await update.message.reply_text("❌ Укажите промокод: /promo CODE123")
        return

    promocode = context.args[0]

    # Отправляем сообщение о начале обработки
    processing_msg = await update.message.reply_text(f"⏳ Активирую промокод: `{promocode}`...", parse_mode='Markdown')

    try:
        # Активируем промокод
        result = await bot.process_single_promocode(promocode)

        if result['success']:
            await processing_msg.edit_text(f"✅ *Успех!*\nПромокод: `{promocode}`\nРезультат: {result['message']}",
                                           parse_mode='Markdown')
        else:
            await processing_msg.edit_text(f"❌ *Ошибка!*\nПромокод: `{promocode}`\nОшибка: {result['message']}",
                                           parse_mode='Markdown')

    except Exception as e:
        await processing_msg.edit_text(f"💥 *Критическая ошибка!*\nПромокод: `{promocode}`\nОшибка: {str(e)}",
                                       parse_mode='Markdown')


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статус бота"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        return

    status_msg = "🤖 *Статус Betboom Bot*\n\n"
    status_msg += "✅ Бот работает 24/7\n"
    status_msg += "🌐 Облачный сервер\n"
    status_msg += "⚡ Всегда онлайн\n"
    status_msg += f"👑 Админы: {len(ADMIN_IDS)}\n\n"
    status_msg += "Используй /promo CODE для активации"

    await update.message.reply_text(status_msg, parse_mode='Markdown')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка обычных сообщений с промокодами"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    message_text = update.message.text

    # Автоматически ищем промокоды в сообщении
    promocodes = bot.PROMOCODE_PATTERN.findall(message_text)

    if promocodes:
        for promocode in promocodes:
            await update.message.reply_text(f"🔍 Найден промокод: `{promocode}`\nАктивирую...", parse_mode='Markdown')

            try:
                result = await bot.process_single_promocode(promocode)

                if result['success']:
                    await update.message.reply_text(f"✅ Успех: `{promocode}`", parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"❌ Ошибка `{promocode}`: {result['message']}",
                                                    parse_mode='Markdown')

            except Exception as e:
                await update.message.reply_text(f"💥 Ошибка: {str(e)}")


async def init_bot():
    """Инициализация бота при запуске"""
    logger.info("🚀 Инициализация Betboom Bot...")
    success = await bot.init_browser()
    if success:
        logger.info("✅ Betboom Bot готов к работе")
    else:
        logger.error("❌ Не удалось инициализировать бота")


def main():
    """Основная функция"""
    if not BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен")
        return

    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("promo", promo_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    logger.info("🤖 Запуск Telegram Bot...")
    application.run_polling()


if __name__ == "__main__":
    # Инициализируем и запускаем
    asyncio.run(init_bot())
    main()
