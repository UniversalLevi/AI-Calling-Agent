"""
Conversation Memory System
Stores per-call context and conversation history for better responses
"""

import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading

@dataclass
class ConversationExchange:
    """Single exchange in conversation"""
    timestamp: float
    user_text: str
    bot_response: str
    language: str
    confidence: float

@dataclass
class CallContext:
    """Context information for a call"""
    call_sid: str
    start_time: float
    language: str
    user_name: Optional[str] = None
    user_location: Optional[str] = None
    service_type: Optional[str] = None  # hotel, train, restaurant, flight
    preferences: Dict[str, Any] = None
    conversation_history: List[ConversationExchange] = None
    
    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}
        if self.conversation_history is None:
            self.conversation_history = []

class ConversationMemory:
    """Manages conversation memory and context for calls"""
    
    def __init__(self, max_history_per_call: int = 10, ttl_hours: int = 24, 
                 short_term_recall: int = 5, context_fade_threshold: int = 3):
        self.active_calls: Dict[str, CallContext] = {}
        self.max_history_per_call = max_history_per_call
        self.ttl_hours = ttl_hours
        self.short_term_recall = short_term_recall  # Limit recall to recent turns
        self.context_fade_threshold = context_fade_threshold  # Fade older context
        self.lock = threading.Lock()
        
        print(f"🧠 Conversation Memory initialized (max_history: {max_history_per_call}, TTL: {ttl_hours}h, short_term: {short_term_recall})")
    
    def start_call(self, call_sid: str, language: str = 'en') -> CallContext:
        """Start tracking a new call"""
        with self.lock:
            context = CallContext(
                call_sid=call_sid,
                start_time=time.time(),
                language=language
            )
            self.active_calls[call_sid] = context
            print(f"🧠 Started conversation memory for call: {call_sid}")
            return context
    
    def end_call(self, call_sid: str):
        """End tracking for a call"""
        with self.lock:
            if call_sid in self.active_calls:
                del self.active_calls[call_sid]
                print(f"🧠 Ended conversation memory for call: {call_sid}")
    
    def add_exchange(self, call_sid: str, user_text: str, bot_response: str, 
                    language: str, confidence: float = 1.0):
        """Add a conversation exchange to memory"""
        with self.lock:
            if call_sid not in self.active_calls:
                return
            
            context = self.active_calls[call_sid]
            exchange = ConversationExchange(
                timestamp=time.time(),
                user_text=user_text,
                bot_response=bot_response,
                language=language,
                confidence=confidence
            )
            
            context.conversation_history.append(exchange)
            
            # Keep only recent history
            if len(context.conversation_history) > self.max_history_per_call:
                context.conversation_history = context.conversation_history[-self.max_history_per_call:]
            
            print(f"🧠 Added exchange to memory for {call_sid}: {user_text[:30]}...")
    
    def update_context(self, call_sid: str, **kwargs):
        """Update call context information"""
        with self.lock:
            if call_sid not in self.active_calls:
                return
            
            context = self.active_calls[call_sid]
            for key, value in kwargs.items():
                if hasattr(context, key):
                    setattr(context, key, value)
                    print(f"🧠 Updated {key} for {call_sid}: {value}")
    
    def extract_and_store_info(self, call_sid: str, user_text: str):
        """Extract and store information from user text"""
        with self.lock:
            if call_sid not in self.active_calls:
                return
            
            context = self.active_calls[call_sid]
            text_lower = user_text.lower()
            
            # Extract name patterns
            name_patterns = [
                r'my name is (\w+)',
                r'i am (\w+)',
                r'this is (\w+)',
                r'main (\w+) hun',
                r'mera naam (\w+) hai'
            ]
            
            for pattern in name_patterns:
                import re
                match = re.search(pattern, text_lower)
                if match and not context.user_name:
                    context.user_name = match.group(1).title()
                    print(f"🧠 Extracted name: {context.user_name}")
                    break
            
            # Extract location patterns
            locations = ['delhi', 'mumbai', 'bangalore', 'chennai', 'kolkata', 'hyderabad', 
                        'pune', 'jaipur', 'ahmedabad', 'surat', 'udaipur', 'kanpur', 
                        'lucknow', 'varanasi']
            
            for location in locations:
                if location in text_lower and not context.user_location:
                    context.user_location = location.title()
                    print(f"🧠 Extracted location: {context.user_location}")
                    break
            
            # Extract service type
            service_keywords = {
                'hotel': ['hotel', 'room', 'booking', 'stay', 'accommodation'],
                'train': ['train', 'railway', 'ticket', 'journey', 'travel'],
                'restaurant': ['restaurant', 'food', 'dining', 'eat', 'meal'],
                'flight': ['flight', 'airplane', 'airline', 'airport']
            }
            
            for service_type, keywords in service_keywords.items():
                if any(keyword in text_lower for keyword in keywords) and not context.service_type:
                    context.service_type = service_type
                    print(f"🧠 Extracted service type: {service_type}")
                    break
    
    def get_context_summary(self, call_sid: str) -> str:
        """Get a summary of call context for AI with short-term recall and context fade"""
        with self.lock:
            if call_sid not in self.active_calls:
                return ""
            
            context = self.active_calls[call_sid]
            summary_parts = []
            
            # Basic info (always include)
            if context.user_name:
                summary_parts.append(f"User's name: {context.user_name}")
            
            if context.user_location:
                summary_parts.append(f"User's location: {context.user_location}")
            
            if context.service_type:
                summary_parts.append(f"Service type: {context.service_type}")
            
            # Short-term conversation recall (last 3-5 turns only)
            if context.conversation_history:
                recent_exchanges = context.conversation_history[-self.short_term_recall:]
                
                # Apply context fade - older exchanges get less weight
                weighted_topics = []
                for i, exchange in enumerate(recent_exchanges):
                    if len(exchange.user_text) > 10:  # Only meaningful exchanges
                        # Calculate fade weight (recent = 1.0, older = 0.5)
                        fade_weight = 1.0 if i >= len(recent_exchanges) - self.context_fade_threshold else 0.5
                        
                        # Truncate older exchanges more aggressively
                        max_length = 50 if fade_weight == 1.0 else 30
                        topic_text = exchange.user_text[:max_length]
                        
                        if fade_weight == 1.0:
                            weighted_topics.append(topic_text)
                        else:
                            weighted_topics.append(f"[older context] {topic_text}")
                
                if weighted_topics:
                    summary_parts.append(f"Recent conversation: {'; '.join(weighted_topics)}")
            
            return ". ".join(summary_parts) if summary_parts else ""
    
    def get_conversation_history(self, call_sid: str) -> List[ConversationExchange]:
        """Get conversation history for a call"""
        with self.lock:
            if call_sid not in self.active_calls:
                return []
            
            return self.active_calls[call_sid].conversation_history.copy()
    
    def get_recent_conversation_history(self, call_sid: str) -> List[ConversationExchange]:
        """Get only recent conversation history (last 3-5 turns) for AI processing"""
        with self.lock:
            if call_sid not in self.active_calls:
                return []
            
            context = self.active_calls[call_sid]
            recent_history = context.conversation_history[-self.short_term_recall:]
            
            # Apply context fade to older exchanges
            faded_history = []
            for i, exchange in enumerate(recent_history):
                # Create a copy with faded content
                faded_exchange = ConversationExchange(
                    timestamp=exchange.timestamp,
                    user_text=exchange.user_text,
                    bot_response=exchange.bot_response,
                    language=exchange.language,
                    confidence=exchange.confidence
                )
                
                # Fade older exchanges by truncating them
                if i < len(recent_history) - self.context_fade_threshold:
                    faded_exchange.user_text = exchange.user_text[:30] + "..." if len(exchange.user_text) > 30 else exchange.user_text
                    faded_exchange.bot_response = exchange.bot_response[:30] + "..." if len(exchange.bot_response) > 30 else exchange.bot_response
                
                faded_history.append(faded_exchange)
            
            return faded_history
    
    def store_neutral_facts(self, call_sid: str, user_text: str):
        """Store only neutral, factual information to avoid overfitting"""
        with self.lock:
            if call_sid not in self.active_calls:
                return
            
            context = self.active_calls[call_sid]
            text_lower = user_text.lower()
            
            # Only store neutral facts, not emotional or subjective content
            neutral_patterns = {
                'name': [r'my name is (\w+)', r'i am (\w+)', r'this is (\w+)', r'main (\w+) hun', r'mera naam (\w+) hai'],
                'location': [r'i am from (\w+)', r'i live in (\w+)', r'mera sheher (\w+) hai'],
                'phone': [r'my number is (\d+)', r'phone number (\d+)', r'mera number (\d+) hai'],
                'email': [r'my email is (\S+@\S+)', r'email (\S+@\S+)', r'mera email (\S+@\S+) hai']
            }
            
            for fact_type, patterns in neutral_patterns.items():
                for pattern in patterns:
                    import re
                    match = re.search(pattern, text_lower)
                    if match:
                        fact_value = match.group(1)
                        
                        # Store in preferences with fact type
                        if fact_type not in context.preferences:
                            context.preferences[fact_type] = fact_value
                            print(f"🧠 Stored neutral fact ({fact_type}): {fact_value}")
                        break
    
    def get_neutral_context(self, call_sid: str) -> str:
        """Get only neutral, factual context for AI (avoids emotional overfitting)"""
        with self.lock:
            if call_sid not in self.active_calls:
                return ""
            
            context = self.active_calls[call_sid]
            neutral_parts = []
            
            # Only include neutral facts
            if context.user_name:
                neutral_parts.append(f"User's name: {context.user_name}")
            
            if context.user_location:
                neutral_parts.append(f"User's location: {context.user_location}")
            
            if context.service_type:
                neutral_parts.append(f"Service type: {context.service_type}")
            
            # Include stored neutral facts from preferences
            if 'name' in context.preferences:
                neutral_parts.append(f"User's name: {context.preferences['name']}")
            
            if 'location' in context.preferences:
                neutral_parts.append(f"User's location: {context.preferences['location']}")
            
            if 'phone' in context.preferences:
                neutral_parts.append(f"User's phone: {context.preferences['phone']}")
            
            if 'email' in context.preferences:
                neutral_parts.append(f"User's email: {context.preferences['email']}")
            return ". ".join(neutral_parts) if neutral_parts else ""
    
    def get_call_context(self, call_sid: str) -> Optional[CallContext]:
        """Get full call context"""
        with self.lock:
            return self.active_calls.get(call_sid)
    
    def cleanup_expired_calls(self):
        """Clean up expired calls based on TTL"""
        with self.lock:
            current_time = time.time()
            expired_calls = []
            
            for call_sid, context in self.active_calls.items():
                if current_time - context.start_time > (self.ttl_hours * 3600):
                    expired_calls.append(call_sid)
            
            for call_sid in expired_calls:
                del self.active_calls[call_sid]
                print(f"🧠 Cleaned up expired call: {call_sid}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        with self.lock:
            total_exchanges = sum(
                len(context.conversation_history) 
                for context in self.active_calls.values()
            )
            
            return {
                "active_calls": len(self.active_calls),
                "total_exchanges": total_exchanges,
                "max_history_per_call": self.max_history_per_call,
                "ttl_hours": self.ttl_hours
            }


# Global memory instance
_conversation_memory = None

def get_conversation_memory() -> ConversationMemory:
    """Get global conversation memory instance"""
    global _conversation_memory
    if _conversation_memory is None:
        _conversation_memory = ConversationMemory()
    return _conversation_memory

def start_call_memory(call_sid: str, language: str = 'en') -> CallContext:
    """Start tracking a new call"""
    memory = get_conversation_memory()
    return memory.start_call(call_sid, language)

def end_call_memory(call_sid: str):
    """End tracking for a call"""
    memory = get_conversation_memory()
    memory.end_call(call_sid)

def add_conversation_exchange(call_sid: str, user_text: str, bot_response: str, 
                            language: str, confidence: float = 1.0):
    """Add a conversation exchange to memory"""
    memory = get_conversation_memory()
    memory.add_exchange(call_sid, user_text, bot_response, language, confidence)

def update_call_context(call_sid: str, **kwargs):
    """Update call context information"""
    memory = get_conversation_memory()
    memory.update_context(call_sid, **kwargs)

def extract_and_store_info(call_sid: str, user_text: str):
    """Extract and store information from user text"""
    memory = get_conversation_memory()
    memory.extract_and_store_info(call_sid, user_text)

def get_context_summary(call_sid: str) -> str:
    """Get a summary of call context for AI"""
    memory = get_conversation_memory()
    return memory.get_context_summary(call_sid)

def get_recent_conversation_history(call_sid: str) -> List[ConversationExchange]:
    """Get only recent conversation history (last 3-5 turns) for AI processing"""
    memory = get_conversation_memory()
    return memory.get_recent_conversation_history(call_sid)

def store_neutral_facts(call_sid: str, user_text: str):
    """Store only neutral, factual information to avoid overfitting"""
    memory = get_conversation_memory()
    memory.store_neutral_facts(call_sid, user_text)

def get_neutral_context(call_sid: str) -> str:
    """Get only neutral, factual context for AI (avoids emotional overfitting)"""
    memory = get_conversation_memory()
    return memory.get_neutral_context(call_sid)
