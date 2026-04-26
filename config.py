import os
from pathlib import Path
from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден. Создай файл .env и добавь туда токен бота.")

DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")

AI_DAILY_LIMIT: int = int(os.getenv("AI_DAILY_LIMIT", "20"))
