"""Inline-клавиатура со списком городов."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from weather.cities import CITIES

# Кнопки по 2 в ряд для компактности
BUTTONS_PER_ROW = 2


def get_cities_keyboard() -> InlineKeyboardMarkup:
    """Возвращает inline-клавиатуру с кнопками городов (callback_data: city_<id>)."""
    rows = []
    row = []
    for city in CITIES:
        row.append(
            InlineKeyboardButton(
                text=city.name,
                callback_data=f"city_{city.id}",
            )
        )
        if len(row) >= BUTTONS_PER_ROW:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)
