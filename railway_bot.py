import os
import asyncio
import logging
import re
import time
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = "8370087721"

# ID групп для мониторинга (ИНФОРМАЦИЯ)
GROUP_IDS = [-1002445382077, -1003125973812, -1002276863165, -1007994393341]

class BetboomBot:
    def __init__(self):
        self.activation_history = []
    
    async def activate_promocode(self, promocode):
        """Имитация активации промокода"""
        try:
            await asyncio.sleep(2)
            success = True
            message = "✅ Промокод успешно активирован"
            
            self.activation_history.append({
                'promocode': promocode,
                'success': success,
                'timestamp': time.time()
            })
            
            # Логируем в Telegram
            self.send_log(f"🎰 Активирован промокод: `{promocode}`")
            
            return success, message
            
        except Exception as e:
            error_msg = f"❌ Ошибка: {str(e)}"
            self.send_log(f"💥 {error_msg}")
            return False, error_msg
    
    def send_log(self, message):
        """Отправка логов в Telegram"""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, json=payload)
        except Exception as e:
            logger.error(f"Ошибка отправки лога: {e}")

bot = BetboomBot()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎰 *Betboom Bot 24/7* 🎰\n\n"
        "🤖 *Режим работы:*\n"
        "• Ручная активация промокодов\n"
        "• Логирование операций\n" 
        "• Работа 24/7 в облаке\n\n"
        "*Команды:*\n"
        "/promo CODE - Активировать промокод\n"
        "/status - Статус системы\n\n"
        "📝 Отправь промокод сообщением или через /promo",
        parse_mode='Markdown'
    )

async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Укажите промокод: /promo CODE123")
        return
    
    promocode = context.args[0]
    processing_msg = await update.message.reply_text(f"⏳ Активирую: `{promocode}`...", parse_mode='Markdown')
    
    try:
        success, message = await bot.activate_promocode(promocode)
        if success:
            await processing_msg.edit_text(f"✅ *Успех!*\n`{promocode}`\n{message}", parse_mode='Markdown')
        else:
            await processing_msg.edit_text(f"❌ *Ошибка!*\n`{promocode}`\n{message}", parse_mode='Markdown')
    except Exception as e:
        await processing_msg.edit_text(f"💥 Ошибка: {str(e)}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = (
        "🤖 *Статус Betboom Bot*\n\n"
        "✅ Бот работает 24/7\n"
        "🌐 Облачный сервер Render\n" 
        f"📊 Активаций: {len(bot.activation_history)}\n"
        "⚡ Все системы работают\n\n"
        "Используй /promo CODE"
    )
    await update.message.reply_text(status_msg, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    
    # Простой поиск промокодов (слова из 5-20 символов)
    promocodes = re.findall(r'\b[A-Za-z0-9]{5,20}\b', message_text)
    
    if promocodes:
        for promocode in promocodes[:2]:
            await update.message.reply_text(f"🔍 Найден: `{promocode}`\nАктивирую...", parse_mode='Markdown')
            try:
                success, message = await bot.activate_promocode(promocode)
                if success:
                    await update.message.reply_text(f"✅ Успех: `{promocode}`", parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"❌ Ошибка: `{promocode}`", parse_mode='Markdown')
            except Exception as e:
                await update.message.reply_text(f"💥 Ошибка: {str(e)}")

def main():
    if not BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен")
        return
        
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("promo", promo_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("🤖 Запуск Telegram Bot...")
    bot.send_log("🚀 Betboom Bot 24/7 запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()
