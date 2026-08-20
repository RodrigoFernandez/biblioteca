# AGENTS.md — Biblioteca

## Stack

- **Runtime:** Python 3.11+
- **API:** FastAPI + Uvicorn
- **DB:** SQLite + SQLAlchemy 2.0 (async-safe with `check_same_thread=False`)
- **Migrations:** Alembic
- **Bot:** python-telegram-bot v20+ (async)
- **Image processing:** OpenCV + Pyzbar (barcode), PaddleOCR (OCR, lazy-loaded)
- **HTTP client:** httpx (async)
- **Validation:** Pydantic v2
- **Deps:** uv (pyproject.toml)
- **Lint:** ruff (E, F, I, UP rules, line-length 100)

## Project structure

```
app/
  config.py      # Settings via pydantic-settings, BIBLIOTECA_* env prefix
  database.py    # SQLAlchemy engine, SessionLocal, Base, get_db()
  models.py      # Book ORM model
  schemas.py     # Pydantic response/request models
  services.py    # Image processing pipeline + Open Library lookup
  api.py         # FastAPI app + POST /api/books/process-image
  bot.py         # Telegram bot with ConversationHandler (/nuevo)
Dockers/desa/   # Docker dev: docker-compose.yml + Dockerfile
tests/          # pytest: unit (services), integracion (api/bot), fixtures con fotos reales
```

## Run commands

```bash
# Docker dev (recomendado)
docker compose -f Dockers/desa/docker-compose.yml build
docker compose -f Dockers/desa/docker-compose.yml up          # api + bot
docker compose -f Dockers/desa/docker-compose.yml up api      # solo api
docker compose -f Dockers/desa/docker-compose.yml run --rm api uv run pytest tests/ -v

# Without Docker
BIBLIOTECA_TELEGRAM_BOT_TOKEN=xxx uv run uvicorn app.api:app --reload
BIBLIOTECA_TELEGRAM_BOT_TOKEN=xxx uv run python -m app.bot
uv run pytest tests/ -v
uv run ruff check app/
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

## Key conventions

- **Env prefix:** All settings use `BIBLIOTECA_` prefix (e.g. `BIBLIOTECA_DATABASE_URL`)
- **Image storage:** UUID-named files in `storage/images/`, paths stored as strings in DB
- **Image processing:** All images redimensionadas a 600px máximo lado más largo (manteniendo aspect ratio), codificadas como WebP calidad 85 — tamaño ~50-100 KB desde fotos de celular
- **Lazy imports:** PaddleOCR is imported inside `ocr_text()` only — heavy lib, never at module level
- **Flat package:** Single `app/` directory, no nested sub-packages
- **Barcodes:** Pyzbar tries raw image first, then preprocessed (blur + Otsu threshold). Accepts 10-digit (ISBN-10) and 13-digit (ISBN-13)
- **OCR fallback:** Only runs if barcode lookup didn't produce a title. Also extracts ISBN-10/ISBN-13 from OCR text (`extract_isbn`) and persists it when barcode is absent
- **Bot <-> API:** Bot calls API over HTTP (httpx), they run as separate processes

## Architecture decision: separate processes

Bot and API are independent processes communicating via HTTP. This keeps them decoupled and independently restartable. Do not embed the bot inside FastAPI's lifespan without a clear reason.
