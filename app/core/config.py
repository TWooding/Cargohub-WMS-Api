from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings, read from environment variables (or a .env file)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CargoHUB WMS API"
    api_prefix: str = "/api/v2"
    database_url: str = "postgresql+psycopg://cargohub:cargohub@localhost:5432/cargohub"
    # Comma-separated, e.g. "key1,key2"
    api_keys: str = "dev-key"

    @property
    def api_key_list(self) -> set[str]:
        return {key.strip() for key in self.api_keys.split(",") if key.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
