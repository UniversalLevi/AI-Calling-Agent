"""
Mixed Language AI Brain - Supports Hindi and English
===================================================

This module provides AI conversation capabilities for mixed Hindi-English conversations.
"""

import os
from typing import Optional
from abc import ABC, abstractmethod

try:
    from .language_detector import detect_language, get_language_prompt, get_greeting, get_fallback_message
except ImportError:
    # Handle direct execution
    from language_detector import detect_language, get_language_prompt, get_greeting, get_fallback_message


class MixedAIProvider(ABC):
    """Abstract base class for mixed language AI providers"""
    
    @abstractmethod
    def ask(self, user_text: str, language: str = None) -> str:
        """Process user input and return AI response in appropriate language"""
        pass


class MixedOpenAIProvider(MixedAIProvider):
    """OpenAI GPT implementation with mixed language support"""
    
    def __init__(self):
        from openai import OpenAI
        
        api_key = os.getenv('OPENAI_API_KEY')
        model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
        if not api_key or api_key == "REPLACE_ME":
            raise RuntimeError("OPENAI_API_KEY is missing. Please set it in .env")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.history = []
        print(f"🧠 Mixed OpenAI Provider initialized with {model}")
    
    def ask(self, user_text: str, language: str = None) -> str:
        """Process user input with OpenAI and respond in appropriate language"""
        # Detect language if not specified
        if language is None:
            language = detect_language(user_text)
        
        # Check for inappropriate content and redirect to service focus
        if self._is_inappropriate_content(user_text):
            return self._get_service_redirect_response(language)
        
        # Check if user is asking for non-service related content
        if self._is_non_service_request(user_text):
            return self._get_service_focus_response(language)
        
        # Get appropriate system prompt
        system_prompt = get_language_prompt(language)
        
        # Add system prompt if this is the first message
        if not self.history:
            self.history.append({"role": "system", "content": system_prompt})
        
        # Add user message
        self.history.append({"role": "user", "content": user_text})
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                temperature=0.6,
            )
            
            reply = completion.choices[0].message.content or ""
            self.history.append({"role": "assistant", "content": reply})
            
            return reply.strip()
            
        except Exception as e:
            print(f"❌ OpenAI error: {e}")
            return get_fallback_message(language)
    
    def _is_inappropriate_content(self, text: str) -> bool:
        """Check if content is inappropriate or offensive"""
        inappropriate_keywords = [
            'sex', 'sexy', 'fuck', 'shit', 'damn', 'hell', 'bitch', 'ass', 'chut', 'lund', 'gand',
            'mar', 'maar', 'kill', 'die', 'hate', 'stupid', 'idiot', 'moron', 'fool'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in inappropriate_keywords)
    
    def _is_non_service_request(self, text: str) -> bool:
        """Check if user is asking for non-service related content"""
        non_service_keywords = [
            'girlfriend', 'boyfriend', 'date', 'marry', 'marriage', 'love', 'relationship',
            'personal', 'private', 'family', 'friend', 'social', 'chat', 'talk', 'conversation',
            'joke', 'funny', 'entertainment', 'game', 'play', 'music', 'movie', 'song'
        ]
        
        # Service-related keywords that should NOT be blocked (English + Hindi/Hinglish)
        service_keywords = [
            # English service keywords
            'hotel', 'restaurant', 'booking', 'reservation', 'travel', 'trip', 'visit', 'place',
            'tour', 'sightseeing', 'attraction', 'destination', 'city', 'jaipur', 'delhi', 'mumbai',
            'recommendation', 'suggest', 'help', 'service', 'plan', 'planning', 'book', 'bikaner',
            
            # Hindi/Hinglish service keywords
            'book karo', 'book karna', 'book kar', 'booking karo', 'booking karna',
            'hotel book', 'restaurant book', 'travel book', 'trip book',
            'ghumne', 'ghumna', 'jane', 'jana', 'dekhne', 'dekhna',
            'suggest karo', 'suggest karna', 'help karo', 'help karna',
            'plan karo', 'plan karna', 'arrange karo', 'arrange karna'
        ]
        
        text_lower = text.lower()
        
        # If it contains service keywords, it's a service request
        if any(keyword in text_lower for keyword in service_keywords):
            return False
        
        # Otherwise check for non-service keywords
        return any(keyword in text_lower for keyword in non_service_keywords)
    
    def _get_service_redirect_response(self, language: str) -> str:
        """Get response redirecting to service focus"""
        if language in ['hi', 'mixed']:
            return "Main yahan aapki service ke liye hun. Kya main aapki koi help kar sakta hun? Restaurant booking, hotel reservation, ya koi aur service?"
        else:
            return "I'm here to help you with services. How can I assist you today? Restaurant booking, hotel reservation, or any other service?"
    
    def _get_service_focus_response(self, language: str) -> str:
        """Get response focusing on services"""
        if language in ['hi', 'mixed']:
            return "Main sirf services provide karta hun - restaurant booking, hotel reservation, travel planning. Aap kya service chahte hain?"
        else:
            return "I only provide services - restaurant booking, hotel reservation, travel planning. What service do you need?"


