from sqlalchemy.orm import Session
from ..models import BusinessMemory

def load_memory(db: Session, seller_id: int, limit: int = 20):
    rows = (
        db.query(BusinessMemory)
        .filter(BusinessMemory.seller_id == seller_id, BusinessMemory.is_sensitive == False)
        .order_by(BusinessMemory.created_at.desc())
        .limit(limit)
        .all()
    )
    return [{"type": r.memory_type, "content": r.content} for r in rows]
