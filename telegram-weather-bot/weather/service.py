"""Сервис погоды: запрос к Open-Meteo API, маппинг WMO, форматирование."""

import logging
from typing import Any

import aiohttp

from weather.cities import City, get_city

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# WMO Weather interpretation codes → краткое описание на русском
# https://open-meteo.com/en/docs#api_form
WMO_RU: dict[int, str] = {
    0: "Ясно",
    1: "Преимущественно ясно",
    2: "Переменная облачность",
    3: "Пасмурно",
    45: "Туман",
    48: "Изморозь",
    51: "Морось: слабая",
    53: "Морось: умеренная",
    55: "Морось: сильная",
    56: "Ледяная морось: слабая",
    57: "Ледяная морось: сильная",
    61: "Дождь: слабый",
    63: "Дождь: умеренный",
    65: "Дождь: сильный",
    66: "Ледяной дождь: слабый",
    67: "Ледяной дождь: сильный",
    71: "Снег: слабый",
    73: "Снег: умеренный",
    75: "Снег: сильный",
    77: "Снежные зёрна",
    80: "Ливень: слабый",
    81: "Ливень: умеренный",
    82: "Ливень: сильный",
    85: "Снежный ливень: слабый",
    86: "Снежный ливень: сильный",
    95: "Гроза",
    96: "Гроза с градом",
    99: "Гроза с сильным градом",
}


def _weather_description(code: int) -> str:
    return WMO_RU.get(code, "Без описания")


async def fetch_weather(city: City) -> dict[str, Any] | None:
    """
    Запрашивает текущую погоду в Open-Meteo по координатам города.
    Возвращает словарь с полями current или None при ошибке.
    """
    params = {
        "latitude": city.latitude,
        "longitude": city.longitude,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "timezone": city.timezone,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(OPEN_METEO_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    logger.warning("Open-Meteo returned status %s for %s", resp.status, city.name)
                    return None
                data = await resp.json()
    except aiohttp.ClientError as e:
        logger.exception("Open-Meteo request failed for %s: %s", city.name, e)
        return None
    except Exception as e:
        logger.exception("Unexpected error fetching weather for %s: %s", city.name, e)
        return None

    if "current" not in data:
        logger.warning("Open-Meteo response missing 'current' for %s", city.name)
        return None
    return data


def format_weather_message(city_name: str, data: dict[str, Any]) -> str:
    """Форматирует ответ API в читаемое сообщение для Telegram."""
    cur = data["current"]
    temp = cur.get("temperature_2m")
    humidity = cur.get("relative_humidity_2m")
    wind = cur.get("wind_speed_10m")
    code = cur.get("weather_code", 0)
    desc = _weather_description(code)

    parts = [f"Погода в {city_name}", "", desc]
    if temp is not None:
        parts.append(f"Температура: {temp:.0f} °C")
    if humidity is not None:
        parts.append(f"Влажность: {humidity}%")
    if wind is not None:
        parts.append(f"Ветер: {wind:.0f} км/ч")
    return "\n".join(parts)


async def get_weather_message(city_id: str) -> str | None:
    """
    По id города получает погоду и возвращает готовое сообщение для пользователя.
    Возвращает None при ошибке (город не найден или API недоступен).
    """
    city = get_city(city_id)
    if not city:
        return None
    data = await fetch_weather(city)
    if not data:
        return None
    return format_weather_message(city.name, data)
