from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

from keyboards.keyboards import main_menu_keyboard

router = Router()

WELCOME_TEXT = (
    "👋 Привет! Я — твой личный дневник настроения.\n\n"
    "Каждый день ты можешь быстро зафиксировать своё состояние — "
    "настроение, энергию, сон и многое другое. Это займёт всего 20–30 секунд.\n\n"
    "Выбери, что хочешь сделать:"
)

HELP_TEXT = (
    "❓ <b>Как пользоваться ботом</b>\n\n"
    "📝 <b>Заполнить запись</b>\n"
    "Пройди ежедневный чек-ин: настроение, энергия, стресс, сон, "
    "заметка и теги.\n\n"
    "📋 <b>История</b>\n"
    "Посмотри свои последние записи.\n\n"
    "📊 <b>Статистика</b>\n"
    "Средние показатели за последние 7 дней.\n\n"
    "💡 Если ты заполняешь запись повторно в тот же день — "
    "она обновится, а не создастся заново."
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard())


@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode="HTML")


@router.callback_query(F.data == "goto_menu")
async def goto_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()
