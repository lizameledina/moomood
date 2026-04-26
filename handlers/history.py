import html
import asyncio
from aiogram import Router, F
from aiogram.types import Message

from database.db import get_daily_history, get_user_timezone
from keyboards.keyboards import main_menu_keyboard

router = Router()

MOOD_LABELS = {
    1: "Очень плохо",
    2: "Плохо",
    3: "Нормально",
    4: "Хорошо",
    5: "Отлично",
}

TAG_LABELS = {
    "work":    "Работа",
    "sport":   "Спорт",
    "friends": "Друзья",
    "relax":   "Отдых",
    "study":   "Учёба",
    "family":  "Семья",
    "health":  "Здоровье",
    "walk":    "Прогулка",
    "hobby":   "Хобби",
    "home":    "Дом",
    "trips":   "Поездки",
    "children": "Дети",
}

DIVIDER = "\n\n──────────────\n\n"


def _format_entry(row) -> str:
    mood_avg = float(row["mood"])
    mood_round = int(round(mood_avg))
    mood_round = max(1, min(5, mood_round))
    parts = [
        f"<b>{row['date']}</b>",
        f"Настроение: {mood_avg:.1f}/5 (≈ {MOOD_LABELS.get(mood_round, mood_round)})",
        f"Энергия: {float(row['energy']):.1f}/10",
        f"Стресс: {float(row['stress']):.1f}/10",
    ]
    if row.get("sleep") is not None:
        parts.append(f"Сон: {float(row['sleep']):.1f} ч.")
    if row.get("count"):
        parts.append(f"Чек-инов за день: {row['count']}")
    if row.get("note"):
        parts.append(f"Заметка: {html.escape(str(row['note']))}")
    if row.get("tags"):
        tag_names = " · ".join(TAG_LABELS.get(t, t) for t in str(row["tags"]).split(","))
        parts.append(f"Теги: {tag_names}")
    return "\n".join(parts)


async def send_history_reply(message: Message, user_id: int) -> None:
    tz_name = await asyncio.to_thread(get_user_timezone, user_id)
    rows = await asyncio.to_thread(get_daily_history, user_id, tz_name, 7)
    if not rows:
        await message.answer(
            "У тебя пока нет записей.\n\nНажми «Заполнить запись», чтобы начать.",
            reply_markup=main_menu_keyboard(),
        )
        return

    entries = [_format_entry(row) for row in rows]
    text = f"<b>Последние записи:</b>{DIVIDER}{DIVIDER.join(entries)}"
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "История")
async def show_history(message: Message) -> None:
    await send_history_reply(message, message.from_user.id)
