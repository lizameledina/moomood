import re
import asyncio

from aiogram import F, Router
from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from database.db import get_daily_series, get_user_timezone
from keyboards.keyboards import analytics_keyboard
from utils.analytics import build_analytics_html

router = Router()

DEFAULT_PERIOD = "7"
DEFAULT_METRIC = "m"

ANALYTICS_CB = re.compile(r"^a(7|30|0)(m|e|r|h)$")


def _parse_analytics_cb(data: str) -> tuple[str, str] | None:
    m = ANALYTICS_CB.match(data)
    if not m:
        return None
    return m.group(1), m.group(2)


class AnalyticsCallbackFilter(Filter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return _parse_analytics_cb(callback.data) is not None


async def build_analytics_message(user_id: int, period: str, metric: str) -> str:
    tz_name = await asyncio.to_thread(get_user_timezone, user_id)
    rows = await asyncio.to_thread(get_daily_series, user_id, tz_name, period)
    return build_analytics_html(rows, period, metric)


async def send_analytics_default(message: Message, user_id: int) -> None:
    text = await build_analytics_message(user_id, DEFAULT_PERIOD, DEFAULT_METRIC)
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=analytics_keyboard(DEFAULT_PERIOD, DEFAULT_METRIC),
    )


@router.message(F.text == "Статистика")
async def show_stats(message: Message) -> None:
    await send_analytics_default(message, message.from_user.id)


@router.callback_query(F.data == "goto_stats")
async def goto_stats(callback: CallbackQuery) -> None:
    text = await build_analytics_message(callback.from_user.id, DEFAULT_PERIOD, DEFAULT_METRIC)
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=analytics_keyboard(DEFAULT_PERIOD, DEFAULT_METRIC),
    )
    await callback.answer()


@router.callback_query(AnalyticsCallbackFilter())
async def analytics_change(callback: CallbackQuery) -> None:
    parsed = _parse_analytics_cb(callback.data)
    if not parsed:
        await callback.answer()
        return
    period, metric = parsed
    text = await build_analytics_message(callback.from_user.id, period, metric)
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=analytics_keyboard(period, metric),
    )
    await callback.answer()
