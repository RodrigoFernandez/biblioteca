# Docker para desarrollo

## Prerrequisitos

- Docker + Docker Compose (incluido en Docker Desktop / Docker Engine v27+)

## Archivos

| Archivo | Rol |
|---------|-----|
| `Dockers/desa/Dockerfile` | Imagen base: Python 3.11 slim + OpenCV + Pyzbar + PaddleOCR |
| `Dockers/desa/docker-compose.yml` | Servicios `api` y `bot` con volúmenes para live reload |
| `Dockers/desa/.dockerignore` | Excluye `.git`, `__pycache__`, `.env` del context de build |

## Uso

### 1. Variables de entorno

Crear `.env` en la raíz del proyecto (no está versionado):

```bash
BIBLIOTECA_TELEGRAM_BOT_TOKEN=tu_token_aqui
```

### 2. Construir la imagen

```bash
docker compose -f Dockers/desa/docker-compose.yml build
```

La primera vez instala system deps + Python packages (incluyendo PaddleOCR, que es pesado). Reconstruir solo hace falta si cambian las dependencias en `pyproject.toml`.

### 3. Levantar servicios

```bash
# Solo API
docker compose -f Dockers/desa/docker-compose.yml up api

# API + Bot
docker compose -f Dockers/desa/docker-compose.yml up

# En background
docker compose -f Dockers/desa/docker-compose.yml up -d
```

- API escucha en `http://localhost:8000`
- Bot se conecta a la API internamente vía `http://api:8000`

### 4. Live reload

Los directorios montados como volúmenes:

- `../../app:/app/app` (desde `Dockers/desa/`) — código fuente, cambios se reflejan al instante
- `storage_data:/app/storage` — imágenes + SQLite persistente entre reinicios

`uvicorn --reload` reinicia la API automáticamente al modificar archivos.

### 5. Comandos útiles

```bash
# Logs en tiempo real
docker compose -f Dockers/desa/docker-compose.yml logs -f

# Ejecutar tests dentro del contenedor
docker compose -f Dockers/desa/docker-compose.yml run --rm api uv run pytest tests/ -v

# Lint
docker compose -f Dockers/desa/docker-compose.yml run --rm api uv run ruff check app/

# Shell dentro del contenedor
docker compose -f Dockers/desa/docker-compose.yml run --rm api bash

# Reconstruir sin cache
docker compose -f Dockers/desa/docker-compose.yml build --no-cache

# Bajar todo
docker compose -f Dockers/desa/docker-compose.yml down
```

## Notas

- Todos los comandos usan `-f Dockers/desa/docker-compose.yml`. Podés crear un alias: `alias dc='docker compose -f Dockers/desa/docker-compose.yml'`
- La base de datos SQLite se guarda en el volumen `storage_data`, no desaparece al bajar los contenedores.
- Si agregás una dependencia nueva a `pyproject.toml`, corré `docker compose -f Dockers/desa/docker-compose.yml build` para actualizar la imagen.
- PaddleOCR tarda ~10s en la primera inferencia (descarga modelos). En el contenedor ocurre igual que en el host.
- `tests/test_fixtures.py` (fotos reales con OCR) solo corre en el contenedor (tiene `paddleocr`); en el host sin el extra `[ocr]` se salta.
