import asyncio
from typing import AsyncIterator
from sqlalchemy.orm import Session
from .llm import get_engine
from .context import seller_context
from ..config import settings
from .hybrid import build_hybrid_context
from .maps_mcp import maps_grounding
from .agent_contract import normalize_agent_output, grounding_summary

AGENTS = {
    "memory": "You are the Memory Agent for GramSell AI. Select only useful long-term business context. Never invent memory. Never infer a fact as stored history unless it is present in the supplied records. Return JSON with keys facts, recommendations, uncertainties, actions, evidence.",
    "insight": "You are the Insight Agent for GramSell AI. Analyze supplied business records and supplied external context. Separate recorded facts from analysis. Never fabricate market, weather, customer, sales, or financial facts. Treat Maps Grounding Lite output as external evidence and preserve attribution data. Return JSON with keys facts, recommendations, uncertainties, actions, evidence.",
    "guide": "You are the Guide Agent for GramSell AI. Provide practical options for the seller using only supplied facts. Recommendations must be clearly labeled as recommendations, not facts. Return JSON with keys facts, recommendations, uncertainties, actions, evidence.",
    "decision": "You are the Decision Agent for GramSell AI. Select the safest and most useful business action from the outputs and evidence supplied by earlier agents. Never claim a bank approved credit. Never create a transaction or payment confirmation. Return JSON with keys facts, recommendations, uncertainties, actions, evidence.",
    "action": "You are the Action Agent for GramSell AI. Convert an approved decision into an executable business action such as a listing draft, order workflow, reminder, record update, or customer response. Never report an action as completed unless the application has actually executed it. Return JSON with keys facts, recommendations, uncertainties, actions, evidence."
}


def _ground_business_context(message: str, seller: dict, hybrid: dict):
    return _ground_business_context_async(message, seller, hybrid)


async def _ground_business_context_async(message: str, seller: dict, hybrid: dict):
    external = {}
    intent = hybrid["intent"]
    latitude = seller.get("latitude")
    longitude = seller.get("longitude")
    country = seller.get("country")
    location = {"lat_lng": {"latitude": latitude, "longitude": longitude}} if latitude is not None and longitude is not None else None
    if intent in {"pricing", "product_listing", "general_business", "sales"}:
        query = f"markets, shops, and businesses relevant to {message}"
        external["nearby_market"] = await maps_grounding.search_places(query, location)
    if intent in {"weather", "savings", "pricing", "general_business", "sales"} and latitude is not None and longitude is not None:
        external["weather"] = await maps_grounding.lookup_weather(float(latitude), float(longitude))
    return external


async def _run_agent(name: str, evidence: dict, results: dict):
    model = settings.vertex_decision_model if name == "decision" and settings.google_genai_use_vertexai else settings.gemini_model
    payload = {"evidence": evidence, "previous_agent_output": results}
    return await asyncio.to_thread(get_engine().run, model, AGENTS[name], payload)


async def run_pipeline_events(db: Session, seller_id: int, message: str, external_context: dict | None = None) -> AsyncIterator[dict]:
    context = seller_context(db, seller_id)
    if context is None:
        raise ValueError("Seller not found")
    seller = context["seller"]
    country = seller.get("country")
    language = seller.get("language")
    if not country:
        raise ValueError("Seller country is required")

    hybrid = build_hybrid_context(message, country, language)
    yield {"type": "pipeline", "status": "grounding", "intent": hybrid["intent"]}
    grounded = await _ground_business_context_async(message, seller, hybrid)
    evidence = {
        "request": message,
        "hybrid_context": hybrid,
        "business_context": context,
        "external_context": {**(external_context or {}), **grounded},
    }

    results = {}
    for name in ("memory", "insight", "guide", "decision", "action"):
        yield {"type": "agent", "agent": name, "status": "running"}
        results[name] = normalize_agent_output(name, await _run_agent(name, evidence, results), evidence["external_context"])
        yield {"type": "agent", "agent": name, "status": "completed"}

    yield {"type": "complete", "agents": results, "grounding": grounded, "grounding_summary": grounding_summary(grounded), "language": hybrid["language"], "intent": hybrid["intent"], "data_policy": "real_data_only"}


async def run_pipeline(db: Session, seller_id: int, message: str, external_context: dict | None = None):
    final = None
    async for event in run_pipeline_events(db, seller_id, message, external_context):
        if event.get("type") == "complete":
            final = event
    return final["agents"] if final else {}