class MixedGeminiProvider(MixedAIProvider):
    """Google Gemini implementation with mixed language support"""
    
    def __init__(self):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("Google Generative AI not installed. Run: pip install google-generativeai")
        
        api_key = os.getenv('GEMINI_API_KEY')
        model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
        
        if not api_key or api_key == "REPLACE_ME":
            raise RuntimeError("GEMINI_API_KEY is missing. Please set it in .env")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.history = []
        print(f"🧠 Mixed Gemini Provider initialized with {model_name}")
    
    def ask(self, user_text: str, language: str = None) -> str:
        """Process user input with Gemini and respond in appropriate language"""
        # Detect language if not specified
        if language is None:
            language = detect_language(user_text)
        
        # Check for inappropriate content and redirect to service focus
        if self._is_inappropriate_content(user_text):
            return self._get_service_redirect_response(language)
        
        # Check if user is asking for non-service related content
        if self._is_non_service_request(user_text):
            return self._get_service_focus_response(language)
        
        # Get appropriate system prompt
        system_prompt = get_language_prompt(language)
        
        try:
            # Create conversation context
            if not self.history:
                # First message - include system prompt
                response = self.model.generate_content(
                    f"{system_prompt}\n\nUser: {user_text}"
                )
            else:
                # Continue conversation
                response = self.model.generate_content(user_text)
            
            reply = response.text.strip()
            
            # Add to history
            self.history.append({"role": "user", "parts": [user_text]})
            self.history.append({"role": "assistant", "parts": [reply]})
            
            return reply
            
        except Exception as e:
            print(f"❌ Gemini error: {e}")
            return get_fallback_message(language)
    
    def _is_inappropriate_content(self, text: str) -> bool:
        """Check if content is inappropriate or offensive"""
        inappropriate_keywords = [
            'sex', 'sexy', 'fuck', 'shit', 'damn', 'hell', 'bitch', 'ass', 'chut', 'lund', 'gand',
            'mar', 'maar', 'kill', 'die', 'hate', 'stupid', 'idiot', 'moron', 'fool'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in inappropriate_keywords)
    
    def _is_non_service_request(self, text: str) -> bool:
        """Check if user is asking for non-service related content"""
        non_service_keywords = [
            'girlfriend', 'boyfriend', 'date', 'marry', 'marriage', 'love', 'relationship',
            'personal', 'private', 'family', 'friend', 'social', 'chat', 'talk', 'conversation',
            'joke', 'funny', 'entertainment', 'game', 'play', 'music', 'movie', 'song'
        ]
        
        # Service-related keywords that should NOT be blocked (English + Hindi/Hinglish)
        service_keywords = [
            # English service keywords
            'hotel', 'restaurant', 'booking', 'reservation', 'travel', 'trip', 'visit', 'place',
            'tour', 'sightseeing', 'attraction', 'destination', 'city', 'jaipur', 'delhi', 'mumbai',
            'recommendation', 'suggest', 'help', 'service', 'plan', 'planning', 'book', 'bikaner',
            
            # Hindi/Hinglish service keywords
            'book karo', 'book karna', 'book kar', 'booking karo', 'booking karna',
            'hotel book', 'restaurant book', 'travel book', 'trip book',
            'ghumne', 'ghumna', 'jane', 'jana', 'dekhne', 'dekhna',
            'suggest karo', 'suggest karna', 'help karo', 'help karna',
            'plan karo', 'plan karna', 'arrange karo', 'arrange karna'
        ]
        
        text_lower = text.lower()
        
        # If it contains service keywords, it's a service request
        if any(keyword in text_lower for keyword in service_keywords):
            return False
        
        # Otherwise check for non-service keywords
        return any(keyword in text_lower for keyword in non_service_keywords)
    
    def _get_service_redirect_response(self, language: str) -> str:
        """Get response redirecting to service focus"""
        if language in ['hi', 'mixed']:
            return "Main yahan aapki service ke liye hun. Kya main aapki koi help kar sakta hun? Restaurant booking, hotel reservation, ya koi aur service?"
        else:
            return "I'm here to help you with services. How can I assist you today? Restaurant booking, hotel reservation, or any other service?"
    
    def _get_service_focus_response(self, language: str) -> str:
        """Get response focusing on services"""
        if language in ['hi', 'mixed']:
            return "Main sirf services provide karta hun - restaurant booking, hotel reservation, travel planning. Aap kya service chahte hain?"
        else:
            return "I only provide services - restaurant booking, hotel reservation, travel planning. What service do you need?"


