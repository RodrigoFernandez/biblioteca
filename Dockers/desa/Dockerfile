FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libgomp1 \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml .
RUN uv sync --extra ocr --frozen

COPY . .
RUN uv sync --extra ocr --frozen

CMD ["uv", "run", "uvicorn", "app.api:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
