"""Обработка callback от кнопок выбора города."""

import json
import logging
import os

from aiogram import Router
from aiogram.types import CallbackQuery

from weather.service import get_weather_message

logger = logging.getLogger(__name__)

router = Router(name="handlers/callbacks")

ERROR_MESSAGE = "Не удалось получить погоду. Попробуйте позже."


def _debug_log(message: str, data: dict) -> None:
    # #region agent log
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "debug-ef3bc0.log")
    try:
        payload = {"sessionId": "ef3bc0", "location": "callbacks.py", "message": message, "data": data, "timestamp": __import__("time").time() * 1000}
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
    # #endregion


def _agent_log(location: str, message: str, data: dict, hypothesis_id: str) -> None:
    # #region agent log
    try:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        ws = os.path.dirname(base)
        log_path = os.path.join(ws, "debug-390bef.log")
        payload = {"sessionId": "390bef", "location": location, "message": message, "data": {**data, "hypothesisId": hypothesis_id}, "timestamp": int(__import__("time").time() * 1000)}
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
    # #endregion


@router.callback_query(lambda c: c.data and c.data.startswith("city_"))
async def on_city_selected(callback: CallbackQuery) -> None:
    """Обработка нажатия на город: запрос погоды и ответ пользователю."""
    # #region agent log
    _debug_log("callback received", {"callback_data": getattr(callback, "data", None), "chat_id": callback.message.chat.id if callback.message else None, "hypothesisId": "A"})
    # #endregion
    try:
        await callback.answer()
        city_id = callback.data.removeprefix("city_")
        if not city_id:
            await callback.message.answer(ERROR_MESSAGE)
            return

        # Показываем индикатор «печатает»
        await callback.message.bot.send_chat_action(
            chat_id=callback.message.chat.id,
            action="typing",
        )
        text = await get_weather_message(city_id)
        # #region agent log
        _debug_log("get_weather_message result", {"city_id": city_id, "is_none": text is None, "len_text": len(text) if text else 0, "hypothesisId": "B"})
        _agent_log("callbacks.py:on_city_selected", "after get_weather_message", {"city_id": city_id, "text_is_none": text is None, "len_text": len(text) if text else 0, "has_nmu": (text or "").find("Параметры, требующие внимания") >= 0}, "C")
        # #endregion
        if text is None:
            logger.warning("Weather failed for city_id=%s", city_id)
            await callback.message.answer(ERROR_MESSAGE)
            return
        # #region agent log
        _debug_log("before answer", {"len_text": len(text), "hypothesisId": "D"})
        _agent_log("callbacks.py:before_answer", "sending message", {"len_text": len(text), "has_nmu_block": "Параметры, требующие внимания" in (text or "")}, "D")
        # #endregion
        await callback.message.answer(text)
        # #region agent log
        _debug_log("after answer ok", {"hypothesisId": "D"})
        # #endregion
    except Exception as e:
        # #region agent log
        _debug_log("exception in handler", {"error": str(e), "type": type(e).__name__, "hypothesisId": "C"})
        # #endregion
        logger.exception("on_city_selected error: %s", e)
        try:
            await callback.message.answer(ERROR_MESSAGE)
        except Exception:
            pass
