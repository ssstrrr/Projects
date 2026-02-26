"""Список русских городов с координатами и таймзонами для запросов погоды."""

from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    """Город с координатами и таймзоной."""
    id: str
    name: str
    latitude: float
    longitude: float
    timezone: str


CITIES: tuple[City, ...] = (
    City("moscow", "Москва", 55.7558, 37.6173, "Europe/Moscow"),
    City("spb", "Санкт-Петербург", 59.9343, 30.3351, "Europe/Moscow"),
    City("novosibirsk", "Новосибирск", 55.0084, 82.9357, "Asia/Novosibirsk"),
    City("ekaterinburg", "Екатеринбург", 56.8389, 60.6057, "Asia/Yekaterinburg"),
    City("kazan", "Казань", 55.8304, 49.0661, "Europe/Moscow"),
    City("nizhny_novgorod", "Нижний Новгород", 56.2965, 43.9361, "Europe/Moscow"),
    City("chelyabinsk", "Челябинск", 55.1644, 61.4368, "Asia/Yekaterinburg"),
    City("samara", "Самара", 53.1959, 50.1002, "Europe/Samara"),
    City("omsk", "Омск", 54.9885, 73.3242, "Asia/Omsk"),
    City("rostov", "Ростов-на-Дону", 47.2357, 39.7015, "Europe/Moscow"),
    City("ufa", "Уфа", 54.7388, 55.9721, "Asia/Yekaterinburg"),
    City("krasnoyarsk", "Красноярск", 56.0153, 92.8932, "Asia/Krasnoyarsk"),
    City("voronezh", "Воронеж", 51.6720, 39.1843, "Europe/Moscow"),
    City("perm", "Пермь", 58.0105, 56.2502, "Asia/Yekaterinburg"),
    City("volgograd", "Волгоград", 48.7080, 44.5133, "Europe/Volgograd"),
    City("krasnodar", "Краснодар", 45.0353, 38.9753, "Europe/Moscow"),
    City("saratov", "Саратов", 51.5924, 46.0342, "Europe/Saratov"),
    City("tyumen", "Тюмень", 57.1531, 65.5343, "Asia/Yekaterinburg"),
    City("tolyatti", "Тольятти", 53.5303, 49.3461, "Europe/Samara"),
    City("izhevsk", "Ижевск", 56.8498, 53.2045, "Europe/Samara"),
    City("barnaul", "Барнаул", 53.3606, 83.7545, "Asia/Barnaul"),
    City("ulyanovsk", "Ульяновск", 54.3282, 48.3866, "Europe/Ulyanovsk"),
    City("irkutsk", "Иркутск", 52.2978, 104.2964, "Asia/Irkutsk"),
    City("khabarovsk", "Хабаровск", 48.4827, 135.0838, "Asia/Vladivostok"),
    City("yaroslavl", "Ярославль", 57.6299, 39.8737, "Europe/Moscow"),
    City("vladivostok", "Владивосток", 43.1198, 131.8869, "Asia/Vladivostok"),
    City("makhachkala", "Махачкала", 42.9849, 47.5047, "Europe/Moscow"),
    City("tomsk", "Томск", 56.4846, 84.9476, "Asia/Tomsk"),
    City("orenburg", "Оренбург", 51.7682, 55.0970, "Asia/Yekaterinburg"),
)

CITIES_BY_ID: dict[str, City] = {c.id: c for c in CITIES}


def get_city(city_id: str) -> City | None:
    """Возвращает город по id или None."""
    return CITIES_BY_ID.get(city_id)
