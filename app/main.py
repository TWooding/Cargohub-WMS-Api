import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.backend.database import init_db
from app.core.config import get_settings
from app.frontend.router import api_router, auth_router, public_router
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.request_timing import RequestTimingMiddleware

logging.basicConfig(level=logging.INFO)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(RequestTimingMiddleware)
app.add_middleware(RequestContextMiddleware)
# Strikte CORS-allowlist (leeg = geen cross-origin toegang).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "API_KEY", "X-CSRF-Token", "X-Request-ID"],
)

app.include_router(public_router)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(api_router, prefix=settings.api_prefix)
