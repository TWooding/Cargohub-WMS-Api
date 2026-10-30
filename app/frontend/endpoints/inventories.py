from fastapi import APIRouter, status

from app.frontend.endpoints._stubs import not_implemented

router = APIRouter(prefix="/inventories", tags=["inventories"])

# Voorraadregels hebben een samengestelde sleutel (item_id, location_id);
# er is daarom bewust geen GET/PUT/DELETE op één id.


@router.get("", summary="Lijst van voorraadregels")
def list_inventories():
    """Geef alle voorraadregels (item per locatie) terug."""
    not_implemented()


@router.post("", status_code=status.HTTP_201_CREATED, summary="Voorraadregel aanmaken")
def create_inventory():
    """Maak een nieuwe voorraadregel voor een item op een locatie aan."""
    not_implemented()
