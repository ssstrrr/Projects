"""Обработка callback от кнопок выбора города."""

import logging

from aiogram import Router
from aiogram.types import CallbackQuery

from weather.service import get_weather_message

logger = logging.getLogger(__name__)

router = Router(name="handlers/callbacks")

ERROR_MESSAGE = "Не удалось получить погоду. Попробуйте позже."


@router.callback_query(lambda c: c.data and c.data.startswith("city_"))
async def on_city_selected(callback: CallbackQuery) -> None:
    """Обработка нажатия на город: запрос погоды и ответ пользователю."""
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
    if text is None:
        logger.warning("Weather failed for city_id=%s", city_id)
        await callback.message.answer(ERROR_MESSAGE)
        return
    await callback.message.answer(text)
