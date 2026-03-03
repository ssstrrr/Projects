"""Клавиатура с действиями для выбранного города."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_city_menu_keyboard(city_id: str) -> InlineKeyboardMarkup:
    """
    Возвращает inline-клавиатуру с действиями по выбранному городу.

    callback_data:
    - weather_<id>  — показать погоду
    - photos_<id>   — показать фото города
    - food_<id>     — показать места, где вкусно поесть
    - back_to_cities — вернуться к выбору города
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Узнать погоду",
                    callback_data=f"weather_{city_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Посмотреть фото",
                    callback_data=f"photos_{city_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Вкусно поесть",
                    callback_data=f"food_{city_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Вернуться назад",
                    callback_data="back_to_cities",
                ),
            ],
        ]
    )

