from dataclasses import dataclass

@dataclass(frozen=True)
class PaymentVerification:
    status: str
    verified: bool
    reason: str
    provider_reference: str | None = None

class PaymentProviderAdapter:
    provider_name = "unconfigured"

    def verify(self, provider_reference: str) -> PaymentVerification:
        return PaymentVerification(
            "pending",
            False,
            "Official payment-provider verification is not configured.",
            provider_reference,
        )

class BkashAdapter(PaymentProviderAdapter):
    provider_name = "bkash"

class NagadAdapter(PaymentProviderAdapter):
    provider_name = "nagad"

class UpiAdapter(PaymentProviderAdapter):
    provider_name = "upi"

ADAPTERS = {
    "bkash": BkashAdapter(),
    "nagad": NagadAdapter(),
    "upi": UpiAdapter(),
}

def verify_payment(provider: str | None, provider_reference: str | None) -> PaymentVerification:
    if not provider_reference:
        return PaymentVerification("pending", False, "No authoritative provider reference was supplied.")
    normalized_provider = (provider or "").strip().lower()
    adapter = ADAPTERS.get(normalized_provider)
    if adapter is None:
        return PaymentVerification(
            "pending",
            False,
            "The seller payment provider has no configured official verification adapter.",
            provider_reference,
        )
    return adapter.verify(provider_reference)
