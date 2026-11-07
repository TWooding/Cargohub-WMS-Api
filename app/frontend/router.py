from fastapi import APIRouter, Depends

from app.frontend.endpoints import (
    clients,
    health,
    inventories,
    item_groups,
    item_lines,
    item_types,
    items,
    locations,
    orders,
    shipments,
    suppliers,
    transfers,
    warehouses,
)
from app.middleware.auth import require_api_key

# Public routes (no API key)
public_router = APIRouter()
public_router.include_router(health.router)

# Protected routes: every endpoint here requires a valid API_KEY header
api_router = APIRouter(dependencies=[Depends(require_api_key)])
api_router.include_router(warehouses.router)
api_router.include_router(locations.router)
api_router.include_router(transfers.router)
api_router.include_router(items.router)
api_router.include_router(item_lines.router)
api_router.include_router(item_groups.router)
api_router.include_router(item_types.router)
api_router.include_router(inventories.router)
api_router.include_router(suppliers.router)
api_router.include_router(orders.router)
api_router.include_router(clients.router)
api_router.include_router(shipments.router)
