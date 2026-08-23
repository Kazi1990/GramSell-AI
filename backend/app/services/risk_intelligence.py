from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..models import Order, Product, PaymentEvent, Seller

REALIZED_STATES = {"paid", "collected"}


def build_credit_evidence(db: Session, seller_id: int) -> dict:
    seller = db.get(Seller, seller_id)
    if seller is None:
        raise ValueError("Seller not found")

    orders = db.query(Order).filter(Order.seller_id == seller_id).all()
    products = db.query(Product).filter(Product.seller_id == seller_id).all()
    payment_events = (
        db.query(PaymentEvent)
        .join(Order, PaymentEvent.order_id == Order.id)
        .filter(Order.seller_id == seller_id)
        .all()
    )

    verified_orders = [o for o in orders if o.payment_status in REALIZED_STATES]
    verified_revenue = sum((o.unit_price * o.quantity for o in verified_orders), Decimal("0"))
    verified_cost = sum((o.unit_cost * o.quantity for o in verified_orders), Decimal("0"))
    verified_profit = verified_revenue - verified_cost
    realized_margin = (verified_profit / verified_revenue * Decimal("100")) if verified_revenue else None
    verified_units = sum(o.quantity for o in verified_orders)
    average_verified_order_value = (
        verified_revenue / Decimal(len(verified_orders)) if verified_orders else None
    )
    payment_verified_count = sum(1 for event in payment_events if event.verified)
    payment_event_count = len(payment_events)
    payment_verification_rate = (
        Decimal(payment_verified_count) / Decimal(payment_event_count) * Decimal("100")
        if payment_event_count
        else None
    )
    inventory_value = sum(
        (p.production_cost * p.quantity_available for p in products), Decimal("0")
    )

    completeness = {
        "has_verified_sales": bool(verified_orders),
        "has_payment_verification_history": bool(payment_events),
        "has_inventory_records": bool(products),
        "has_product_costs": all(p.production_cost is not None for p in products) if products else False,
    }

    return {
        "seller_id": seller.id,
        "currency": seller.currency,
        "score_status": "not_scored",
        "score_reason": "No generic credit score is fabricated. A lender or authorized scoring provider must apply its own policy to verified evidence.",
        "verified_activity": {
            "verified_order_count": len(verified_orders),
            "verified_units_sold": verified_units,
            "verified_revenue": str(verified_revenue),
            "verified_cost": str(verified_cost),
            "verified_profit": str(verified_profit),
            "realized_margin_percent": str(realized_margin) if realized_margin is not None else None,
            "average_verified_order_value": str(average_verified_order_value) if average_verified_order_value is not None else None,
        },
        "payment_behavior": {
            "payment_event_count": payment_event_count,
            "verified_payment_event_count": payment_verified_count,
            "verification_rate_percent": str(payment_verification_rate) if payment_verification_rate is not None else None,
        },
        "inventory_exposure": {
            "active_product_count": len(products),
            "recorded_inventory_cost_value": str(inventory_value),
            "units_available": sum(p.quantity_available for p in products),
        },
        "data_completeness": completeness,
        "evidence_policy": {
            "only_authoritative_payment_events_count_as_verified": True,
            "seller_confirmed_payments_are_not_verified": True,
            "unobserved_income_is_not_invented": True,
            "external_market_or_weather_data_is_not_credit_history": True,
        },
    }
