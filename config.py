import os
from pathlib import Path
from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден. Создай файл .env и добавь туда токен бота.")

def _read_env_value_from_file(path: Path, key: str) -> str:
    if not path.exists():
        return ""
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if not line.startswith(f"{key}="):
                continue
            value = line.split("=", 1)[1].strip()
            if value.startswith(("\"", "'")) and value.endswith(("\"", "'")) and len(value) >= 2:
                value = value[1:-1]
            return value
    except Exception:
        return ""
    return ""


def _sanitize_env_value(value: str) -> str:
    value = value.strip()
    if value.startswith(("\"", "'")) and value.endswith(("\"", "'")) and len(value) >= 2:
        value = value[1:-1]
    return value.strip()


DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    DEEPSEEK_API_KEY = _read_env_value_from_file(_ENV_PATH, "DEEPSEEK_API_KEY")
DEEPSEEK_API_KEY = _sanitize_env_value(DEEPSEEK_API_KEY)

AI_DAILY_LIMIT: int = int(os.getenv("AI_DAILY_LIMIT", "20"))
