from fastapi import APIRouter, status

from app.frontend.endpoints._stubs import not_implemented

router = APIRouter(prefix="/item_groups", tags=["item_groups"])


@router.get("", summary="Lijst van productgroepen")
def list_item_groups():
    """Geef alle productgroepen terug."""
    not_implemented()


@router.get("/{item_group_id}", summary="Productgroep ophalen")
def get_item_group(item_group_id: int):
    """Geef één productgroep terug op basis van id."""
    not_implemented()


@router.get("/{item_group_id}/items", summary="Items in productgroep")
def list_item_group_items(item_group_id: int):
    """Geef alle items terug die bij deze productgroep horen."""
    not_implemented()


@router.post("", status_code=status.HTTP_201_CREATED, summary="Productgroep aanmaken")
def create_item_group():
    """Maak een nieuwe productgroep aan."""
    not_implemented()


@router.put("/{item_group_id}", summary="Productgroep bijwerken")
def update_item_group(item_group_id: int):
    """Werk een bestaande productgroep bij."""
    not_implemented()


@router.delete("/{item_group_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Productgroep verwijderen")
def delete_item_group(item_group_id: int):
    """Verwijder een productgroep."""
    not_implemented()
