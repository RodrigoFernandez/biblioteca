# biblioteca

Gestion de inventario de libros via procesamiento inteligente de imagenes. FastAPI + Telegram Bot.

## Stack

| Componente | Tecnologia |
|------------|-----------|
| API | FastAPI + Uvicorn |
| Bot | python-telegram-bot v20+ |
| DB | SQLite + SQLAlchemy 2.0 |
| Migraciones | Alembic |
| Vision | Pyzbar (barras) + PaddleOCR (texto) |
| Dependencias | uv |

## Estructura

```
app/
  config.py      # Settings (BIBLIOTECA_* env vars)
  database.py    # SQLAlchemy engine + session
  models.py      # Book model
  schemas.py     # Pydantic schemas
  services.py    # Pipeline: barcode -> Open Library -> OCR
  api.py         # FastAPI endpoint
  bot.py         # Telegram ConversationHandler
storage/images/  # Imagenes guardadas (UUID)
tests/           # Tests basicos
```

## Para correr

```bash
# Instalar dependencias
uv sync
uv sync --extra ocr    # solo si necesitas PaddleOCR

# API
BIBLIOTECA_TELEGRAM_BOT_TOKEN=tu_token uv run uvicorn app.api:app --reload

# Bot (otra terminal)
BIBLIOTECA_TELEGRAM_BOT_TOKEN=tu_token uv run python -m app.bot

# Tests
uv run pytest tests/ -v

# Lint
uv run ruff check app/

# Primera migracion
uv run alembic revision --autogenerate -m "init"
uv run alembic upgrade head
```
