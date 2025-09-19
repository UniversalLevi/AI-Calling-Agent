from typing import Optional

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from .config import (SAMPLE_RATE, CHANNELS, RECORD_SECONDS, LANGUAGE, 
                    WHISPER_MODEL_SIZE, DEVICE_INDEX_IN, SILENCE_THRESHOLD,
                    MIN_SPEECH_DURATION, MAX_SILENCE_DURATION)


class STTEngine:
    def __init__(self) -> None:
        self.model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")

    def record_audio(self) -> np.ndarray:
        duration = RECORD_SECONDS
        
        # Try different audio backends for Windows compatibility
        backends = [None, 'wasapi', 'directsound', 'mme']
        
        for backend in backends:
            try:
                if backend:
                    sd.default.hostapi = backend
                audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, 
                             channels=CHANNELS, dtype="float32", device=None)
                sd.wait()
                print(f"Using audio backend: {backend or 'default'}")
                return audio.flatten()
            except Exception as e:
                continue
        
        raise Exception("No working audio backend found. Check microphone permissions and ensure microphone is connected.")

    def listen_continuously(self) -> Optional[np.ndarray]:
        """Listen continuously and detect voice activity"""
        chunk_duration = 1.0  # 1 second chunks
        chunks = []
        silence_duration = 0
        speech_detected = False
        
        # Try different audio backends for Windows compatibility
        backends = [None, 'wasapi', 'directsound', 'mme']
        working_device = None
        
        for backend in backends:
            try:
                if backend:
                    sd.default.hostapi = backend
                chunk = sd.rec(int(0.1 * SAMPLE_RATE), samplerate=SAMPLE_RATE, 
                             channels=CHANNELS, dtype="float32", device=None)
                sd.wait()
                working_device = None
                print(f"Using audio backend: {backend or 'default'}")
                break
            except Exception as e:
                continue
        else:
            raise Exception("No working audio backend found. Check microphone permissions.")
        
        try:
            while True:
                # Record a chunk
                chunk = sd.rec(int(chunk_duration * SAMPLE_RATE), 
                             samplerate=SAMPLE_RATE, channels=CHANNELS, 
                             dtype="float32", device=working_device)
                sd.wait()
                chunk = chunk.flatten()
                
                # Check if there's speech in this chunk
                volume = np.sqrt(np.mean(chunk**2))
                
                if volume > SILENCE_THRESHOLD:
                    # Speech detected
                    chunks.append(chunk)
                    silence_duration = 0
                    speech_detected = True
                else:
                    # Silence detected
                    if speech_detected:
                        silence_duration += chunk_duration
                        chunks.append(chunk)  # Keep some silence for context
                        
                        # If we've had enough silence, stop recording
                        if silence_duration >= MAX_SILENCE_DURATION:
                            break
                
                # Prevent infinite recording
                if len(chunks) > 30:  # Max 30 seconds
                    break
        
        except KeyboardInterrupt:
            return None
            
        if speech_detected and len(chunks) >= int(MIN_SPEECH_DURATION / chunk_duration):
            return np.concatenate(chunks)
        
        return None

    def transcribe(self, audio: np.ndarray) -> str:
        segments, _ = self.model.transcribe(audio, language=LANGUAGE, vad_filter=True)
        text_parts = [seg.text for seg in segments]
        return " ".join(part.strip() for part in text_parts).strip()


def capture_and_transcribe() -> Optional[str]:
    stt = STTEngine()
    audio = stt.record_audio()
    text = stt.transcribe(audio)
    return text if text else None


