"""
Mixed Language AI Brain - Supports Hindi and English
===================================================

This module provides AI conversation capabilities for mixed Hindi-English conversations.
"""

import os
from typing import Optional
from abc import ABC, abstractmethod
try:
    from .debug_logger import logger, log_timing
except Exception:
    class _Null:
        def __getattr__(self, *_):
            return lambda *a, **k: None
    logger = _Null()
    def log_timing(name):
        def _d(f):
            return f
        return _d

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
    
    def ask_stream(self, user_text: str, language: str = None):
        """Stream AI response tokens as they arrive (optional implementation)"""
        # Default implementation falls back to regular ask()
        response = self.ask(user_text, language)
        yield response


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
    
    @log_timing("AI response (OpenAI)")
    def ask(self, user_text: str, language: str = None) -> str:
        """Process user input with OpenAI and respond in appropriate language"""
        # Detect language if not specified
        if language is None:
            language = detect_language(user_text)
        
        # Get appropriate system prompt
        system_prompt = get_language_prompt(language)
        
        # Add language instruction based on detected language
        if language in ['hi', 'mixed']:
            language_instruction = "\n\nIMPORTANT: User is speaking Hindi/Hinglish. Respond in Romanized Hinglish (like: 'Bilkul! Aapko kis sheher mein hotel chahiye?'). Do NOT respond in English."
        else:
            language_instruction = "\n\nRespond in English."
        
        # Append language instruction to system prompt
        enhanced_prompt = system_prompt + language_instruction
        
        # Add system prompt if this is the first message
        if not self.history:
            self.history.append({"role": "system", "content": enhanced_prompt})
        
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
            try:
                from .debug_logger import logger
                logger.error(f"OpenAI chat error: {type(e).__name__}: {e}")
            except Exception:
                pass
            return get_fallback_message(language)
    
    def ask_stream(self, user_text: str, language: str = None):
        """Process user input with OpenAI streaming and yield tokens as they arrive"""
        # Detect language if not specified
        if language is None:
            language = detect_language(user_text)
        
        # Get appropriate system prompt
        system_prompt = get_language_prompt(language)
        
        # Add language instruction based on detected language
        if language in ['hi', 'mixed']:
            language_instruction = "\n\nIMPORTANT: User is speaking Hindi/Hinglish. Respond in Romanized Hinglish (like: 'Bilkul! Aapko kis sheher mein hotel chahiye?'). Do NOT respond in English."
        else:
            language_instruction = "\n\nRespond in English."
        
        # Append language instruction to system prompt
        enhanced_prompt = system_prompt + language_instruction
        
        # Add system prompt if this is the first message
        if not self.history:
            self.history.append({"role": "system", "content": enhanced_prompt})
        
        # Add user message
        self.history.append({"role": "user", "content": user_text})
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                temperature=0.6,
                stream=True
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            # Add complete response to history
            self.history.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            print(f"❌ OpenAI streaming error: {e}")
            fallback = get_fallback_message(language)
            yield fallback


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
        
        # Get appropriate system prompt
        system_prompt = get_language_prompt(language)
        
        # Add language instruction based on detected language
        if language in ['hi', 'mixed']:
            language_instruction = "\n\nIMPORTANT: User is speaking Hindi/Hinglish. Respond in Romanized Hinglish (like: 'Bilkul! Aapko kis sheher mein hotel chahiye?'). Do NOT respond in English."
        else:
            language_instruction = "\n\nRespond in English."
        
        # Append language instruction to system prompt
        enhanced_prompt = system_prompt + language_instruction
        
        try:
            # Create conversation context
            if not self.history:
                # First message - include system prompt
                response = self.model.generate_content(
                    f"{enhanced_prompt}\n\nUser: {user_text}"
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