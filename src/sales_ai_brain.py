"""
Sales AI Brain - Advanced Sales-Focused AI System
==================================================

This module extends the MixedAIBrain with sales-specific capabilities including
SPIN selling, Consultative approach, Challenger closing, and dynamic script loading.
"""

import os
import json
import time
import requests
from typing import Optional, Dict, List, Tuple
from abc import ABC, abstractmethod

try:
    from .mixed_ai_brain import MixedAIBrain
    from .language_detector import detect_language, get_language_prompt
except ImportError:
    # Handle direct execution
    from mixed_ai_brain import MixedAIBrain
    from language_detector import detect_language, get_language_prompt


class SalesAIBrain(MixedAIBrain):
    """Sales-focused AI Brain with advanced selling techniques"""
    
    def __init__(self, product_id: str = None):
        super().__init__()
        self.product_id = product_id or os.getenv('ACTIVE_PRODUCT_ID')
        self.sales_config = {}
        self.conversation_stage = 'greeting'
        self.bant_scores = {'budget': 0, 'authority': 0, 'need': 0, 'timeline': 0}
        self.objections_faced = []
        self.techniques_used = []
        self.sentiment_history = []
        self.key_phrases = []
        self.call_start_time = time.time()
        
        # Resolve active product if not provided
        if not self.product_id:
            try:
                dashboard_url = os.getenv('SALES_API_URL', 'http://localhost:5000')
                r = requests.get(f"{dashboard_url}/api/sales/products/active")
                if r.status_code == 200 and r.json().get('data'):
                    self.product_id = r.json()['data']['_id']
            except Exception:
                pass
        # Load sales configuration now
        self._load_sales_config()
        
        print(f"🎯 Sales AI Brain initialized for product: {self.product_id}")
    
    def _load_sales_config(self):
        """Load sales configuration from dashboard API"""
        try:
            dashboard_url = os.getenv('SALES_API_URL', 'http://localhost:5000')
            response = requests.get(f"{dashboard_url}/api/sales/active-campaign/{self.product_id}")
            
            if response.status_code == 200:
                self.sales_config = response.json()['data']
                print(f"✅ Sales config loaded: {len(self.sales_config.get('scripts', []))} scripts")
            else:
                print(f"⚠️ Failed to load sales config: {response.status_code}")
                self._load_default_config()
                
        except Exception as e:
            print(f"❌ Error loading sales config: {e}")
            self._load_default_config()
    
    def _load_default_config(self):
        """Load default sales configuration"""
        self.sales_config = {
            'product': {
                'name': 'Hotel Booking Service',
                'description': 'Premium hotel booking assistance',
                'price': 299,
                'currency': 'USD'
            },
            'scripts': [],
            'objectionHandlers': [],
            'techniques': []
        }
    
    def ask(self, user_text: str, language: str = None) -> str:
        """Process user input with sales-focused response"""
        try:
            # Detect language if not specified
            if language is None:
                language = detect_language(user_text)
            
            # Analyze conversation context
            context = self._analyze_conversation_context(user_text, language)
            
            # Update conversation stage
            self._update_conversation_stage(user_text, context)
            
            # Detect objections
            objections = self._detect_objections(user_text, language)
            if objections:
                self.objections_faced.extend(objections)
                return self._handle_objections(objections, language)
            
            # Generate sales-focused response
            response = self._generate_sales_response(user_text, language, context)
            
            # Track analytics
            self._track_analytics(user_text, response, language)
            
            return response
            
        except Exception as e:
            print(f"❌ Sales AI error: {e}")
            return super().ask(user_text, language)
    
    def _analyze_conversation_context(self, user_text: str, language: str) -> Dict:
        """Analyze conversation context for sales decisions"""
        user_lower = user_text.lower()
        
        # Buying signals
        buying_signals = ['yes', 'okay', 'book', 'interested', 'sounds good', 'tell me more', 
                         'haan', 'theek hai', 'book karo', 'interested', 'aur batao']
        
        # Objection signals
        objection_signals = ['expensive', 'cost', 'think', 'later', 'busy', 'not sure',
                           'mahanga', 'soch', 'baad mein', 'busy', 'pata nahi']
        
        # Qualification signals
        qualification_signals = ['budget', 'price', 'cost', 'decision', 'manager', 'boss',
                               'paisa', 'budget', 'decision', 'manager']
        
        context = {
            'buying_signals': any(signal in user_lower for signal in buying_signals),
            'objection_signals': any(signal in user_lower for signal in objection_signals),
            'qualification_signals': any(signal in user_lower for signal in qualification_signals),
            'urgency_level': self._detect_urgency(user_text),
            'sentiment': self._analyze_sentiment(user_text)
        }
        
        return context
    
    def _detect_urgency(self, user_text: str) -> str:
        """Detect urgency level in user input"""
        user_lower = user_text.lower()
        
        urgent_keywords = ['urgent', 'immediate', 'asap', 'quick', 'fast', 'jaldi', 'urgent']
        if any(keyword in user_lower for keyword in urgent_keywords):
            return 'high'
        
        moderate_keywords = ['soon', 'this week', 'month', 'jaldi', 'jald']
        if any(keyword in user_lower for keyword in moderate_keywords):
            return 'medium'
        
        return 'low'
    
    def _analyze_sentiment(self, user_text: str) -> float:
        """Analyze sentiment of user input"""
        # Simple sentiment analysis based on keywords
        positive_keywords = ['good', 'great', 'excellent', 'amazing', 'perfect', 'love',
                           'achha', 'badhiya', 'perfect', 'excellent']
        negative_keywords = ['bad', 'terrible', 'awful', 'hate', 'disappointed', 'angry',
                           'bura', 'kharab', 'hate', 'disappointed']
        
        user_lower = user_text.lower()
        positive_count = sum(1 for word in positive_keywords if word in user_lower)
        negative_count = sum(1 for word in negative_keywords if word in user_lower)
        
        if positive_count > negative_count:
            return 0.5
        elif negative_count > positive_count:
            return -0.5
        else:
            return 0.0
    
    def _update_conversation_stage(self, user_text: str, context: Dict):
        """Update conversation stage based on context"""
        if self.conversation_stage == 'greeting':
            if context['qualification_signals'] or len(user_text.split()) > 5:
                self.conversation_stage = 'qualification'
        elif self.conversation_stage == 'qualification':
            if context['buying_signals'] or 'tell me more' in user_text.lower():
                self.conversation_stage = 'presentation'
        elif self.conversation_stage == 'presentation':
            if context['objection_signals']:
                self.conversation_stage = 'objection'
            elif context['buying_signals']:
                self.conversation_stage = 'closing'
        elif self.conversation_stage == 'objection':
            if context['buying_signals']:
                self.conversation_stage = 'closing'
    
    def _detect_objections(self, user_text: str, language: str) -> List[str]:
        """Detect objections in user input"""
        objections = []
        user_lower = user_text.lower()
        
        objection_patterns = {
            'price': ['expensive', 'cost', 'price', 'budget', 'mahanga', 'paisa'],
            'timing': ['later', 'think', 'decide', 'busy', 'baad mein', 'soch'],
            'competition': ['already have', 'other company', 'competitor', 'pehle se'],
            'trust': ['trust', 'believe', 'sure', 'bharosa', 'yakeen'],
            'authority': ['boss', 'manager', 'decision', 'approve', 'boss', 'manager'],
            'need': ['need', 'want', 'require', 'zaroorat', 'chahiye']
        }
        
        for objection_type, keywords in objection_patterns.items():
            if any(keyword in user_lower for keyword in keywords):
                objections.append(objection_type)
        
        return objections
    
    def _handle_objections(self, objections: List[str], language: str) -> str:
        """Handle detected objections"""
        try:
            dashboard_url = os.getenv('SALES_API_URL', 'http://localhost:5000')
            
            for objection in objections:
                response = requests.get(f"{dashboard_url}/api/sales/objections/{objection}/{language}")
                if response.status_code == 200:
                    handler = response.json()['data']
                    return handler['response']
            
            # Fallback objection handling
            return self._get_fallback_objection_response(objections[0], language)
            
        except Exception as e:
            print(f"❌ Error handling objections: {e}")
            return self._get_fallback_objection_response(objections[0], language)
    
    def _get_fallback_objection_response(self, objection_type: str, language: str) -> str:
        """Get fallback objection response"""
        responses = {
            'price': {
                'en': "I understand price is important. Let me show you the value you'll get...",
                'hi': "Main samajh sakta hun ki price important hai. Main aapko value dikhata hun...",
                'mixed': "Main samajh sakta hun ki price important hai. Let me show you the value..."
            },
            'timing': {
                'en': "I understand you need time to think. What specific concerns do you have?",
                'hi': "Main samajh sakta hun ki aapko sochne ka time chahiye. Kya concerns hain?",
                'mixed': "Main samajh sakta hun ki aapko sochne ka time chahiye. What concerns do you have?"
            },
            'competition': {
                'en': "That's great that you're comparing options. What made you consider alternatives?",
                'hi': "Achha hai ki aap options compare kar rahe hain. Kya reason hai alternatives consider karne ka?",
                'mixed': "Achha hai ki aap options compare kar rahe hain. What made you consider alternatives?"
            }
        }
        
        return responses.get(objection_type, responses['price']).get(language, responses['price']['en'])
    
    def _generate_sales_response(self, user_text: str, language: str, context: Dict) -> str:
        """Generate sales-focused response based on stage and context"""
        try:
            # Get appropriate script for current stage
            script = self._get_script_for_stage(language)
            
            if script:
                return self._process_script(script, user_text, context, language)
            else:
                # Fallback to base AI with sales context
                return self._generate_contextual_response(user_text, language, context)
                
        except Exception as e:
            print(f"❌ Error generating sales response: {e}")
            return super().ask(user_text, language)
    
    def _get_script_for_stage(self, language: str) -> Optional[Dict]:
        """Get script for current conversation stage"""
        scripts = self.sales_config.get('scripts', [])
        
        for script in scripts:
            if (script.get('scriptType') == self.conversation_stage and 
                script.get('language') == language and 
                script.get('isActive', True)):
                return script
        
        return None
    
    def _process_script(self, script: Dict, user_text: str, context: Dict, language: str) -> str:
        """Process sales script with dynamic content"""
        content = script.get('content', '')
        
        # Replace variables in script
        product = self.sales_config.get('product', {})
        content = content.replace('{product_name}', product.get('name', 'our service'))
        content = content.replace('{product_price}', str(product.get('price', 0)))
        
        # Add technique-specific enhancements
        technique = script.get('technique', 'Generic')
        if technique == 'SPIN':
            content = self._enhance_spin_response(content, context)
        elif technique == 'Consultative':
            content = self._enhance_consultative_response(content, context)
        elif technique == 'Challenger':
            content = self._enhance_challenger_response(content, context)
        
        return content
    
    def _enhance_spin_response(self, content: str, context: Dict) -> str:
        """Enhance response with SPIN technique"""
        if self.conversation_stage == 'qualification':
            if 'Situation' in content:
                content += " Tell me about your current situation..."
            elif 'Problem' in content:
                content += " What challenges are you facing?"
        elif self.conversation_stage == 'presentation':
            if 'Implication' in content:
                content += " How does this affect your business?"
            elif 'Need-payoff' in content:
                content += " What would it mean if we could solve this?"
        
        return content
    
    def _enhance_consultative_response(self, content: str, context: Dict) -> str:
        """Enhance response with Consultative technique"""
        empathy_phrases = [
            "I understand your concern...",
            "That makes perfect sense...",
            "I can see why that would be important..."
        ]
        
        if context['objection_signals']:
            content = empathy_phrases[0] + " " + content
        
        return content
    
    def _enhance_challenger_response(self, content: str, context: Dict) -> str:
        """Enhance response with Challenger technique"""
        if self.conversation_stage == 'closing':
            urgency_phrases = [
                "This is a limited-time offer...",
                "Only a few spots left...",
                "Many customers are booking this week..."
            ]
            content += " " + urgency_phrases[0]
        
        return content
    
    def _generate_contextual_response(self, user_text: str, language: str, context: Dict) -> str:
        """Generate contextual response when no script is available"""
        # Handle greeting stage specifically
        if self.conversation_stage == 'greeting':
            return self._generate_greeting_response(language)
        
        # Create enhanced system prompt with sales context
        base_prompt = get_language_prompt(language)
        
        sales_context = f"""
SALES CONTEXT:
- Product: {self.sales_config.get('product', {}).get('name', 'our service')}
- Current Stage: {self.conversation_stage}
- BANT Scores: {self.bant_scores}
- Buying Signals: {context['buying_signals']}
- Objection Signals: {context['objection_signals']}

SALES TECHNIQUES TO USE:
- SPIN: Ask about Situation, Problem, Implication, Need-payoff
- Consultative: Show empathy and build trust
- Challenger: Teach value and create urgency when appropriate

RESPOND AS A SALES PROFESSIONAL WITH THESE TECHNIQUES.
"""
        
        enhanced_prompt = base_prompt + sales_context
        
        # Temporarily replace system prompt
        original_history = self.provider.history.copy()
        if self.provider.history and self.provider.history[0]['role'] == 'system':
            self.provider.history[0]['content'] = enhanced_prompt
        else:
            self.provider.history.insert(0, {'role': 'system', 'content': enhanced_prompt})
        
        try:
            response = self.provider.ask(user_text, language)
            return response
        finally:
            # Restore original history
            self.provider.history = original_history
    
    def _generate_greeting_response(self, language: str) -> str:
        """Generate sales-focused greeting response"""
        product = self.sales_config.get('product', {})
        product_name = product.get('name', 'our service')
        
        if language == 'hi':
            greetings = [
                f"Namaste! Main Sara hun aur main aapko {product_name} ke baare mein batana chahti hun. Kya aap interested hain?",
                f"Hello! Main Sara hun aur main aapko {product_name} ke baare mein call kar rahi hun. Kya aap sun sakte hain?",
                f"Hi! Main Sara hun aur main aapko {product_name} ke baare mein baat karna chahti hun. Kya aap interested hain?"
            ]
        elif language == 'mixed':
            greetings = [
                f"Namaste! Main Sara hun aur main aapko {product_name} ke baare mein batana chahti hun. Kya aap interested hain?",
                f"Hello! Main Sara hun aur main aapko {product_name} ke baare mein call kar rahi hun. Kya aap sun sakte hain?",
                f"Hi! Main Sara hun aur main aapko {product_name} ke baare mein baat karna chahti hun. Kya aap interested hain?"
            ]
        else:  # English
            greetings = [
                f"Hello! This is Sara calling about {product_name}. Do you have a moment to talk?",
                f"Hi! I'm Sara and I'm calling about {product_name}. Are you interested in learning more?",
                f"Hello! This is Sara from {product_name}. I'd like to tell you about our amazing offer. Are you available?"
            ]
        
        import random
        return random.choice(greetings)
    
    def _track_analytics(self, user_text: str, response: str, language: str):
        """Track analytics data"""
        # Track sentiment
        sentiment = self._analyze_sentiment(user_text)
        self.sentiment_history.append({
            'timestamp': time.time(),
            'score': sentiment,
            'text': user_text
        })
        
        # Track key phrases
        buying_phrases = ['yes', 'okay', 'book', 'interested', 'haan', 'theek hai']
        objection_phrases = ['expensive', 'cost', 'think', 'later', 'mahanga', 'soch']
        
        user_lower = user_text.lower()
        for phrase in buying_phrases:
            if phrase in user_lower:
                self.key_phrases.append({
                    'phrase': phrase,
                    'category': 'buying_signal',
                    'timestamp': time.time(),
                    'context': user_text
                })
        
        for phrase in objection_phrases:
            if phrase in user_lower:
                self.key_phrases.append({
                    'phrase': phrase,
                    'category': 'objection',
                    'timestamp': time.time(),
                    'context': user_text
                })
        
        # Track techniques used
        if hasattr(self, '_current_technique'):
            self.techniques_used.append({
                'technique': self._current_technique,
                'stage': self.conversation_stage,
                'timestamp': time.time(),
                'success': sentiment > 0
            })
    
    def get_conversation_summary(self) -> Dict:
        """Get summary of current conversation"""
        duration = time.time() - self.call_start_time
        
        return {
            'product_id': self.product_id,
            'conversation_stage': self.conversation_stage,
            'bant_scores': self.bant_scores,
            'objections_faced': self.objections_faced,
            'techniques_used': self.techniques_used,
            'sentiment_history': self.sentiment_history,
            'key_phrases': self.key_phrases,
            'duration': duration,
            'call_start_time': self.call_start_time
        }
    
    def update_bant_score(self, bant_type: str, score: int):
        """Update BANT qualification score"""
        if bant_type in self.bant_scores:
            self.bant_scores[bant_type] = score
            print(f"📊 Updated {bant_type} score: {score}")
    
    def get_qualification_score(self) -> int:
        """Get total BANT qualification score"""
        return sum(self.bant_scores.values())
    
    def is_qualified(self, threshold: int = 20) -> bool:
        """Check if lead is qualified based on BANT score"""
        return self.get_qualification_score() >= threshold


# Backward compatibility
class SalesBrain(SalesAIBrain):
    """Backward compatibility alias"""
    pass
