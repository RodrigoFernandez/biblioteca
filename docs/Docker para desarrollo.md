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
- `storage_data:/app/storage` — imágenes
- `../../data:/app/data` — SQLite persistente en el host (`./data/biblioteca.db`)

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
- La base de datos SQLite se guarda en el bind mount `data/` (servicio `api`, con `BIBLIOTECA_DATABASE_URL=sqlite:///./data/biblioteca.db`), en `./data/biblioteca.db` del host; no desaparece al bajar los contenedores. Las imágenes quedan en el volumen `storage_data`.
- Si agregás una dependencia nueva a `pyproject.toml`, corré `docker compose -f Dockers/desa/docker-compose.yml build` para actualizar la imagen.
- PaddleOCR (API 3.x): la primera inferencia tarda más (~15-20s, descarga ~3 modelos: detección, reconocimiento y orientación de líneas). El código desactiva MKLDNN (`enable_mkldnn=False`) por un bug de paddlepaddle 3.3.x CPU; no reactivarlo sin subir paddlepaddle.
- `tests/test_fixtures.py` (fotos reales con OCR) solo corre en el contenedor (tiene `paddleocr`); en el host sin el extra `[ocr]` se salta. Requiere memoria suficiente: con fotos de cámara a resolución completa y ~6GB RAM el contenedor puede morir de OOM.

## Con Podman

### Prerrequisitos

- Podman con el plugin `podman compose`. El paquete `podman-compose` de apt **no** sirve: no autoloada el `.env` del host para la interpolación (falla el guard `:?`). Instalá el plugin nativo:

  ```bash
  sudo apt install docker-compose-v2
  ```

  Verificá: `podman compose version` debe mostrar Docker Compose v2 (no `podman-compose 1.0.6`).

- El socket de la API de Podman debe estar activo para que `podman compose build` conecte:

  ```bash
  systemctl --user enable --now podman.socket
  ```

  Si falta, el build falla con `Cannot connect to the Docker daemon at .../podman.sock`.

- Correr los comandos desde la raíz del proyecto (o usar el script `pc`, que lo hace solo).

### Uso

Los comandos son idénticos a los de Docker Compose salvo por `docker compose` → `podman compose`. Se usa el mismo `Dockers/desa/docker-compose.yml` y el mismo `Dockerfile`, sin cambios.

**Importante:** los comandos `podman compose` directos se corren **desde la raíz del proyecto**; así el `env_file` (`../../.env`, relativo a `Dockers/desa/`) resuelve al `.env` de la raíz. El script `pc` ya maneja esto solo.

#### 1. Variables de entorno

Crear `.env` en la raíz del proyecto (no está versionado):

```bash
BIBLIOTECA_TELEGRAM_BOT_TOKEN=tu_token_real
```

Es el único `.env` que se usa (el compose lo referencia vía `env_file: ../../.env` y el script `pc` hace `source` de él para la interpolación del host). No hay `.env` en `Dockers/desa/`. Está excluido del build context por el `.dockerignore` de la raíz, así que el token no entra en la imagen.

#### 2. Construir la imagen

```bash
podman compose -f Dockers/desa/docker-compose.yml build
```

Reconstruir solo hace falta si cambian las dependencias en `pyproject.toml`.

#### 3. Levantar servicios

```bash
# Solo API
podman compose -f Dockers/desa/docker-compose.yml up api

# API + Bot
podman compose -f Dockers/desa/docker-compose.yml up

# En background
podman compose -f Dockers/desa/docker-compose.yml up -d
```

#### 4. Live reload

Los mismos volúmenes montados (`../../app:/app/app`, `storage_data:/app/storage` y `../../data:/app/data` en el `api`) se reflejan al instante; `uvicorn --reload` funciona igual.

#### 5. Comandos útiles

```bash
# Logs en tiempo real
podman compose -f Dockers/desa/docker-compose.yml logs -f

# Ejecutar tests dentro del contenedor
podman compose -f Dockers/desa/docker-compose.yml run --rm api uv run pytest tests/ -v

# Lint
podman compose -f Dockers/desa/docker-compose.yml run --rm api uv run ruff check app/

# Shell dentro del contenedor
podman compose -f Dockers/desa/docker-compose.yml run --rm api bash

# Reconstruir sin cache
podman compose -f Dockers/desa/docker-compose.yml build --no-cache

# Bajar todo
podman compose -f Dockers/desa/docker-compose.yml down
```

#### 6. Script `pc`

Encapsula el `source .env` de la raíz + `podman compose`, y siempre corre desde la raíz del proyecto.

| Comando | Qué hace |
|---------|----------|
| `./scripts/pc` | build + up (API+Bot, foreground) |
| `./scripts/pc build` | solo build |
| `./scripts/pc down` | baja todo |
| `./scripts/pc up` | up (API+Bot, foreground) |
| `./scripts/pc api` | up api (solo API) |
| `./scripts/pc background` | up -d (todo en background) |
| `./scripts/pc api background` | up -d api (solo API en background) |

Los parámetros `api` y `background` se combinan en cualquier orden (p. ej. `./scripts/pc background api`).

### Notas

- Podman es **rootless** (sin daemon): las imágenes quedan en `~/.local/share/containers` y no hace falta un service ni `sudo` para `up`/`-d`.
- El reenvío de puertos (API en `http://localhost:8000`) funciona sin flags extra (usa `passt`/slirp4netns).
- `podman compose down`/`up`, el volumen `storage_data` y el bind mount `data/` (SQLite en el host) se comportan igual que con Docker.
