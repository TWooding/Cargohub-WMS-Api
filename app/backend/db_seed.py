import json

from sqlmodel import Session, create_engine, func, select

from app.backend.models import (
    Client,
    Inventory,
    Item,
    ItemGroup,
    ItemLine,
    ItemType,
    Location,
    Order,
    OrderItem,
    Shipment,
    ShipmentItem,
    Supplier,
    Transfer,
    TransferItem,
    Warehouse,
)
from app.core.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)

tables: dict[str, type] = {
    "warehouse": Warehouse,
    "client": Client,
    "item_group": ItemGroup,
    "item_line": ItemLine,
    "item_type": ItemType,
    "supplier": Supplier,
    "item": Item,
    "location": Location,
    "inventory": Inventory,
    "order": Order,
    "order_item": OrderItem,
    "shipment": Shipment,
    "shipment_item": ShipmentItem,
    "transfer": Transfer,
    "transfer_item": TransferItem,
}


def seed_table(table_class: type, file_name: str):
    with Session(engine) as session:
        if session.exec(select(func.count()).select_from(table_class)).one() != 0:
            return

    with open(f"../../legacy/data/{file_name}.json") as file:
        data = json.load(file)

    if file_name == "item":
        for item in data:
            item["item_code"] = item.pop("code")

    with Session(engine) as session:
        session.bulk_insert_mappings(table_class, data)
        session.commit()


for file_name, table_class in tables.items():
    seed_table(table_class, file_name)
