"""
Integrated SIP Voice Bot - Combines Phase 1 (STT->GPT->TTS) with Phase 2 (SIP Integration)
"""
import sys
import os
import threading
import time
import logging
from typing import Optional

# Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from .config import PRINT_TRANSCRIPTS, PRINT_BOT_TEXT, SAMPLE_RATE, RECORD_SECONDS
    from .gpt_brain import GPTBrain
    from .stt import STTEngine
    from .tts import speak
    from .sip_client import create_sip_client
except ImportError:
    # Handle direct execution
    from config import PRINT_TRANSCRIPTS, PRINT_BOT_TEXT, SAMPLE_RATE, RECORD_SECONDS
    from gpt_brain import GPTBrain
    from stt import STTEngine
    from tts import speak
    from sip_client import create_sip_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SIPVoiceBot:
    """Integrated voice bot that works with SIP calls"""
    
    def __init__(self, server_ip: str = "localhost", username: str = "1001", password: str = "botpass123"):
        self.server_ip = server_ip
        self.username = username
        self.password = password
        
        # Initialize components (defer GPTBrain initialization)
        self.brain = None
        self.stt = STTEngine()
        self.sip_client = create_sip_client(server_ip, username, password)
        
        # State management
        self.is_running = False
        self.call_active = False
        self.conversation_active = False
        
        # Audio processing
        self.audio_buffer = []
        self.processing_thread = None
        
    def initialize(self) -> bool:
        """Initialize all components"""
        try:
            logger.info("Initializing SIP Voice Bot...")
            
            # Initialize GPT Brain
            try:
                self.brain = GPTBrain()
                logger.info("GPT Brain initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize GPT Brain: {e}")
                return False
            
            # Initialize SIP client
            if not self.sip_client.initialize():
                logger.error("Failed to initialize SIP client")
                return False
            
            # Register with SIP server
            if not self.sip_client.register_account():
                logger.error("Failed to register SIP account")
                return False
            
            logger.info("SIP Voice Bot initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize SIP Voice Bot: {e}")
            return False
    
    def start(self):
        """Start the voice bot"""
        if not self.initialize():
            logger.error("Cannot start bot - initialization failed")
            return False
        
        self.is_running = True
        logger.info("SIP Voice Bot started. Waiting for calls...")
        
        # Start main loop
        self._main_loop()
        
        return True
    
    def stop(self):
        """Stop the voice bot"""
        logger.info("Stopping SIP Voice Bot...")
        self.is_running = False
        self.conversation_active = False
        
        if self.processing_thread:
            self.processing_thread.join()
        
        self.sip_client.cleanup()
        logger.info("SIP Voice Bot stopped")
    
    def make_call(self, target: str) -> bool:
        """Make a call to target extension"""
        if not self.is_running:
            logger.error("Bot is not running")
            return False
        
        logger.info(f"Making call to {target}")
        if self.sip_client.make_call(target):
            self.call_active = True
            self._start_conversation()
            return True
        return False
    
    def answer_call(self) -> bool:
        """Answer incoming call"""
        if not self.is_running:
            logger.error("Bot is not running")
            return False
        
        logger.info("Answering call")
        if self.sip_client.answer_call():
            self.call_active = True
            self._start_conversation()
            return True
        return False
    
    def hangup_call(self):
        """Hangup current call"""
        logger.info("Hanging up call")
        self.conversation_active = False
        self.call_active = False
        self.sip_client.hangup_call()
    
    def _start_conversation(self):
        """Start conversation mode"""
        if self.conversation_active:
            return
        
        self.conversation_active = True
        self.sip_client.start_audio_bridge()
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._conversation_loop)
        self.processing_thread.start()
        
        # Send initial greeting
        greeting = "Hello! I'm your AI assistant. How can I help you today?"
        self._speak_response(greeting)
    
    def _conversation_loop(self):
        """Main conversation processing loop"""
        logger.info("Conversation started")
        
        while self.conversation_active and self.is_running:
            try:
                # Record audio from call
                audio = self._record_call_audio()
                if audio is None:
                    time.sleep(0.1)
                    continue
                
                # Transcribe audio
                text = self.stt.transcribe(audio)
                if PRINT_TRANSCRIPTS and text:
                    print(f"You: {text}")
                
                if not text:
                    continue
                
                # Process with GPT
                response = self.brain.ask(text)
                if PRINT_BOT_TEXT:
                    print(f"Bot: {response}")
                
                # Speak response
                self._speak_response(response)
                
            except Exception as e:
                logger.error(f"Error in conversation loop: {e}")
                time.sleep(1)
        
        logger.info("Conversation ended")
    
    def _record_call_audio(self):
        """Record audio from SIP call"""
        try:
            # In a real implementation, this would capture audio from SIP RTP stream
            # For now, we'll simulate by recording from microphone
            import sounddevice as sd
            audio = sd.rec(int(RECORD_SECONDS * SAMPLE_RATE), 
                          samplerate=SAMPLE_RATE, channels=1, dtype='float32')
            sd.wait()
            return audio.flatten()
        except Exception as e:
            logger.error(f"Error recording audio: {e}")
            return None
    
    def _speak_response(self, text: str):
        """Speak response through SIP call"""
        try:
            # In a real implementation, this would send audio to SIP RTP stream
            # For now, we'll use the local TTS
            speak(text)
        except Exception as e:
            logger.error(f"Error speaking response: {e}")
    
    def _main_loop(self):
        """Main control loop"""
        try:
            while self.is_running:
                # Check for user input
                user_input = input("\nCommands: 'call <number>', 'answer', 'hangup', 'quit': ").strip().lower()
                
                if user_input == 'quit':
                    break
                elif user_input.startswith('call '):
                    target = user_input.split(' ', 1)[1]
                    self.make_call(target)
                elif user_input == 'answer':
                    self.answer_call()
                elif user_input == 'hangup':
                    self.hangup_call()
                else:
                    print("Unknown command")
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()


def main():
    """Main entry point"""
    print("🎤 SIP Voice Bot - Phase 1 + Phase 2 Integration")
    print("=" * 60)
    
    # Get configuration from environment or use defaults
    server_ip = os.getenv("SIP_SERVER_IP", "localhost")
    username = os.getenv("SIP_USERNAME", "1001")
    password = os.getenv("SIP_PASSWORD", "botpass123")
    
    print(f"SIP Server: {server_ip}")
    print(f"SIP Username: {username}")
    print(f"SIP Password: {'*' * len(password)}")
    print()
    
    # Create and start bot
    bot = SIPVoiceBot(server_ip, username, password)
    
    try:
        bot.start()
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

