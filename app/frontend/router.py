from fastapi import APIRouter, Depends

from app.frontend.endpoints import (
    api_keys,
    auth,
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
    users,
    warehouses,
)
from app.middleware.auth import require_route_permission

# Public routes (geen authenticatie)
public_router = APIRouter()
public_router.include_router(health.router)

# /auth/*: maakt de identiteit aan (login, refresh, ...) en heeft zelf geen permissie nodig
auth_router = APIRouter()
auth_router.include_router(auth.router)

# Protected routes: de default guard eist de permissie `<resource>:<method>` voor de principal
# (sessie, bearer of API key). Een resource die niet in de permissiematrix staat, geeft 403.
api_router = APIRouter(dependencies=[Depends(require_route_permission)])
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
api_router.include_router(api_keys.router)
api_router.include_router(users.router)
