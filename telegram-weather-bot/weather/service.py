"""Сервис погоды: запрос к Open-Meteo API, маппинг WMO, форматирование блоков."""

import json
import logging
import os
from typing import Any

import aiohttp

from weather.cities import City, get_city

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Параметры current: расширенный набор для всех блоков
CURRENT_PARAMS = (
    "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,"
    "apparent_temperature,pressure_msl,wind_direction_10m,wind_gusts_10m,"
    "precipitation,visibility,cloud_cover"
)
DAILY_PARAMS = (
    "sunrise,sunset,daylight_duration,temperature_2m_min,temperature_2m_max,"
    "uv_index_max,precipitation_sum,precipitation_probability_max"
)

# WMO Weather interpretation codes → краткое описание на русском
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

# Направление ветра: градусы → краткое название
WIND_DIR = [
    (22.5, "С"), (67.5, "СВ"), (112.5, "В"), (157.5, "ЮВ"),
    (202.5, "Ю"), (247.5, "ЮЗ"), (292.5, "З"), (337.5, "СЗ"), (360.0, "С"),
]


def _weather_description(code: int) -> str:
    return WMO_RU.get(code, "Без описания")


def _wind_direction_text(degrees: float | None) -> str:
    if degrees is None:
        return ""
    for limit, name in WIND_DIR:
        if degrees < limit:
            return name
    return "С"


# --- Запрос к API ---


