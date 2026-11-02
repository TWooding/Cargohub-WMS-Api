from fastapi import APIRouter, status

from app.frontend.endpoints._stubs import not_implemented

router = APIRouter(prefix="/item_types", tags=["item_types"])


@router.get("", summary="Lijst van producttypes")
def list_item_types():
    """Geef alle producttypes terug."""
    not_implemented()


@router.get("/{item_type_id}", summary="Producttype ophalen")
def get_item_type(item_type_id: int):
    """Geef één producttype terug op basis van id."""
    not_implemented()


@router.get("/{item_type_id}/items", summary="Items van producttype")
def list_item_type_items(item_type_id: int):
    """Geef alle items terug die bij dit producttype horen."""
    not_implemented()


@router.post("", status_code=status.HTTP_201_CREATED, summary="Producttype aanmaken")
def create_item_type():
    """Maak een nieuw producttype aan."""
    not_implemented()


@router.put("/{item_type_id}", summary="Producttype bijwerken")
def update_item_type(item_type_id: int):
    """Werk een bestaand producttype bij."""
    not_implemented()


@router.delete("/{item_type_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Producttype verwijderen")
def delete_item_type(item_type_id: int):
    """Verwijder een producttype."""
    not_implemented()
