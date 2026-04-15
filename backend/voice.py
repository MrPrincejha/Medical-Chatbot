"""Text-to-speech synthesis using gTTS."""
from __future__ import annotations

from gtts import gTTS


def text_to_speech(input_text: str, output_filepath: str) -> str:
    """Convert *input_text* to speech and save it as an MP3 at *output_filepath*."""
    tts = gTTS(text=input_text, lang="en", slow=False)
    tts.save(output_filepath)
    return output_filepath
