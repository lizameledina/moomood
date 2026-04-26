import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден. Создай файл .env и добавь туда токен бота.")

DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "")
DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "")

AI_DAILY_LIMIT: int = int(os.getenv("AI_DAILY_LIMIT", "20"))
