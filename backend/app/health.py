from .config import settings
from .database import database_ready

def configuration_status() -> dict:
    return {
        "environment": settings.app_env,
        "vertex_ai_enabled": settings.google_genai_use_vertexai,
        "google_cloud_project_configured": bool(settings.google_cloud_project),
        "database_configured": bool(settings.database_url),
        "weather_configured": bool(settings.google_weather_api_key),
        "maps_configured": bool(settings.google_maps_api_key),
        "storage_bucket_configured": bool(settings.google_cloud_storage_bucket),
        "write_auth_required": settings.write_api_key_required,
    }

def readiness_status() -> dict:
    result = configuration_status()
    try:
        result["database_ready"] = database_ready()
    except Exception:
        result["database_ready"] = False
    result["vertex_ready"] = bool(settings.google_cloud_project and settings.google_genai_use_vertexai)
    result["ready"] = bool(result["database_ready"] and result["vertex_ready"])
    return result
