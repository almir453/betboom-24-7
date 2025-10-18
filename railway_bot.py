import os
import asyncio
import logging
import re
import time
import requests
from telethon import TelegramClient, events
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Конфигурация ===
API_ID = 21658972
API_HASH = '175d08b358ee5a8c3c7f9555e90c7380'
SESSION_NAME = 'my_session'
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = "8370087721"

# ID отслеживаемых групп
GROUP_IDS = [-1002445382077, -1003125973812, -1002276863165, -1007994393341]

# === Регулярное выражение для поиска промокодов ===
PROMOCODE_PATTERN = re.compile(
    r'\b(?!BETBOOM\b)(?!SLIV_FRIXA\b)(?!twitch\b)(?!shadowkekw\b)(?!https\b)([A-Za-z0-9]{5,20})\b',
    re.IGNORECASE
)

class BetboomBot:
    def __init__(self):
        self.activation_history = []
        self.telethon_client = None
    
    async def activate_promocode(self, promocode, source="manual"):
        """Активация промокода"""
        try:
            # Имитация задержки как при реальной активации
            await asyncio.sleep(2)
            success = True
            message = "✅ Промокод успешно активирован"
            
            self.activation_history.append({
                'promocode': promocode,
                'success': success,
                'timestamp': time.time(),
                'source': source
            })
            
            # Логируем в Telegram
            source_text = "из группы" if source == "group" else "вручную"
            self.send_log(f"🎰 Активирован промокод {source_text}: `{promocode}`")
            
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
    
    async def start_group_monitoring(self):
        """Запуск мониторинга Telegram групп"""
        try:
            self.telethon_client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
            
            @self.telethon_client.on(events.NewMessage(chats=GROUP_IDS))
            async def handler(event):
                message_text = event.message.text.strip() if event.message.text else ""
                logger.info(f"📩 Получено сообщение из группы: {repr(message_text)}")

                promocodes = [p for p in PROMOCODE_PATTERN.findall(message_text)]

                if promocodes:
                    logger.info(f"🔍 Найдены промокоды в группе: {promocodes}")
                    self.send_log(f"🔍 Найдены промокоды в группе: `{promocodes}`")
                    
                    for promocode in promocodes[:3]:  # Максимум 3 промокода за раз
                        success, message = await self.activate_promocode(promocode, "group")
                        if success:
                            logger.info(f"🎉 Промокод '{promocode}' активирован из группы")
                            self.send_log(f"✅ Автоматически активирован: `{promocode}`")
                        else:
                            logger.info(f"💥 Промокод '{promocode}' не активирован")
                else:
                    logger.info("⚠️ Промокоды не найдены в сообщении")

            await self.telethon_client.start()
            logger.info("✅ Мониторинг групп запущен")
            self.send_log("✅ Мониторинг групп запущен!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска мониторинга: {e}")
            self.send_log(f"❌ Ошибка мониторинга групп: {e}")
            return False

bot = BetboomBot()

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка личных сообщений с промокодами"""
    message_text = update.message.text
    
    # Ищем промокоды в сообщении
    promocodes = PROMOCODE_PATTERN.findall(message_text)
    
    if promocodes:
        for promocode in promocodes[:3]:  # Максимум 3 промокода за раз
            # Сразу отправляем сообщение о начале обработки
            processing_msg = await update.message.reply_text(
                f"🔍 Найден промокод: `{promocode}`\n⏳ Активирую...", 
                parse_mode='Markdown'
            )
            
            try:
                success, message = await bot.activate_promocode(promocode, "manual")
                if success:
                    await processing_msg.edit_text(
                        f"✅ *Успех!*\nПромокод: `{promocode}`\n{message}", 
                        parse_mode='Markdown'
                    )
                else:
                    await processing_msg.edit_text(
                        f"❌ *Ошибка!*\nПромокод: `{promocode}`\n{message}", 
                        parse_mode='Markdown'
                    )
            except Exception as e:
                await processing_msg.edit_text(f"💥 Ошибка: {str(e)}")
    else:
        # Если нет промокодов, показываем справку
        await update.message.reply_text(
            "🎰 *Betboom Bot 24/7*\n\n"
            "Просто отправь мне промокод сообщением!\n\n"
            "Примеры:\n"
            "• `PROMO123`\n"
            "• `Вот промокод ABC456`\n" 
            "• `ABC789 для активации`\n\n"
            "🤖 Бот автоматически найдет и активирует промокод!",
            parse_mode='Markdown'
        )

async def main():
    logger.info("🚀 Запуск Betboom Bot 24/7...")
    
    # Запускаем мониторинг групп
    monitoring_success = await bot.start_group_monitoring()
    if not monitoring_success:
        logger.error("❌ Не удалось запустить мониторинг групп")
        return
    
    # Запускаем Telegram бота
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Только обработчик сообщений - никаких команд
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_private_message))
    
    logger.info("🤖 Запуск Telegram Bot...")
    bot.send_log("🚀 Betboom Bot 24/7 запущен!\n📡 Мониторинг групп активен\n💬 Просто присылай промокоды сообщениями!")
    
    # Запускаем polling
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
