from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database.db import get_stats_7d

router = Router()

MOOD_LABELS = {
    1: "😞 Очень плохо",
    2: "🙁 Плохо",
    3: "😐 Нормально",
    4: "🙂 Хорошо",
    5: "😄 Отлично",
}


def _mood_label(avg: float) -> str:
    return MOOD_LABELS.get(round(avg), f"{avg:.1f}")


def build_stats_text(user_id: int) -> str:
    row = get_stats_7d(user_id)
    if not row or row["count"] == 0:
        return (
            "📊 <b>Статистика за 7 дней</b>\n\n"
            "Пока нет данных для статистики.\n\n"
            "Начни с ежедневного чек-ина — и через несколько дней здесь появятся твои показатели."
        )
    return (
        f"📊 <b>Статистика за 7 дней</b>\n\n"
        f"Записей: {row['count']}\n"
        f"Среднее настроение: {_mood_label(row['avg_mood'])}\n"
        f"Средняя энергия: {row['avg_energy']:.1f}/10\n"
        f"Средний стресс: {row['avg_stress']:.1f}/10\n"
        f"Средний сон: {row['avg_sleep']:.1f} ч."
    )


@router.message(F.text == "📊 Статистика")
async def show_stats(message: Message) -> None:
    await message.answer(build_stats_text(message.from_user.id), parse_mode="HTML")


@router.callback_query(F.data == "goto_stats")
async def goto_stats(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        build_stats_text(callback.from_user.id),
        parse_mode="HTML",
    )
    await callback.answer()
