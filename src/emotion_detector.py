"""
Emotion Detection Module
========================

Hybrid emotion detection using keyword-based quick detection and GPT sentiment analysis
for complex cases. Provides emotion-aware response generation.
"""

import os
import time
from typing import Dict, List, Optional, Tuple
from enum import Enum
from src.config import EMOTION_DETECTION_MODE
from src.mixed_ai_brain import MixedAIBrain

class EmotionalTone(Enum):
    """Emotional tone enumeration"""
    EMPATHETIC = "empathetic"
    CURIOUS = "curious"
    CONFIDENT = "confident"
    HELPFUL = "helpful"
    NEUTRAL = "neutral"
    ANGRY = "angry"
    CONFUSED = "confused"
    HAPPY = "happy"


class EmotionDetector:
    """Hybrid emotion detection with keyword and GPT-based analysis."""
    
    def __init__(self):
        self.ai_brain = MixedAIBrain()
        self.turn_count = 0
        self.emotion_history = []
        
        # Keyword-based emotion indicators
        self.emotion_keywords = {
            'angry': {
                'en': ['angry', 'frustrated', 'upset', 'annoyed', 'mad', 'irritated', 'pissed', 'furious'],
                'hi': ['gussa', 'pareshan', 'problem', 'problem hai', 'boring', 'tension', 'dikkat', 'pareshan hun', 'gussa hai'],
                'mixed': ['angry', 'frustrated', 'gussa', 'problem', 'upset', 'annoyed', 'pareshan']
            },
            'confused': {
                'en': ['confused', 'don\'t understand', 'unclear', 'not sure', 'what is', 'how does', 'why is', 'where is'],
                'hi': ['samajh nahi', 'confused', 'kaise', 'kya', 'kahan', 'kyun', 'kab', 'kya matlab', 'samajh nahi aaya', 'samajh nahi aata'],
                'mixed': ['confused', 'samajh nahi', 'don\'t understand', 'kaise', 'kya', 'how', 'samajh nahi aaya']
            },
            'happy': {
                'en': ['great', 'good', 'perfect', 'wonderful', 'excellent', 'amazing', 'fantastic', 'love'],
                'hi': ['accha', 'shabash', 'bahut accha', 'perfect', 'wonderful', 'excellent', 'mast', 'bahut accha hai'],
                'mixed': ['great', 'accha', 'perfect', 'shabash', 'wonderful', 'excellent', 'mast', 'bahut accha']
            },
            'sad': {
                'en': ['sad', 'disappointed', 'unhappy', 'depressed', 'down', 'upset', 'hurt'],
                'hi': ['dukhi', 'upset', 'sad', 'problem', 'tension', 'pareshan'],
                'mixed': ['sad', 'dukhi', 'upset', 'disappointed', 'problem', 'tension']
            },
            'excited': {
                'en': ['excited', 'thrilled', 'enthusiastic', 'pumped', 'eager', 'can\'t wait'],
                'hi': ['excited', 'enthusiastic', 'eager', 'ready', 'thrilled'],
                'mixed': ['excited', 'thrilled', 'enthusiastic', 'ready', 'eager']
            },
            'neutral': {
                'en': ['okay', 'fine', 'alright', 'sure', 'yes', 'no', 'maybe'],
                'hi': ['theek', 'okay', 'haan', 'nahi', 'shayad', 'bilkul'],
                'mixed': ['okay', 'theek', 'fine', 'sure', 'haan', 'nahi']
            },
            'empathetic': {
                'en': ['help', 'support', 'assist', 'sorry', 'apologize', 'understand', 'feel', 'need help', 'struggling', 'difficult'],
                'hi': ['madad', 'sahayata', 'maaf', 'sorry', 'samajh', 'feel', 'help', 'pareshan', 'dikkat'],
                'mixed': ['help', 'madad', 'support', 'sorry', 'maaf', 'understand', 'samajh', 'pareshan', 'dikkat']
            }
        }
        
        # Emotion intensity modifiers
        self.intensity_modifiers = {
            'very': 1.5,
            'really': 1.3,
            'so': 1.2,
            'quite': 1.1,
            'extremely': 1.8,
            'super': 1.4,
            'bahut': 1.3,
            'zyada': 1.2
        }
    
    def detect_emotion(self, text: str, language: str = 'en', use_gpt: bool = False) -> EmotionalTone:
        """
        Detect emotion in text using hybrid approach.
        
        Args:
            text: Input text to analyze
            language: Language of the text
            use_gpt: Force GPT analysis even for quick detection
            
        Returns:
            EmotionalTone enum value
        """
        self.turn_count += 1
        
        # Quick keyword-based detection
        quick_emotion, quick_confidence = self._quick_emotion_detect(text, language)
        
        # GPT sentiment check every 3-4 turns or when forced
        if use_gpt or self.turn_count % 4 == 0:
            gpt_emotion, gpt_confidence = self._gpt_sentiment_analysis(text, language)
            
            # Use GPT result if confidence is higher or quick detection failed
            if gpt_confidence > quick_confidence or quick_emotion == 'neutral':
                emotion = gpt_emotion
                confidence = gpt_confidence
            else:
                emotion = quick_emotion
                confidence = quick_confidence
        else:
            emotion = quick_emotion
            confidence = quick_confidence
        
        # Store emotion history for context
        self.emotion_history.append((emotion, confidence, time.time()))
        
        # Keep only recent history (last 10 emotions)
        if len(self.emotion_history) > 10:
            self.emotion_history = self.emotion_history[-10:]
        
        # Convert string emotion to EmotionalTone enum
        try:
            return EmotionalTone(emotion)
        except ValueError:
            return EmotionalTone.NEUTRAL
    
    def _quick_emotion_detect(self, text: str, language: str) -> Tuple[str, float]:
        """Quick emotion detection using keyword matching."""
        if not text or not text.strip():
            return 'neutral', 0.5
        
        text_lower = text.lower().strip()
        words = text_lower.split()
        
        emotion_scores = {}
        
        # Check each emotion category
        for emotion, lang_keywords in self.emotion_keywords.items():
            score = 0
            keywords = lang_keywords.get(language, lang_keywords.get('en', []))
            
            for keyword in keywords:
                if keyword in text_lower:
                    # Base score for keyword match
                    score += 1
                    
                    # Check for intensity modifiers
                    for modifier, multiplier in self.intensity_modifiers.items():
                        if modifier in text_lower:
                            score *= multiplier
                            break
            
            if score > 0:
                emotion_scores[emotion] = score
        
        if not emotion_scores:
            return 'neutral', 0.5
        
        # Get emotion with highest score
        best_emotion = max(emotion_scores, key=emotion_scores.get)
        best_score = emotion_scores[best_emotion]
        
        # Convert score to confidence (0.5 to 1.0)
        confidence = min(0.5 + (best_score * 0.1), 1.0)
        
        return best_emotion, confidence
    
    def _gpt_sentiment_analysis(self, text: str, language: str) -> Tuple[str, float]:
        """GPT-based sentiment analysis for complex cases."""
        try:
            if language in ['hi', 'mixed']:
                prompt = f"""Analyze the emotion in this Hindi/Hinglish text: '{text}'
                
Respond with only one word from: angry, confused, happy, sad, excited, neutral
Then give confidence score 0.0 to 1.0

Format: emotion:confidence
Example: happy:0.8"""
            else:
                prompt = f"""Analyze the emotion in this English text: '{text}'
                
Respond with only one word from: angry, confused, happy, sad, excited, neutral
Then give confidence score 0.0 to 1.0

Format: emotion:confidence
Example: happy:0.8"""
            
            response = self.ai_brain.ask(prompt, 'en')
            
            # Parse response
            if ':' in response:
                emotion, confidence_str = response.split(':', 1)
                emotion = emotion.strip().lower()
                try:
                    confidence = float(confidence_str.strip())
                    confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1
                except ValueError:
                    confidence = 0.7
            else:
                emotion = response.strip().lower()
                confidence = 0.7
            
            # Validate emotion
            valid_emotions = ['angry', 'confused', 'happy', 'sad', 'excited', 'neutral']
            if emotion not in valid_emotions:
                emotion = 'neutral'
                confidence = 0.5
            
            return emotion, confidence
            
        except Exception as e:
            print(f"GPT sentiment analysis error: {e}")
            return 'neutral', 0.5
    
    def get_emotion_context(self) -> Dict[str, any]:
        """Get recent emotion context for response generation."""
        if not self.emotion_history:
            return {'current_emotion': 'neutral', 'trend': 'stable', 'intensity': 'medium'}
        
        recent_emotions = [e[0] for e in self.emotion_history[-3:]]
        recent_confidences = [e[1] for e in self.emotion_history[-3:]]
        
        # Determine trend
        if len(recent_emotions) >= 2:
            if recent_emotions[-1] == recent_emotions[-2]:
                trend = 'stable'
            elif recent_emotions[-1] in ['happy', 'excited'] and recent_emotions[-2] in ['angry', 'sad']:
                trend = 'improving'
            elif recent_emotions[-1] in ['angry', 'sad'] and recent_emotions[-2] in ['happy', 'excited']:
                trend = 'declining'
            else:
                trend = 'changing'
        else:
            trend = 'stable'
        
        # Determine intensity
        avg_confidence = sum(recent_confidences) / len(recent_confidences)
        if avg_confidence > 0.8:
            intensity = 'high'
        elif avg_confidence > 0.6:
            intensity = 'medium'
        else:
            intensity = 'low'
        
        return {
            'current_emotion': recent_emotions[-1],
            'previous_emotion': recent_emotions[-2] if len(recent_emotions) > 1 else 'neutral',
            'trend': trend,
            'intensity': intensity,
            'confidence': avg_confidence
        }
    
    def get_emotion_response_guidance(self, emotion: str, language: str) -> str:
        """Get response guidance based on detected emotion."""
        if language in ['hi', 'mixed']:
            guidance = {
                'angry': 'User is frustrated. Respond with extra patience and empathy. Use calming language like "Chinta mat kariye" and "Main samajh sakti hun".',
                'confused': 'User is confused. Slow down your response, use simple language, and ask clarifying questions. Use "Step by step kar lete hain".',
                'happy': 'User is happy. Match their energy slightly while staying professional. Use positive language like "Bahut accha" and "Shabash".',
                'sad': 'User seems sad or disappointed. Be extra empathetic and supportive. Use comforting language like "Koi baat nahi" and "Main help kar sakti hun".',
                'excited': 'User is excited. Match their enthusiasm appropriately while staying professional. Use encouraging language.',
                'neutral': 'Respond normally with warm, helpful tone.'
            }
        else:
            guidance = {
                'angry': 'User is frustrated. Respond with extra patience and empathy. Use calming language.',
                'confused': 'User is confused. Slow down your response and use simple language.',
                'happy': 'User is happy. Match their energy slightly while staying professional.',
                'sad': 'User seems sad or disappointed. Be extra empathetic and supportive.',
                'excited': 'User is excited. Match their enthusiasm appropriately while staying professional.',
                'neutral': 'Respond normally with warm, helpful tone.'
            }
        
        return guidance.get(emotion, guidance['neutral'])
    
    def clear_history(self):
        """Clear emotion history."""
        self.emotion_history.clear()
        self.turn_count = 0


# Global emotion detector instance
_emotion_detector = None

def get_emotion_detector() -> EmotionDetector:
    """Get the global emotion detector instance."""
    global _emotion_detector
    if _emotion_detector is None:
        _emotion_detector = EmotionDetector()
    return _emotion_detector

def detect_emotion(text: str, language: str = 'en', use_gpt: bool = False) -> EmotionalTone:
    """Convenience function to detect emotion."""
    detector = get_emotion_detector()
    return detector.detect_emotion(text, language, use_gpt)

def get_emotion_context() -> Dict[str, any]:
    """Convenience function to get emotion context."""
    detector = get_emotion_detector()
    return detector.get_emotion_context()
