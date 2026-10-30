from fastapi import APIRouter, status

from app.frontend.endpoints._stubs import not_implemented

router = APIRouter(prefix="/shipments", tags=["shipments"])


@router.get("", summary="Lijst van zendingen")
def list_shipments():
    """Geef alle zendingen terug."""
    not_implemented()


@router.get("/{shipment_id}", summary="Zending ophalen")
def get_shipment(shipment_id: int):
    """Geef één zending terug op basis van id."""
    not_implemented()


@router.get("/{shipment_id}/orders", summary="Orders in zending")
def list_shipment_orders(shipment_id: int):
    """Geef de id's van de orders in deze zending terug."""
    not_implemented()


@router.get("/{shipment_id}/items", summary="Items in zending")
def list_shipment_items(shipment_id: int):
    """Geef de items (met aantallen) in deze zending terug."""
    not_implemented()


@router.post("", status_code=status.HTTP_201_CREATED, summary="Zending aanmaken")
def create_shipment():
    """Maak een nieuwe zending aan."""
    not_implemented()


@router.put("/{shipment_id}", summary="Zending bijwerken")
def update_shipment(shipment_id: int):
    """Werk een bestaande zending bij."""
    not_implemented()


@router.put("/{shipment_id}/orders", summary="Orders in zending vervangen")
def update_shipment_orders(shipment_id: int):
    """Vervang de orders van een zending door de aangeleverde lijst."""
    not_implemented()


@router.put("/{shipment_id}/items", summary="Items in zending vervangen")
def update_shipment_items(shipment_id: int):
    """Vervang de items van een zending door de aangeleverde lijst."""
    not_implemented()


@router.delete("/{shipment_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Zending verwijderen")
def delete_shipment(shipment_id: int):
    """Verwijder een zending."""
    not_implemented()
