"""
Legacy Response Handler
=======================

Preserves the current response behavior for backward compatibility
when HUMANIZED_MODE is disabled.
"""

from typing import Optional
from src.mixed_ai_brain import MixedAIBrain
from src.language_detector import detect_language


class LegacyResponseHandler:
    """Handles responses using the current/legacy approach."""
    
    def __init__(self):
        self.ai_brain = MixedAIBrain()
    
    def generate_response(self, user_text: str, call_sid: str = None, 
                         context: str = "booking") -> str:
        """
        Generate response using legacy approach.
        
        Args:
            user_text: User's input text
            call_sid: Call session ID
            context: Conversation context
            
        Returns:
            Generated response text
        """
        # Detect language
        language = detect_language(user_text)
        
        # Generate response using current AI brain
        response = self.ai_brain.ask(user_text, language)
        
        return response
    
    def get_greeting(self, language: str = None) -> str:
        """Get greeting using legacy approach."""
        return self.ai_brain.get_greeting(language)


