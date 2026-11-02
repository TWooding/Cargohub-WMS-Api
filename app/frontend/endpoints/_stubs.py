from fastapi import HTTPException, status


def not_implemented() -> None:
    """Gedeelde 501-respons voor endpoints die nog een skelet zijn."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
