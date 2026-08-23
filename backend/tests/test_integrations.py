import os
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("SOCIAL_PUBLISH_PROVIDERS", "")

from app.services.social import status_for_seller, publish


def test_unconfigured_social_provider_is_not_published():
    status = status_for_seller("facebook")
    assert status.connected is False
    result = publish("facebook", {"text": "draft"})
    assert result["published"] is False
    assert result["status"] == "not_configured"


def test_configured_provider_still_requires_real_adapter():
    result = publish(None, {"text": "draft"})
    assert result["published"] is False
