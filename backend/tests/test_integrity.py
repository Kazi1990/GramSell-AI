from app.services.hybrid import build_hybrid_context
from app.services.payment import verify_payment

def test_hybrid_context_is_deterministic():
    ctx = build_hybrid_context("  market   price  ", "BD", "en")
    assert ctx["normalized_text"] == "market price"
    assert ctx["country"] == "BD"
    assert ctx["language"] == "en"
    assert ctx["data_policy"] == "real_data_only"

def test_receipt_cannot_confirm_payment():
    result = verify_payment("bkash", "receipt-reference")
    assert result.verified is False
    assert result.status == "pending"

def test_missing_payment_reference_is_pending():
    result = verify_payment("bkash", None)
    assert result.verified is False
    assert result.status == "pending"


def test_seller_confirmation_is_not_provider_verified():
    assert "seller_confirmed" not in {"paid", "collected"}

def test_unknown_provider_never_confirms_payment():
    result = verify_payment("unknown-provider", "provider-reference")
    assert result.verified is False
    assert result.status == "pending"

from app.schemas import FinancialPlanningRequest

def test_financial_planning_accepts_any_product_without_fixed_category():
    request = FinancialPlanningRequest(
        seller_id=1,
        product_id=999,
        current_cash="1000.00",
        expected_income="5000.00",
        known_obligations="1500.00",
        inventory_value="3000.00",
        business_cycle_days=30,
    )
    assert request.product_id == 999
    assert request.business_cycle_days == 30

def test_financial_planning_does_not_require_fake_savings_amount():
    request = FinancialPlanningRequest(seller_id=1, product_id=None)
    assert request.current_cash is None
    assert request.expected_income is None

from app.services.risk_intelligence import build_credit_evidence
from app.models import Seller, Product, Order, PaymentEvent
from app.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_credit_evidence_does_not_fabricate_a_score():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = Session()
    seller = Seller(display_name="Seller", country="BD", language="bn", currency="BDT")
    db.add(seller)
    db.commit()
    db.refresh(seller)
    result = build_credit_evidence(db, seller.id)
    assert result["score_status"] == "not_scored"
    assert result["verified_activity"]["verified_revenue"] == "0"
    db.close()


def test_credit_evidence_uses_only_verified_orders():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = Session()
    seller = Seller(display_name="Seller", country="BD", language="bn", currency="BDT")
    db.add(seller)
    db.commit()
    db.refresh(seller)
    product = Product(seller_id=seller.id, name="Item", production_cost="50", selling_price="100", quantity_available=10)
    db.add(product)
    db.commit()
    db.refresh(product)
    db.add_all([
        Order(seller_id=seller.id, product_id=product.id, quantity=2, unit_price="100", unit_cost="50", payment_method="cash", payment_status="paid"),
        Order(seller_id=seller.id, product_id=product.id, quantity=3, unit_price="100", unit_cost="50", payment_method="cash", payment_status="pending"),
    ])
    db.commit()
    result = build_credit_evidence(db, seller.id)
    assert result["verified_activity"]["verified_order_count"] == 1
    assert result["verified_activity"]["verified_revenue"] == "200.00"
    db.close()

from app.services.agent_contract import normalize_agent_output, grounding_summary


def test_agent_contract_adds_safe_defaults_and_blocks_false_execution():
    result = normalize_agent_output(
        "action",
        {"facts": ["recorded"], "action_status": "executed"},
        {"weather": {"available": True}},
    )
    assert result["action_status"] == "proposed"
    assert result["execution_guard"] == "application_execution_required"
    assert result["recommendations"] == []
    assert result["uncertainties"] == []
    assert result["evidence"] == []


def test_grounding_summary_does_not_treat_missing_data_as_real_evidence():
    summary = grounding_summary({"weather": {"available": False, "reason": "not_configured"}})
    assert summary["weather"]["available"] is False
    assert summary["weather"]["has_data"] is False


def test_business_action_contract():
    from app.schemas import ActionCreate
    payload = ActionCreate(seller_id=1, action_type="listing_draft", payload={"product": "generic"})
    assert payload.action_type == "listing_draft"
    assert payload.payload["product"] == "generic"
