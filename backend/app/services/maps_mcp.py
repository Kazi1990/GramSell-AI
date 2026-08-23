import json
import httpx
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from ..config import settings

class MapsGroundingClient:
    def __init__(self):
        self.url = settings.maps_mcp_url
        self.api_key = settings.google_maps_api_key

    async def _call(self, tool_name: str, arguments: dict):
        if not self.api_key:
            return {"available": False, "reason": "Google Maps API key is not configured"}
        async with httpx.AsyncClient(
            headers={
                "X-Goog-Api-Key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            timeout=httpx.Timeout(settings.maps_timeout_seconds, read=settings.maps_read_timeout_seconds),
            follow_redirects=True,
        ) as http_client:
            transport = streamable_http_client(self.url, http_client=http_client)
            async with Client(transport) as client:
                result = await client.call_tool(tool_name, arguments)
                return {"available": True, "tool": tool_name, "data": self._extract(result)}

    async def search_places(self, text_query: str, location_bias: dict | None = None):
        arguments = {"text_query": text_query}
        if location_bias:
            arguments["location_bias"] = location_bias
        return await self._call("search_places", arguments)

    async def lookup_weather(self, latitude: float, longitude: float):
        return await self._call(
            "lookup_weather",
            {"location": {"lat_lng": {"latitude": latitude, "longitude": longitude}}},
        )

    async def compute_routes(self, origin: dict, destination: dict, travel_mode: str = "DRIVE"):
        return await self._call(
            "compute_routes",
            {"origin": origin, "destination": destination, "travel_mode": travel_mode},
        )

    @staticmethod
    def _extract(result):
        data = []
        for item in getattr(result, "content", []) or []:
            text = getattr(item, "text", None)
            if text is not None:
                try:
                    data.append(json.loads(text))
                except json.JSONDecodeError:
                    data.append(text)
            else:
                raw = getattr(item, "model_dump", None)
                data.append(raw() if callable(raw) else str(item))
        structured = getattr(result, "structuredContent", None)
        if structured is not None:
            return {"content": data, "structured": structured}
        return data

maps_grounding = MapsGroundingClient()
