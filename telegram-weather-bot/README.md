# Telegram-бот «Погода в городах России»

По кнопке «Старт» бот показывает список русских городов. При выборе города отображается текущая погода (Open-Meteo API, без ключа).

## Требования

- Python 3.10+
- Токен бота Telegram

## Получение токена

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram.
2. Отправьте команду `/newbot` и следуйте подсказкам (имя и username бота).
3. В ответ придёт токен вида `123456789:ABCdefGHI...` — сохраните его.

## Установка и запуск

```bash
cd telegram-weather-bot
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

Создайте файл `.env` (или задайте переменную окружения):

```bash
# Windows (PowerShell)
$env:BOT_TOKEN="ваш_токен_от_BotFather"

# Или скопируйте .env.example в .env и подставьте токен
copy .env.example .env
```

Запуск:

```bash
python -m bot.main
```

Остановка: `Ctrl+C`. Бот корректно завершит работу (graceful shutdown).

## Структура проекта

- `bot/` — инициализация бота, команды, обработчики, клавиатуры
- `weather/` — список городов, запрос к Open-Meteo, форматирование погоды

Погода берётся с [Open-Meteo](https://open-meteo.com/) (бесплатно, без регистрации).
