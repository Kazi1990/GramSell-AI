from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Seller
from ..schemas import SellerCreate

router = APIRouter()

@router.post("")
def create_seller(payload: SellerCreate, request: Request, db: Session = Depends(get_db)):
    raise HTTPException(status_code=410, detail="Use /api/auth/register to create a seller account")
    seller = Seller(**payload.model_dump())
    db.add(seller)
    db.commit()
    db.refresh(seller)
    return seller
