"""
AIDA Context Manager
Manages conversation state and stage transitions for the AIDA sales framework
"""

import os
import json
import time
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
import logging

from .intent_classifier import IntentClassifier, IntentType

logger = logging.getLogger(__name__)

class AIDAStage(Enum):
    """AIDA sales stages"""
    ATTENTION = "attention"
    INTEREST = "interest"
    DESIRE = "desire"
    ACTION = "action"

class AidaContextManager:
    """
    Manages AIDA sales conversation context and stage transitions
    """
    
    def __init__(self, call_id: str, product_data: Dict = None):
        self.call_id = call_id
        self.product_data = product_data or {}
        
        # AIDA state
        self.current_stage = AIDAStage.ATTENTION
        self.stage_history = []
        self.conversation_history = []
        
        # Intent tracking
        self.intent_classifier = IntentClassifier()
        self.last_intent = IntentType.NEUTRAL
        self.intent_history = []
        
        # Stage timing
        self.stage_start_time = time.time()
        self.stage_durations = {}
        
        # Objection tracking
        self.objections_raised = []
        self.objection_responses_given = []
        
        # Context data
        self.user_preferences = {}
        self.user_concerns = []
        self.user_agreements = []
        
        logger.info(f"🎯 AIDA Context Manager initialized for call {call_id}")
        logger.info(f"📦 Product: {self.product_data.get('product_name', 'Unknown')}")
    
    def analyze_user_intent(self, user_input: str) -> Tuple[IntentType, float]:
        """
        Analyze user input and classify intent
        
        Args:
            user_input: User's speech input
            
        Returns:
            Tuple of (IntentType, confidence)
        """
        intent, confidence = self.intent_classifier.classify_intent(
            user_input, 
            self.conversation_history
        )
        
        self.last_intent = intent
        self.intent_history.append({
            'intent': intent.value,
            'confidence': confidence,
            'timestamp': time.time(),
            'input': user_input
        })
        
        logger.info(f"🧠 Intent classified: {intent.value} (confidence: {confidence:.2f})")
        
        return intent, confidence
    
    def should_transition_stage(self, intent: IntentType) -> bool:
        """
        Determine if stage transition should occur
        
        Args:
            intent: Current user intent
            
        Returns:
            True if stage should transition
        """
        return self.intent_classifier.should_transition_stage(intent, self.current_stage.value)
    
    def transition_to_stage(self, new_stage: AIDAStage, reason: str = ""):
        """
        Transition to a new AIDA stage
        
        Args:
            new_stage: Target AIDA stage
            reason: Reason for transition
        """
        if new_stage == self.current_stage:
            return
            
        # Record stage duration
        duration = time.time() - self.stage_start_time
        self.stage_durations[self.current_stage.value] = duration
        
        # Add to stage history
        self.stage_history.append({
            'from_stage': self.current_stage.value,
            'to_stage': new_stage.value,
            'reason': reason,
            'timestamp': time.time(),
            'duration': duration
        })
        
        # Update current stage
        old_stage = self.current_stage
        self.current_stage = new_stage
        self.stage_start_time = time.time()
        
        logger.info(f"🔄 Stage transition: {old_stage.value} → {new_stage.value}")
        logger.info(f"📝 Reason: {reason}")
        logger.info(f"⏱️ Duration in {old_stage.value}: {duration:.1f}s")
    
    def get_current_stage(self) -> AIDAStage:
        """Get current AIDA stage"""
        return self.current_stage
    
    def get_stage_context(self) -> Dict:
        """
        Get context information for current stage
        
        Returns:
            Dictionary with stage-specific context
        """
        context = {
            'current_stage': self.current_stage.value,
            'stage_duration': time.time() - self.stage_start_time,
            'stage_history': self.stage_history,
            'last_intent': self.last_intent.value,
            'intent_history': self.intent_history[-5:],  # Last 5 intents
            'objections_raised': self.objections_raised,
            'user_preferences': self.user_preferences,
            'user_concerns': self.user_concerns,
            'user_agreements': self.user_agreements,
            'product_data': self.product_data
        }
        
        return context
    
    def generate_response_context(self) -> Dict:
        """
        Generate context for AI response generation
        
        Returns:
            Dictionary with response context
        """
        stage_context = self.get_stage_context()
        
        # Add stage-specific guidance
        stage_guidance = self._get_stage_guidance()
        
        response_context = {
            **stage_context,
            'stage_guidance': stage_guidance,
            'conversation_summary': self._get_conversation_summary(),
            'next_actions': self._get_suggested_actions()
        }
        
        return response_context
    
    def _get_stage_guidance(self) -> Dict:
        """Get guidance for current stage"""
        guidance = {
            AIDAStage.ATTENTION: {
                'goal': 'Capture attention and create interest',
                'tone': 'Energetic, friendly, or trust-based',
                'focus': 'Hook with value proposition',
                'avoid': 'Long explanations or technical details'
            },
            AIDAStage.INTEREST: {
                'goal': 'Build curiosity and uncover relevance',
                'tone': 'Conversational and inquisitive',
                'focus': 'Ask open-ended questions about needs',
                'avoid': 'Pushing for immediate decisions'
            },
            AIDAStage.DESIRE: {
                'goal': 'Create emotional or logical desire',
                'tone': 'Confident, reassuring, persuasive',
                'focus': 'Benefits and emotional connection',
                'avoid': 'Being too aggressive or pushy'
            },
            AIDAStage.ACTION: {
                'goal': 'Convert or get commitment',
                'tone': 'Direct but friendly',
                'focus': 'Clear next steps and urgency',
                'avoid': 'Being vague about next steps'
            }
        }
        
        return guidance.get(self.current_stage, {})
    
    def _get_conversation_summary(self) -> str:
        """Generate a summary of the conversation so far"""
        if not self.conversation_history:
            return "Conversation just started"
        
        # Count interactions by stage
        stage_counts = {}
        for entry in self.stage_history:
            stage = entry['to_stage']
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
        
        summary = f"Currently in {self.current_stage.value} stage. "
        summary += f"User has shown {self.last_intent.value} intent. "
        
        if self.objections_raised:
            summary += f"Objections raised: {', '.join(self.objections_raised)}. "
        
        if self.user_preferences:
            summary += f"User preferences noted: {', '.join(self.user_preferences.keys())}. "
        
        return summary
    
    def _get_suggested_actions(self) -> List[str]:
        """Get suggested actions for current stage"""
        actions = []
        
        if self.current_stage == AIDAStage.ATTENTION:
            actions.extend([
                'Use attention-grabbing hook from product data',
                'Introduce brand and value proposition',
                'Ask engaging question to gauge interest'
            ])
            
        elif self.current_stage == AIDAStage.INTEREST:
            actions.extend([
                'Ask about current situation or needs',
                'Listen for pain points or challenges',
                'Build rapport and trust'
            ])
            
        elif self.current_stage == AIDAStage.DESIRE:
            actions.extend([
                'Connect benefits to user needs',
                'Use emotional language and storytelling',
                'Address concerns and objections'
            ])
            
        elif self.current_stage == AIDAStage.ACTION:
            actions.extend([
                'Present clear call-to-action',
                'Create urgency or scarcity',
                'Handle final objections'
            ])
        
        return actions
    
    def record_objection(self, objection_type: str, user_input: str):
        """Record an objection raised by the user"""
        objection = {
            'type': objection_type,
            'input': user_input,
            'timestamp': time.time(),
            'stage': self.current_stage.value
        }
        
        self.objections_raised.append(objection)
        logger.info(f"🚫 Objection recorded: {objection_type}")
    
    def record_user_preference(self, key: str, value: str):
        """Record user preference or information"""
        self.user_preferences[key] = value
        logger.info(f"👤 User preference recorded: {key} = {value}")
    
    def record_user_concern(self, concern: str):
        """Record user concern"""
        if concern not in self.user_concerns:
            self.user_concerns.append(concern)
            logger.info(f"⚠️ User concern recorded: {concern}")
    
    def record_user_agreement(self, agreement: str):
        """Record user agreement or positive response"""
        if agreement not in self.user_agreements:
            self.user_agreements.append(agreement)
            logger.info(f"✅ User agreement recorded: {agreement}")
    
    def add_conversation_entry(self, role: str, content: str):
        """Add entry to conversation history"""
        entry = {
            'role': role,
            'content': content,
            'timestamp': time.time(),
            'stage': self.current_stage.value
        }
        
        self.conversation_history.append(entry)
        
        # Keep only last 20 entries to prevent memory bloat
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def get_conversation_summary(self) -> Dict:
        """Get comprehensive conversation summary"""
        return {
            'call_id': self.call_id,
            'current_stage': self.current_stage.value,
            'stage_duration': time.time() - self.stage_start_time,
            'total_duration': sum(self.stage_durations.values()) + (time.time() - self.stage_start_time),
            'stage_history': self.stage_history,
            'stage_durations': self.stage_durations,
            'intent_history': self.intent_history,
            'objections_raised': self.objections_raised,
            'user_preferences': self.user_preferences,
            'user_concerns': self.user_concerns,
            'user_agreements': self.user_agreements,
            'conversation_length': len(self.conversation_history),
            'product_data': self.product_data
        }
    
    def should_end_conversation(self) -> bool:
        """Determine if conversation should end"""
        # End if user says goodbye
        if self.last_intent == IntentType.GOODBYE:
            return True
        
        # End if too many objections without resolution
        if len(self.objections_raised) >= 3:
            return True
        
        # End if conversation is too long (more than 10 minutes)
        total_duration = sum(self.stage_durations.values()) + (time.time() - self.stage_start_time)
        if total_duration > 600:  # 10 minutes
            return True
        
        return False
    
    def get_stage_progress(self) -> Dict:
        """Get progress through AIDA stages"""
        stage_order = [AIDAStage.ATTENTION, AIDAStage.INTEREST, AIDAStage.DESIRE, AIDAStage.ACTION]
        current_index = stage_order.index(self.current_stage)
        
        return {
            'current_stage': self.current_stage.value,
            'stage_index': current_index,
            'total_stages': len(stage_order),
            'progress_percentage': (current_index / (len(stage_order) - 1)) * 100,
            'stages_completed': [stage.value for stage in stage_order[:current_index]],
            'remaining_stages': [stage.value for stage in stage_order[current_index + 1:]]
        }

