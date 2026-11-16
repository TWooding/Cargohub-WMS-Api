from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings, read from environment variables (or a .env file)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CargoHUB WMS API"
    api_prefix: str = "/api/v2"
    database_url: str = "postgresql+psycopg://cargohub:cargohub@localhost:5432/cargohub"

    # --- Auth (zie Auth System Design) ---
    jwt_secret: str  # verplicht, minimaal 32 tekens
    cookie_secure: bool = True  # alleen uitzetten voor lokale http-dev
    cors_origins: str = ""  # komma-gescheiden allowlist; leeg = geen cross-origin
    session_ttl_seconds: int = 8 * 3600
    access_token_ttl_seconds: int = 15 * 60
    refresh_token_ttl_seconds: int = 30 * 24 * 3600
    min_password_length: int = 12

    # Brute-force bescherming
    login_ip_limit: int = 30  # pogingen per IP per window
    login_user_limit: int = 10  # pogingen per username per window
    rate_window_seconds: int = 900
    refresh_ip_limit: int = 60
    api_key_fail_limit: int = 20  # mislukte key-checks per IP per window
    lockout_after: int = 10  # mislukte logins voor een tijdelijke lock
    lockout_seconds: int = 900

    # Optionele eerste beheerder: wordt aangemaakt als er nog geen users zijn.
    bootstrap_admin_username: str = ""
    bootstrap_admin_email: str = ""
    bootstrap_admin_password: str = ""

    @field_validator("jwt_secret")
    @classmethod
    def _secret_long_enough(cls, v: str) -> str:
        if len(v.encode()) < 32:
            raise ValueError("JWT_SECRET moet minimaal 32 bytes zijn")
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
