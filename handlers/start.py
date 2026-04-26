import re
import asyncio
from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from database.db import get_user_timezone, set_user_timezone
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
    "она дополнится (можно сделать несколько чек-инов за день)."
    "\n\n"
    "<b>AI-поддержка</b>\n"
    "/ai — начать разговор\n"
    "/ai_off — выключить\n\n"
    "<b>Часовой пояс</b>\n"
    "Чтобы «день» считался правильно, можно настроить часовой пояс:\n"
    "/timezone — показать текущий\n"
    "/timezone Europe/Moscow — установить (также работает /tz)"
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
    if callback.message and callback.message.reply_markup is not None:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
    await callback.message.answer(
        "Главное меню",
        reply_markup=main_menu_inline_keyboard(),
    )
    await callback.message.answer(
        "Кнопки у поля ввода:",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.message(Command("timezone"))
@router.message(Command("tz"))
async def cmd_timezone(message: Message) -> None:
    text = (message.text or "").strip()
    parts = text.split(maxsplit=1)

    if len(parts) == 1:
        tz_name = await asyncio.to_thread(get_user_timezone, message.from_user.id)
        await message.answer(
            f"Твой часовой пояс: <b>{tz_name}</b>\n\n"
            "Чтобы изменить:\n"
            "<code>/timezone Europe/Moscow</code>\n"
            "<code>/timezone UTC</code>",
            parse_mode="HTML",
        )
        return

    tz_candidate = parts[1].strip()
    try:
        ZoneInfo(tz_candidate)
    except Exception:
        await message.answer(
            "Не понимаю такой часовой пояс.\n\n"
            "Примеры:\n"
            "<code>/timezone Europe/Moscow</code>\n"
            "<code>/timezone Europe/Kyiv</code>\n"
            "<code>/timezone Asia/Almaty</code>\n"
            "<code>/timezone UTC</code>",
            parse_mode="HTML",
        )
        return

    await asyncio.to_thread(set_user_timezone, message.from_user.id, tz_candidate)
    await message.answer(
        f"Готово! Часовой пояс установлен: <b>{tz_candidate}</b>.",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "mm_write")
async def menu_write(callback: CallbackQuery, state: FSMContext) -> None:
    await begin_checkin(callback.message, state, user_id=callback.from_user.id)
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
