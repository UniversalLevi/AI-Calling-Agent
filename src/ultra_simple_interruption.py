"""
Ultra-Simple Interruption System
===============================

This implements a dead-simple interruption system that actually works.
Uses short gather cycles with immediate processing - no complex logic.
"""

import time
import logging
import os
from typing import Optional
from twilio.twiml.voice_response import VoiceResponse

logger = logging.getLogger(__name__)

class UltraSimpleInterruption:
    """
    Ultra-simple interruption system that actually works
    """
    
    def __init__(self):
        """Initialize the ultra-simple interruption handler"""
        self.call_states = {}
        self.gather_timeout = 3  # 3 seconds - short enough for interruption
        
        logger.info("🎧 Ultra-simple interruption initialized")
    
    def create_response(self, call_sid: str, bot_text: str, language: str = 'en') -> VoiceResponse:
        """
        Create a response with ultra-simple interruption
        
        Args:
            call_sid: Twilio call SID
            bot_text: Bot's response text
            language: Language code ('en', 'hi', 'mixed')
        
        Returns:
            VoiceResponse with interruption handling
        """
        response = VoiceResponse()
        
        # Initialize call state
        if call_sid not in self.call_states:
            self.call_states[call_sid] = {
                'response_count': 0,
                'last_activity': time.time()
            }
        
        self.call_states[call_sid]['response_count'] += 1
        self.call_states[call_sid]['last_activity'] = time.time()
        
        # Add gather FIRST for immediate interruption detection
        gather = response.gather(
            input='speech',
            action='/process_speech_realtime?interruption=simple',
            timeout=self.gather_timeout,  # Short timeout for interruption
            speech_timeout='auto',
            language='hi-IN' if language in ['hi', 'mixed'] else 'en-IN',
            enhanced='true',
            profanity_filter='false'
        )
        
        # Play bot response INSIDE gather for true interruption
        if bot_text:
            try:
                from src.enhanced_hindi_tts import speak_mixed_enhanced
                audio_file = speak_mixed_enhanced(bot_text)
                if audio_file:
                    gather.play(f"/audio/{audio_file}")
                    logger.info(f"🎵 Playing TTS inside gather: {bot_text[:50]}...")
                else:
                    # Fallback to Twilio voice
                    logger.warning("⚠️ TTS returned None, using Twilio voice fallback")
                    self._add_twilio_voice_to_gather(gather, bot_text, language)
            except Exception as e:
                logger.error(f"❌ TTS error: {e}")
                self._add_twilio_voice_to_gather(gather, bot_text, language)
        else:
            # If no bot text, add a default message to prevent empty gather
            logger.warning("⚠️ No bot text provided, adding default message")
            self._add_twilio_voice_to_gather(gather, "Hello! How can I help you?", language)
        
        response.append(gather)
        
        # If gather times out, continue listening
        response.redirect('/ultra_simple_interruption_timeout')
        
        logger.info(f"⚡ Created ultra-simple response with true interruption (timeout: {self.gather_timeout}s)")
        
        # Debug: Print the TwiML response
        twiml_str = str(response)
        logger.info(f"📞 TwiML Response:\n{twiml_str}")
        
        return response
    
    def _add_twilio_voice(self, response: VoiceResponse, text: str, language: str):
        """Add Twilio voice to response"""
        try:
            if language in ['hi', 'mixed']:
                response.say(text, voice=os.getenv('TWILIO_VOICE_HI', 'Polly.Aditi'), language='hi-IN')
            else:
                response.say(text, voice=os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna'), language='en-IN')
        except Exception as e:
            logger.error(f"❌ Twilio voice error: {e}")
            response.say(text, voice=os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna'), language='en-IN')
    
    def _add_twilio_voice_to_gather(self, gather, text: str, language: str):
        """Add Twilio voice to gather element"""
        try:
            if language in ['hi', 'mixed']:
                gather.say(text, voice=os.getenv('TWILIO_VOICE_HI', 'Polly.Aditi'), language='hi-IN')
            else:
                gather.say(text, voice=os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna'), language='en-IN')
        except Exception as e:
            logger.error(f"❌ Twilio voice to gather error: {e}")
            gather.say(text, voice=os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna'), language='en-IN')
    
    def handle_timeout(self, call_sid: str) -> VoiceResponse:
        """
        Handle timeout - continue listening
        """
        response = VoiceResponse()
        
        logger.info(f"⏰ Timeout for call {call_sid} - continuing to listen")
        
        # Continue listening with short timeout
        gather = response.gather(
            input='speech',
            action='/process_speech_realtime?interruption=simple',
            timeout=self.gather_timeout,
            speech_timeout='auto',
            language='en-IN',
            enhanced='true',
            profanity_filter='false'
        )
        
        response.append(gather)
        response.redirect('/ultra_simple_interruption_timeout')
        
        return response
    
    def cleanup_call(self, call_sid: str):
        """Clean up call state when call ends"""
        if call_sid in self.call_states:
            del self.call_states[call_sid]
            logger.info(f"🧹 Cleaned up call state for {call_sid}")


# Global instance
ultra_simple_interruption = UltraSimpleInterruption()

def create_ultra_simple_response(call_sid: str, bot_text: str, language: str = 'en') -> VoiceResponse:
    """
    Create an ultra-simple interruption response
    
    Args:
        call_sid: Twilio call SID
        bot_text: Bot's response text
        language: Language code ('en', 'hi', 'mixed')
    
    Returns:
        VoiceResponse with ultra-simple interruption handling
    """
    return ultra_simple_interruption.create_response(call_sid, bot_text, language)

def handle_ultra_simple_timeout(call_sid: str) -> VoiceResponse:
    """
    Handle timeout for ultra-simple interruption
    
    Args:
        call_sid: Twilio call SID
    
    Returns:
        VoiceResponse for timeout handling
    """
    return ultra_simple_interruption.handle_timeout(call_sid)
