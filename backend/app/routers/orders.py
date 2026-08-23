from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from ..database import get_db
from ..models import Order, Product, Seller, PaymentEvent
from ..schemas import OrderCreate, PaymentVerificationRequest
from ..services.payment import verify_payment
from ..authz import require_seller_access

router = APIRouter()
VALID_METHODS = {"full_payment", "advance_payment", "cash_on_delivery"}
REALIZED_PAYMENT_STATES = {"paid", "collected"}

@router.post("")
def create_order(payload: OrderCreate, request: Request, db: Session = Depends(get_db)):
    require_seller_access(request, payload.seller_id)
    if payload.payment_method not in VALID_METHODS:
        raise HTTPException(400, "Unsupported payment method")
    seller = db.execute(select(Seller).where(Seller.id == payload.seller_id).with_for_update()).scalar_one_or_none()
    product = db.execute(select(Product).where(Product.id == payload.product_id).with_for_update()).scalar_one_or_none()
    if not seller or not product or product.seller_id != seller.id:
        raise HTTPException(404, "Seller or product not found")
    if product.selling_price is None:
        raise HTTPException(400, "Product selling price is not configured")
    if payload.quantity > product.quantity_available:
        raise HTTPException(409, "Insufficient inventory")
    order = Order(
        seller_id=seller.id,
        product_id=product.id,
        quantity=payload.quantity,
        unit_price=product.selling_price,
        unit_cost=product.production_cost,
        payment_method=payload.payment_method,
        payment_status="pending",
        customer_name=payload.customer_name,
        customer_contact=payload.customer_contact,
        delivery_address=payload.delivery_address,
    )
    product.quantity_available -= payload.quantity
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.get("/seller/{seller_id}/summary")
def seller_summary(seller_id: int, request: Request, db: Session = Depends(get_db)):
    require_seller_access(request, seller_id)
    if not db.get(Seller, seller_id):
        raise HTTPException(404, "Seller not found")
    orders = db.query(Order).filter(Order.seller_id == seller_id).all()
    realized = [o for o in orders if o.payment_status in REALIZED_PAYMENT_STATES]
    revenue = sum((o.unit_price * o.quantity for o in realized), Decimal("0"))
    cost = sum((o.unit_cost * o.quantity for o in realized), Decimal("0"))
    profit = revenue - cost
    margin = profit / revenue * 100 if revenue else Decimal("0")
    return {"seller_id": seller_id, "recorded_orders": len(orders), "verified_revenue": str(revenue), "recorded_cost": str(cost), "recorded_profit": str(profit), "realized_margin_percent": str(margin)}

@router.post("/{order_id}/payment/verify")
def verify_order_payment(order_id: int, payload: PaymentVerificationRequest, request: Request, db: Session = Depends(get_db)):
    order = db.execute(select(Order).where(Order.id == order_id).with_for_update()).scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Order not found")
    require_seller_access(request, order.seller_id)
    if order.payment_status == "cancelled":
        raise HTTPException(409, "Cancelled orders cannot be paid")
    seller = db.get(Seller, order.seller_id)
    if not seller:
        raise HTTPException(404, "Seller not found")
    if not payload.provider_reference:
        raise HTTPException(400, "An authoritative provider reference is required for provider verification")
    existing = db.execute(
        select(PaymentEvent).where(
            PaymentEvent.provider == (seller.payment_provider or "unknown"),
            PaymentEvent.provider_reference == payload.provider_reference,
        )
    ).scalar_one_or_none()
    if existing:
        return {
            "order_id": order.id,
            "payment_status": order.payment_status,
            "verification": {
                "status": existing.status,
                "verified": existing.verified,
                "reason": existing.reason,
                "provider_reference": existing.provider_reference,
            },
            "receipt_present": payload.receipt_present,
            "idempotent": True,
        }
    result = verify_payment(seller.payment_provider, payload.provider_reference)
    if result.verified:
        order.payment_status = "paid"
    event = PaymentEvent(
        order_id=order.id,
        provider=seller.payment_provider or "unknown",
        provider_reference=payload.provider_reference,
        status=result.status,
        verified=result.verified,
        reason=result.reason,
    )
    db.add(event)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.execute(
            select(PaymentEvent).where(
                PaymentEvent.provider == (seller.payment_provider or "unknown"),
                PaymentEvent.provider_reference == payload.provider_reference,
            )
        ).scalar_one_or_none()
        if existing:
            return {
                "order_id": order.id,
                "payment_status": order.payment_status,
                "verification": {
                    "status": existing.status,
                    "verified": existing.verified,
                    "reason": existing.reason,
                    "provider_reference": existing.provider_reference,
                },
                "receipt_present": payload.receipt_present,
                "idempotent": True,
            }
        raise
    db.refresh(order)
    return {"order_id": order.id, "payment_status": order.payment_status, "verification": {"status": result.status, "verified": result.verified, "reason": result.reason, "provider_reference": result.provider_reference}, "receipt_present": payload.receipt_present, "idempotent": False}

@router.post("/{order_id}/payment/seller-confirm")
def seller_confirm_payment(order_id: int, request: Request, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    require_seller_access(request, order.seller_id)
    if order.payment_status in REALIZED_PAYMENT_STATES:
        return {"order_id": order.id, "payment_status": order.payment_status, "verified": True, "source": "authoritative_provider"}
    if order.payment_status == "cancelled":
        raise HTTPException(409, "Cancelled orders cannot be confirmed")
    order.payment_status = "seller_confirmed"
    db.commit()
    db.refresh(order)
    return {"order_id": order.id, "payment_status": order.payment_status, "verified": False, "source": "seller_confirmation"}

@router.patch("/{order_id}/payment")
def update_payment(order_id: int, status: str, request: Request, db: Session = Depends(get_db)):
    if status in REALIZED_PAYMENT_STATES:
        raise HTTPException(403, "Paid status requires authoritative payment-provider verification")
    if status not in {"pending", "failed", "cancelled"}:
        raise HTTPException(400, "Invalid payment status")
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    require_seller_access(request, order.seller_id)
    if order.payment_status in REALIZED_PAYMENT_STATES and status != order.payment_status:
        raise HTTPException(409, "Confirmed payment state cannot be changed by this endpoint")
    if order.payment_status == "cancelled" and status != "cancelled":
        raise HTTPException(409, "Cancelled orders cannot change payment state")
    if status == "cancelled" and order.payment_status != "cancelled":
        product = db.get(Product, order.product_id)
        if product:
            product.quantity_available += order.quantity
    order.payment_status = status
    db.commit()
    db.refresh(order)
    return order
