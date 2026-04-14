import re

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from keyboards.keyboards import main_menu_inline_keyboard, main_menu_keyboard

from handlers.checkin import begin_checkin
from handlers.history import send_history_reply
from handlers.stats import send_analytics_default

router = Router()

WELCOME_TEXT = (
    "Привет! Я — твой личный дневник настроения.\n\n"
    "Каждый день ты можешь быстро зафиксировать своё состояние — "
    "настроение, энергию, сон и многое другое. Это займёт всего 20–30 секунд.\n\n"
    "Выбери, что хочешь сделать:"
)

HELP_TEXT = (
    "<b>Как пользоваться ботом</b>\n\n"
    "<b>Заполнить запись</b>\n"
    "Пройди ежедневный чек-ин: настроение, энергия, стресс, сон, "
    "заметка и теги.\n\n"
    "<b>История</b>\n"
    "Посмотри свои последние записи.\n\n"
    "<b>Статистика</b>\n"
    "Аналитика: связи между метриками и короткие инсайты. "
    "Период и метрику можно переключать кнопками под сообщением.\n\n"
    "Если ты заполняешь запись повторно в тот же день — "
    "она обновится, а не создастся заново."
)

# Если CommandStart не сработал (например /start@другой_бот в группе), но текст всё ещё /start…
_START_TEXT_RE = re.compile(r"^/start(\s|$|@)")


async def send_welcome(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        WELCOME_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_inline_keyboard(),
    )


# ignore_mention=True: клиенты часто шлют /start@ИмяБота — иначе фильтр отбрасывает команду
@router.message(CommandStart(ignore_mention=True))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await send_welcome(message, state)


@router.message(F.text.regexp(_START_TEXT_RE))
async def cmd_start_text(message: Message, state: FSMContext) -> None:
    await send_welcome(message, state)


@router.message(F.text == "Помощь")
async def cmd_help(message: Message) -> None:
    await message.answer(
        HELP_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "goto_menu")
async def goto_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Главное меню",
        reply_markup=main_menu_inline_keyboard(),
    )
    await callback.message.answer(
        "Кнопки у поля ввода:",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "mm_write")
async def menu_write(callback: CallbackQuery, state: FSMContext) -> None:
    await begin_checkin(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "mm_hist")
async def menu_hist(callback: CallbackQuery) -> None:
    await send_history_reply(callback.message, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data == "mm_stat")
async def menu_stat(callback: CallbackQuery) -> None:
    await send_analytics_default(callback.message, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data == "mm_help")
async def menu_help(callback: CallbackQuery) -> None:
    await callback.message.answer(
        HELP_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()
