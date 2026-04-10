from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📝 Заполнить запись"),
        KeyboardButton(text="📋 История"),
    )
    builder.row(
        KeyboardButton(text="📊 Статистика"),
        KeyboardButton(text="❓ Помощь"),
    )
    return builder.as_markup(resize_keyboard=True)


MOOD_OPTIONS = [
    ("😞 Очень плохо", "mood_1"),
    ("🙁 Плохо",       "mood_2"),
    ("😐 Нормально",   "mood_3"),
    ("🙂 Хорошо",      "mood_4"),
    ("😄 Отлично",     "mood_5"),
]


def mood_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text, data in MOOD_OPTIONS:
        builder.button(text=text, callback_data=data)
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return builder.as_markup()


def scale_keyboard(prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(1, 11):
        builder.button(text=str(i), callback_data=f"{prefix}_{i}")
    builder.adjust(5)
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel")
    return builder.as_markup()


def skip_or_cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Пропустить", callback_data="skip")
    builder.button(text="❌ Отмена",     callback_data="cancel")
    builder.adjust(2)
    return builder.as_markup()


TAG_OPTIONS = [
    ("💼 Работа", "work"),
    ("🏋️ Спорт",  "sport"),
    ("👥 Друзья", "friends"),
    ("🛋️ Отдых",  "relax"),
]


def tags_keyboard(selected: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text, data in TAG_OPTIONS:
        label = f"✅ {text}" if data in selected else text
        builder.button(text=label, callback_data=f"tag_{data}")
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="✔️ Готово",    callback_data="tags_done"),
        InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip"),
    )
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return builder.as_markup()


def after_checkin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Посмотреть статистику", callback_data="goto_stats")
    builder.button(text="🏠 Главное меню",           callback_data="goto_menu")
    builder.adjust(1)
    return builder.as_markup()
