"""Обработка callback от кнопок выбора города."""

import json
import logging
import os

from aiogram import Router
from aiogram.types import CallbackQuery, InputMediaPhoto

from bot.keyboards.cities import get_cities_keyboard
from bot.keyboards.city_menu import get_city_menu_keyboard
from places.food import get_city_places
from places.photos import get_city_photos
from weather.service import get_weather_message

logger = logging.getLogger(__name__)

router = Router(name="handlers/callbacks")

ERROR_MESSAGE = "Произошла ошибка. Попробуйте позже."
NO_PHOTOS_MESSAGE = "Не удалось найти красивые фото для этого города. Попробуйте другой город."
NO_PLACES_MESSAGE = "Не удалось найти кафе и рестораны поблизости. Попробуйте другой город."


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
    """Обработка выбора города: показываем меню действий по городу."""
    # #region agent log
    _debug_log("city_selected", {"callback_data": getattr(callback, "data", None), "chat_id": callback.message.chat.id if callback.message else None, "hypothesisId": "A"})
    # #endregion
    try:
        await callback.answer()
        city_id = callback.data.removeprefix("city_")
        if not city_id or not callback.message:
            await callback.message.answer(ERROR_MESSAGE)
            return

        await callback.message.answer(
            "Что вы хотите узнать про этот город?",
            reply_markup=get_city_menu_keyboard(city_id),
        )
    except Exception as e:
        # #region agent log
        _debug_log("exception in on_city_selected", {"error": str(e), "type": type(e).__name__, "hypothesisId": "C"})
        # #endregion
        logger.exception("on_city_selected error: %s", e)
        try:
            await callback.message.answer(ERROR_MESSAGE)
        except Exception:
            pass


@router.callback_query(lambda c: c.data and c.data.startswith("weather_"))
async def on_weather_requested(callback: CallbackQuery) -> None:
    """Обработка запроса погоды по выбранному городу."""
    # #region agent log
    _debug_log("weather_requested", {"callback_data": getattr(callback, "data", None), "chat_id": callback.message.chat.id if callback.message else None, "hypothesisId": "B"})
    # #endregion
    try:
        await callback.answer()
        city_id = callback.data.removeprefix("weather_")
        if not city_id or not callback.message:
            await callback.message.answer(ERROR_MESSAGE)
            return

        await callback.message.bot.send_chat_action(
            chat_id=callback.message.chat.id,
            action="typing",
        )
        text = await get_weather_message(city_id)
        # #region agent log
        _debug_log("get_weather_message result", {"city_id": city_id, "is_none": text is None, "len_text": len(text) if text else 0, "hypothesisId": "B"})
        _agent_log("callbacks.py:on_weather_requested", "after get_weather_message", {"city_id": city_id, "text_is_none": text is None, "len_text": len(text) if text else 0, "has_nmu": (text or "").find("Параметры, требующие внимания") >= 0}, "C")
        # #endregion
        if text is None:
            logger.warning("Weather failed for city_id=%s", city_id)
            await callback.message.answer("Не удалось получить погоду. Попробуйте позже.")
            return
        # #region agent log
        _debug_log("before answer weather", {"len_text": len(text), "hypothesisId": "D"})
        _agent_log("callbacks.py:before_answer_weather", "sending weather message", {"len_text": len(text), "has_nmu_block": "Параметры, требующие внимания" in (text or "")}, "D")
        # #endregion
        await callback.message.answer(text)
    except Exception as e:
        # #region agent log
        _debug_log("exception in on_weather_requested", {"error": str(e), "type": type(e).__name__, "hypothesisId": "E"})
        # #endregion
        logger.exception("on_weather_requested error: %s", e)
        try:
            await callback.message.answer("Не удалось получить погоду. Попробуйте позже.")
        except Exception:
            pass


@router.callback_query(lambda c: c.data and c.data.startswith("photos_"))
async def on_photos_requested(callback: CallbackQuery) -> None:
    """Обработка запроса красивых фото города."""
    # #region agent log
    _debug_log("photos_requested", {"callback_data": getattr(callback, "data", None), "chat_id": callback.message.chat.id if callback.message else None, "hypothesisId": "F"})
    # #endregion
    try:
        await callback.answer()
        city_id = callback.data.removeprefix("photos_")
        if not city_id or not callback.message:
            await callback.message.answer(ERROR_MESSAGE)
            return

        await callback.message.bot.send_chat_action(
            chat_id=callback.message.chat.id,
            action="upload_photo",
        )

        photos = await get_city_photos(city_id)
        if not photos:
            await callback.message.answer(NO_PHOTOS_MESSAGE)
            return

        if len(photos) == 1:
            p = photos[0]
            await callback.message.answer_photo(
                photo=p.url,
                caption=p.title,
            )
            return

        media = [
            InputMediaPhoto(media=p.url, caption=p.title if idx == 0 else None)
            for idx, p in enumerate(photos)
        ]
        await callback.message.bot.send_media_group(
            chat_id=callback.message.chat.id,
            media=media,
        )
    except Exception as e:
        # #region agent log
        _debug_log("exception in on_photos_requested", {"error": str(e), "type": type(e).__name__, "hypothesisId": "G"})
        # #endregion
        logger.exception("on_photos_requested error: %s", e)
        try:
            await callback.message.answer(NO_PHOTOS_MESSAGE)
        except Exception:
            pass


@router.callback_query(lambda c: c.data and c.data.startswith("food_"))
async def on_food_requested(callback: CallbackQuery) -> None:
    """Обработка запроса мест, где вкусно поесть."""
    # #region agent log
    _debug_log("food_requested", {"callback_data": getattr(callback, "data", None), "chat_id": callback.message.chat.id if callback.message else None, "hypothesisId": "H"})
    # #endregion
    try:
        await callback.answer()
        city_id = callback.data.removeprefix("food_")
        if not city_id or not callback.message:
            await callback.message.answer(ERROR_MESSAGE)
            return

        await callback.message.bot.send_chat_action(
            chat_id=callback.message.chat.id,
            action="typing",
        )

        places = await get_city_places(city_id)
        if not places:
            await callback.message.answer(NO_PLACES_MESSAGE)
            return

        lines = ["Подборка мест, где можно вкусно поесть:"]
        for idx, place in enumerate(places, start=1):
            if place.address:
                lines.append(f"{idx}. {place.name} — {place.kind} ({place.address})")
            else:
                lines.append(f"{idx}. {place.name} — {place.kind}")

        await callback.message.answer("\n".join(lines))
    except Exception as e:
        # #region agent log
        _debug_log("exception in on_food_requested", {"error": str(e), "type": type(e).__name__, "hypothesisId": "I"})
        # #endregion
        logger.exception("on_food_requested error: %s", e)
        try:
            await callback.message.answer(NO_PLACES_MESSAGE)
        except Exception:
            pass


@router.callback_query(lambda c: c.data == "back_to_cities")
async def on_back_to_cities(callback: CallbackQuery) -> None:
    """Возврат к выбору города."""
    # #region agent log
    _debug_log("back_to_cities", {"callback_data": getattr(callback, "data", None), "chat_id": callback.message.chat.id if callback.message else None, "hypothesisId": "J"})
    # #endregion
    try:
        await callback.answer()
        if not callback.message:
            return
        await callback.message.answer(
            "Выберите город:",
            reply_markup=get_cities_keyboard(),
        )
    except Exception as e:
        # #region agent log
        _debug_log("exception in on_back_to_cities", {"error": str(e), "type": type(e).__name__, "hypothesisId": "K"})
        # #endregion
        logger.exception("on_back_to_cities error: %s", e)