class MixedAIBrain:
    """Main AI Brain class with mixed language support"""
    
    def __init__(self):
        self.provider = self._get_provider()
        self.provider_name = os.getenv('AI_PROVIDER', 'openai').lower()
        print(f"🧠 Mixed AI Brain initialized with: {self.provider_name.upper()}")
    
    def _get_provider(self) -> MixedAIProvider:
        """Get the appropriate AI provider based on environment"""
        provider = os.getenv('AI_PROVIDER', 'openai').lower()
        
        if provider == 'gemini':
            return MixedGeminiProvider()
        elif provider == 'openai':
            return MixedOpenAIProvider()
        else:
            print(f"⚠️ Unknown provider '{provider}', defaulting to OpenAI")
            return MixedOpenAIProvider()
    
    def ask(self, user_text: str, language: str = None) -> str:
        """Process user input with mixed language support"""
        try:
            return self.provider.ask(user_text, language)
        except Exception as e:
            print(f"❌ Error with {self.provider_name}: {e}")
            # Fallback to OpenAI if Gemini fails
            if self.provider_name == 'gemini':
                print("🔄 Falling back to OpenAI...")
                try:
                    fallback_provider = MixedOpenAIProvider()
                    return fallback_provider.ask(user_text, language)
                except Exception as fallback_error:
                    detected_lang = detect_language(user_text) if language is None else language
                    return get_fallback_message(detected_lang)
            else:
                detected_lang = detect_language(user_text) if language is None else language
                return get_fallback_message(detected_lang)
    
    def get_greeting(self, language: str = None) -> str:
        """Get appropriate greeting based on language"""
        if language is None:
            language = os.getenv('DEFAULT_LANGUAGE', 'en')
        return get_greeting(language)
    
    def get_provider_info(self) -> dict:
        """Get information about the current provider"""
        return {
            "provider": self.provider_name,
            "model": getattr(self.provider, 'model', 'unknown'),
            "history_length": len(getattr(self.provider, 'history', []))
        }


# Backward compatibility
class FlexibleAIBrain(MixedAIBrain):
    """Backward compatibility alias"""
    pass


class GPTBrain(MixedAIBrain):
    """Backward compatibility alias"""
    pass
