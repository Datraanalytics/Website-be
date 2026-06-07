from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache
from urllib.parse import quote_plus

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # Database — all values come from the environment / .env (no hardcoded target)
    db_host: str = ""
    db_port: int = 3306
    db_name: str = ""
    db_user: str = ""
    db_password: str = ""

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    @property
    def database_url(self) -> str:
        # URL encode password to handle special characters like @
        encoded_password = quote_plus(self.db_password)
        return f"mysql+pymysql://{self.db_user}:{encoded_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def async_database_url(self) -> str:
        # URL encode password to handle special characters like @
        encoded_password = quote_plus(self.db_password)
        return f"mysql+aiomysql://{self.db_user}:{encoded_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
