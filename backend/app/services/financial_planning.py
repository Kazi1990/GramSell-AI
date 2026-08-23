from sqlalchemy.orm import Session
from .llm import get_engine
from .context import seller_context
from .maps_mcp import maps_grounding
from ..config import settings

FINANCIAL_PLANNING_SYSTEM = """You are the GramSell Financial Planning Agent. Use only the supplied seller inputs, business records, and grounded external evidence. Never invent prices, income, expenses, forecasts, savings amounts, credit scores, or risk facts. A reserve recommendation is a recommendation, not a fact. The seller retains final control. If evidence is insufficient, return insufficient_evidence=true and do not manufacture a numeric recommendation. Distinguish observed data, calculated values, and recommendations. Consider the product generically; never assume a fixed product category. Return JSON with keys: summary, observed_data, risk_factors, reserve_recommendation, confidence, insufficient_evidence, evidence_attribution."""

async def build_financial_plan(db: Session, seller_id: int, product_id: int | None, snapshot: dict):
    context = seller_context(db, seller_id)
    if context is None:
        raise ValueError("Seller not found")
    seller = context["seller"]
    latitude = seller.get("latitude")
    longitude = seller.get("longitude")
    external = {}
    if latitude is not None and longitude is not None:
        external["weather"] = await maps_grounding.lookup_weather(float(latitude), float(longitude))
    evidence = {
        "seller": seller,
        "business_context": context,
        "product_id": product_id,
        "financial_snapshot": snapshot,
        "external_context": external,
    }
    return get_engine().run(
        settings.vertex_decision_model if settings.google_genai_use_vertexai else settings.gemini_model,
        FINANCIAL_PLANNING_SYSTEM,
        {"evidence": evidence},
    )
