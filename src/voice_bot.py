import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from .config import PRINT_TRANSCRIPTS, PRINT_BOT_TEXT
    from .mixed_ai_brain import MixedAIBrain
    from .mixed_stt import MixedSTTEngine
    from .mixed_tts import speak_mixed
    from .language_detector import detect_language
except ImportError:
    # Handle direct execution
    from config import PRINT_TRANSCRIPTS, PRINT_BOT_TEXT
    from mixed_ai_brain import MixedAIBrain
    from mixed_stt import MixedSTTEngine
    from mixed_tts import speak_mixed
    from language_detector import detect_language


def main() -> int:
    print("🎤 Mixed Language Voice Bot Ready!")
    print("Supports: English (en) and Hindi (hi)")
    print("Press Enter to speak, or type 'quit' to exit.")
    
    brain = MixedAIBrain()
    stt = MixedSTTEngine()

    while True:
        user_cmd = input("")
        if user_cmd.strip().lower() in {"q", "quit", "exit"}:
            break

        print("🎤 Listening…")
        audio = stt.record_audio()
        text, detected_language = stt.transcribe_with_language(audio, "auto")
        
        if PRINT_TRANSCRIPTS:
            print(f"You ({detected_language}): {text}")

        if not text:
            print("(No speech detected)")
            continue

        reply = brain.ask(text, detected_language)
        if PRINT_BOT_TEXT:
            print(f"Bot ({detected_language}): {reply}")
        speak_mixed(reply, detected_language)

    print("👋 Goodbye!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


