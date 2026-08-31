import json
from google import genai
from google.genai import types
from ..config import settings

class LLMEngine:
    def __init__(self):
        if not settings.google_genai_use_vertexai:
            raise RuntimeError("GOOGLE_GENAI_USE_VERTEXAI must be true for GramSell AI.")
        if not settings.google_cloud_project:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT is required.")
        self.client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
            http_options=types.HttpOptions(api_version="v1"),
        )

    def run(self, model: str, system_instruction: str, payload: dict, use_maps_grounding: bool = False):
        tools = [types.Tool(google_maps=types.GoogleMaps())] if use_maps_grounding else None
        response = self.client.models.generate_content(
            model=model,
            contents=json.dumps(payload, ensure_ascii=False, default=str),
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.1,
                max_output_tokens=1200,
                tools=tools,
            ),
        )
        return self._parse(response)

    def run_grounded(self, model: str, system_instruction: str, payload: dict, latitude: float | None = None, longitude: float | None = None, language_code: str = "en_US"):
        tools = []
        if settings.google_search_grounding:
            tools.append(types.Tool(google_search=types.GoogleSearch()))
        if settings.google_maps_grounding:
            tools.append(types.Tool(google_maps=types.GoogleMaps()))
        tool_config = None
        if latitude is not None and longitude is not None and settings.google_maps_grounding:
            tool_config = types.ToolConfig(
                retrieval_config=types.RetrievalConfig(
                    lat_lng=types.LatLng(latitude=latitude, longitude=longitude),
                    language_code=language_code,
                )
            )
        response = self.client.models.generate_content(
            model=model,
            contents=json.dumps(payload, ensure_ascii=False, default=str),
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.1,
                max_output_tokens=1200,
                tools=tools or None,
                tool_config=tool_config,
            ),
        )
        return self._parse(response)

    def run_multimodal(self, model: str, system_instruction: str, text: str, image_bytes: bytes, mime_type: str):
        part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=[text, part],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.1,
                    max_output_tokens=900,
                ),
            )
            return self._parse(response)
        except Exception:
            if model == settings.gemini_fallback_model:
                raise
            response = self.client.models.generate_content(
                model=settings.gemini_fallback_model,
                contents=[text, part],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.1,
                    max_output_tokens=900,
                ),
            )
            return self._parse(response)

    @staticmethod
    def _parse(response):
        if not response.text:
            raise RuntimeError("Vertex AI returned an empty response.")
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Vertex AI returned invalid JSON.") from exc
        if not isinstance(result, dict):
            raise RuntimeError("Vertex AI returned an invalid response object.")
        return result

_engine = None

def get_engine() -> LLMEngine:
    global _engine
    if _engine is None:
        _engine = LLMEngine()
    return _engine
