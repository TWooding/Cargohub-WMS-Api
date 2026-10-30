from fastapi import APIRouter, status

from app.frontend.endpoints._stubs import not_implemented

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", summary="Lijst van locaties")
def list_locations():
    """Geef alle locaties terug."""
    not_implemented()


@router.get("/{location_id}", summary="Locatie ophalen")
def get_location(location_id: int):
    """Geef één locatie terug op basis van id."""
    not_implemented()


@router.post("", status_code=status.HTTP_201_CREATED, summary="Locatie aanmaken")
def create_location():
    """Maak een nieuwe locatie aan."""
    not_implemented()


@router.put("/{location_id}", summary="Locatie bijwerken")
def update_location(location_id: int):
    """Werk een bestaande locatie bij."""
    not_implemented()


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Locatie verwijderen")
def delete_location(location_id: int):
    """Verwijder een locatie."""
    not_implemented()
