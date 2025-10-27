"""
Humanizer Module for Natural Speech Patterns
Adds natural pauses, fillers, and emotional tone to make responses more human-like
"""

import random
import re
from typing import List, Dict, Tuple
from enum import Enum
from src.config import FILLER_FREQUENCY, ENABLE_MICRO_SENTENCES, ENABLE_SEMANTIC_PACING

class EmotionalTone(Enum):
    EMPATHETIC = "empathetic"
    CURIOUS = "curious"
    CONFIDENT = "confident"
    HELPFUL = "helpful"
    NEUTRAL = "neutral"

class Humanizer:
    """Adds human-like elements to AI responses"""
    
    def __init__(self):
        # Get settings from dashboard or use defaults
        try:
            from .dashboard_integration import sales_dashboard
            settings = sales_dashboard.get_voice_settings()
            self.filler_frequency = settings.get('filler_frequency', FILLER_FREQUENCY)
            self.enable_micro_sentences = settings.get('enable_micro_sentences', ENABLE_MICRO_SENTENCES)
            self.enable_semantic_pacing = settings.get('enable_semantic_pacing', ENABLE_SEMANTIC_PACING)
        except Exception:
            # Fallback to config values
            self.filler_frequency = FILLER_FREQUENCY
            self.enable_micro_sentences = ENABLE_MICRO_SENTENCES
            self.enable_semantic_pacing = ENABLE_SEMANTIC_PACING
            
        # Filler words by language
        self.fillers = {
            'en': {
                'thinking': ['um', 'uh', 'let me see', 'well', 'okay'],
                'confirmation': ['sure', 'absolutely', 'definitely', 'of course'],
                'processing': ['give me a moment', 'let me check', 'one second'],
                'positive': ['great', 'perfect', 'excellent', 'wonderful'],
                'understanding': ['I see', 'I understand', 'got it', 'makes sense']
            },
            'hi': {
                'thinking': ['um', 'acha', 'dekho', 'theek hai'],
                'confirmation': ['bilkul', 'zaroor', 'pakka', 'theek hai'],
                'processing': ['ek minute', 'thoda ruko', 'dekho'],
                'positive': ['bahut accha', 'shabash', 'excellent'],
                'understanding': ['samajh gaya', 'theek hai', 'acha']
            },
            'mixed': {
                'thinking': ['umm okay', 'let me see', 'acha wait', 'dekho'],
                'confirmation': ['sure', 'bilkul', 'theek hai', 'okay'],
                'processing': ['ek minute', 'let me check', 'dekho'],
                'positive': ['great', 'accha', 'perfect', 'shabash'],
                'understanding': ['samajh gaya', 'got it', 'theek hai']
            }
        }
        
        # Emotional tone templates
        self.tone_templates = {
            EmotionalTone.EMPATHETIC: {
                'en': ['I understand', 'That makes sense', 'I can see why', 'I hear you'],
                'hi': ['Main samajh sakti hun', 'Ye theek hai', 'Main dekh sakti hun'],
                'mixed': ['I understand', 'Samajh sakti hun', 'Theek hai']
            },
            EmotionalTone.CURIOUS: {
                'en': ['Interesting!', 'Tell me more', 'That\'s fascinating', 'I\'d love to know'],
                'hi': ['Interesting!', 'Aur batao', 'Ye interesting hai', 'Main janna chahti hun'],
                'mixed': ['Interesting!', 'Aur batao', 'Tell me more']
            },
            EmotionalTone.CONFIDENT: {
                'en': ['Absolutely!', 'Sure thing!', 'No problem', 'I can help with that'],
                'hi': ['Bilkul!', 'Zaroor!', 'Koi problem nahi', 'Main madad kar sakti hun'],
                'mixed': ['Absolutely!', 'Bilkul!', 'Sure thing!']
            },
            EmotionalTone.HELPFUL: {
                'en': ['I\'d be happy to help', 'Let me assist you', 'I\'m here to help'],
                'hi': ['Main madad kar sakti hun', 'Main aapki help kar sakti hun'],
                'mixed': ['I can help', 'Main madad kar sakti hun', 'Let me help']
            }
        }
        
        # Pause patterns (in milliseconds)
        self.pause_patterns = {
            'short': (200, 400),
            'medium': (400, 600),
            'long': (600, 1000),
            'thinking': (800, 1200)
        }
    
    def add_natural_elements(self, text: str, language: str = 'en', 
                           tone: EmotionalTone = EmotionalTone.NEUTRAL,
                           filler_frequency: float = None) -> str:
        """
        Add natural human-like elements to text
        
        Args:
            text: Original text
            language: Language code ('en', 'hi', 'mixed')
            tone: Emotional tone to apply
            filler_frequency: Probability of adding fillers (0.0 to 1.0), uses config default if None
            
        Returns:
            Enhanced text with natural elements
        """
        if filler_frequency is None:
            filler_frequency = FILLER_FREQUENCY
            
        enhanced_text = text
        
        # Convert to micro-sentences if enabled
        if ENABLE_MICRO_SENTENCES:
            enhanced_text = self._convert_to_micro_sentences(enhanced_text)
        
        # Add emotional tone prefix occasionally
        if random.random() < 0.15:  # Reduced to 15% chance
            enhanced_text = self._add_tone_prefix(enhanced_text, language, tone)
        
        # Add contextual fillers
        if random.random() < filler_frequency:
            enhanced_text = self._add_contextual_filler(enhanced_text, language, tone)
        
        # Add semantic pauses if enabled
        if ENABLE_SEMANTIC_PACING:
            enhanced_text = self._add_semantic_pauses(enhanced_text)
        
        return enhanced_text
    
    def _add_tone_prefix(self, text: str, language: str, tone: EmotionalTone) -> str:
        """Add emotional tone prefix to text"""
        if tone == EmotionalTone.NEUTRAL:
            return text
        
        tone_options = self.tone_templates.get(tone, {}).get(language, [])
        if not tone_options:
            return text
        
        prefix = random.choice(tone_options)
        
        # Add appropriate punctuation
        if prefix.endswith('!'):
            return f"{prefix} {text}"
        else:
            return f"{prefix}, {text}"
    
    def _convert_to_micro_sentences(self, text: str) -> str:
        """Convert long sentences to shorter, more natural micro-sentences."""
        sentences = text.split('. ')
        micro_sentences = []
        
        for sentence in sentences:
            if len(sentence.split()) > 12:  # Long sentence
                # Split on conjunctions and commas
                parts = re.split(r'[,;]\s*|\s+(and|aur|lekin|but|ya|or)\s+', sentence)
                if len(parts) > 1:
                    # Clean up parts and add them
                    for part in parts:
                        if part and part.strip():
                            micro_sentences.append(part.strip())
                else:
                    micro_sentences.append(sentence)
            else:
                micro_sentences.append(sentence)
        
        return '. '.join(micro_sentences)
    
    def _add_contextual_filler(self, text: str, language: str, tone: EmotionalTone) -> str:
        """Add contextual filler based on emotion and content."""
        filler_categories = self.fillers.get(language, self.fillers['en'])
        
        # Choose filler category based on tone and content
        if tone == EmotionalTone.EMPATHETIC:
            category = 'understanding'
        elif tone == EmotionalTone.CONFIDENT:
            category = 'confirmation'
        elif tone == EmotionalTone.CURIOUS:
            category = 'thinking'
        elif any(word in text.lower() for word in ['check', 'see', 'dekho', 'let me']):
            category = 'processing'
        elif any(word in text.lower() for word in ['great', 'perfect', 'accha', 'shabash']):
            category = 'positive'
        else:
            category = 'thinking'
        
        fillers = filler_categories.get(category, filler_categories['thinking'])
        filler = random.choice(fillers)
        
        # Insert filler at natural break points
        sentences = re.split(r'[.!?]', text)
        if len(sentences) > 1:
            # Add filler before the second sentence
            sentences[1] = f"{filler}, {sentences[1].strip()}"
            return '. '.join(sentences)
        else:
            # Add filler at the beginning
            return f"{filler}, {text}"
    
    def _add_semantic_pauses(self, text: str) -> str:
        """Add semantic pauses instead of random SSML breaks."""
        # Add pauses only at natural break points
        enhanced_text = text
        
        # Add pauses after commas (shorter)
        enhanced_text = re.sub(r',\s*', ', <break time="200ms"/> ', enhanced_text)
        
        # Add pauses after periods (longer)
        enhanced_text = re.sub(r'\.\s*', '. <break time="400ms"/> ', enhanced_text)
        
        # Add thinking pauses before specific phrases
        thinking_phrases = [
            'let me check', 'let me see', 'give me a moment',
            'dekho', 'ek minute', 'thoda ruko', 'main dekh leti hun'
        ]
        
        for phrase in thinking_phrases:
            pattern = f'\\b{re.escape(phrase)}\\b'
            enhanced_text = re.sub(
                pattern, 
                f'<break time="600ms"/> {phrase}', 
                enhanced_text, 
                flags=re.IGNORECASE
            )
        
        return enhanced_text
    
    def _add_filler(self, text: str, language: str) -> str:
        """Legacy filler method - kept for backward compatibility."""
        return self._add_contextual_filler(text, language, EmotionalTone.NEUTRAL)
    
    def _add_natural_pauses(self, text: str) -> str:
        """Add natural pauses using SSML breaks"""
        # Add pauses at natural break points
        enhanced_text = text
        
        # Add pauses after commas
        enhanced_text = re.sub(r',\s*', ', <break time="200ms"/> ', enhanced_text)
        
        # Add longer pauses after periods
        enhanced_text = re.sub(r'\.\s*', '. <break time="400ms"/> ', enhanced_text)
        
        # Add thinking pauses before certain phrases
        thinking_phrases = [
            'let me check', 'let me see', 'give me a moment',
            'dekho', 'ek minute', 'thoda ruko'
        ]
        
        for phrase in thinking_phrases:
            pattern = f'\\b{re.escape(phrase)}\\b'
            enhanced_text = re.sub(
                pattern, 
                f'<break time="600ms"/> {phrase}', 
                enhanced_text, 
                flags=re.IGNORECASE
            )
        
    def convert_to_spoken_tone(self, text: str, language: str = 'en') -> str:
        """Convert written tone to spoken tone for more natural speech."""
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
                'Absolutely': 'Zarur',
                'Please confirm': 'Confirm kar dijiyega',
                'Please provide': 'Bata dijiyega',
                'I can help': 'Main help kar sakti hun',
                'No problem': 'Koi problem nahi',
                'That\'s correct': 'Bilkul sahi hai',
                'I\'m sorry': 'Sorry',
                'Excuse me': 'Maaf kariye'
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
                'Absolutely': 'Definitely',
                'Please confirm': 'Can you confirm that?',
                'Please provide': 'Could you give me',
                'I can help': 'I can help with that',
                'No problem': 'No worries',
                'That\'s correct': 'That\'s right',
                'I\'m sorry': 'Sorry about that',
                'Excuse me': 'Pardon me'
            }
        
        result = text
        for formal, spoken in conversions.items():
            result = result.replace(formal, spoken)
        
        return result
    
    def get_ssml_response(self, text: str, language: str = 'en', 
                         tone: EmotionalTone = EmotionalTone.NEUTRAL) -> str:
        """
        Convert text to SSML with natural speech patterns
        
        Args:
            text: Text to convert
            language: Language code
            tone: Emotional tone
            
        Returns:
            SSML formatted text
        """
        # Add natural elements
        enhanced_text = self.add_natural_elements(text, language, tone)
        
        # Wrap in SSML
        ssml = f'<speak>{enhanced_text}</speak>'
        
        return ssml
    
    def detect_context_tone(self, text: str) -> EmotionalTone:
        """Detect appropriate emotional tone based on text content"""
        text_lower = text.lower()
        
        # Empathetic indicators
        if any(word in text_lower for word in ['sorry', 'problem', 'issue', 'help', 'maaf', 'problem']):
            return EmotionalTone.EMPATHETIC
        
        # Curious indicators
        if any(word in text_lower for word in ['tell me', 'what', 'how', 'why', 'batao', 'kaise']):
            return EmotionalTone.CURIOUS
        
        # Confident indicators
        if any(word in text_lower for word in ['sure', 'absolutely', 'definitely', 'bilkul', 'zaroor']):
            return EmotionalTone.CONFIDENT
        
        # Helpful indicators
        if any(word in text_lower for word in ['help', 'assist', 'support', 'madad', 'help']):
            return EmotionalTone.HELPFUL
        
        return EmotionalTone.NEUTRAL
    
    def enhance_response(self, text: str, language: str = 'en') -> str:
        """
        Main method to enhance any response with human-like elements
        
        Args:
            text: Original response text
            language: Detected language
            
        Returns:
            Enhanced response with natural elements
        """
        # Detect appropriate tone
        tone = self.detect_context_tone(text)
        
        # Add natural elements
        enhanced = self.add_natural_elements(text, language, tone)
        
        # Convert to spoken tone
        enhanced = self.convert_to_spoken_tone(enhanced, language)
        
        return enhanced


# Global humanizer instance
_humanizer = None

def get_humanizer() -> Humanizer:
    """Get global humanizer instance"""
    global _humanizer
    if _humanizer is None:
        _humanizer = Humanizer()
    return _humanizer

def enhance_response(text: str, language: str = 'en') -> str:
    """Convenience function to enhance any response"""
    humanizer = get_humanizer()
    return humanizer.enhance_response(text, language)
