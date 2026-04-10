import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.db import init_db
from handlers import start, checkin, history, stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    init_db()
    logger.info("База данных готова.")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Порядок важен: checkin содержит общий cancel-хэндлер,
    # поэтому его регистрируем раньше start и stats.
    dp.include_router(checkin.router)
    dp.include_router(start.router)
    dp.include_router(history.router)
    dp.include_router(stats.router)

    logger.info("Завершение предыдущей сессии Telegram...")
    try:
        await bot.log_out()
    except Exception as e:
        logger.warning("log_out() завершился с ошибкой (игнорируем): %s", e)

    logger.info("Бот запущен.")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
