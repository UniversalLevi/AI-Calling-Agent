"""
Response Factory
================

Factory pattern for selecting between legacy and humanized response handlers
based on the HUMANIZED_MODE feature flag.
"""

from typing import Optional
from src.config import is_humanized_mode_enabled
from .legacy_response import LegacyResponseHandler
from .humanized_response import HumanizedResponseHandler


class ResponseFactory:
    """Factory for creating appropriate response handlers."""
    
    def __init__(self):
        self._legacy_handler = None
        self._humanized_handler = None
    
    def get_handler(self):
        """Get the appropriate response handler based on feature flag."""
        if is_humanized_mode_enabled():
            if self._humanized_handler is None:
                self._humanized_handler = HumanizedResponseHandler()
            return self._humanized_handler
        else:
            if self._legacy_handler is None:
                self._legacy_handler = LegacyResponseHandler()
            return self._legacy_handler
    
    def generate_response(self, user_text: str, call_sid: str = None, 
                         context: str = "booking", phone_number: str = None,
                         product_id: str = None, product: dict = None) -> str:
        """
        Generate response using the appropriate handler.
        
        Args:
            user_text: User's input text
            call_sid: Call session ID
            context: Conversation context
            phone_number: User's phone number
            product_id: Active product ID for script integration
            product: Product information for script formatting
            
        Returns:
            Generated response text
        """
        handler = self.get_handler()
        
        if is_humanized_mode_enabled():
            return handler.generate_response(user_text, call_sid, context, phone_number, product_id, product)
        else:
            return handler.generate_response(user_text, call_sid, context)
    
    def get_greeting(self, language: str = None) -> str:
        """Get greeting using the appropriate handler."""
        handler = self.get_handler()
        return handler.get_greeting(language)
    
    def clear_cache(self):
        """Clear handler cache to force recreation."""
        self._legacy_handler = None
        self._humanized_handler = None


# Global response factory instance
_response_factory = None

def get_response_factory() -> ResponseFactory:
    """Get the global response factory instance."""
    global _response_factory
    if _response_factory is None:
        _response_factory = ResponseFactory()
    return _response_factory

def generate_response(user_text: str, call_sid: str = None, 
                     context: str = "booking", phone_number: str = None,
                     product_id: str = None, product: dict = None) -> str:
    """Convenience function to generate response using appropriate handler."""
    factory = get_response_factory()
    return factory.generate_response(user_text, call_sid, context, phone_number, product_id, product)

def get_greeting(language: str = None) -> str:
    """Convenience function to get greeting using appropriate handler."""
    factory = get_response_factory()
    return factory.get_greeting(language)


