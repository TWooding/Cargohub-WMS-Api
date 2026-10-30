from fastapi import APIRouter, status

from app.frontend.endpoints._stubs import not_implemented

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.get("", summary="Lijst van transfers")
def list_transfers():
    """Geef alle transfers terug."""
    not_implemented()


@router.get("/{transfer_id}", summary="Transfer ophalen")
def get_transfer(transfer_id: int):
    """Geef één transfer terug op basis van id."""
    not_implemented()


@router.get("/{transfer_id}/items", summary="Items in transfer")
def list_transfer_items(transfer_id: int):
    """Geef de items (met aantallen) van een transfer terug."""
    not_implemented()


@router.post("", status_code=status.HTTP_201_CREATED, summary="Transfer aanmaken")
def create_transfer():
    """Plan een nieuwe transfer tussen twee locaties in."""
    not_implemented()


@router.put("/{transfer_id}", summary="Transfer bijwerken")
def update_transfer(transfer_id: int):
    """Werk een bestaande transfer bij."""
    not_implemented()


@router.put("/{transfer_id}/commit", summary="Transfer verwerken")
def commit_transfer(transfer_id: int):
    """Verwerk de transfer: boek voorraad om van bron- naar doellocatie en zet de status op Processed."""
    not_implemented()


@router.delete("/{transfer_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Transfer verwijderen")
def delete_transfer(transfer_id: int):
    """Verwijder een transfer."""
    not_implemented()
