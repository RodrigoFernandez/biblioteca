from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./biblioteca.db"
    storage_path: Path = Path("storage/images")
    api_base_url: str = "http://127.0.0.1:8000"
    telegram_bot_token: str = ""

    model_config = {"env_prefix": "BIBLIOTECA_"}


settings = Settings()
