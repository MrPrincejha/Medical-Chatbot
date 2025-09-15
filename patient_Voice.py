import logging
import speech_recognition as sr
from pydub import AudioSegment
from io import BytesIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def record_audio(file_path, timeout=30, phrase_time_limit=10):
    recognizer = sr.Recognizer()
    
    try:
        with sr.Microphone() as source:
            logging.info("Adjusting for ambient noise (1 second)...")
            recognizer.adjust_for_ambient_noise(source, duration=1)

            logging.info("Listening for speech (you have %d seconds to start)...", timeout)
            audio_data = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            logging.info("Speech detected and recorded.")

            
            wav_data = audio_data.get_wav_data()
            audio_segment = AudioSegment.from_wav(BytesIO(wav_data))
            audio_segment.export(file_path, format="mp3", bitrate="128k")
            logging.info(f"Audio saved successfully at: {file_path}")

    except sr.WaitTimeoutError:
        logging.error("Timeout: No speech detected within the timeout period.")
    except sr.UnknownValueError:
        logging.error("Could not understand the audio.")
    except sr.RequestError as e:
        logging.error(f"Speech recognition service error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

audio_file_path = "Patient_voice_test.mp3"
# record_audio(file_path=audio_file_path)
import os
from groq import Groq
stt_Model  = "whisper-large-v3"
def transcribe_groq (GROQ_API_KEY,audio_filepath,stt_Model):
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


    client = Groq(api_key = GROQ_API_KEY)
    audio_file = open(audio_filepath, "rb")

    transcription = client.audio.transcriptions.create(
        model = stt_Model,
        file = audio_file,
        language = "en"
    )
    return transcription.text