import httpx
from ..config import settings

async def weather_context(latitude: float, longitude: float, language: str = "en"):
    if not settings.google_weather_api_key:
        return {"available": False, "reason": "Google Weather API is not configured"}
    url = "https://weather.googleapis.com/v1/currentConditions:lookup"
    params = {
        "key": settings.google_weather_api_key,
        "location.latitude": latitude,
        "location.longitude": longitude,
        "unitsSystem": "METRIC",
        "languageCode": language,
    }
    async with httpx.AsyncClient(timeout=settings.weather_timeout_seconds) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return {"available": True, "source": "Google Weather API", "data": response.json()}
