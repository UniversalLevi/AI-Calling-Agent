from typing import Optional

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from .config import SAMPLE_RATE, CHANNELS, RECORD_SECONDS, LANGUAGE, WHISPER_MODEL_SIZE, DEVICE_INDEX_IN


class STTEngine:
    def __init__(self) -> None:
        self.model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")

    def record_audio(self) -> np.ndarray:
        duration = RECORD_SECONDS
        device = DEVICE_INDEX_IN
        
        try:
            audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32", device=device)
            sd.wait()
            return audio.flatten()
        except Exception as e:
            print(f"Error with device {device}, trying default device...")
            try:
                audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32", device=None)
                sd.wait()
                return audio.flatten()
            except Exception as e2:
                print(f"Audio recording failed: {e2}")
                print("Try running: python -m src.tools.list_devices")
                print("Then set DEVICE_INDEX_IN in your .env file")
                raise

    def transcribe(self, audio: np.ndarray) -> str:
        segments, _ = self.model.transcribe(audio, language=LANGUAGE, vad_filter=True)
        text_parts = [seg.text for seg in segments]
        return " ".join(part.strip() for part in text_parts).strip()


def capture_and_transcribe() -> Optional[str]:
    stt = STTEngine()
    audio = stt.record_audio()
    text = stt.transcribe(audio)
    return text if text else None


