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
    
    def __init__(self, max_history_per_call: int = 10, ttl_hours: int = 24):
        self.active_calls: Dict[str, CallContext] = {}
        self.max_history_per_call = max_history_per_call
        self.ttl_hours = ttl_hours
        self.lock = threading.Lock()
        
        print(f"🧠 Conversation Memory initialized (max_history: {max_history_per_call}, TTL: {ttl_hours}h)")
    
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
        """Get a summary of call context for AI"""
        with self.lock:
            if call_sid not in self.active_calls:
                return ""
            
            context = self.active_calls[call_sid]
            summary_parts = []
            
            # Basic info
            if context.user_name:
                summary_parts.append(f"User's name: {context.user_name}")
            
            if context.user_location:
                summary_parts.append(f"User's location: {context.user_location}")
            
            if context.service_type:
                summary_parts.append(f"Service type: {context.service_type}")
            
            # Recent conversation topics
            if context.conversation_history:
                recent_topics = []
                for exchange in context.conversation_history[-3:]:  # Last 3 exchanges
                    if len(exchange.user_text) > 10:  # Only meaningful exchanges
                        recent_topics.append(exchange.user_text[:50])
                
                if recent_topics:
                    summary_parts.append(f"Recent topics: {'; '.join(recent_topics)}")
            
            return ". ".join(summary_parts) if summary_parts else ""
    
    def get_conversation_history(self, call_sid: str) -> List[ConversationExchange]:
        """Get conversation history for a call"""
        with self.lock:
            if call_sid not in self.active_calls:
                return []
            
            return self.active_calls[call_sid].conversation_history.copy()
    
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
