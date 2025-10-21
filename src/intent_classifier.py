"""
Intent Classification System
Classifies user input into different intent categories for AIDA stage transitions
"""

import os
import json
from typing import Dict, List, Tuple, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class IntentType(Enum):
    """Intent categories for user input classification"""
    POSITIVE = "positive"      # Shows interest, curiosity
    NEGATIVE = "negative"      # Rejection, not interested
    INQUIRY = "inquiry"        # Asking questions
    AGREEMENT = "agreement"    # Ready to proceed
    OBJECTION = "objection"    # Concern about price, timing, etc.
    NEUTRAL = "neutral"        # Non-committal, unsure
    GREETING = "greeting"      # Hello, hi, etc.
    GOODBYE = "goodbye"        # Bye, thank you, etc.

class IntentClassifier:
    """
    Classifies user input into intent categories using LLM-based analysis
    """
    
    def __init__(self):
        self.openai_client = None
        self._init_openai()
        
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OPENAI_API_KEY not found, using fallback classification")
                return
                
            self.openai_client = OpenAI(api_key=api_key)
            logger.info("✅ Intent classifier initialized with OpenAI")
        except Exception as e:
            logger.warning(f"⚠️ OpenAI not available for intent classification: {e}")
    
    def classify_intent(self, user_input: str, conversation_history: List[Dict] = None) -> Tuple[IntentType, float]:
        """
        Classify user input into intent categories
        
        Args:
            user_input: The user's speech input
            conversation_history: Previous conversation context
            
        Returns:
            Tuple of (IntentType, confidence_score)
        """
        if not user_input or not user_input.strip():
            return IntentType.NEUTRAL, 0.5
            
        user_input = user_input.strip().lower()
        
        # First try rule-based classification for common patterns
        rule_based_intent, rule_confidence = self._rule_based_classification(user_input)
        
        # If we have OpenAI available, use LLM for more sophisticated classification
        if self.openai_client:
            try:
                llm_intent, llm_confidence = self._llm_classification(user_input, conversation_history)
                
                # Combine rule-based and LLM results
                if rule_confidence > 0.8:  # High confidence rule-based
                    return rule_based_intent, rule_confidence
                elif llm_confidence > 0.7:  # High confidence LLM
                    return llm_intent, llm_confidence
                else:
                    # Use rule-based as fallback
                    return rule_based_intent, max(rule_confidence, 0.6)
                    
            except Exception as e:
                logger.warning(f"⚠️ LLM classification failed: {e}")
                return rule_based_intent, rule_confidence
        else:
            return rule_based_intent, rule_confidence
    
    def _rule_based_classification(self, user_input: str) -> Tuple[IntentType, float]:
        """Rule-based intent classification using keyword patterns"""
        
        # Greeting patterns
        greeting_patterns = [
            'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
            'namaste', 'namaskar', 'salam', 'hi there', 'hey there'
        ]
        
        # Goodbye patterns
        goodbye_patterns = [
            'bye', 'goodbye', 'see you', 'thank you', 'thanks', 'take care',
            'have a good day', 'talk to you later', 'catch you later',
            'dhanyawad', 'shukriya', 'alvida'
        ]
        
        # Positive/Interest patterns
        positive_patterns = [
            'yes', 'yeah', 'yep', 'sure', 'okay', 'ok', 'alright', 'good',
            'interesting', 'tell me more', 'sounds good', 'i like', 'i want',
            'i need', 'i am interested', 'sounds interesting', 'that sounds good',
            'haan', 'bilkul', 'theek hai', 'achha', 'pasand hai'
        ]
        
        # Negative patterns
        negative_patterns = [
            'no', 'nope', 'not interested', 'not now', 'not today', 'maybe later',
            'i don\'t want', 'i don\'t need', 'not for me', 'not interested',
            'nahi', 'nahi chahiye', 'pasand nahi', 'interest nahi hai'
        ]
        
        # Inquiry patterns
        inquiry_patterns = [
            'what', 'how', 'when', 'where', 'why', 'who', 'which', 'can you',
            'could you', 'would you', 'tell me', 'explain', 'describe',
            'kya', 'kaise', 'kab', 'kahan', 'kyun', 'kaun', 'konsa'
        ]
        
        # Agreement patterns
        agreement_patterns = [
            'i agree', 'that\'s right', 'exactly', 'absolutely', 'definitely',
            'i think so', 'you\'re right', 'correct', 'true', 'yes, i want',
            'sahi hai', 'bilkul sahi', 'theek hai', 'haan chahiye'
        ]
        
        # Objection patterns
        objection_patterns = [
            'expensive', 'cost', 'price', 'budget', 'money', 'afford',
            'too much', 'too expensive', 'can\'t afford', 'not in budget',
            'time', 'busy', 'not now', 'later', 'maybe', 'not sure',
            'mahanga', 'paisa', 'budget nahi hai', 'time nahi hai'
        ]
        
        # Check patterns
        if any(pattern in user_input for pattern in greeting_patterns):
            return IntentType.GREETING, 0.9
            
        if any(pattern in user_input for pattern in goodbye_patterns):
            return IntentType.GOODBYE, 0.9
            
        if any(pattern in user_input for pattern in positive_patterns):
            return IntentType.POSITIVE, 0.8
            
        if any(pattern in user_input for pattern in negative_patterns):
            return IntentType.NEGATIVE, 0.8
            
        if any(pattern in user_input for pattern in inquiry_patterns):
            return IntentType.INQUIRY, 0.7
            
        if any(pattern in user_input for pattern in agreement_patterns):
            return IntentType.AGREEMENT, 0.8
            
        if any(pattern in user_input for pattern in objection_patterns):
            return IntentType.OBJECTION, 0.7
            
        # Default to neutral
        return IntentType.NEUTRAL, 0.5
    
    def _llm_classification(self, user_input: str, conversation_history: List[Dict] = None) -> Tuple[IntentType, float]:
        """Use LLM for sophisticated intent classification"""
        
        # Build context from conversation history
        context = ""
        if conversation_history:
            recent_messages = conversation_history[-3:]  # Last 3 messages
            context = "Recent conversation:\n"
            for msg in recent_messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                context += f"{role}: {content}\n"
        
        prompt = f"""Classify the user's intent from their input. Consider the conversation context.

{context}

User input: "{user_input}"

Intent categories:
- positive: Shows interest, curiosity, wants to know more
- negative: Rejection, not interested, declining
- inquiry: Asking questions, seeking information
- agreement: Ready to proceed, accepting offer
- objection: Concern about price, timing, or other barriers
- neutral: Non-committal, unsure, neutral response
- greeting: Hello, hi, greetings
- goodbye: Bye, thank you, ending conversation

Respond with only the intent category and confidence (0.0-1.0) in this format:
intent: [category]
confidence: [score]"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse the response
            lines = result.split('\n')
            intent_str = "neutral"
            confidence = 0.5
            
            for line in lines:
                if line.startswith('intent:'):
                    intent_str = line.split(':', 1)[1].strip()
                elif line.startswith('confidence:'):
                    try:
                        confidence = float(line.split(':', 1)[1].strip())
                    except ValueError:
                        confidence = 0.5
            
            # Convert string to IntentType
            try:
                intent = IntentType(intent_str)
            except ValueError:
                intent = IntentType.NEUTRAL
                
            return intent, confidence
            
        except Exception as e:
            logger.warning(f"⚠️ LLM classification error: {e}")
            return IntentType.NEUTRAL, 0.5
    
    def detect_objection_type(self, user_input: str) -> Optional[str]:
        """
        Detect specific type of objection
        
        Returns:
            Objection type: 'price', 'timing', 'authority', 'need', 'competition', or None
        """
        user_input = user_input.lower()
        
        # Price objections
        price_keywords = [
            'expensive', 'cost', 'price', 'budget', 'money', 'afford',
            'too much', 'too expensive', 'can\'t afford', 'not in budget',
            'mahanga', 'paisa', 'budget nahi hai', 'expensive hai'
        ]
        
        # Timing objections
        timing_keywords = [
            'time', 'busy', 'not now', 'later', 'maybe', 'not sure',
            'time nahi hai', 'busy hai', 'baad mein', 'abhi nahi'
        ]
        
        # Authority objections
        authority_keywords = [
            'boss', 'manager', 'decision', 'approval', 'permission',
            'boss se puchna hai', 'manager se baat karni hai'
        ]
        
        # Need objections
        need_keywords = [
            'don\'t need', 'not needed', 'already have', 'not required',
            'jarurat nahi hai', 'already hai', 'chahiye nahi'
        ]
        
        # Competition objections
        competition_keywords = [
            'competitor', 'other company', 'different option', 'alternative',
            'dusri company', 'alternative option'
        ]
        
        if any(keyword in user_input for keyword in price_keywords):
            return 'price'
        elif any(keyword in user_input for keyword in timing_keywords):
            return 'timing'
        elif any(keyword in user_input for keyword in authority_keywords):
            return 'authority'
        elif any(keyword in user_input for keyword in need_keywords):
            return 'need'
        elif any(keyword in user_input for keyword in competition_keywords):
            return 'competition'
        
        return None
    
    def get_intent_confidence(self) -> float:
        """Get the confidence score from the last classification"""
        return getattr(self, '_last_confidence', 0.5)
    
    def should_transition_stage(self, current_intent: IntentType, current_stage: str) -> bool:
        """
        Determine if stage transition should occur based on intent
        
        Args:
            current_intent: The classified intent
            current_stage: Current AIDA stage
            
        Returns:
            True if stage should transition
        """
        # Define transition rules based on current stage and intent
        transition_rules = {
            'ATTENTION': {
                IntentType.POSITIVE: True,      # Move to INTEREST
                IntentType.INQUIRY: True,       # Move to INTEREST
                IntentType.NEGATIVE: False,     # Stay and handle objection
                IntentType.GOODBYE: False,      # End conversation
            },
            'INTEREST': {
                IntentType.POSITIVE: True,      # Move to DESIRE
                IntentType.AGREEMENT: True,     # Move to DESIRE
                IntentType.INQUIRY: False,      # Stay and answer questions
                IntentType.OBJECTION: False,   # Stay and handle objection
                IntentType.NEGATIVE: False,     # Stay and handle objection
            },
            'DESIRE': {
                IntentType.AGREEMENT: True,     # Move to ACTION
                IntentType.POSITIVE: True,      # Move to ACTION
                IntentType.OBJECTION: False,    # Stay and handle objection
                IntentType.INQUIRY: False,      # Stay and answer questions
            },
            'ACTION': {
                IntentType.AGREEMENT: False,    # Close the sale
                IntentType.OBJECTION: False,    # Handle final objections
                IntentType.NEGATIVE: False,     # Handle rejection
            }
        }
        
        stage_rules = transition_rules.get(current_stage, {})
        return stage_rules.get(current_intent, False)

