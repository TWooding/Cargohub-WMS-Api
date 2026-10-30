from fastapi import APIRouter, status

from app.frontend.endpoints._stubs import not_implemented

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", summary="Lijst van items")
def list_items():
    """Geef alle items terug."""
    not_implemented()


@router.get("/{item_id}", summary="Item ophalen")
def get_item(item_id: int):
    """Geef één item terug op basis van id."""
    not_implemented()


@router.get("/{item_id}/inventory", summary="Voorraad van item")
def list_item_inventory(item_id: int):
    """Geef de voorraadregels van een item per locatie terug."""
    not_implemented()


@router.get("/{item_id}/inventory/totals", summary="Voorraadtotalen van item")
def get_item_inventory_totals(item_id: int):
    """Geef de voorraadtotalen van een item over alle locaties terug."""
    not_implemented()


@router.post("", status_code=status.HTTP_201_CREATED, summary="Item aanmaken")
def create_item():
    """Maak een nieuw item aan."""
    not_implemented()


@router.put("/{item_id}", summary="Item bijwerken")
def update_item(item_id: int):
    """Werk een bestaand item bij."""
    not_implemented()


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Item verwijderen")
def delete_item(item_id: int):
    """Verwijder een item."""
    not_implemented()
