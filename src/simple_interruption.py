"""
Simple and Reliable Interruption System
======================================

This module implements a reliable interruption system using enhanced short-cycle
gathering with smart timeout management - a proven approach that works consistently.
"""

import time
import logging
import os
from typing import Optional, Callable, Dict, Any
from flask import request
from twilio.twiml.voice_response import VoiceResponse

logger = logging.getLogger(__name__)

class SimpleInterruptionHandler:
    """
    Simple but reliable interruption handler using short gather cycles
    """
    
    def __init__(self):
        """Initialize the simple interruption handler"""
        self.call_states = {}  # Track state for each call
        self.interruption_timeout = 2  # Very short timeout for responsiveness
        self.max_silence_timeout = 8  # Maximum silence before prompting
        
        logger.info("🎧 Simple interruption handler initialized")
    
    def create_interruption_response(self, call_sid: str, bot_response: str, language: str = 'en') -> VoiceResponse:
        """
        Create a Twilio response with interruption-friendly gathering
        """
        response = VoiceResponse()
        
        # Initialize call state if needed
        if call_sid not in self.call_states:
            self.call_states[call_sid] = {
                'last_response_time': time.time(),
                'response_count': 0,
                'is_bot_speaking': False
            }
        
        # Update call state
        self.call_states[call_sid]['last_response_time'] = time.time()
        self.call_states[call_sid]['response_count'] += 1
        self.call_states[call_sid]['is_bot_speaking'] = True
        
        # Play the bot response
        if bot_response:
            # Use enhanced TTS if available
            try:
                from src.enhanced_hindi_tts import speak_mixed_enhanced
                audio_file = speak_mixed_enhanced(bot_response)
                if audio_file:
                    response.play(f"/audio/{audio_file}")
                    logger.info(f"🎵 Playing TTS: {bot_response[:50]}...")
                else:
                    # Fallback to Twilio voice
                    self._add_twilio_speech(response, bot_response, language)
            except ImportError:
                # Fallback to Twilio voice
                self._add_twilio_speech(response, bot_response, language)
            except Exception as e:
                # Handle any TTS errors gracefully
                logger.error(f"❌ TTS error: {e}")
                self._add_twilio_speech(response, bot_response, language)
        
        # Add very short gather for immediate interruption detection
        gather = response.gather(
            input='speech',
            action='/process_speech_realtime?interruption=simple',
            timeout=self.interruption_timeout,  # Very short for responsiveness
            speech_timeout='auto',
            language='hi-IN' if language in ['hi', 'mixed'] else 'en-IN',
            enhanced='true',
            profanity_filter='false'
        )
        
        # Mark bot as no longer speaking
        self.call_states[call_sid]['is_bot_speaking'] = False
        
        response.append(gather)
        
        # Add timeout handler - this will only execute if gather times out
        response.redirect('/simple_interruption_timeout')
        
        logger.info(f"⚡ Created interruption-friendly response (timeout: {self.interruption_timeout}s)")
        
        # Debug: Print the TwiML response
        twiml_str = str(response)
        logger.info(f"📞 TwiML Response:\n{twiml_str}")
        
        return response
    
    def _add_twilio_speech(self, response: VoiceResponse, text: str, language: str):
        """Add Twilio speech to response"""
        try:
            if language in ['hi', 'mixed']:
                response.say(text, voice=os.getenv('TWILIO_VOICE_HI', 'Polly.Aditi'), language='hi-IN')
            else:
                response.say(text, voice=os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna'), language='en-IN')
        except Exception as e:
            logger.error(f"❌ Twilio speech error: {e}")
            # Ultimate fallback
            response.say(text, voice=os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna'), language='en-IN')
    
    def handle_timeout(self, call_sid: str) -> VoiceResponse:
        """
        Handle timeout - either prompt user or continue listening
        """
        response = VoiceResponse()
        
        if call_sid in self.call_states:
            call_state = self.call_states[call_sid]
            time_since_last = time.time() - call_state['last_response_time']
            
            # If it's been too long, prompt the user
            if time_since_last > self.max_silence_timeout:
                response.say("I'm still here. How can I help you?", voice=os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna'), language='en-IN')
                call_state['last_response_time'] = time.time()
            
            # Continue listening with short timeout
            gather = response.gather(
                input='speech',
                action='/process_speech_realtime?interruption=simple',
                timeout=self.interruption_timeout,
                speech_timeout='auto',
                language='en-IN',
                enhanced='true',
                profanity_filter='false'
            )
            response.append(gather)
        
        return response
    
    def is_bot_speaking(self, call_sid: str) -> bool:
        """Check if bot is currently speaking"""
        if call_sid in self.call_states:
            return self.call_states[call_sid].get('is_bot_speaking', False)
        return False
    
    def cleanup_call(self, call_sid: str):
        """Clean up call state when call ends"""
        if call_sid in self.call_states:
            del self.call_states[call_sid]
            logger.info(f"🧹 Cleaned up call state for {call_sid}")


# Global instance
simple_interruption_handler = SimpleInterruptionHandler()

def get_simple_interruption_handler() -> SimpleInterruptionHandler:
    """Get the global simple interruption handler"""
    return simple_interruption_handler

def create_interruption_response(call_sid: str, bot_response: str, language: str = 'en') -> VoiceResponse:
    """
    Create an interruption-friendly response
    
    Args:
        call_sid: Twilio call SID
        bot_response: Bot's response text
        language: Language code ('en', 'hi', 'mixed')
    
    Returns:
        VoiceResponse with interruption handling
    """
    return simple_interruption_handler.create_interruption_response(call_sid, bot_response, language)

def handle_interruption_timeout(call_sid: str) -> VoiceResponse:
    """
    Handle interruption timeout
    
    Args:
        call_sid: Twilio call SID
    
    Returns:
        VoiceResponse for timeout handling
    """
    return simple_interruption_handler.handle_timeout(call_sid)
