from sqlalchemy.orm import Session
from ..models import Seller, Product, Order
from .memory import load_memory

def seller_context(db: Session, seller_id: int):
    seller = db.get(Seller, seller_id)
    if not seller:
        return None
    products = db.query(Product).filter(Product.seller_id == seller_id).all()
    orders = db.query(Order).filter(Order.seller_id == seller_id).order_by(Order.created_at.desc()).limit(50).all()
    return {
        "seller": {
            "id": seller.id,
            "display_name": seller.display_name,
            "country": seller.country,
            "language": seller.language,
            "currency": seller.currency,
            "payment_provider": seller.payment_provider,
            "payment_destination": seller.payment_destination,
            "latitude": float(seller.latitude) if seller.latitude is not None else None,
            "longitude": float(seller.longitude) if seller.longitude is not None else None
        },
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "production_cost": str(p.production_cost),
                "selling_price": str(p.selling_price) if p.selling_price is not None else None,
                "margin_percent": str(p.margin_percent) if p.margin_percent is not None else None,
                "quantity_available": p.quantity_available
            } for p in products
        ],
        "recent_orders": [
            {
                "id": o.id,
                "product_id": o.product_id,
                "quantity": o.quantity,
                "unit_price": str(o.unit_price),
                "unit_cost": str(o.unit_cost),
                "payment_method": o.payment_method,
                "payment_status": o.payment_status
            } for o in orders
        ],
        "memory": load_memory(db, seller_id)
    }
