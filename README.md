# biblioteca

Gestion de inventario de libros via procesamiento inteligente de imagenes. FastAPI + Telegram Bot.

## Stack

| Componente | Tecnologia |
|------------|-----------|
| API | FastAPI + Uvicorn |
| Bot | python-telegram-bot v20+ |
| DB | SQLite + SQLAlchemy 2.0 |
| Migraciones | Alembic |
| Vision | Pyzbar (barras) + PaddleOCR (texto) + OpenCV (redimension WebP) |
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
Dockers/desa/    # Docker para desarrollo (compose + Dockerfile)
storage/images/  # Imagenes guardadas (UUID .webp)
tests/           # Tests basicos
```

## Para correr

### Con Docker (recomendado para desarrollo)

```bash
# Crear .env con tu token
echo "BIBLIOTECA_TELEGRAM_BOT_TOKEN=tu_token" > .env

# Construir
docker compose -f Dockers/desa/docker-compose.yml build

# Levantar todo
docker compose -f Dockers/desa/docker-compose.yml up
```

Ver `docs/Docker para desarrollo.md` para más detalles (tests, lint, comandos útiles).

### Sin Docker (instalación local)

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

## Tests

Los tests no requieren que la API ni el bot esten corriendo ni acceso a red.

```bash
# Correr toda la suite
uv run pytest tests/ -v

# Lint
uv run ruff check app/ tests/
```

Cobertura actual (`tests/test_services.py`):

- `test_save_image` — guarda la imagen en `storage_path` y conserva los bytes
- `test_read_barcode_returns_none_on_blank` — imagen sin codigo de barras devuelve `None`
- `test_extract_structured_data` — texto completo se mapea a titulo, autor y editorial
- `test_extract_structured_data_minimal` — una sola linea solo completa el titulo
