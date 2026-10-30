from fastapi import APIRouter, status

from app.frontend.endpoints._stubs import not_implemented

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", summary="Lijst van orders")
def list_orders():
    """Geef alle orders terug."""
    not_implemented()


@router.get("/{order_id}", summary="Order ophalen")
def get_order(order_id: int):
    """Geef één order terug op basis van id."""
    not_implemented()


@router.get("/{order_id}/items", summary="Items in order")
def list_order_items(order_id: int):
    """Geef de orderregels (items met aantallen) van een order terug."""
    not_implemented()


@router.post("", status_code=status.HTTP_201_CREATED, summary="Order aanmaken")
def create_order():
    """Maak een nieuwe order aan."""
    not_implemented()


@router.put("/{order_id}", summary="Order bijwerken")
def update_order(order_id: int):
    """Werk een bestaande order bij."""
    not_implemented()


@router.put("/{order_id}/items", summary="Items in order vervangen")
def update_order_items(order_id: int):
    """Vervang de orderregels van een order door de aangeleverde lijst."""
    not_implemented()


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Order verwijderen")
def delete_order(order_id: int):
    """Verwijder een order."""
    not_implemented()
