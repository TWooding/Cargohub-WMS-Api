from fastapi import APIRouter, status

from app.frontend.endpoints._stubs import not_implemented

router = APIRouter(prefix="/item_lines", tags=["item_lines"])


@router.get("", summary="Lijst van productlijnen")
def list_item_lines():
    """Geef alle productlijnen terug."""
    not_implemented()


@router.get("/{item_line_id}", summary="Productlijn ophalen")
def get_item_line(item_line_id: int):
    """Geef één productlijn terug op basis van id."""
    not_implemented()


@router.get("/{item_line_id}/items", summary="Items in productlijn")
def list_item_line_items(item_line_id: int):
    """Geef alle items terug die bij deze productlijn horen."""
    not_implemented()


@router.post("", status_code=status.HTTP_201_CREATED, summary="Productlijn aanmaken")
def create_item_line():
    """Maak een nieuwe productlijn aan."""
    not_implemented()


@router.put("/{item_line_id}", summary="Productlijn bijwerken")
def update_item_line(item_line_id: int):
    """Werk een bestaande productlijn bij."""
    not_implemented()


@router.delete("/{item_line_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Productlijn verwijderen")
def delete_item_line(item_line_id: int):
    """Verwijder een productlijn."""
    not_implemented()
