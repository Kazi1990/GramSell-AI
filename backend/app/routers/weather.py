from fastapi import APIRouter, HTTPException
from ..services.google_context import weather_context

router = APIRouter()

@router.get("")
async def get_weather(latitude: float, longitude: float, language: str = "en"):
    try:
        return await weather_context(latitude, longitude, language)
    except Exception as exc:
        raise HTTPException(502, f"Google Weather API request failed: {exc}")
