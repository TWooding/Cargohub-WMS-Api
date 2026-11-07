from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlmodel import Session

from app.backend.database import get_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health():
    return {"status": "ok"}


@router.get("/db")
def health_db(session: Session = Depends(get_session)):
    session.exec(text("SELECT 1"))
    return {"status": "ok", "database": "reachable"}
