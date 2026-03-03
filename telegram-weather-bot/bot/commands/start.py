"""Обработчик команды /start."""

import json
import os

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards.cities import get_cities_keyboard

router = Router(name="commands/start")


def _session_log(message: str, data: dict, hypothesis_id: str) -> None:
    # #region agent log
    try:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        ws = os.path.dirname(base)
        log_path = os.path.join(ws, "debug-bfb7f9.log")
        payload = {
            "sessionId": "bfb7f9",
            "location": "bot/commands/start.py",
            "message": message,
            "data": data,
            "hypothesisId": hypothesis_id,
            "timestamp": int(__import__("time").time() * 1000),
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
    # #endregion


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Приветствие и клавиатура с выбором города."""
    _session_log(
        "cmd_start_enter",
        {
            "chat_id": getattr(message.chat, "id", None),
            "from_id": getattr(message.from_user, "id", None),
            "text": message.text,
        },
        "H_start",
    )
    await message.answer(
        "Привет! Выберите город, чтобы узнать текущую погоду.",
        reply_markup=get_cities_keyboard(),
    )
