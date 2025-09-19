import sys

from .config import PRINT_TRANSCRIPTS, PRINT_BOT_TEXT
from .gpt_brain import GPTBrain
from .stt import STTEngine
from .tts import speak


def main() -> int:
    print("Voice bot ready. Press Enter to speak, or type 'quit' to exit.")
    brain = GPTBrain()
    stt = STTEngine()

    while True:
        user_cmd = input("")
        if user_cmd.strip().lower() in {"q", "quit", "exit"}:
            break

        print("Listening…")
        audio = stt.record_audio()
        text = stt.transcribe(audio)
        if PRINT_TRANSCRIPTS:
            print(f"You: {text}")

        if not text:
            print("(No speech detected)")
            continue

        reply = brain.ask(text)
        if PRINT_BOT_TEXT:
            print(f"Bot: {reply}")
        speak(reply)

    print("Goodbye.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


