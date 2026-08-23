from fastapi import HTTPException, Request


def authenticated_seller_id(request: Request) -> int | None:
    value = getattr(request.state, "seller_id", None)
    return int(value) if value is not None else None


def require_seller_access(request: Request, seller_id: int) -> None:
    current = authenticated_seller_id(request)
    if current is not None and current != seller_id:
        raise HTTPException(status_code=403, detail="Seller access denied")
