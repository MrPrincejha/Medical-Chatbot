"""FastAPI backend for the Medical Chatbot.

Exposes:
  GET  /api/health   – liveness check
  POST /api/analyze  – accept audio + optional image, return transcription,
                       doctor response, and base64 TTS audio

Static files in ../frontend/ are served at / when present.
"""
from __future__ import annotations

import base64
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

from brain import analyze_img, encode_img  # noqa: E402
from patient import transcribe_groq  # noqa: E402
from voice import text_to_speech  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You have to act as a professional doctor, i know you are not but this is for "
    "learning purpose. What's in this image? Do you find anything wrong with it "
    "medically? If you make a differential, suggest some remedies for them. Do not "
    "add any numbers or special characters in your response. Your response should be "
    "in one long paragraph. Also always answer as if you are answering to a real "
    "person. Do not say 'In the image I see' but say 'With what I see, I think you "
    "have ...'. Do not respond as an AI model in markdown, your answer should mimic "
    "that of an actual doctor not an AI bot. Keep your answer concise (max 2 "
    "sentences). No preamble, start your answer right away please."
)

LLM_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

_AUDIO_EXT: dict[str, str] = {
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/mp4": ".mp4",
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
}

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Medical Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/health")
def health_check():
    """Liveness probe."""
    return {"status": "ok", "message": "Medical Chatbot API is running"}


@app.post("/api/analyze")
async def analyze(
    audio: UploadFile = File(...),
    image: UploadFile = File(None),
):
    """Analyse patient voice + optional medical image.

    Returns
    -------
    JSON with keys:
      - transcription   : patient query as text
      - doctor_response : LLM-generated medical response
      - audio_base64    : base64-encoded MP3 of the doctor's spoken response
    """
    transcription = ""
    doctor_response = ""
    audio_b64 = ""
    temp_files: list[str] = []

    try:
        # ── Save audio to a temp file ───────────────────────────────────────
        content_type = (audio.content_type or "audio/webm").split(";")[0].strip()
        audio_ext = _AUDIO_EXT.get(content_type, ".webm")
        with tempfile.NamedTemporaryFile(delete=False, suffix=audio_ext) as tmp:
            tmp.write(await audio.read())
            audio_path = tmp.name
        temp_files.append(audio_path)

        # ── Save image to a temp file (optional) ────────────────────────────
        image_path: str | None = None
        if image and image.filename:
            img_suffix = Path(image.filename).suffix or ".jpg"
            with tempfile.NamedTemporaryFile(delete=False, suffix=img_suffix) as tmp:
                tmp.write(await image.read())
                image_path = tmp.name
            temp_files.append(image_path)

        # ── Speech → Text ────────────────────────────────────────────────────
        transcription = transcribe_groq(audio_filepath=audio_path)

        # ── Image analysis ───────────────────────────────────────────────────
        if image_path:
            full_query = f"{SYSTEM_PROMPT} Patient says: {transcription}"
            doctor_response = analyze_img(
                query=full_query,
                encoded_img=encode_img(image_path),
                model=LLM_MODEL,
                img_path=image_path,
            )
        else:
            doctor_response = (
                "No image provided. Please upload a medical image so I can "
                "properly assess your condition."
            )

        # ── Text → Speech ────────────────────────────────────────────────────
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            out_path = tmp.name
        temp_files.append(out_path)

        text_to_speech(input_text=doctor_response, output_filepath=out_path)

        with open(out_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    finally:
        for path in temp_files:
            try:
                os.unlink(path)
            except OSError:
                pass

    return JSONResponse(
        {
            "transcription": transcription,
            "doctor_response": doctor_response,
            "audio_base64": audio_b64,
        }
    )


# ---------------------------------------------------------------------------
# Serve frontend static files
# ---------------------------------------------------------------------------

_frontend_dir = Path(__file__).parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="static")
