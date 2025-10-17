"""
Humanizer Module for Natural Speech Patterns
Adds natural pauses, fillers, and emotional tone to make responses more human-like
"""

import random
import re
from typing import List, Dict, Tuple
from enum import Enum

class EmotionalTone(Enum):
    EMPATHETIC = "empathetic"
    CURIOUS = "curious"
    CONFIDENT = "confident"
    HELPFUL = "helpful"
    NEUTRAL = "neutral"

class Humanizer:
    """Adds human-like elements to AI responses"""
    
    def __init__(self):
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
                           filler_frequency: float = 0.3) -> str:
        """
        Add natural human-like elements to text
        
        Args:
            text: Original text
            language: Language code ('en', 'hi', 'mixed')
            tone: Emotional tone to apply
            filler_frequency: Probability of adding fillers (0.0 to 1.0)
            
        Returns:
            Enhanced text with natural elements
        """
        enhanced_text = text
        
        # Add emotional tone prefix occasionally
        if random.random() < 0.2:  # 20% chance
            enhanced_text = self._add_tone_prefix(enhanced_text, language, tone)
        
        # Add fillers occasionally
        if random.random() < filler_frequency:
            enhanced_text = self._add_filler(enhanced_text, language)
        
        # Add natural pauses using SSML breaks
        enhanced_text = self._add_natural_pauses(enhanced_text)
        
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
    
    def _add_filler(self, text: str, language: str) -> str:
        """Add natural filler words"""
        filler_categories = self.fillers.get(language, self.fillers['en'])
        
        # Choose filler category based on context
        if any(word in text.lower() for word in ['sorry', 'maaf', 'excuse']):
            category = 'understanding'
        elif any(word in text.lower() for word in ['great', 'perfect', 'accha', 'shabash']):
            category = 'positive'
        elif any(word in text.lower() for word in ['check', 'see', 'dekho', 'let me']):
            category = 'processing'
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
        
        return enhanced_text
    
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
        enhanced = self.add_natural_elements(text, language, tone, filler_frequency=0.25)
        
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
