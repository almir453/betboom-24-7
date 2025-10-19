import logging
import requests
import re
import asyncio
from telethon import TelegramClient, events
from playwright.async_api import async_playwright
import os
import random
import pickle

# === Конфигурация ===
API_ID = 21658972
API_HASH = '175d08b358ee5a8c3c7f9555e90c7380'
SESSION_NAME = 'my_session'
BOT_TOKEN = "7996821935:AAG4TMSyo_00gW0tcv5D7Ojosu09edG8Tyk"
CHAT_ID = "8370087721"

# ID отслеживаемых групп
GROUP_IDS = [-1002445382077, -1003125973812, -1002276863165, -1007994393341]

# === Регулярное выражение для поиска промокодов ===
PROMOCODE_PATTERN = re.compile(
    r'\b(?!BETBOOM\b)(?!SLIV_FRIXA\b)(?!twitch\b)(?!shadowkekw\b)(?!https\b)([A/-Za-z0-9]{5,20})\b',
    re.IGNORECASE
)

# === Логирование ===
class TelegramLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        send_log_to_telegram(log_entry)


def send_log_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Ошибка отправки лога в Telegram: {e}")


logger = logging.getLogger("__main__")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(console_handler)
telegram_handler = TelegramLogHandler()
logger.addHandler(telegram_handler)
logger.info("✅ Бот запущен, логи отправляются в консоль и Telegram.")

# === Инициализация Telegram-клиента ===
client = TelegramClient(SESSION_NAME, API_ID, API_HASH, timeout=10)

# === Playwright и работа с куками ===
browser = None
page = None


async def save_cookies(page, file_path="cookies.pkl"):
    cookies = await page.context.cookies()
    with open(file_path, "wb") as f:
        pickle.dump(cookies, f)
    logger.info(f"🍪 Куки сохранены в файл {file_path}.")


async def load_cookies(page, file_path="cookies.pkl"):
    if os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                cookies = pickle.load(f)
            await page.context.add_cookies(cookies)
            logger.info("✅ Куки загружены успешно.")
        except Exception as e:
            logger.error(f"⚠️ Ошибка загрузки куки: {e}")


async def init_playwright():
    global browser, page
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    page = await context.new_page()
    await load_cookies(page)
    await page.goto("https://betboom.ru/actions#online", timeout=60000)
    await save_cookies(page)


# === Ввод промокодов ===
async def enter_promocode(promocode):
    try:
        await page.wait_for_selector("#promocode", timeout=3000)
        await page.locator("#promocode").fill(promocode)
        await page.locator("#buttonpromo").click()
        logger.info(f"✅ Промокод '{promocode}' введён.")
        return True
    except Exception as e:
        logger.error(f"⚠️ Ошибка при вводе промокода '{promocode}': {e}")
        return False


async def check_errors():
    try:
        await asyncio.sleep(4)
        error_element = await page.query_selector("span.Alert__AlertText-sc-1389vo9-1")
        if error_element:
            error_text = (await error_element.inner_text()).strip().lower()
            logger.info(f"⚠️ Ошибка: {error_text}")
            return error_text
    except Exception as e:
        logger.error(f"⚠️ Ошибка при проверке ошибок: {e}")


async def human_like_delay():
    delay = random.uniform(0.7, 0.8)
    await asyncio.sleep(delay)
    logger.info(f"⏳ Задержка: {delay:.2f} секунд.")


async def enter_promocode_with_retry(promocode):
    first_attempt = True
    while True:
        if first_attempt:
            logger.info(f"🔁 Первая попытка ввода промокода: {promocode}")
            success = await enter_promocode(promocode)
            first_attempt = False
        else:
            logger.info(f"🔁 Повторная попытка ввода промокода: {promocode}")
            await human_like_delay()
            success = await enter_promocode(promocode)

        if success:
            error = await check_errors()
            if error:
                if "технические работы" in error:
                    logger.info(f"⚠️ Ошибка '{error}', повтор через 0.9 секунды.")
                    await asyncio.sleep(0.9)
                    continue
                elif "лимит" in error or "активирован" in error or "не существует" in error:
                    logger.info(f"❌ Промокод '{promocode}' не применён: {error}")
                    return False
                else:
                    logger.info(f"✅ Промокод '{promocode}' успешно применён! (неизвестная ошибка)")
                    return True
            else:
                logger.info(f"✅ Промокод '{promocode}' успешно применён (без ошибок)!")
                return True
        else:
            await asyncio.sleep(0.5)


# === Обработка новых сообщений ===
@client.on(events.NewMessage(chats=GROUP_IDS))
async def handler(event):
    message_text = event.message.text.strip() if event.message.text else ""
    logger.info(f"📩 Получено сообщение: {repr(message_text)}")

    promocodes = [p for p in PROMOCODE_PATTERN.findall(message_text)]

    if promocodes:
        logger.info(f"🔍 Найдены промокоды: {promocodes}")
        tasks = [enter_promocode_with_retry(promocode) for promocode in promocodes]
        await asyncio.gather(*tasks)
    else:
        logger.info("⚠️ Промокоды не найдены.")


# === Основная функция ===
async def main():
    try:
        await init_playwright()
        logger.info("🚀 Telegram клиент запускается...")
        await client.start()
        logger.info("✅ Telegram клиент запущен.")
        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    finally:
        if browser is not None:
            await browser.close()
        await client.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚠️ Программа завершена пользователем.")
    except Exception as e:
        logger.error(f"❌ Ошибка в главной функции: {e}")
