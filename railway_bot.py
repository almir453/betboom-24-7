import os
import asyncio
import logging
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '8370087721').split(',')]

class SimpleBetboomBot:
    def __init__(self):
        self.PROMOCODE_PATTERN = re.compile(r'\b[A-Za-z0-9]{5,20}\b')
        self.activation_history = []
    
    async def activate_promocode(self, promocode):
        """Имитация активации промокода"""
        try:
            # Имитируем задержку как при реальной активации
            await asyncio.sleep(2)
            
            # В реальной версии здесь будет работа с Betboom
            # Сейчас просто имитируем успешную активацию
            success = True
            message = "✅ Промокод успешно активирован"
            
            # Сохраняем в историю
            self.activation_history.append({
                'promocode': promocode,
                'success': success,
                'timestamp': asyncio.get_event_loop().time()
            })
            
            return success, message
            
        except Exception as e:
            return False, f"❌ Ошибка активации: {str(e)}"

bot = SimpleBetboomBot()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    await update.message.reply_text(
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

async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Укажите промокод: /promo CODE123")
        return
    
    promocode = context.args[0]
    processing_msg = await update.message.reply_text(f"⏳ Активирую промокод: `{promocode}`...", parse_mode='Markdown')
    
    try:
        success, message = await bot.activate_promocode(promocode)
        if success:
            await processing_msg.edit_text(f"✅ *Успех!*\nПромокод: `{promocode}`\n{message}", parse_mode='Markdown')
        else:
            await processing_msg.edit_text(f"❌ *Ошибка!*\nПромокод: `{promocode}`\n{message}", parse_mode='Markdown')
    except Exception as e:
        await processing_msg.edit_text(f"💥 Критическая ошибка: {str(e)}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    await update.message.reply_text(status_msg, parse_mode='Markdown')

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    
    if not bot.activation_history:
        await update.message.reply_text("📝 История активаций пуста")
        return
    
    history_text = "📝 *Последние активации:*\n\n"
    for i, item in enumerate(list(reversed(bot.activation_history))[-10:], 1):
        status = "✅" if item['success'] else "❌"
        history_text += f"{i}. {status} `{item['promocode']}`\n"
    
    await update.message.reply_text(history_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    
    message_text = update.message.text
    promocodes = bot.PROMOCODE_PATTERN.findall(message_text)
    
    if promocodes:
        for promocode in promocodes[:3]:  # Максимум 3 промокода за раз
            await update.message.reply_text(f"🔍 Найден промокод: `{promocode}`\nАктивирую...", parse_mode='Markdown')
            
            try:
                success, message = await bot.activate_promocode(promocode)
                if success:
                    await update.message.reply_text(f"✅ Успех: `{promocode}`", parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"❌ Ошибка: `{promocode}` - {message}", parse_mode='Markdown')
            except Exception as e:
                await update.message.reply_text(f"💥 Ошибка: {str(e)}")

def main():
    if not BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен")
        return
        
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("promo", promo_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("🤖 Запуск Telegram Bot...")
    application.run_polling()

if __name__ == "__main__":
    main()
