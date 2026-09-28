# AVA Club Service

Базовый проект серверной части системы управления спортивным клубом.

## Требования

- Python 3.12+
- PostgreSQL

## Локальный запуск

```powershell
cd product
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
cp .env.example .env
uvicorn club_service.main:app --reload --env-file .env
```

Перед запуском создайте базу `ava_club` в локальном PostgreSQL и при необходимости
измените `DATABASE_URL` в `.env`. Health-check не создаёт таблицы и не требует миграций.

После запуска доступны:

- `GET http://127.0.0.1:8000/api/v1/health/live` — проверка процесса приложения;
- `GET http://127.0.0.1:8000/api/v1/health/ready` — проверка соединения с PostgreSQL;
- `http://127.0.0.1:8000/docs` — Swagger UI;
- `http://127.0.0.1:8000/redoc` — ReDoc.


Настройки читаются из переменных окружения. Пример находится в `.env.example`.

## Проверки

```powershell
pytest
ruff check .
```

## Структура

```text
product/
├── src/club_service/
│   ├── api/              # HTTP-маршруты и зависимости FastAPI
│   ├── core/             # Конфигурация и общесистемный код
│   ├── domain/           # Доменные сущности и правила
│   ├── infrastructure/   # База данных и внешние интеграции
│   ├── repositories/     # Интерфейсы доступа к данным
│   ├── schemas/          # Входные и выходные DTO API
│   └── services/         # Прикладные сценарии
└── tests/                # Автоматические тесты
```

Каркас оставляет предметные модули пустыми намеренно: модели пользователей, ролей,
мероприятий, заявок, абонементов и посещений будут добавляться по мере реализации.
