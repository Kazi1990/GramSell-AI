from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Product, Seller
from ..schemas import ProductCreate
from ..authz import require_seller_access

router = APIRouter()

@router.post("")
def create_product(payload: ProductCreate, request: Request, db: Session = Depends(get_db)):
    require_seller_access(request, payload.seller_id)
    seller = db.get(Seller, payload.seller_id)
    if not seller:
        raise HTTPException(404, "Seller not found")
    data = payload.model_dump()
    if data["selling_price"] is not None:
        data["margin_percent"] = ((data["selling_price"] - data["production_cost"]) / data["selling_price"]) * 100
    product = Product(**data)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return product
