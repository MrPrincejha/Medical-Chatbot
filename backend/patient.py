"""Speech-to-text transcription using the Groq Whisper API."""
from __future__ import annotations

import os

from groq import Groq

STT_MODEL = "whisper-large-v3"


def transcribe_groq(audio_filepath: str, stt_model: str = STT_MODEL) -> str:
    """Transcribe an audio file to text using Groq's Whisper model."""
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    with open(audio_filepath, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model=stt_model,
            file=audio_file,
            language="en",
        )
    return transcription.text
