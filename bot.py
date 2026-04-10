import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.db import init_db
from handlers import start, checkin, history, stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

MAX_RETRIES = 10
RETRY_DELAY_SECONDS = 5


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

    logger.info("Бот запущен.")
    retry_count = 0
    try:
        while True:
            try:
                await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
                break
            except TelegramBadRequest as e:
                if "Logged out" in str(e):
                    retry_count += 1
                    if retry_count > MAX_RETRIES:
                        logger.error(
                            "Превышено максимальное количество попыток (%d). "
                            "Telegram не восстановил сессию. Завершение работы.",
                            MAX_RETRIES,
                        )
                        sys.exit(1)
                    logger.warning(
                        "Telegram вернул 'Logged out'. "
                        "Попытка %d/%d. Повтор через %d сек...",
                        retry_count,
                        MAX_RETRIES,
                        RETRY_DELAY_SECONDS,
                    )
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
                else:
                    raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
