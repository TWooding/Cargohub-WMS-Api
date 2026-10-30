from typing import Optional

from sqlmodel import Session, select

from app.backend.models import Warehouse, WarehouseCreate, WarehouseUpdate


def list_warehouses(session: Session, offset: int = 0, limit: int = 100) -> list[Warehouse]:
    return list(session.exec(select(Warehouse).offset(offset).limit(limit)).all())


def get_warehouse(session: Session, warehouse_id: int) -> Optional[Warehouse]:
    return session.get(Warehouse, warehouse_id)


def create_warehouse(session: Session, data: WarehouseCreate) -> Warehouse:
    warehouse = Warehouse.model_validate(data)
    session.add(warehouse)
    session.commit()
    session.refresh(warehouse)
    return warehouse


def update_warehouse(session: Session, warehouse: Warehouse, data: WarehouseUpdate) -> Warehouse:
    warehouse.sqlmodel_update(data.model_dump(exclude_unset=True))
    session.add(warehouse)
    session.commit()
    session.refresh(warehouse)
    return warehouse


def delete_warehouse(session: Session, warehouse: Warehouse) -> None:
    session.delete(warehouse)
    session.commit()
