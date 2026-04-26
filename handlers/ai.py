import asyncio
import logging
from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from zoneinfo import ZoneInfo

from config import AI_DAILY_LIMIT, DEEPSEEK_API_KEY
from database.db import get_ai_usage_count, get_user_timezone, increment_ai_usage
from keyboards.keyboards import main_menu_inline_keyboard, main_menu_keyboard
from states.ai_states import AiStates
from utils.deepseek_client import chat_completions

router = Router()
logger = logging.getLogger(__name__)

DEEPSEEK_DEFAULT_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_DEFAULT_MODEL = "deepseek-chat"

SYSTEM_PROMPT = (
    "Ты — бережный компаньон для саморефлексии в дневнике настроения. "
    "Твоя задача: поддержать и помочь прояснить состояние, но ты не психотерапевт и не врач. "
    "Не ставь диагнозы, не дави, не давай медицинских советов. "
    "Отвечай кратко (2–6 предложений), максимум 1 мягкий вопрос и 1 простое действие/практика (не обязательно)."
)

CRISIS_HINT = (
    "Мне очень жаль, что тебе так тяжело. Я не могу заменить срочную помощь. "
    "Если есть риск, что ты можешь причинить себе вред, пожалуйста, обратись за помощью прямо сейчас: "
    "в экстренные службы или к близкому человеку рядом. "
    "Если ты в России — можно набрать 112 (единый номер экстренных служб). "
    "Если ты в другой стране — скажи, где ты находишься, и я помогу найти местные контакты помощи."
)


def _looks_like_crisis(text: str) -> bool:
    t = text.lower()
    keywords = (
        "суицид",
        "самоубий",
        "покончить с собой",
        "не хочу жить",
        "хочу умереть",
        "убить себя",
        "самоповреж",
        "режу",
        "порезать",
        "kill myself",
        "suicide",
    )
    return any(k in t for k in keywords)


async def _enter_ai(message: Message, state: FSMContext) -> None:
    await state.set_state(AiStates.chat)
    await state.update_data(
        ai_messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
    )
    await message.answer(
        "AI-поддержка включена.\n\n"
        "Напиши, что происходит, и я помогу аккуратно это прояснить.\n"
        "Чтобы выйти: /ai_off",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("ai"))
async def cmd_ai(message: Message, state: FSMContext) -> None:
    await _enter_ai(message, state)


@router.message(Command("ai_off"))
async def cmd_ai_off(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("AI-поддержка выключена.", reply_markup=main_menu_keyboard())


@router.message(F.text == "AI-поддержка")
async def menu_ai(message: Message, state: FSMContext) -> None:
    await _enter_ai(message, state)


@router.callback_query(F.data == "mm_ai")
async def menu_ai_inline(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        await _enter_ai(callback.message, state)


@router.message(AiStates.chat, F.text, ~F.text.startswith("/"))
async def ai_chat(message: Message, state: FSMContext) -> None:
    if not DEEPSEEK_API_KEY:
        await message.answer(
            "AI пока не настроен. Нужны переменные окружения:\n"
            "DEEPSEEK_API_KEY\n\n"
            "Подсказка: ключ должен быть задан в окружении процесса бота (на сервере/хостинге) "
            "или лежать в файле .env рядом с bot.py/config.py. После изменения ключа перезапусти бота.",
        )
        return

    user_text = (message.text or "").strip()
    if not user_text:
        return

    if _looks_like_crisis(user_text):
        await message.answer(CRISIS_HINT)
        return

    tz_name = await asyncio.to_thread(get_user_timezone, message.from_user.id)
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    local_date = datetime.now(timezone.utc).astimezone(tz).date().isoformat()

    current_count = await asyncio.to_thread(get_ai_usage_count, message.from_user.id, local_date)
    if current_count >= AI_DAILY_LIMIT:
        await message.answer(
            "На сегодня лимит AI-ответов исчерпан. Попробуем завтра.",
            reply_markup=main_menu_keyboard(),
        )
        return
    await asyncio.to_thread(increment_ai_usage, message.from_user.id, local_date)

    data = await state.get_data()
    msgs = list(data.get("ai_messages") or [{"role": "system", "content": SYSTEM_PROMPT}])
    msgs.append({"role": "user", "content": user_text})

    try:
        reply = await chat_completions(
            base_url=DEEPSEEK_DEFAULT_BASE_URL,
            api_key=DEEPSEEK_API_KEY,
            model=DEEPSEEK_DEFAULT_MODEL,
            messages=msgs,
        )
    except Exception as e:
        logger.exception(
            "DeepSeek request failed (user_id=%s, base_url=%s, model=%s)",
            message.from_user.id,
            DEEPSEEK_DEFAULT_BASE_URL,
            DEEPSEEK_DEFAULT_MODEL,
        )
        await message.answer(
            "Не получилось получить ответ от AI.\n\n"
            f"Техническая причина: {str(e)[:300]}",
        )
        return

    await message.answer(reply, reply_markup=main_menu_keyboard())

    msgs.append({"role": "assistant", "content": reply})
    system = msgs[0:1]
    tail = msgs[1:][-20:]
    await state.update_data(ai_messages=system + tail)
