from fastapi import APIRouter, status

from app.frontend.endpoints._stubs import not_implemented

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", summary="Lijst van klanten")
def list_clients():
    """Geef alle klanten terug."""
    not_implemented()


@router.get("/{client_id}", summary="Klant ophalen")
def get_client(client_id: int):
    """Geef één klant terug op basis van id."""
    not_implemented()


@router.get("/{client_id}/orders", summary="Orders van klant")
def list_client_orders(client_id: int):
    """Geef alle orders van deze klant terug."""
    not_implemented()


@router.post("", status_code=status.HTTP_201_CREATED, summary="Klant aanmaken")
def create_client():
    """Maak een nieuwe klant aan."""
    not_implemented()


@router.put("/{client_id}", summary="Klant bijwerken")
def update_client(client_id: int):
    """Werk een bestaande klant bij."""
    not_implemented()


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Klant verwijderen")
def delete_client(client_id: int):
    """Verwijder een klant."""
    not_implemented()
