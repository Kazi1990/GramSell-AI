from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..authz import require_seller_access
from ..models import Seller
from ..services.social import status_for_seller
from ..config import settings

router = APIRouter()


@router.get("/seller/{seller_id}")
def integration_status(seller_id: int, request: Request, db: Session = Depends(get_db)):
    require_seller_access(request, seller_id)
    seller = db.get(Seller, seller_id)
    if not seller:
        raise HTTPException(404, "Seller not found")
    social = status_for_seller(seller.social_provider)
    return {
        "seller_id": seller_id,
        "social": {
            "connected": social.connected,
            "publish_ready": social.publish_ready,
            "provider": social.provider,
            "reason": social.reason,
        },
        "maps_grounding": bool(settings.maps_mcp_url),
        "vertex_ai": bool(settings.google_genai_use_vertexai),
        "payment_provider_configured": bool(seller.payment_provider),
    }
