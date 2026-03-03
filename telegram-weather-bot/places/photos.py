"""Поиск красивых фотографий города из открытых источников (Wikipedia/Wikimedia)."""

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
        payload = {"sessionId": "bfb7f9", "location": "places/photos.py", "message": message, "data": data, "hypothesisId": hypothesis_id, "timestamp": int(__import__("time").time() * 1000)}
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
    # #endregion

WIKI_API_URL = "https://ru.wikipedia.org/w/api.php"
COMMONS_API_URL = "https://commons.wikimedia.org/w/api.php"


@dataclass(frozen=True)
class CityPhoto:
    title: str
    url: str


async def _wiki_request(params: dict[str, Any]) -> dict[str, Any] | None:
    """Выполняет запрос к Wikipedia API с базовыми параметрами и таймаутом."""
    base_params = {
        "format": "json",
        "formatversion": "2",
        "origin": "*",
    }
    query = {**base_params, **params}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                WIKI_API_URL,
                params=query,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    logger.warning("Wikipedia returned status %s for %s", resp.status, query)
                    return None
                return await resp.json()
    except Exception as e:
        logger.exception("Wikipedia request failed: %s", e)
        return None


async def _commons_request(params: dict[str, Any]) -> dict[str, Any] | None:
    """Выполняет запрос к Wikimedia Commons API."""
    base_params = {
        "format": "json",
        "formatversion": "2",
        "origin": "*",
    }
    query = {**base_params, **params}
    headers = {"User-Agent": "TelegramWeatherBot/1.0 (https://github.com/; contact for images)"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                COMMONS_API_URL,
                params=query,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    logger.warning("Commons returned status %s for %s", resp.status, query)
                    return None
                return await resp.json()
    except Exception as e:
        logger.exception("Commons request failed: %s", e)
        return None


async def _search_city_pages(city: City) -> list[int]:
    """Ищет страницы по городу и возвращает id страниц (город + достопримечательности)."""
    seen: set[int] = set()
    for query_term in (city.name, f"{city.name} достопримечательности"):
        data = await _wiki_request(
            {
                "action": "query",
                "list": "search",
                "srsearch": query_term,
                "srlimit": 10,
            }
        )
        if not data or "query" not in data:
            continue
        for item in data["query"].get("search", []):
            if "pageid" in item and item["pageid"] not in seen:
                seen.add(item["pageid"])
    return list(seen)


async def _commons_search_photos(city: City) -> list[CityPhoto]:
    """Резервный поиск картинок города напрямую по Wikimedia Commons."""
    data = await _commons_request(
        {
            "action": "query",
            "prop": "imageinfo",
            "generator": "search",
            "gsrsearch": city.name,
            "gsrwhat": "text",
            "gsrnamespace": 6,
            "gsrlimit": 20,
            "iiprop": "url",
        }
    )
    # #region agent log
    _session_log(
        "commons_response",
        {
            "city": city.name,
            "has_data": data is not None,
            "has_query": data.get("query") is not None if data else False,
            "pages_type": type(data["query"].get("pages")).__name__ if data and data.get("query") else None,
            "pages_len": len(data["query"].get("pages") or []) if data and data.get("query") else 0,
        },
        "H2",
    )
    # #endregion
    if not data or "query" not in data:
        return []

    raw_pages = data["query"].get("pages")
    # formatversion=2: pages может быть list или dict по pageid
    pages = raw_pages if isinstance(raw_pages, list) else (list(raw_pages.values()) if raw_pages else [])
    photos: list[CityPhoto] = []
    for page in pages:
        title = page.get("title")
        info = page.get("imageinfo")
        url = None
        if isinstance(info, list) and info:
            url = info[0].get("url")
        if not title or not url:
            continue
        photos.append(CityPhoto(title=title, url=url))
    return photos


async def _load_page_images(page_ids: list[int]) -> list[CityPhoto]:
    """По page id загружает изображения страниц (original или thumbnail)."""
    if not page_ids:
        return []
    data = await _wiki_request(
        {
            "action": "query",
            "prop": "pageimages",
            "pageids": "|".join(str(pid) for pid in page_ids),
            "piprop": "original|thumbnail",
            "pithumbsize": 640,
        }
    )
    if not data or "query" not in data:
        return []
    raw_pages = data["query"].get("pages")
    # API может вернуть list (formatversion=2) или dict по pageid
    pages = raw_pages if isinstance(raw_pages, list) else (list(raw_pages.values()) if raw_pages else [])
    photos: list[CityPhoto] = []
    for page in pages:
        title = page.get("title")
        img = page.get("original") or page.get("thumbnail")
        if not title or not img:
            continue
        url = img.get("source") if isinstance(img, dict) else None
        if not url:
            continue
        photos.append(CityPhoto(title=title, url=url))
    return photos


async def get_city_photos(city_id: str, limit: int = 5) -> list[CityPhoto]:
    """
    Возвращает до `limit` фотографий для выбранного города.

    Фото берутся из Wikipedia/Wikimedia, без ключей и регистрации.
    """
    city = get_city(city_id)
    if not city:
        # #region agent log
        _session_log("photos_flow", {"city_id": city_id, "city_found": False}, "H2")
        # #endregion
        return []

    page_ids = await _search_city_pages(city)
    # #region agent log
    _session_log("photos_flow", {"city_id": city_id, "page_ids_len": len(page_ids)}, "H2")
    # #endregion

    photos: list[CityPhoto] = []
    if page_ids:
        photos = await _load_page_images(page_ids)
        # #region agent log
        _session_log("photos_flow", {"city_id": city_id, "photos_len": len(photos)}, "H2")
        # #endregion

    if not photos:
        # #region agent log
        _session_log("photos_flow", {"city_id": city_id, "entering_commons": True}, "H2")
        # #endregion
        commons_photos = await _commons_search_photos(city)
        # #region agent log
        _session_log("photos_flow", {"city_id": city_id, "commons_photos_len": len(commons_photos)}, "H2")
        # #endregion
        photos = commons_photos

    if not photos:
        return []

    random.shuffle(photos)
    return photos[:limit]

