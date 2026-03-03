"""Поиск кафе и ресторанов поблизости от города через Overpass (OpenStreetMap)."""

from __future__ import annotations

import json
import logging
import os
import random
from dataclasses import dataclass
from typing import Any

import aiohttp

from weather.cities import City, get_city

logger = logging.getLogger(__name__)


def _session_log(message: str, data: dict, hypothesis_id: str) -> None:
    # #region agent log
    try:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ws = os.path.dirname(base)
        log_path = os.path.join(ws, "debug-bfb7f9.log")
        payload = {"sessionId": "bfb7f9", "location": "places/food.py", "message": message, "data": data, "hypothesisId": hypothesis_id, "timestamp": int(__import__("time").time() * 1000)}
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
    # #endregion

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


@dataclass(frozen=True)
class Place:
    name: str
    kind: str
    address: str | None = None


def _build_overpass_query(city: City, radius_m: int = 12000) -> str:
    """
    Строит Overpass-запрос для поиска кафе и ресторанов вокруг координат города.
    """
    lat = city.latitude
    lon = city.longitude
    return f"""
    [out:json][timeout:15];
    (
      node["amenity"~"^(restaurant|cafe|fast_food|bar)$"](around:{radius_m},{lat},{lon});
      way["amenity"~"^(restaurant|cafe|fast_food|bar)$"](around:{radius_m},{lat},{lon});
    );
    out center 80;
    """


async def _fetch_overpass(query: str) -> dict[str, Any] | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                OVERPASS_URL,
                data=query.encode("utf-8"),
                timeout=aiohttp.ClientTimeout(total=15),
                headers={"Content-Type": "text/plain; charset=utf-8"},
            ) as resp:
                if resp.status != 200:
                    logger.warning("Overpass returned status %s", resp.status)
                    return None
                return await resp.json()
    except Exception as e:
        logger.exception("Overpass request failed: %s", e)
        return None


def _place_from_element(el: dict[str, Any]) -> Place | None:
    tags = el.get("tags") or {}
    name = tags.get("name:ru") or tags.get("name")
    if not name:
        return None
    amenity = tags.get("amenity", "")
    if amenity == "restaurant":
        kind = "Ресторан"
    elif amenity == "cafe":
        kind = "Кафе"
    elif amenity == "fast_food":
        kind = "Фастфуд"
    elif amenity == "bar":
        kind = "Бар"
    else:
        kind = "Заведение"

    parts = []
    city = tags.get("addr:city")
    street = tags.get("addr:street")
    house = tags.get("addr:housenumber")
    if city:
        parts.append(city)
    if street:
        parts.append(street)
    if house:
        parts.append(house)
    address = ", ".join(parts) if parts else None
    return Place(name=name, kind=kind, address=address)


async def get_city_places(city_id: str, limit: int = 5) -> list[Place]:
    """
    Возвращает список до `limit` кафе/ресторанов рядом с выбранным городом.
    Данные берутся из OpenStreetMap (Overpass API).
    """
    city = get_city(city_id)
    if not city:
        # #region agent log
        _session_log("food_flow", {"city_id": city_id, "city_found": False}, "H3")
        # #endregion
        return []

    query = _build_overpass_query(city)
    data = await _fetch_overpass(query)
    # #region agent log
    _session_log("food_flow", {"city_id": city_id, "data_ok": data is not None, "elements_count": len(data.get("elements") or []) if data else 0}, "H3")
    # #endregion
    if not data:
        return []

    elements = data.get("elements") or []
    places: list[Place] = []
    for el in elements:
        place = _place_from_element(el)
        if place:
            places.append(place)

    # Убираем дубликаты по имени
    unique: dict[str, Place] = {}
    for p in places:
        if p.name not in unique:
            unique[p.name] = p

    all_places = list(unique.values())
    # #region agent log
    _session_log("food_flow", {"city_id": city_id, "places_count": len(all_places)}, "H3")
    # #endregion
    if not all_places:
        return []

    random.shuffle(all_places)
    return all_places[:limit]

