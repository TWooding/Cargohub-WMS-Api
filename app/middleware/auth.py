from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.config import Settings, get_settings

# Same header name as API v1. Shows up as the "Authorize" button in Swagger.
api_key_header = APIKeyHeader(name="API_KEY", auto_error=False)


def require_api_key(
    api_key: str | None = Depends(api_key_header),
    settings: Settings = Depends(get_settings),
) -> str:
    """Dependency that rejects requests without a valid API key.

    TODO: replace the env-based key list with users + per-endpoint rights from the database.
    """
    if api_key is None or api_key not in settings.api_key_list:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
    return api_key
