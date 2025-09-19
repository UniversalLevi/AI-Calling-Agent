import os
import shutil
import subprocess
import tempfile
from typing import Optional

from gtts import gTTS

from .config import TTS_VOICE, USE_COQUI_TTS


def _play_with_ffplay(file_path: str) -> None:
    ffplay = shutil.which("ffplay")
    if not ffplay:
        # Graceful fallback: skip playback if ffplay isn't installed yet
        print("[TTS] ffplay not found. Install FFmpeg to enable audio playback. Showing text instead:")
        print(f"[TTS] {file_path}")
        return
    subprocess.run([ffplay, "-nodisp", "-autoexit", file_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def tts_gtts(text: str) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        mp3_path = os.path.join(tmpdir, "out.mp3")
        tts = gTTS(text=text, lang=TTS_VOICE)
        tts.save(mp3_path)
        _play_with_ffplay(mp3_path)


def tts_coqui(text: str) -> None:
    # Lazy import to avoid heavy startup when not used
    try:
        from TTS.api import TTS  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Coqui TTS not installed. Run: pip install TTS") from exc

    # Use a default English model; you can change to a local model name
    model_name = "tts_models/en/ljspeech/tacotron2-DDC"
    tts = TTS(model_name)
    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = os.path.join(tmpdir, "out.wav")
        tts.tts_to_file(text=text, file_path=wav_path)
        _play_with_ffplay(wav_path)


def speak(text: str) -> Optional[bool]:
    if not text:
        return None
    if USE_COQUI_TTS:
        try:
            tts_coqui(text)
        except RuntimeError:
            print("[TTS] Coqui not installed; falling back to gTTS + text-only if no ffplay.")
            tts_gtts(text)
    else:
        try:
            tts_gtts(text)
        except Exception as exc:
            print(f"[TTS] Playback error: {exc}. Showing text instead.")
            print(f"Bot: {text}")
    return True


