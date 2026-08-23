import re

COUNTRY_PROFILES = {
    "BD": {"languages": {"bn", "en"}, "currency": "BDT"},
    "IN": {"languages": {"hi", "en"}, "currency": "INR"},
    "ZA": {"languages": {"en", "af", "zu", "xh", "st", "tn", "ts", "ss", "ve", "nr", "nso"}, "currency": "ZAR"},
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def detect_language(text: str, country: str, requested: str | None) -> str:
    profile = COUNTRY_PROFILES.get(country)
    if not profile:
        raise ValueError("Unsupported country")
    if requested and requested in profile["languages"]:
        return requested
    if country == "BD" and re.search(r"[\u0980-\u09FF]", text):
        return "bn"
    if country == "IN" and re.search(r"[\u0900-\u097F]", text):
        return "hi"
    return "en"


def detect_intent(text: str) -> str:
    value = text.lower()
    rules = {
        "pricing": ("price", "cost", "sell", "selling", "market"),
        "sales": ("sale", "sold", "sales", "revenue"),
        "product_listing": ("listing", "post", "facebook", "whatsapp", "product"),
        "payment": ("payment", "paid", "receipt", "transaction"),
        "weather": ("weather", "rain", "storm", "forecast"),
        "savings": ("save", "saving", "savings"),
    }
    for intent, terms in rules.items():
        if any(term in value for term in terms):
            return intent
    return "general_business"


def build_hybrid_context(text: str, country: str, language: str | None) -> dict:
    normalized = normalize_text(text)
    if not normalized:
        raise ValueError("Message cannot be empty")
    resolved = detect_language(normalized, country, language)
    profile = COUNTRY_PROFILES[country]
    return {
        "normalized_text": normalized,
        "country": country,
        "language": resolved,
        "intent": detect_intent(normalized),
        "processing": "deterministic_validation_then_vertex_ai",
        "data_policy": "real_data_only",
        "currency": profile["currency"],
    }
