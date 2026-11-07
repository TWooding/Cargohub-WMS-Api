from fastapi import APIRouter, status

from app.frontend.endpoints._stubs import not_implemented

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", summary="Lijst van leveranciers")
def list_suppliers():
    """Geef alle leveranciers terug."""
    not_implemented()


@router.get("/{supplier_id}", summary="Leverancier ophalen")
def get_supplier(supplier_id: int):
    """Geef één leverancier terug op basis van id."""
    not_implemented()


@router.get("/{supplier_id}/items", summary="Items van leverancier")
def list_supplier_items(supplier_id: int):
    """Geef alle items terug die door deze leverancier geleverd worden."""
    not_implemented()


@router.post("", status_code=status.HTTP_201_CREATED, summary="Leverancier aanmaken")
def create_supplier():
    """Maak een nieuwe leverancier aan."""
    not_implemented()


@router.put("/{supplier_id}", summary="Leverancier bijwerken")
def update_supplier(supplier_id: int):
    """Werk een bestaande leverancier bij."""
    not_implemented()


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Leverancier verwijderen")
def delete_supplier(supplier_id: int):
    """Verwijder een leverancier."""
    not_implemented()
