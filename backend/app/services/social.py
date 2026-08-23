from dataclasses import dataclass
from ..config import settings


@dataclass(frozen=True)
class SocialStatus:
    provider: str | None
    connected: bool
    publish_ready: bool
    reason: str


def status_for_seller(provider: str | None) -> SocialStatus:
    if not provider:
        return SocialStatus(None, False, False, "No social account connected")
    provider_key = provider.strip().lower()
    configured = provider_key in {item.strip().lower() for item in settings.social_publish_providers.split(",") if item.strip()}
    if not configured:
        return SocialStatus(provider_key, False, False, "Provider connector is not configured")
    return SocialStatus(provider_key, True, True, "Provider connector is configured")


def publish(provider: str | None, payload: dict) -> dict:
    status = status_for_seller(provider)
    if not status.publish_ready:
        return {
            "published": False,
            "status": "not_configured",
            "provider": status.provider,
            "reason": status.reason,
        }
    return {
        "published": False,
        "status": "connector_pending",
        "provider": status.provider,
        "reason": "Provider adapter is not implemented in this build",
    }
