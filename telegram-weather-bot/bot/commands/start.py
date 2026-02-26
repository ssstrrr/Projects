"""Обработчик команды /start."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards.cities import get_cities_keyboard

router = Router(name="commands/start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Приветствие и клавиатура с выбором города."""
    await message.answer(
        "Привет! Выберите город, чтобы узнать текущую погоду.",
        reply_markup=get_cities_keyboard(),
    )
