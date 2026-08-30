from google.cloud import speech_v2
from google.cloud.speech_v2.types import cloud_speech
from ..config import settings

def transcribe_audio(audio_bytes: bytes, language_codes: list[str]) -> tuple[str, str]:
    if not settings.google_cloud_project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT is required.")
    if not audio_bytes:
        raise ValueError("Audio content is empty.")
    client = speech_v2.SpeechClient()
    recognizer = f"projects/{settings.google_cloud_project}/locations/global/recognizers/_"
    request = cloud_speech.RecognizeRequest(
        recognizer=recognizer,
        config=cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=language_codes,
            model="chirp_3",
        ),
        content=audio_bytes,
    )
    response = client.recognize(request=request)
    parts = []
    detected_language = ""
    for result in response.results:
        if result.alternatives:
            parts.append(result.alternatives[0].transcript)
        if result.language_code and not detected_language:
            detected_language = result.language_code
    transcript = " ".join(parts).strip()
    if not transcript:
        raise RuntimeError("Speech-to-Text returned no transcript.")
    return transcript, detected_language
