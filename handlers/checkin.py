import html
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states.states import CheckinStates
from keyboards.keyboards import (
    mood_keyboard,
    scale_keyboard,
    cancel_keyboard,
    skip_or_cancel_keyboard,
    tags_keyboard,
    after_checkin_keyboard,
    main_menu_inline_keyboard,
    main_menu_keyboard,
)
from database.db import upsert_record

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


# ── Запуск чек-ина ──────────────────────────────────────────────────────

async def begin_checkin(message: Message, state: FSMContext) -> None:
    await state.set_state(CheckinStates.mood)
    await message.answer(
        "Как ты себя чувствуешь прямо сейчас?",
        reply_markup=mood_keyboard(),
    )


@router.message(F.text == "Заполнить запись")
async def start_checkin(message: Message, state: FSMContext) -> None:
    await begin_checkin(message, state)


# ── Шаг 1: Настроение ──────────────────────────────────────────────────

@router.callback_query(CheckinStates.mood, F.data.startswith("mood_"))
async def process_mood(callback: CallbackQuery, state: FSMContext) -> None:
    mood = int(callback.data.split("_")[1])
    await state.update_data(mood=mood)
    await state.set_state(CheckinStates.energy)
    await callback.message.edit_text(
        f"Настроение: {MOOD_LABELS[mood]}\n\n"
        "Какой у тебя уровень энергии сегодня?\n"
        "1 — совсем нет сил, 10 — на подъёме",
        reply_markup=scale_keyboard("energy"),
    )
    await callback.answer()


# Пользователь написал текст вместо выбора кнопки (/start и др. команды не перехватываем)
@router.message(
    CheckinStates.mood,
    F.text,
    ~F.text.startswith("/"),
)
@router.message(
    CheckinStates.energy,
    F.text,
    ~F.text.startswith("/"),
)
@router.message(
    CheckinStates.stress,
    F.text,
    ~F.text.startswith("/"),
)
async def prompt_use_buttons(message: Message) -> None:
    await message.answer("Пожалуйста, выбери вариант из кнопок выше.")


# ── Шаг 2: Энергия ─────────────────────────────────────────────────────

@router.callback_query(CheckinStates.energy, F.data.startswith("energy_"))
async def process_energy(callback: CallbackQuery, state: FSMContext) -> None:
    energy = int(callback.data.split("_")[1])
    await state.update_data(energy=energy)
    await state.set_state(CheckinStates.stress)
    await callback.message.edit_text(
        f"Энергия: {energy}/10\n\n"
        "Насколько ты был(а) в напряжении сегодня?\n"
        "1 — совсем спокойно, 10 — очень много стресса",
        reply_markup=scale_keyboard("stress"),
    )
    await callback.answer()


# ── Шаг 3: Стресс ──────────────────────────────────────────────────────

@router.callback_query(CheckinStates.stress, F.data.startswith("stress_"))
async def process_stress(callback: CallbackQuery, state: FSMContext) -> None:
    stress = int(callback.data.split("_")[1])
    await state.update_data(stress=stress)
    await state.set_state(CheckinStates.sleep)
    await callback.message.edit_text(
        f"Стресс: {stress}/10\n\n"
        "Сколько часов ты спал(а) прошлой ночью?\n"
        "Введи число, например: <b>7</b> или <b>6.5</b>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# ── Шаг 4: Сон ─────────────────────────────────────────────────────────

@router.message(CheckinStates.sleep, F.text, ~F.text.startswith("/"))
async def process_sleep(message: Message, state: FSMContext) -> None:
    raw = message.text.strip().replace(",", ".")
    try:
        sleep = float(raw)
        if not (0 <= sleep <= 24):
            raise ValueError
    except ValueError:
        await message.answer(
            "Введи число от 0 до 24, например: 7 или 6.5",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.update_data(sleep=sleep)
    await state.set_state(CheckinStates.note)
    await message.answer(
        f"Сон: {sleep} ч.\n\n"
        "Хочешь добавить короткую заметку о своём дне?\n"
        "Напиши что-нибудь или пропусти этот шаг.",
        reply_markup=skip_or_cancel_keyboard(),
    )


# ── Шаг 5: Заметка ─────────────────────────────────────────────────────

@router.message(CheckinStates.note, F.text, ~F.text.startswith("/"))
async def process_note(message: Message, state: FSMContext) -> None:
    await state.update_data(note=message.text.strip())
    await state.set_state(CheckinStates.tags)
    await message.answer(
        "Что было в твоём дне?\n"
        "Выбери подходящие теги или пропусти.",
        reply_markup=tags_keyboard([]),
    )


@router.callback_query(CheckinStates.note, F.data == "skip")
async def skip_note(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(note=None)
    await state.set_state(CheckinStates.tags)
    await callback.message.edit_text(
        "Что было в твоём дне?\n"
        "Выбери подходящие теги или пропусти.",
        reply_markup=tags_keyboard([]),
    )
    await callback.answer()


# ── Шаг 6: Теги ────────────────────────────────────────────────────────

@router.callback_query(CheckinStates.tags, F.data.startswith("tag_"))
async def toggle_tag(callback: CallbackQuery, state: FSMContext) -> None:
    tag = callback.data[4:]  # убираем префикс "tag_"
    data = await state.get_data()
    selected: list = data.get("selected_tags", [])

    if tag in selected:
        selected.remove(tag)
    else:
        selected.append(tag)

    await state.update_data(selected_tags=selected)
    await callback.message.edit_reply_markup(reply_markup=tags_keyboard(selected))
    await callback.answer()


@router.callback_query(CheckinStates.tags, F.data == "tags_done")
async def finish_checkin_with_tags(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await _save_and_confirm(callback, state, data, data.get("selected_tags", []))


@router.callback_query(CheckinStates.tags, F.data == "skip")
async def skip_tags(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await _save_and_confirm(callback, state, data, [])


@router.message(CheckinStates.tags, F.text, ~F.text.startswith("/"))
async def prompt_use_tag_buttons(message: Message) -> None:
    await message.answer(
        "Выбери теги из кнопок выше или нажми «Готово» / «Пропустить»."
    )


# ── Сохранение и подтверждение ──────────────────────────────────────────

async def _save_and_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    data: dict,
    tags: list,
) -> None:
    upsert_record(
        user_id=callback.from_user.id,
        mood=data["mood"],
        energy=data["energy"],
        stress=data["stress"],
        sleep=data["sleep"],
        note=data.get("note"),
        tags=",".join(tags) if tags else None,
    )
    await state.clear()

    lines = [
        "<b>Запись сохранена.</b>\n",
        f"Настроение: {MOOD_LABELS[data['mood']]}",
        f"Энергия: {data['energy']}/10",
        f"Стресс: {data['stress']}/10",
        f"Сон: {data['sleep']} ч.",
    ]
    if data.get("note"):
        lines.append(f"Заметка: {html.escape(data['note'])}")
    if tags:
        tag_names = " · ".join(TAG_LABELS.get(t, t) for t in tags)
        lines.append(f"Теги: {tag_names}")

    lines.append("\nЧто дальше?")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=after_checkin_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# ── Отмена ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "cancel")
async def cancel_checkin(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Заполнение отменено.")
    await callback.message.answer(
        "Главное меню",
        reply_markup=main_menu_inline_keyboard(),
    )
    await callback.message.answer(
        "Кнопки у поля ввода:",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()
