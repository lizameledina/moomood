import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, DEEPSEEK_API_KEY
from database.db import init_db
from handlers import ai, start, checkin, history, stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Меняй при правках, чтобы в логе было видно, что запущена новая версия
MOODBOT_BUILD = "2026-04-12-ignore-mention"


async def main() -> None:
    root = Path(__file__).resolve().parent
    logger.info("Сборка %s", MOODBOT_BUILD)
    logger.info("Рабочая папка бота: %s", root)
    logger.info("Файл bot.py: %s", Path(__file__).resolve())

    init_db()
    logger.info("База данных готова.")
    logger.info("DeepSeek key set: %s (len=%d)", bool(DEEPSEEK_API_KEY), len(DEEPSEEK_API_KEY))

    bot = Bot(token=BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)

    dp = Dispatcher(storage=MemoryStorage())

    # Сначала общие команды и экраны (/start, история, статистика),
    # затем сценарий чек-ина (широкие FSM-хэндлеры и cancel).
    dp.include_router(start.router)
    dp.include_router(ai.router)
    dp.include_router(history.router)
    dp.include_router(stats.router)
    dp.include_router(checkin.router)

    logger.info("Бот запущен.")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
