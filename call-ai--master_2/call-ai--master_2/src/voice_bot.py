import sys
import threading
import time

from .config import PRINT_TRANSCRIPTS, PRINT_BOT_TEXT
from .gpt_brain import GPTBrain
from .stt import STTEngine
from .tts import speak


def main() -> int:
    print("Voice bot ready. Start speaking! Press Ctrl+C to exit.")
    brain = GPTBrain()
    stt = STTEngine()
    
    try:
        while True:
            print("Listening for your voice...")
            audio = stt.listen_continuously()
            
            if audio is not None:
                text = stt.transcribe(audio)
                if PRINT_TRANSCRIPTS:
                    print(f"You: {text}")

                if not text:
                    continue

                reply = brain.ask(text)
                if PRINT_BOT_TEXT:
                    print(f"Bot: {reply}")
                speak(reply)
                
                # Brief pause before listening again
                time.sleep(0.5)
                
    except KeyboardInterrupt:
        print("\nGoodbye.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())


