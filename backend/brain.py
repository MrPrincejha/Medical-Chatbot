"""Image analysis using the Groq vision LLM."""
from __future__ import annotations

import base64
import mimetypes
import os

from groq import Groq


def encode_img(img_path: str) -> str:
    """Base64-encode an image file for the Groq API."""
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def _media_type(img_path: str) -> str:
    mime, _ = mimetypes.guess_type(img_path)
    return mime or "image/jpeg"


def analyze_img(query: str, encoded_img: str, model: str, img_path: str | None = None) -> str:
    """Send an image + text query to the Groq vision model and return the response."""
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    media_type = _media_type(img_path) if img_path else "image/jpeg"

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{media_type};base64,{encoded_img}"},
                },
            ],
        }
    ]
    chat_completion = client.chat.completions.create(messages=messages, model=model)
    return chat_completion.choices[0].message.content
