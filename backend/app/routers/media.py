from fastapi import APIRouter, File, HTTPException, UploadFile
from ..services.llm import get_engine
from ..services.speech import transcribe_audio

router = APIRouter()

LANGUAGE_MAP = {
    "bn": ["bn-BD", "en-US"],
    "hi": ["hi-IN", "en-IN"],
    "en": ["en-US"],
    "af": ["af-ZA", "en-ZA"],
    "zu": ["zu-ZA", "en-ZA"],
    "xh": ["xh-ZA", "en-ZA"],
    "st": ["st-ZA", "en-ZA"],
}

@router.post("/speech/transcribe")
async def speech_transcribe(language: str = "en", audio: UploadFile = File(...)):
    if language not in LANGUAGE_MAP:
        raise HTTPException(400, "Unsupported speech language")
    if audio.content_type not in {"audio/wav", "audio/x-wav", "audio/webm", "audio/ogg", "audio/mp4", "audio/mpeg"}:
        raise HTTPException(415, "Unsupported audio type")
    content = await audio.read()
    if len(content) > 8 * 1024 * 1024:
        raise HTTPException(413, "Audio file too large")
    try:
        transcript = transcribe_audio(content, LANGUAGE_MAP[language])
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(502, f"Google Speech-to-Text request failed: {exc}")
    return {"language": language, "transcript": transcript}

@router.post("/image/analyze")
async def image_analyze(language: str = "en", instruction: str = "Describe only observable product attributes.", image: UploadFile = File(...)):
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if image.content_type not in allowed:
        raise HTTPException(415, "Unsupported image type")
    content = await image.read()
    if len(content) > 8 * 1024 * 1024:
        raise HTTPException(413, "Image file too large")
    prompt = (
        "Analyze the supplied product image for GramSell AI. "
        "Return only observable attributes. Do not invent brand, price, quantity, ownership, "
        "condition, authenticity, customer, transaction, payment, or market facts. "
        f"Respond in {language}. Instruction: {instruction}"
    )
    try:
        result = get_engine().run_multimodal("gemini-3.1-flash-lite", "Return strict JSON.", prompt, content, image.content_type)
    except Exception as exc:
        raise HTTPException(502, f"Vertex AI image analysis failed: {exc}")
    return {"language": language, "analysis": result}
