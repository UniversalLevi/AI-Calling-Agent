"""
Humanized Response Handler
=========================

Implements the new humanized response pipeline with:
Intent Detection → Emotion Context → Personality Filter → AI Generation → Humanizer → Spoken Tone Converter
"""

import os
import time
from typing import Optional, Dict, Any
from src.mixed_ai_brain import MixedAIBrain
from src.language_detector import detect_language
from src.prompt_manager import get_context_prompt
from src.config import get_humanization_config
from src.script_integration import script_integration


class HumanizedResponseHandler:
    """Handles responses using the new humanized approach."""
    
    def __init__(self):
        self.ai_brain = MixedAIBrain()
        self.config = get_humanization_config()
        self.turn_count = 0
        
    def generate_response(self, user_text: str, call_sid: str = None, 
                         context: str = "booking", phone_number: str = None, 
                         product_id: str = None, product: Dict = None) -> str:
        """
        Generate response using humanized pipeline with script integration.
        
        Args:
            user_text: User's input text
            call_sid: Call session ID
            context: Conversation context (sales, booking, support)
            phone_number: User's phone number for country detection
            product_id: Active product ID for script selection
            product: Product information for script formatting
            
        Returns:
            Generated response text
        """
        self.turn_count += 1
        
        # Step 1: Async Processing (emotion, intent, language detection)
        processing_result = self._process_user_input_async(user_text, phone_number)
        
        # Step 2: Try Script Integration First (for sales context)
        if context == "sales" and product_id:
            script_response = self._try_script_response(
                product_id, user_text, processing_result.language, 
                product, call_sid
            )
            if script_response:
                # Apply humanization to script response
                response = self._apply_humanizer(script_response, processing_result.language, processing_result.emotion)
                response = self._convert_to_spoken_tone(response, processing_result.language)
                return response
        
        # Step 3: Fallback to AI Generation
        system_prompt = self._get_personality_prompt(context, processing_result.emotion, processing_result.language)
        response = self._generate_ai_response(user_text, system_prompt, processing_result.language)
        
        # Step 4: Humanizer (subtle fillers, micro-sentences)
        response = self._apply_humanizer(response, processing_result.language, processing_result.emotion)
        
        # Step 5: Spoken Tone Converter
        response = self._convert_to_spoken_tone(response, processing_result.language)
        
        return response
    
    def _try_script_response(self, product_id: str, user_text: str, language: str, 
                             product: Dict = None, call_sid: str = None) -> Optional[str]:
        """Try to get a script-based response"""
        try:
            # Get conversation history if available
            conversation_history = []
            if call_sid:
                # Try to get conversation history from memory
                try:
                    from src.conversation_memory import conversation_memory
                    if hasattr(conversation_memory, 'get_conversation_history'):
                        history = conversation_memory.get_conversation_history(call_sid)
                        if history:
                            conversation_history = history[-5:]  # Last 5 exchanges
                except Exception:
                    pass
            
            # Get script response
            script_response = script_integration.get_script_response(
                product_id=product_id,
                user_input=user_text,
                language=language,
                conversation_history=conversation_history,
                product=product
            )
            
            if script_response:
                print(f"📜 Using script response: {script_response[:100]}...")
                return script_response
            
            return None
            
        except Exception as e:
            print(f"❌ Error in script integration: {e}")
            return None
    
    def _process_user_input_async(self, user_text: str, phone_number: str = None):
        """Process user input asynchronously for better performance."""
        try:
            from src.async_processor import process_user_input_async
            from src.conversation_memory import get_recent_conversation_history
            
            # Get recent conversation history for context
            conversation_history = None
            if hasattr(self, 'call_sid') and self.call_sid:
                recent_history = get_recent_conversation_history(self.call_sid)
                conversation_history = [exchange.user_text for exchange in recent_history[-3:]]
            
            # Process asynchronously
            result = process_user_input_async(user_text, conversation_history, phone_number)
            
            # Return a simple object with the results
            class ProcessingResult:
                def __init__(self, emotion, language, intent):
                    self.emotion = emotion or 'neutral'
                    self.language = language or 'en'
                    self.intent = intent or 'general'
            
            return ProcessingResult(result.emotion, result.language, result.intent)
            
        except ImportError:
            # Fallback to synchronous processing
            return self._process_user_input_sync(user_text, phone_number)
        except Exception as e:
            print(f"⚠️ Async processing error, falling back: {e}")
            return self._process_user_input_sync(user_text, phone_number)
    
    def _process_user_input_sync(self, user_text: str, phone_number: str = None):
        """Synchronous fallback processing."""
        class ProcessingResult:
            def __init__(self, emotion, language, intent):
                self.emotion = emotion
                self.language = language
                self.intent = intent
        
        # Detect language with bias
        language = self._detect_language_with_bias(user_text, phone_number)
        
        # Detect emotion
        emotion = self._detect_emotion(user_text)
        
        # Detect intent
        intent = self._detect_intent(user_text)
        
        return ProcessingResult(emotion, language, intent)
    
    def _detect_intent(self, user_text: str) -> str:
        """Detect user intent based on keywords."""
        text_lower = user_text.lower()
        
        # Basic intent detection
        intents = {
            'greeting': ['hello', 'hi', 'namaste', 'good morning', 'good afternoon'],
            'booking': ['book', 'reserve', 'booking', 'reservation', 'book karo'],
            'inquiry': ['what', 'how', 'when', 'where', 'kya', 'kaise', 'kab'],
            'confirmation': ['yes', 'no', 'okay', 'sure', 'haan', 'nahi', 'theek'],
            'complaint': ['problem', 'issue', 'complaint', 'wrong', 'bad', 'problem hai'],
            'support': ['help', 'support', 'assistance', 'madad', 'help chahiye'],
            'goodbye': ['bye', 'goodbye', 'see you', 'thank you', 'alvida']
        }
        
        for intent, keywords in intents.items():
            if any(keyword in text_lower for keyword in keywords):
                return intent
        
        return 'general'
    
    def _detect_language_with_bias(self, user_text: str, phone_number: str = None) -> str:
        """Detect language with Hindi bias and phone number detection."""
        # Check phone number country code
        if phone_number and phone_number.startswith('+91'):
            return 'hi'  # Default to Hindi for Indian numbers
        
        # Use existing language detection
        detected_lang = detect_language(user_text)
        
        # Apply Hindi bias threshold
        if detected_lang == 'en' and self.config['hindi_bias_threshold'] > 0.5:
            # Check for Hindi indicators with bias
            hindi_indicators = ['मैं', 'आप', 'है', 'हैं', 'कर', 'करना', 'चाहिए', 'हो', 'होगा']
            if any(word in user_text for word in hindi_indicators):
                return 'hi'
            # For mixed detection, bias toward Hindi
            elif detected_lang == 'mixed':
                return 'hi'
        
        return detected_lang
    
    def _detect_emotion(self, user_text: str) -> str:
        """Detect user emotion using hybrid approach."""
        # Quick keyword-based detection
        emotion = self._quick_emotion_detect(user_text)
        
        # GPT sentiment check every 3-4 turns for recalibration
        if self.turn_count % 4 == 0:
            gpt_emotion = self._gpt_sentiment_check(user_text)
            if gpt_emotion != 'neutral':
                emotion = gpt_emotion
        
        return emotion
    
    def _quick_emotion_detect(self, user_text: str) -> str:
        """Quick emotion detection using keywords."""
        text_lower = user_text.lower()
        
        # Angry indicators
        angry_words = ['angry', 'frustrated', 'upset', 'annoyed', 'gussa', 'pareshan', 'problem']
        if any(word in text_lower for word in angry_words):
            return 'angry'
        
        # Confused indicators
        confused_words = ['confused', 'don\'t understand', 'samajh nahi', 'kaise', 'kya', 'kahan']
        if any(word in text_lower for word in confused_words):
            return 'confused'
        
        # Happy indicators
        happy_words = ['great', 'good', 'perfect', 'accha', 'shabash', 'wonderful', 'excellent']
        if any(word in text_lower for word in happy_words):
            return 'happy'
        
        return 'neutral'
    
    def _gpt_sentiment_check(self, user_text: str) -> str:
        """GPT-based sentiment analysis for complex cases."""
        try:
            # Simple sentiment prompt
            sentiment_prompt = f"Analyze the emotion in this text: '{user_text}'. Respond with only one word: angry, confused, happy, or neutral."
            sentiment = self.ai_brain.ask(sentiment_prompt, 'en')
            return sentiment.strip().lower()
        except:
            return 'neutral'
    
    def _get_personality_prompt(self, context: str, emotion: str, language: str) -> str:
        """Get context-aware personality prompt."""
        try:
            # Load context-specific prompt
            base_prompt = get_context_prompt(context)
            
            # Add emotion-specific instructions
            emotion_instructions = self._get_emotion_instructions(emotion, language)
            
            return f"{base_prompt}\n\n{emotion_instructions}"
        except Exception as e:
            print(f"Warning: Failed to load context prompt, using fallback: {e}")
            return self._get_fallback_prompt(language)
    
    def _get_emotion_instructions(self, emotion: str, language: str) -> str:
        """Get emotion-specific response instructions."""
        if language in ['hi', 'mixed']:
            instructions = {
                'angry': 'User is frustrated. Respond with extra patience and empathy. Use calming language like "Chinta mat kariye" and "Main samajh sakti hun".',
                'confused': 'User is confused. Slow down your response, use simple language, and ask clarifying questions. Use "Step by step kar lete hain".',
                'happy': 'User is happy. Match their energy slightly while staying professional. Use positive language like "Bahut accha" and "Shabash".',
                'neutral': 'Respond normally with warm, helpful tone.'
            }
        else:
            instructions = {
                'angry': 'User is frustrated. Respond with extra patience and empathy. Use calming language.',
                'confused': 'User is confused. Slow down your response and use simple language.',
                'happy': 'User is happy. Match their energy slightly while staying professional.',
                'neutral': 'Respond normally with warm, helpful tone.'
            }
        
        return instructions.get(emotion, instructions['neutral'])
    
    def _generate_ai_response(self, user_text: str, system_prompt: str, language: str) -> str:
        """Generate AI response with custom system prompt."""
        try:
            # Temporarily override system prompt
            original_prompt = self.ai_brain.provider.history[0]['content'] if self.ai_brain.provider.history else None
            
            # Set new system prompt
            if self.ai_brain.provider.history:
                self.ai_brain.provider.history[0]['content'] = system_prompt
            else:
                self.ai_brain.provider.history = [{"role": "system", "content": system_prompt}]
            
            # Generate response
            response = self.ai_brain.ask(user_text, language)
            
            # Restore original prompt
            if original_prompt and self.ai_brain.provider.history:
                self.ai_brain.provider.history[0]['content'] = original_prompt
            
            return response
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return self._get_fallback_response(language)
    
    def _apply_humanizer(self, response: str, language: str, emotion: str) -> str:
        """Apply humanizer with subtle fillers and micro-sentences."""
        if not self.config['enable_micro_sentences']:
            return response
        
        # Convert long sentences to micro-sentences
        response = self._convert_to_micro_sentences(response)
        
        # Add subtle fillers based on emotion and context
        if self.config['filler_frequency'] > 0:
            response = self._add_contextual_fillers(response, language, emotion)
        
        return response
    
    def _convert_to_micro_sentences(self, text: str) -> str:
        """Convert long sentences to shorter, more natural micro-sentences."""
        # Split on common sentence boundaries
        sentences = text.split('. ')
        
        micro_sentences = []
        for sentence in sentences:
            if len(sentence.split()) > 12:  # Long sentence
                # Split into smaller parts
                parts = sentence.split(', ')
                if len(parts) > 1:
                    micro_sentences.extend(parts)
                else:
                    # Split on conjunctions
                    conjunctions = [' aur ', ' and ', ' lekin ', ' but ', ' ya ', ' or ']
                    for conj in conjunctions:
                        if conj in sentence:
                            micro_sentences.extend(sentence.split(conj))
                            break
                    else:
                        micro_sentences.append(sentence)
            else:
                micro_sentences.append(sentence)
        
        return '. '.join(micro_sentences)
    
    def _add_contextual_fillers(self, text: str, language: str, emotion: str) -> str:
        """Add contextual fillers based on emotion and language."""
        import random
        
        if random.random() > self.config['filler_frequency']:
            return text
        
        if language in ['hi', 'mixed']:
            fillers = {
                'angry': ['Hmm, samjha main', 'Theek hai '],
                'confused': ['Achha', 'Dekho'],
                'happy': ['Bilkul', 'Zarur'],
                'neutral': ['Haan', 'Theek hai']
            }
        else:
            fillers = {
                'angry': ['I understand', 'Let me help'],
                'confused': ['I see', 'Let me explain'],
                'happy': ['Great', 'Perfect'],
                'neutral': ['Sure', 'Okay']
            }
        
        filler_options = fillers.get(emotion, fillers['neutral'])
        filler = random.choice(filler_options)
        
        # Add filler at natural break points
        if '. ' in text:
            parts = text.split('. ', 1)
            return f"{parts[0]}. {filler}, {parts[1]}"
        else:
            return f"{filler}, {text}"
    
    def _convert_to_spoken_tone(self, text: str, language: str) -> str:
        """Convert written tone to spoken tone."""
        if not self.config['enable_spoken_tone_converter']:
            return text
        
        if language in ['hi', 'mixed']:
            # Convert formal written patterns to spoken Hindi
            conversions = {
                'Please provide your name': 'Aapka naam bata dijiyega?',
                'Please wait': 'Thoda rukiyega',
                'I will help you': 'Main help karti hoon',
                'Thank you': 'Dhanyawad',
                'You are welcome': 'Koi baat nahi',
                'I understand': 'Main samajh sakti hun',
                'Let me check': 'Main check kar leti hoon',
                'One moment': 'Ek second',
                'Of course': 'Bilkul',
                'Absolutely': 'Zarur'
            }
        else:
            # Convert formal written patterns to spoken English
            conversions = {
                'Please provide your name': 'Could you tell me your name?',
                'Please wait': 'Just a moment',
                'I will help you': 'I\'ll help you with that',
                'Thank you': 'Thanks',
                'You are welcome': 'No problem',
                'I understand': 'I get it',
                'Let me check': 'Let me look that up',
                'One moment': 'One sec',
                'Of course': 'Sure thing',
                'Absolutely': 'Definitely'
            }
        
        result = text
        for formal, spoken in conversions.items():
            result = result.replace(formal, spoken)
        
        return result
    
    def _get_fallback_prompt(self, language: str) -> str:
        """Get fallback prompt if context loading fails."""
        if language in ['hi', 'mixed']:
            return """You are Sara, a friendly AI assistant. Respond in Romanized Hinglish with a warm, helpful tone. Keep responses short and natural."""
        else:
            return """You are Sara, a friendly AI assistant. Respond in English with a warm, helpful tone. Keep responses short and natural."""
    
    def _get_fallback_response(self, language: str) -> str:
        """Get fallback response if AI generation fails."""
        if language in ['hi', 'mixed']:
            return "Sorry, main abhi help nahi kar sakti. Thoda baad mein try kariye."
        else:
            return "Sorry, I can't help right now. Please try again later."
    
    def get_greeting(self, language: str = None) -> str:
        """Get greeting using humanized approach."""
        if language in ['hi', 'mixed']:
            greetings = [
                "Namaste! Main Sara hun. Aapka din kaise chal raha hai?",
                "Hello! Main Sara hun. Kaise hain aap?",
                "Namaste! Main Sara hun, aapki madad ke liye."
            ]
        else:
            greetings = [
                "Hello! I'm Sara. How are you doing today?",
                "Hi there! I'm Sara, how can I help you?",
                "Hello! I'm Sara, here to assist you."
            ]
        
        import random
        return random.choice(greetings)
