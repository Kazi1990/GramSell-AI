from fastapi import APIRouter, File, HTTPException, UploadFile, Request
from ..services.llm import get_engine
from ..config import settings
from ..services.speech import transcribe_audio
from ..authz import require_seller_access

router = APIRouter()

@router.post("/speech/transcribe")
async def speech_transcribe(request: Request, language: str | None = None, seller_id: int | None = None, audio: UploadFile = File(...)):
    if seller_id is not None:
        require_seller_access(request, seller_id)
    if audio.content_type not in {"audio/wav", "audio/x-wav", "audio/webm", "audio/ogg", "audio/mp4", "audio/mpeg"}:
        raise HTTPException(415, "Unsupported audio type")
    content = await audio.read()
    if len(content) > 8 * 1024 * 1024:
        raise HTTPException(413, "Audio file too large")
    language_codes = [language] if language and language != "auto" else ["auto"]
    try:
        transcript, detected_language = transcribe_audio(content, language_codes)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(502, f"Google Speech-to-Text request failed: {exc}")
    return {"language": detected_language or language or "auto", "transcript": transcript}

@router.post("/image/analyze")
async def image_analyze(request: Request, language: str = "en", instruction: str = "Describe only observable product attributes.", seller_id: int | None = None, image: UploadFile = File(...)):
    if seller_id is not None:
        require_seller_access(request, seller_id)
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
        result = get_engine().run_multimodal(settings.gemini_model, "Return strict JSON.", prompt, content, image.content_type)
    except Exception as exc:
        raise HTTPException(502, f"Vertex AI image analysis failed: {exc}")
    return {"language": language, "analysis": result}