async def fetch_weather(city: City) -> dict[str, Any] | None:
    """
    Запрашивает текущую погоду и прогноз на день в Open-Meteo.
    Возвращает словарь с полями current и daily (если API вернул) или None при ошибке.
    """
    params = {
        "latitude": city.latitude,
        "longitude": city.longitude,
        "current": CURRENT_PARAMS,
        "daily": DAILY_PARAMS,
        "forecast_days": 1,
        "timezone": city.timezone,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                OPEN_METEO_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
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


# --- НМУ (неблагоприятные метеоусловия) ---

WMO_HAZARDOUS = {65, 66, 67, 75, 82, 86, 95, 96, 99}  # сильный дождь/снег, гроза, град
WMO_FREEZING_RAIN = {56, 57, 66, 67}  # ледяная морось/дождь


def get_nmu_warnings(current: dict[str, Any], daily: dict[str, Any] | None) -> list[str]:
    """Список фактов по порогам из current (без советов)."""
    warnings: list[str] = []
    temp = current.get("temperature_2m")
    wind_speed = current.get("wind_speed_10m")
    wind_gusts = current.get("wind_gusts_10m")
    visibility = current.get("visibility")
    code = current.get("weather_code", 0)
    precip = current.get("precipitation") or 0

    gusts = wind_gusts if wind_gusts is not None else wind_speed
    wind_max = max((x for x in (wind_speed, gusts) if x is not None), default=0) or 0

    if wind_max > 25:
        warnings.append("Максимальная скорость ветра: %.0f км/ч" % wind_max)
    elif wind_max > 18:
        warnings.append("Скорость ветра выше 18 км/ч: %.0f км/ч" % wind_max)

    if temp is not None:
        if temp < -35:
            warnings.append("Температура ниже −35°: %+.0f°" % temp)
        elif temp < -25:
            warnings.append("Температура ниже −25°: %+.0f°" % temp)
        elif temp > 35:
            warnings.append("Температура выше +35°: %+.0f°" % temp)

    if visibility is not None and visibility < 1000:
        warnings.append("Видимость менее 1 км: %.0f м" % visibility)

    if code in WMO_HAZARDOUS:
        warnings.append("Погодное явление по коду WMO: %d (%s)" % (code, _weather_description(code)))

    if temp is not None and -2 <= temp <= 2 and (precip > 0 or code in WMO_FREEZING_RAIN):
        warnings.append("Условия для гололёда (t %+.0f°, осадки)" % temp)

    return warnings


def format_nmu_block(warnings: list[str]) -> str:
    if warnings:
        return "Параметры, требующие внимания:\n" + "\n".join("• " + w for w in warnings)
    return "По текущим данным значимых аномальных параметров не выявлено."


# --- Основной блок ---


def format_main_block(city_name: str, current: dict[str, Any]) -> str:
    """Только фактические данные из current (Open-Meteo)."""
    cur = current
    temp = cur.get("temperature_2m")
    apparent = cur.get("apparent_temperature")
    humidity = cur.get("relative_humidity_2m")
    pressure = cur.get("pressure_msl")
    wind_speed = cur.get("wind_speed_10m")
    wind_dir = cur.get("wind_direction_10m")
    wind_gusts = cur.get("wind_gusts_10m")
    code = cur.get("weather_code", 0)
    desc = _weather_description(code)

    parts = [f"Погода в {city_name}", "", desc]

    if temp is not None:
        parts.append("Температура: %+.0f°" % temp)
    if apparent is not None:
        parts.append("Ощущается как: %+.0f°" % apparent)
    if humidity is not None:
        parts.append("Влажность: %d%%" % humidity)
    if pressure is not None:
        parts.append("Давление: %d гПа" % round(pressure))

    wind_str = _wind_direction_text(wind_dir) if wind_dir is not None else ""
    if wind_speed is not None:
        s = "Ветер: %.0f км/ч" % wind_speed
        if wind_str:
            s += " (%s)" % wind_str
        if wind_gusts is not None and wind_gusts > wind_speed:
            s += ", порывы до %.0f км/ч" % wind_gusts
        parts.append(s)

    return "\n".join(parts)


# --- Сборка полного сообщения ---


def assemble_full_message(
    city_name: str,
    current: dict[str, Any],
    daily: dict[str, Any] | None,
    timezone: str = "Europe/Moscow",
) -> str:
    """Собирает основной блок и НМУ."""
    blocks = [
        format_main_block(city_name, current),
        "",
        "Параметры, требующие внимания",
        format_nmu_block(get_nmu_warnings(current, daily)),
    ]
    return "\n".join(blocks)


def _debug_log(message: str, data: dict) -> None:
    # #region agent log
    try:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_path = os.path.join(base, "debug-ef3bc0.log")
        payload = {"sessionId": "ef3bc0", "location": "service.py", "message": message, "data": data, "timestamp": __import__("time").time() * 1000}
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
    # #endregion


def _agent_log(location: str, message: str, data: dict, hypothesis_id: str) -> None:
    # #region agent log
    try:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ws = os.path.dirname(base)
        log_path = os.path.join(ws, "debug-390bef.log")
        payload = {"sessionId": "390bef", "location": location, "message": message, "data": {**data, "hypothesisId": hypothesis_id}, "timestamp": int(__import__("time").time() * 1000)}
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
    # #endregion


async def get_weather_message(city_id: str) -> str | None:
    """
    По id города получает погоду и возвращает готовое сообщение для пользователя.
    Возвращает None при ошибке (город не найден или API недоступен).
    """
    # #region agent log
    _debug_log("get_weather_message entry", {"city_id": city_id, "hypothesisId": "B"})
    _agent_log("service.py:get_weather_message", "entry", {"city_id": city_id, "service_file": __file__}, "A")
    # #endregion
    city = get_city(city_id)
    if not city:
        # #region agent log
        _debug_log("get_city returned None", {"city_id": city_id, "hypothesisId": "B"})
        # #endregion
        return None
    data = await fetch_weather(city)
    if not data:
        # #region agent log
        _debug_log("fetch_weather returned None", {"city_id": city_id, "hypothesisId": "B"})
        # #endregion
        return None
    current = data["current"]
    daily = data.get("daily")
    msg = assemble_full_message(city.name, current, daily, city.timezone)
    # #region agent log
    _debug_log("assemble_full_message done", {"len": len(msg), "hypothesisId": "B"})
    _agent_log("service.py:assemble_full_message", "message built", {"msg_len": len(msg), "has_nmu_block": "Параметры, требующие внимания" in msg, "preview": msg[:120] if len(msg) > 120 else msg}, "B")
    # #endregion
    return msg
