"""API key authentication for v1."""

import hmac

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str | None = Security(api_key_header)) -> str:
    """Verify the API key from the request header. Returns the key if valid."""
    if api_key is None or not hmac.compare_digest(api_key, settings.API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key
