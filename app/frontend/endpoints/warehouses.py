from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.backend.database import get_session
from app.backend.models import Warehouse, WarehouseCreate, WarehouseRead, WarehouseUpdate
from app.backend.services import warehouse_service
from app.frontend.endpoints._stubs import not_implemented

router = APIRouter(prefix="/warehouses", tags=["warehouses"])


def _get_or_404(session: Session, warehouse_id: int) -> Warehouse:
    warehouse = warehouse_service.get_warehouse(session, warehouse_id)
    if warehouse is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
    return warehouse


@router.get("", response_model=list[WarehouseRead])
def list_warehouses(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_session),
):
    return warehouse_service.list_warehouses(session, offset, limit)


@router.get("/{warehouse_id}", response_model=WarehouseRead)
def get_warehouse(warehouse_id: int, session: Session = Depends(get_session)):
    return _get_or_404(session, warehouse_id)


@router.get("/{warehouse_id}/locations", summary="Locaties in magazijn")
def list_warehouse_locations(warehouse_id: int):
    """Geef alle locaties terug die in dit magazijn liggen."""
    not_implemented()


@router.post("", response_model=WarehouseRead, status_code=status.HTTP_201_CREATED)
def create_warehouse(data: WarehouseCreate, session: Session = Depends(get_session)):
    return warehouse_service.create_warehouse(session, data)


@router.put("/{warehouse_id}", response_model=WarehouseRead)
def update_warehouse(warehouse_id: int, data: WarehouseUpdate, session: Session = Depends(get_session)):
    return warehouse_service.update_warehouse(session, _get_or_404(session, warehouse_id), data)


@router.delete("/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_warehouse(warehouse_id: int, session: Session = Depends(get_session)):
    warehouse_service.delete_warehouse(session, _get_or_404(session, warehouse_id))
