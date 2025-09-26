"""
Mixed Language TTS Engine - Supports Hindi and English
=====================================================

This module provides text-to-speech capabilities for mixed Hindi-English conversations.
"""

import os
import shutil
import subprocess
import tempfile
from typing import Optional
from gtts import gTTS

try:
    from .config import USE_COQUI_TTS, HINDI_TTS_VOICE, ENGLISH_TTS_VOICE
    from .language_detector import detect_language, get_tts_voice
except ImportError:
    # Handle direct execution
    from config import USE_COQUI_TTS, HINDI_TTS_VOICE, ENGLISH_TTS_VOICE
    from language_detector import detect_language, get_tts_voice


def _play_with_pygame(file_path: str) -> bool:
    """Try to play audio using pygame"""
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        
        pygame.mixer.quit()
        return True
    except Exception as e:
        print(f"[TTS] Pygame playback failed: {e}")
        return False

def _play_with_ffplay(file_path: str, text: str = None) -> None:
    """Play audio file with multiple fallback options"""
    # Check if file exists and has content
    if not os.path.exists(file_path):
        print(f"[TTS] Audio file not found: {file_path}")
        if text:
            print(f"Bot: {text}")
        return
    
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        print(f"[TTS] Audio file is empty: {file_path}")
        if text:
            print(f"Bot: {text}")
        return
    
    print(f"[TTS] Playing audio file: {file_path} (size: {file_size} bytes)")
    
    # Try pygame first (most reliable)
    print("[TTS] Trying pygame...")
    if _play_with_pygame(file_path):
        print("[TTS] Audio played successfully with pygame")
        return
    
    # Try multiple audio players with better error handling
    players = [
        ("ffplay", ["-nodisp", "-autoexit", "-volume", "100"]),
        ("vlc", ["--intf", "dummy", "--play-and-exit"]),
        ("wmplayer", []),
        ("start", [])
    ]
    
    for player_name, args in players:
        if player_name == "start":
            # Windows default player
            try:
                print(f"[TTS] Trying Windows default player...")
                result = subprocess.run(["start", "/wait", file_path], shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"[TTS] Audio played successfully with Windows default player")
                    return
                else:
                    print(f"[TTS] Windows default player failed: {result.stderr}")
            except Exception as e:
                print(f"[TTS] Windows default player error: {e}")
                continue
        else:
            player_path = shutil.which(player_name)
            if player_path:
                try:
                    print(f"[TTS] Trying {player_name}...")
                    cmd = [player_path] + args + [file_path]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        print(f"[TTS] Audio played successfully with {player_name}")
                        return
                    else:
                        print(f"[TTS] {player_name} failed: {result.stderr}")
                except subprocess.TimeoutExpired:
                    print(f"[TTS] {player_name} timed out")
                except Exception as e:
                    print(f"[TTS] {player_name} error: {e}")
                    continue
    
    # If no player works, show the text
    print("[TTS] No audio player worked. Showing text instead:")
    if text:
        print(f"Bot: {text}")
    else:
        print(f"Bot: {file_path}")


def tts_gtts_mixed(text: str, language: str = None) -> None:
    """
    Generate speech using gTTS with automatic language detection.
    
    Args:
        text: Text to convert to speech
        language: Language code ('hi', 'en', 'auto')
    """
    print(f"[TTS] Generating speech for: '{text}'")
    
    # Detect language if not specified
    if language is None or language == "auto":
        detected_lang = detect_language(text)
        voice_code = get_tts_voice(detected_lang)
    else:
        voice_code = get_tts_voice(language)
    
    print(f"[TTS] Using voice: {voice_code}")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            mp3_path = os.path.join(tmpdir, "out.mp3")
            print(f"[TTS] Creating TTS object with language: {voice_code}")
            tts = gTTS(text=text, lang=voice_code)
            print(f"[TTS] Saving audio to: {mp3_path}")
            tts.save(mp3_path)
            
            # Verify the file was created and has content
            if os.path.exists(mp3_path):
                file_size = os.path.getsize(mp3_path)
                print(f"[TTS] Audio file created successfully: {file_size} bytes")
                _play_with_ffplay(mp3_path, text)
            else:
                print("[TTS] Error: Audio file was not created")
                print(f"Bot: {text}")
    except Exception as e:
        print(f"[TTS] Error generating speech: {e}")
        print(f"Bot: {text}")


def tts_gtts_hindi(text: str) -> None:
    """Generate Hindi speech using gTTS."""
    tts_gtts_mixed(text, "hi")


def tts_gtts_english(text: str) -> None:
    """Generate English speech using gTTS."""
    tts_gtts_mixed(text, "en")


def tts_coqui_mixed(text: str, language: str = None) -> None:
    """
    Generate speech using Coqui TTS with language detection.
    
    Args:
        text: Text to convert to speech
        language: Language code ('hi', 'en', 'auto')
    """
    # Lazy import to avoid heavy startup when not used
    try:
        from TTS.api import TTS
    except Exception as exc:
        raise RuntimeError("Coqui TTS not installed. Run: pip install TTS") from exc

    # Detect language if not specified
    if language is None or language == "auto":
        detected_lang = detect_language(text)
    else:
        detected_lang = language
    
    # Select appropriate model based on language
    if detected_lang == "hi":
        # Use a multilingual model that supports Hindi
        model_name = "tts_models/multilingual/multi-dataset/your_tts"
    else:
        # Use English model
        model_name = "tts_models/en/ljspeech/tacotron2-DDC"
    
    print(f"[TTS] Using Coqui model: {model_name} for language: {detected_lang}")
    
    try:
        tts = TTS(model_name)
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = os.path.join(tmpdir, "out.wav")
            tts.tts_to_file(text=text, file_path=wav_path)
            _play_with_ffplay(wav_path, text)
    except Exception as e:
        print(f"[TTS] Coqui TTS error: {e}")
        # Fallback to gTTS
        tts_gtts_mixed(text, detected_lang)


def speak_mixed(text: str, language: str = None) -> Optional[bool]:
    """
    Convert text to speech with automatic language detection.
    
    Args:
        text: Text to convert to speech
        language: Language code ('hi', 'en', 'auto')
        
    Returns:
        True if successful, None if no text
    """
    if not text:
        return None
    
    # Detect language if not specified
    if language is None or language == "auto":
        detected_lang = detect_language(text)
    else:
        detected_lang = language
    
    print(f"[TTS] Detected language: {detected_lang}")
    
    if USE_COQUI_TTS:
        try:
            tts_coqui_mixed(text, detected_lang)
        except RuntimeError:
            print("[TTS] Coqui not installed; falling back to gTTS.")
            tts_gtts_mixed(text, detected_lang)
    else:
        try:
            tts_gtts_mixed(text, detected_lang)
        except Exception as exc:
            print(f"[TTS] Playback error: {exc}. Showing text instead.")
            print(f"Bot: {text}")
    
    return True


def speak(text: str) -> Optional[bool]:
    """
    Convert text to speech with automatic language detection.
    
    Args:
        text: Text to convert to speech
        
    Returns:
        True if successful, None if no text
    """
    return speak_mixed(text, "auto")


# Backward compatibility functions
def tts_gtts(text: str) -> None:
    """Backward compatibility - use mixed language TTS."""
    tts_gtts_mixed(text, "auto")


def tts_coqui(text: str) -> None:
    """Backward compatibility - use mixed language TTS."""
    tts_coqui_mixed(text, "auto")
