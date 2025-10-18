import os
import asyncio
import logging
import re
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '8370087721').split(',')]

class SimpleBetboomBot:
    def __init__(self):
        self.PROMOCODE_PATTERN = re.compile(r'\b[A-Za-z0-9]{5,20}\b')
        self.activation_history = []
    
    def activate_promocode(self, promocode):
        """Имитация активации промокода"""
        try:
            # Имитируем задержку как при реальной активации
            time.sleep(2)
            
            # В реальной версии здесь будет работа с Betboom
            # Сейчас просто имитируем успешную активацию
            success = True
            message = "✅ Промокод успешно активирован"
            
            # Сохраняем в историю
            self.activation_history.append({
                'promocode': promocode,
                'success': success,
                'timestamp': time.time()
            })
            
            return success, message
            
        except Exception as e:
            return False, f"❌ Ошибка активации: {str(e)}"

bot = SimpleBetboomBot()

def start_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        update.message.reply_text("❌ Доступ запрещен")
        return
    
    update.message.reply_text(
        "🎰 *Betboom Bot 24/7* 🎰\n\n"
        "🤖 Бот работает в облаке!\n"
        "⏰ 24/7 без перерывов\n\n"
        "*Команды:*\n"
        "/promo CODE - Активировать промокод\n" 
        "/status - Статус бота\n"
        "/history - История активаций\n\n"
        "📨 Или просто присылай промокоды в сообщениях!",
        parse_mode='Markdown'
    )

def promo_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        update.message.reply_text("❌ Доступ запрещен")
        return
    
    if not context.args:
        update.message.reply_text("❌ Укажите промокод: /promo CODE123")
        return
    
    promocode = context.args[0]
    processing_msg = update.message.reply_text(f"⏳ Активирую промокод: `{promocode}`...", parse_mode='Markdown')
    
    try:
        success, message = bot.activate_promocode(promocode)
        if success:
            processing_msg.edit_text(f"✅ *Успех!*\nПромокод: `{promocode}`\n{message}", parse_mode='Markdown')
        else:
            processing_msg.edit_text(f"❌ *Ошибка!*\nПромокод: `{promocode}`\n{message}", parse_mode='Markdown')
    except Exception as e:
        processing_msg.edit_text(f"💥 Критическая ошибка: {str(e)}")

def status_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    
    status_msg = (
        "🤖 *Статус Betboom Bot*\n\n"
        "✅ Бот работает 24/7\n"
        "🌐 Облачный сервер Render\n"
        "⚡ Всегда онлайн\n"
        f"📊 Активаций: {len(bot.activation_history)}\n"
        f"👑 Админ: {ADMIN_IDS[0]}\n\n"
        "Используй /promo CODE для активации"
    )
    
    update.message.reply_text(status_msg, parse_mode='Markdown')

def history_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    
    if not bot.activation_history:
        update.message.reply_text("📝 История активаций пуста")
        return
    
    history_text = "📝 *Последние активации:*\n\n"
    for i, item in enumerate(list(reversed(bot.activation_history))[-10:], 1):
        status = "✅" if item['success'] else "❌"
        history_text += f"{i}. {status} `{item['promocode']}`\n"
    
    update.message.reply_text(history_text, parse_mode='Markdown')

def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    
    message_text = update.message.text
    promocodes = bot.PROMOCODE_PATTERN.findall(message_text)
    
    if promocodes:
        for promocode in promocodes[:3]:  # Максимум 3 промокода за раз
            update.message.reply_text(f"🔍 Найден промокод: `{promocode}`\nАктивирую...", parse_mode='Markdown')
            
            try:
                success, message = bot.activate_promocode(promocode)
                if success:
                    update.message.reply_text(f"✅ Успех: `{promocode}`", parse_mode='Markdown')
                else:
                    update.message.reply_text(f"❌ Ошибка: `{promocode}` - {message}", parse_mode='Markdown')
            except Exception as e:
                update.message.reply_text(f"💥 Ошибка: {str(e)}")

def main():
    if not BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен")
        return
        
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Добавляем обработчики
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("promo", promo_command))
    dp.add_handler(CommandHandler("status", status_command))
    dp.add_handler(CommandHandler("history", history_command))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    logger.info("🤖 Запуск Telegram Bot...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    import time
    main()
