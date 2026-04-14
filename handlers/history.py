import html
from aiogram import Router, F
from aiogram.types import Message

from database.db import get_history
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
    parts = [
        f"<b>{row['date']}</b>",
        f"Настроение: {MOOD_LABELS.get(row['mood'], str(row['mood']))}",
        f"Энергия: {row['energy']}/10",
        f"Стресс: {row['stress']}/10",
        f"Сон: {row['sleep']} ч.",
    ]
    if row["note"]:
        parts.append(f"Заметка: {html.escape(row['note'])}")
    if row["tags"]:
        tag_names = " · ".join(TAG_LABELS.get(t, t) for t in row["tags"].split(","))
        parts.append(f"Теги: {tag_names}")
    return "\n".join(parts)


async def send_history_reply(message: Message, user_id: int) -> None:
    rows = get_history(user_id, limit=7)
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
