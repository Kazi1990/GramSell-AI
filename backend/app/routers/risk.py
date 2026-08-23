from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..authz import require_seller_access
from ..services.risk_intelligence import build_credit_evidence

router = APIRouter()


@router.get("/seller/{seller_id}/credit-evidence")
def credit_evidence(seller_id: int, request: Request, db: Session = Depends(get_db)):
    require_seller_access(request, seller_id)
    try:
        return build_credit_evidence(db, seller_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
