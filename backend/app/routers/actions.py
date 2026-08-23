import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..authz import require_seller_access
from ..models import BusinessAction, Seller
from ..schemas import ActionCreate

router = APIRouter()

ALLOWED_ACTIONS = {"listing_draft", "reminder", "record_update", "social_publish"}

@router.post("")
def create_action(payload: ActionCreate, request: Request, db: Session = Depends(get_db)):
    require_seller_access(request, payload.seller_id)
    if payload.action_type not in ALLOWED_ACTIONS:
        raise HTTPException(400, "Unsupported action type")
    if not db.get(Seller, payload.seller_id):
        raise HTTPException(404, "Seller not found")
    action = BusinessAction(
        seller_id=payload.seller_id,
        action_type=payload.action_type,
        payload=json.dumps(payload.payload, ensure_ascii=False),
        status="proposed",
        created_at=datetime.utcnow(),
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return {
        "id": action.id,
        "seller_id": action.seller_id,
        "action_type": action.action_type,
        "status": action.status,
        "payload": payload.payload,
    }

@router.post("/{action_id}/execute")
def execute_action(action_id: int, db: Session = Depends(get_db)):
    action = db.execute(select(BusinessAction).where(BusinessAction.id == action_id).with_for_update()).scalar_one_or_none()
    if not action:
        raise HTTPException(404, "Action not found")
    if action.status == "executed":
        return {"id": action.id, "status": "executed", "idempotent": True}
    if action.status != "proposed":
        raise HTTPException(409, "Action is not executable")
    if action.action_type == "social_publish":
        payload = json.loads(action.payload)
        seller = db.get(Seller, action.seller_id)
        if not seller or not seller.social_provider:
            raise HTTPException(409, "No social account is connected")
        result = publish(seller.social_provider, payload)
        if result["status"] != "connector_pending":
            raise HTTPException(503, result["reason"])
        raise HTTPException(503, "Social provider connector is not ready")
    action.status = "executed"
    action.executed_at = datetime.utcnow()
    db.commit()
    db.refresh(action)
    return {"id": action.id, "status": "executed", "executed_at": action.executed_at.isoformat(), "idempotent": False}

@router.get("/seller/{seller_id}")
def seller_actions(seller_id: int, request: Request, db: Session = Depends(get_db)):
    require_seller_access(request, seller_id)
    if not db.get(Seller, seller_id):
        raise HTTPException(404, "Seller not found")
    actions = db.execute(select(BusinessAction).where(BusinessAction.seller_id == seller_id).order_by(BusinessAction.id.desc()).limit(50)).scalars().all()
    return [{
        "id": item.id,
        "action_type": item.action_type,
        "status": item.status,
        "payload": json.loads(item.payload),
        "created_at": item.created_at.isoformat(),
        "executed_at": item.executed_at.isoformat() if item.executed_at else None,
    } for item in actions]
