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
        KeyboardButton(text="Заполнить запись"),
        KeyboardButton(text="История"),
    )
    builder.row(
        KeyboardButton(text="Статистика"),
        KeyboardButton(text="Помощь"),
    )
    return builder.as_markup(
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выбери действие в меню",
    )


def main_menu_inline_keyboard() -> InlineKeyboardMarkup:
    """Дублирует главное меню inline-кнопками — всегда видно под сообщением."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Запись", callback_data="mm_write"),
        InlineKeyboardButton(text="История", callback_data="mm_hist"),
    )
    builder.row(
        InlineKeyboardButton(text="Статистика", callback_data="mm_stat"),
        InlineKeyboardButton(text="Помощь", callback_data="mm_help"),
    )
    return builder.as_markup()


MOOD_OPTIONS = [
    ("Очень плохо", "mood_1"),
    ("Плохо",       "mood_2"),
    ("Нормально",   "mood_3"),
    ("Хорошо",      "mood_4"),
    ("Отлично",     "mood_5"),
]


def mood_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text, data in MOOD_OPTIONS:
        builder.button(text=text, callback_data=data)
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    return builder.as_markup()


def scale_keyboard(prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(1, 11):
        builder.button(text=str(i), callback_data=f"{prefix}_{i}")
    builder.adjust(5)
    builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Отмена", callback_data="cancel")
    return builder.as_markup()


def skip_or_cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Пропустить", callback_data="skip")
    builder.button(text="Отмена",     callback_data="cancel")
    builder.adjust(2)
    return builder.as_markup()


TAG_OPTIONS = [
    ("Работа", "work"),
    ("Спорт",  "sport"),
    ("Друзья", "friends"),
    ("Отдых",  "relax"),
    ("Учёба", "study"),
    ("Семья", "family"),
    ("Здоровье", "health"),
    ("Прогулка", "walk"),
    ("Хобби", "hobby"),
    ("Дом", "home"),
    ("Поездки", "trips"),
    ("Дети", "children"),
]


def tags_keyboard(selected: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text, data in TAG_OPTIONS:
        label = f"Выбрано: {text}" if data in selected else text
        builder.button(text=label, callback_data=f"tag_{data}")
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="Готово",    callback_data="tags_done"),
        InlineKeyboardButton(text="Пропустить", callback_data="skip"),
    )
    builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    return builder.as_markup()


def after_checkin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Посмотреть статистику", callback_data="goto_stats")
    builder.button(text="Главное меню",           callback_data="goto_menu")
    builder.adjust(1)
    return builder.as_markup()


def analytics_keyboard(period: str, metric: str) -> InlineKeyboardMarkup:
    """Период: 7 | 30 | 0 (всё время). Показатель: m | e | r | h."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=("[ " if period == "7" else "") + ("7 дней ]" if period == "7" else "7 дней"),
            callback_data=f"a7{metric}",
        ),
        InlineKeyboardButton(
            text=("[ " if period == "30" else "") + ("30 дней ]" if period == "30" else "30 дней"),
            callback_data=f"a30{metric}",
        ),
        InlineKeyboardButton(
            text=("[ " if period == "0" else "") + ("Всё время ]" if period == "0" else "Всё время"),
            callback_data=f"a0{metric}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=("[ " if metric == "m" else "") + ("Настроение ]" if metric == "m" else "Настроение"),
            callback_data=f"a{period}m",
        ),
        InlineKeyboardButton(
            text=("[ " if metric == "e" else "") + ("Энергия ]" if metric == "e" else "Энергия"),
            callback_data=f"a{period}e",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=("[ " if metric == "r" else "") + ("Стресс ]" if metric == "r" else "Стресс"),
            callback_data=f"a{period}r",
        ),
        InlineKeyboardButton(
            text=("[ " if metric == "h" else "") + ("Сон ]" if metric == "h" else "Сон"),
            callback_data=f"a{period}h",
        ),
    )
    return builder.as_markup()
