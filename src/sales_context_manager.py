"""
Sales Context Manager - Conversation State and Funnel Progression
===============================================================

This module manages conversation state, sales funnel progression, and BANT tracking
for the sales AI system.
"""

import time
from typing import Dict, List, Optional, Tuple
from enum import Enum


class ConversationStage(Enum):
    """Conversation stages in sales funnel"""
    GREETING = "greeting"
    QUALIFICATION = "qualification"
    PRESENTATION = "presentation"
    OBJECTION = "objection"
    CLOSING = "closing"
    CONVERTED = "converted"
    LOST = "lost"


class SalesContextManager:
    """Manages sales conversation context and funnel progression"""
    
    def __init__(self, call_id: str, product_id: str):
        self.call_id = call_id
        self.product_id = product_id
        self.current_stage = ConversationStage.GREETING
        self.stage_history = []
        self.stage_timings = {}
        self.bant_data = {
            'budget': {'score': 0, 'notes': '', 'amount': None, 'timeframe': None},
            'authority': {'score': 0, 'notes': '', 'decision_maker': False, 'influence_level': 'unknown'},
            'need': {'score': 0, 'notes': '', 'pain_points': [], 'urgency_level': 'medium'},
            'timeline': {'score': 0, 'notes': '', 'decision_date': None, 'urgency': 'flexible'}
        }
        self.conversation_context = {
            'questions_asked': [],
            'objections_encountered': [],
            'buying_signals': [],
            'urgency_indicators': [],
            'competitor_mentions': []
        }
        self.call_start_time = time.time()
        self.last_activity_time = time.time()
        
        # Initialize stage timing
        self._start_stage_timing(ConversationStage.GREETING)
        
        print(f"🎯 Sales Context Manager initialized for call: {call_id}")
    
    def update_stage(self, new_stage: ConversationStage, reason: str = ""):
        """Update conversation stage with timing"""
        if new_stage != self.current_stage:
            # End timing for current stage
            self._end_stage_timing(self.current_stage)
            
            # Update stage
            old_stage = self.current_stage
            self.current_stage = new_stage
            
            # Start timing for new stage
            self._start_stage_timing(new_stage)
            
            # Record stage transition
            self.stage_history.append({
                'from_stage': old_stage.value,
                'to_stage': new_stage.value,
                'timestamp': time.time(),
                'reason': reason,
                'duration': self.stage_timings.get(old_stage.value, {}).get('duration', 0)
            })
            
            print(f"🔄 Stage transition: {old_stage.value} → {new_stage.value} ({reason})")
    
    def _start_stage_timing(self, stage: ConversationStage):
        """Start timing for a stage"""
        self.stage_timings[stage.value] = {
            'start_time': time.time(),
            'end_time': None,
            'duration': 0
        }
    
    def _end_stage_timing(self, stage: ConversationStage):
        """End timing for a stage"""
        if stage.value in self.stage_timings:
            end_time = time.time()
            start_time = self.stage_timings[stage.value]['start_time']
            duration = end_time - start_time
            
            self.stage_timings[stage.value].update({
                'end_time': end_time,
                'duration': duration
            })
    
    def analyze_user_input(self, user_input: str) -> Dict:
        """Analyze user input for sales context"""
        user_lower = user_input.lower()
        
        analysis = {
            'stage_triggers': self._detect_stage_triggers(user_lower),
            'bant_signals': self._detect_bant_signals(user_lower),
            'objections': self._detect_objections(user_lower),
            'buying_signals': self._detect_buying_signals(user_lower),
            'urgency_level': self._detect_urgency_level(user_lower),
            'sentiment': self._analyze_sentiment(user_input)
        }
        
        # Update conversation context
        self._update_conversation_context(analysis, user_input)
        
        return analysis
    
    def _detect_stage_triggers(self, user_lower: str) -> List[str]:
        """Detect triggers for stage transitions"""
        triggers = []
        
        # Qualification triggers
        if any(word in user_lower for word in ['budget', 'price', 'cost', 'decision', 'manager', 'boss']):
            triggers.append('qualification')
        
        # Presentation triggers
        if any(word in user_lower for word in ['tell me more', 'explain', 'how does it work', 'features']):
            triggers.append('presentation')
        
        # Objection triggers
        if any(word in user_lower for word in ['expensive', 'costly', 'think', 'later', 'busy', 'not sure']):
            triggers.append('objection')
        
        # Closing triggers
        if any(word in user_lower for word in ['yes', 'okay', 'book', 'interested', 'sounds good']):
            triggers.append('closing')
        
        return triggers
    
    def _detect_bant_signals(self, user_lower: str) -> Dict:
        """Detect BANT qualification signals"""
        signals = {'budget': [], 'authority': [], 'need': [], 'timeline': []}
        
        # Budget signals
        budget_keywords = ['budget', 'price', 'cost', 'afford', 'expensive', 'cheap', 'paisa', 'budget']
        signals['budget'] = [word for word in budget_keywords if word in user_lower]
        
        # Authority signals
        authority_keywords = ['decision', 'manager', 'boss', 'approve', 'permission', 'boss', 'manager']
        signals['authority'] = [word for word in authority_keywords if word in user_lower]
        
        # Need signals
        need_keywords = ['need', 'want', 'require', 'problem', 'issue', 'challenge', 'zaroorat', 'chahiye']
        signals['need'] = [word for word in need_keywords if word in user_lower]
        
        # Timeline signals
        timeline_keywords = ['when', 'timeline', 'schedule', 'urgent', 'immediate', 'soon', 'jaldi', 'urgent']
        signals['timeline'] = [word for word in timeline_keywords if word in user_lower]
        
        return signals
    
    def _detect_objections(self, user_lower: str) -> List[str]:
        """Detect objections in user input"""
        objections = []
        
        objection_patterns = {
            'price': ['expensive', 'cost', 'price', 'budget', 'mahanga', 'paisa', 'costly'],
            'timing': ['later', 'think', 'decide', 'busy', 'baad mein', 'soch', 'time'],
            'competition': ['already have', 'other company', 'competitor', 'pehle se', 'dusra'],
            'trust': ['trust', 'believe', 'sure', 'bharosa', 'yakeen', 'reliable'],
            'authority': ['boss', 'manager', 'decision', 'approve', 'boss', 'manager'],
            'need': ['need', 'want', 'require', 'zaroorat', 'chahiye', 'important']
        }
        
        for objection_type, keywords in objection_patterns.items():
            if any(keyword in user_lower for keyword in keywords):
                objections.append(objection_type)
        
        return objections
    
    def _detect_buying_signals(self, user_lower: str) -> List[str]:
        """Detect buying signals in user input"""
        buying_signals = []
        
        signal_keywords = [
            'yes', 'okay', 'book', 'interested', 'sounds good', 'tell me more',
            'haan', 'theek hai', 'book karo', 'interested', 'aur batao', 'good'
        ]
        
        for signal in signal_keywords:
            if signal in user_lower:
                buying_signals.append(signal)
        
        return buying_signals
    
    def _detect_urgency_level(self, user_lower: str) -> str:
        """Detect urgency level"""
        urgent_keywords = ['urgent', 'immediate', 'asap', 'quick', 'fast', 'jaldi', 'urgent']
        if any(keyword in user_lower for keyword in urgent_keywords):
            return 'high'
        
        moderate_keywords = ['soon', 'this week', 'month', 'jaldi', 'jald']
        if any(keyword in user_lower for keyword in moderate_keywords):
            return 'medium'
        
        return 'low'
    
    def _analyze_sentiment(self, user_input: str) -> float:
        """Analyze sentiment of user input"""
        positive_keywords = ['good', 'great', 'excellent', 'amazing', 'perfect', 'love',
                           'achha', 'badhiya', 'perfect', 'excellent', 'nice']
        negative_keywords = ['bad', 'terrible', 'awful', 'hate', 'disappointed', 'angry',
                           'bura', 'kharab', 'hate', 'disappointed', 'not good']
        
        user_lower = user_input.lower()
        positive_count = sum(1 for word in positive_keywords if word in user_lower)
        negative_count = sum(1 for word in negative_keywords if word in user_lower)
        
        if positive_count > negative_count:
            return 0.5
        elif negative_count > positive_count:
            return -0.5
        else:
            return 0.0
    
    def _update_conversation_context(self, analysis: Dict, user_input: str):
        """Update conversation context with analysis results"""
        # Update questions asked
        if '?' in user_input:
            self.conversation_context['questions_asked'].append({
                'question': user_input,
                'timestamp': time.time()
            })
        
        # Update objections encountered
        for objection in analysis['objections']:
            if objection not in [obj['type'] for obj in self.conversation_context['objections_encountered']]:
                self.conversation_context['objections_encountered'].append({
                    'type': objection,
                    'timestamp': time.time(),
                    'resolved': False
                })
        
        # Update buying signals
        for signal in analysis['buying_signals']:
            self.conversation_context['buying_signals'].append({
                'signal': signal,
                'timestamp': time.time()
            })
        
        # Update urgency indicators
        if analysis['urgency_level'] != 'low':
            self.conversation_context['urgency_indicators'].append({
                'level': analysis['urgency_level'],
                'timestamp': time.time()
            })
        
        self.last_activity_time = time.time()
    
    def update_bant_score(self, bant_type: str, score: int, notes: str = ""):
        """Update BANT score for specific type"""
        if bant_type in self.bant_data:
            self.bant_data[bant_type]['score'] = score
            if notes:
                self.bant_data[bant_type]['notes'] = notes
            
            print(f"📊 Updated {bant_type} score: {score}")
    
    def get_bant_score(self) -> int:
        """Get total BANT score"""
        return sum(data['score'] for data in self.bant_data.values())
    
    def is_qualified(self, threshold: int = 20) -> bool:
        """Check if lead is qualified based on BANT score"""
        return self.get_bant_score() >= threshold
    
    def get_next_action(self) -> Dict:
        """Determine next best action based on current context"""
        actions = []
        
        # Stage-based actions
        if self.current_stage == ConversationStage.GREETING:
            actions.append({
                'action': 'build_rapport',
                'priority': 'high',
                'description': 'Build rapport and identify language preference'
            })
        
        elif self.current_stage == ConversationStage.QUALIFICATION:
            # Check which BANT elements need more information
            for bant_type, data in self.bant_data.items():
                if data['score'] < 5:  # Low score, need more info
                    actions.append({
                        'action': f'qualify_{bant_type}',
                        'priority': 'high',
                        'description': f'Gather more {bant_type} information'
                    })
        
        elif self.current_stage == ConversationStage.PRESENTATION:
            if self.is_qualified():
                actions.append({
                    'action': 'present_solution',
                    'priority': 'high',
                    'description': 'Present product solution tailored to their needs'
                })
            else:
                actions.append({
                    'action': 'continue_qualification',
                    'priority': 'high',
                    'description': 'Continue qualification before presentation'
                })
        
        elif self.current_stage == ConversationStage.OBJECTION:
            unresolved_objections = [obj for obj in self.conversation_context['objections_encountered'] 
                                   if not obj.get('resolved', False)]
            if unresolved_objections:
                actions.append({
                    'action': 'handle_objection',
                    'priority': 'high',
                    'description': f'Address {unresolved_objections[0]["type"]} objection'
                })
        
        elif self.current_stage == ConversationStage.CLOSING:
            actions.append({
                'action': 'ask_for_commitment',
                'priority': 'high',
                'description': 'Ask for commitment and close the deal'
            })
        
        # Context-based actions
        if len(self.conversation_context['buying_signals']) >= 2:
            actions.append({
                'action': 'accelerate_close',
                'priority': 'medium',
                'description': 'Multiple buying signals detected - accelerate closing'
            })
        
        if self.conversation_context['urgency_indicators']:
            latest_urgency = self.conversation_context['urgency_indicators'][-1]
            if latest_urgency['level'] == 'high':
                actions.append({
                    'action': 'create_urgency',
                    'priority': 'medium',
                    'description': 'High urgency detected - create urgency in response'
                })
        
        return {
            'primary_action': actions[0] if actions else {'action': 'continue_conversation', 'priority': 'low'},
            'all_actions': actions,
            'current_stage': self.current_stage.value,
            'bant_score': self.get_bant_score(),
            'is_qualified': self.is_qualified()
        }
    
    def get_conversation_summary(self) -> Dict:
        """Get comprehensive conversation summary"""
        duration = time.time() - self.call_start_time
        
        return {
            'call_id': self.call_id,
            'product_id': self.product_id,
            'current_stage': self.current_stage.value,
            'stage_history': self.stage_history,
            'stage_timings': self.stage_timings,
            'bant_data': self.bant_data,
            'bant_score': self.get_bant_score(),
            'is_qualified': self.is_qualified(),
            'conversation_context': self.conversation_context,
            'duration': duration,
            'call_start_time': self.call_start_time,
            'last_activity_time': self.last_activity_time
        }
    
    def should_trigger_upsell(self) -> bool:
        """Determine if upsell should be triggered"""
        return (self.current_stage == ConversationStage.CONVERTED and 
                self.is_qualified() and 
                len(self.conversation_context['buying_signals']) >= 2)
    
    def get_upsell_opportunities(self) -> List[str]:
        """Get upsell opportunities based on conversation context"""
        opportunities = []
        
        # Analyze conversation for upsell signals
        if 'budget' in str(self.conversation_context).lower():
            opportunities.append('premium_package')
        
        if 'urgent' in str(self.conversation_context).lower():
            opportunities.append('express_service')
        
        if 'multiple' in str(self.conversation_context).lower():
            opportunities.append('bulk_discount')
        
        return opportunities
