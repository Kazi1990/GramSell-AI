from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import FinancialPlanningRequest
from ..services.financial_planning import build_financial_plan

router = APIRouter()

@router.post("/plan")
async def financial_plan(payload: FinancialPlanningRequest, db: Session = Depends(get_db)):
    snapshot = payload.model_dump(mode="json", exclude={"seller_id", "product_id"})
    try:
        result = await build_financial_plan(db, payload.seller_id, payload.product_id, snapshot)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    return {"plan": result}
