# 🩺 Medical Chatbot – Full-Stack AI Doctor Assistant

An AI-powered medical consultation chatbot that accepts a **voice recording** and an optional **medical image**, transcribes the query, analyses the image with a vision LLM, and speaks back a doctor-style response – all through a modern web interface.

> ⚠️ **Disclaimer:** This project is for *educational purposes only*. It is not a substitute for professional medical advice. Always consult a qualified healthcare provider.

---

## Architecture

```
Medical-Chatbot/
├── backend/                  # FastAPI Python backend
│   ├── main.py               # API app: /api/health, /api/analyze + static file serving
│   ├── brain.py              # Vision LLM analysis (Groq)
│   ├── patient.py            # Speech-to-text (Groq Whisper)
│   ├── voice.py              # Text-to-speech (gTTS)
│   └── requirements.txt
│
├── frontend/                 # Vanilla HTML/CSS/JS frontend
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── .env                      # Environment variables (not committed)
├── .env.example              # Example env file
└── Pipfile                   # Legacy Gradio prototype dependencies
```

### Data flow

```
Browser
  │
  │  POST /api/analyze  (multipart: audio + optional image)
  ▼
FastAPI (backend/main.py)
  ├─ patient.py  ──► Groq Whisper  ──► transcription text
  ├─ brain.py    ──► Groq Vision LLM ─► doctor response text
  └─ voice.py    ──► gTTS           ──► MP3 audio (base64)
  │
  │  JSON { transcription, doctor_response, audio_base64 }
  ▼
Browser – display text + play audio
```

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| [Groq API key](https://console.groq.com) | – |
| `ffmpeg` (for audio conversion, optional) | any |

---

## Setup & Installation

### 1. Clone and enter the repository

```bash
git clone https://github.com/MrPrincejha/Medical-Chatbot.git
cd Medical-Chatbot
```

### 2. Configure your API key

```bash
cp .env.example .env
# Edit .env and set your GROQ_API_KEY
```

### 3. Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

---

## Running the application

From the **`backend/`** directory:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then open **[http://localhost:8000](http://localhost:8000)** in your browser.

The FastAPI server automatically serves the `frontend/` directory at `/`, so the full UI is available at the root URL.

---

## API Reference

### `GET /api/health`

Liveness check.

**Response**
```json
{ "status": "ok", "message": "Medical Chatbot API is running" }
```

---

### `POST /api/analyze`

Accept patient audio and an optional medical image. Returns transcription, doctor response, and a base64-encoded MP3.

**Request** – `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `audio` | file | ✅ | Patient voice recording (webm, ogg, mp4, mp3, wav) |
| `image` | file | ❌ | Medical image for visual analysis (jpg, png, gif, webp) |

**Response**
```json
{
  "transcription":   "I have a rash on my arm that appeared yesterday.",
  "doctor_response": "With what I see, I think you have contact dermatitis …",
  "audio_base64":    "<base64-encoded MP3>"
}
```

---

## How to Use

1. Click **Start Recording** and describe your symptoms clearly.
2. Click **Stop Recording** when done.
3. *(Optional)* Upload a photo of the affected area via the image upload area.
4. Click **Analyze** and wait a few seconds.
5. Read the doctor's text response and listen to the audio playback.

---

## Technologies Used

| Layer | Technology |
|-------|-----------|
| Backend API | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| Speech-to-Text | [Groq Whisper](https://console.groq.com/docs/speech-text) (`whisper-large-v3`) |
| Vision LLM | [Groq](https://console.groq.com/docs/vision) (`meta-llama/llama-4-scout-17b-16e-instruct`) |
| Text-to-Speech | [gTTS](https://gtts.readthedocs.io/) |
| Frontend | Vanilla HTML5 / CSS3 / JavaScript (MediaRecorder API) |

---

## Legacy Gradio prototype

The original single-file Gradio prototype is preserved in the root directory:

```bash
# Install Gradio prototype dependencies
pipenv install
pipenv run python voicebot_gradio.py
```
