import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.backend.database import init_db
from app.core.config import get_settings
from app.frontend.router import api_router, public_router
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

app.include_router(public_router)
app.include_router(api_router, prefix=settings.api_prefix)
