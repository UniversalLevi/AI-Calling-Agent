#!/usr/bin/env python3

from .gpt_brain import GPTBrain
from .tts import TTSEngine
from .config import PRINT_TRANSCRIPTS, PRINT_BOT_TEXT


def main():
    brain = GPTBrain()
    tts = TTSEngine()
    
    print("Text bot ready! Type your messages (or 'quit' to exit):")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
                
            if not user_input:
                continue
                
            if PRINT_TRANSCRIPTS:
                print(f"User said: {user_input}")
            
            # Get bot response
            bot_response = brain.get_response(user_input)
            
            if PRINT_BOT_TEXT:
                print(f"Bot: {bot_response}")
            
            # Play TTS response
            tts.speak(bot_response)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
