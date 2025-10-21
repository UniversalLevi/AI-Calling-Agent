"""
AIDA AI Brain
Specialized AI brain for AIDA sales framework with dynamic prompt generation
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .mixed_ai_brain import MixedAIBrain
from .aida_context_manager import AidaContextManager, AIDAStage
from .intent_classifier import IntentType

logger = logging.getLogger(__name__)

class AidaAIBrain(MixedAIBrain):
    """
    AI Brain specialized for AIDA sales framework
    Inherits from MixedAIBrain but adds AIDA-specific functionality
    """
    
    def __init__(self, product_id: str = None):
        super().__init__()
        self.product_id = product_id
        self.aida_context = None
        self.product_data = {}
        
        # Load product data
        self._load_product_data()
        
        logger.info(f"🎯 AIDA AI Brain initialized for product: {self.product_id}")
    
    def _load_product_data(self):
        """Load product data from dashboard or local file"""
        try:
            # Try to load from dashboard API first
            dashboard_url = os.getenv('SALES_API_URL', 'http://localhost:5000')
            if self.product_id:
                import requests
                response = requests.get(f"{dashboard_url}/api/sales/products/{self.product_id}", timeout=2)
                if response.status_code == 200:
                    self.product_data = response.json()['data']
                    logger.info(f"✅ Product data loaded from API: {self.product_data.get('product_name', 'Unknown')}")
                    return
        except Exception as e:
            logger.warning(f"⚠️ Dashboard unavailable, using default product data: {e}")
        
        # Fallback to default product data
        self.product_data = {
            'brand_name': 'Sara',
            'product_name': 'AI Calling Service',
            'category': 'service',
            'product_type': 'medium',
            'offer_tagline': 'Revolutionary AI-powered calling solution',
            'features': ['Real-time conversation', 'Multi-language support', 'Smart analytics'],
            'benefits': ['Save time', 'Increase efficiency', 'Better customer experience'],
            'emotion_tone': 'friendly',
            'call_to_action': 'book a demo',
            'attention_hooks': [
                'Hi! I have something exciting to share with you',
                'Hello! I wanted to tell you about a game-changing solution',
                'Hi there! I have great news that could help your business'
            ],
            'interest_questions': [
                'What challenges are you facing with your current calling system?',
                'How much time do you spend on repetitive calling tasks?',
                'What would it mean to you if you could automate your calling process?'
            ],
            'desire_statements': [
                'Imagine having an AI assistant that handles all your calling needs',
                'You deserve a solution that works 24/7 without breaks',
                'This could transform how you communicate with your customers'
            ],
            'action_prompts': [
                'Can I schedule a demo for you right now?',
                'Would you like to try this solution for free?',
                'Shall we get you started today?'
            ],
            'objection_responses': {
                'price': [
                    'I understand cost is important. Let me show you the ROI',
                    'The investment pays for itself within the first month',
                    'We have flexible payment options to fit your budget'
                ],
                'timing': [
                    'I understand you\'re busy. This will actually save you time',
                    'Just 15 minutes to see how this could help you',
                    'Perfect timing - we have a special offer this week'
                ],
                'authority': [
                    'I\'d love to speak with your decision maker',
                    'Who else should be involved in this decision?',
                    'Can we schedule a call with your team?'
                ]
            }
        }
        
        logger.info("✅ Default product data loaded")
    
    def initialize_aida_context(self, call_id: str):
        """Initialize AIDA context for a new call"""
        self.aida_context = AidaContextManager(call_id, self.product_data)
        logger.info(f"🎯 AIDA context initialized for call: {call_id}")
    
    def ask(self, user_input: str, conversation_history: List[Dict] = None) -> str:
        """
        Generate AI response using AIDA framework
        
        Args:
            user_input: User's speech input
            conversation_history: Previous conversation context
            
        Returns:
            AI-generated response
        """
        if not self.aida_context:
            logger.warning("⚠️ AIDA context not initialized, falling back to regular AI")
            return super().ask(user_input, conversation_history)
        
        # Add user input to conversation history
        self.aida_context.add_conversation_entry('user', user_input)
        
        # Analyze user intent
        intent, confidence = self.aida_context.analyze_user_intent(user_input)
        
        # Handle special intents
        if intent == IntentType.GOODBYE:
            return self._handle_goodbye()
        
        # Check for objections
        objection_type = self.aida_context.intent_classifier.detect_objection_type(user_input)
        if objection_type:
            self.aida_context.record_objection(objection_type, user_input)
            return self._handle_objection(objection_type)
        
        # Check for stage transition
        if self.aida_context.should_transition_stage(intent):
            self._handle_stage_transition(intent)
        
        # Generate stage-appropriate response
        response = self._generate_stage_response(intent, user_input)
        
        # Add AI response to conversation history
        self.aida_context.add_conversation_entry('assistant', response)
        
        return response
    
    def _handle_goodbye(self) -> str:
        """Handle goodbye intent"""
        responses = [
            "Thank you for your time! Have a great day!",
            "It was great talking with you. Take care!",
            "Thanks for the conversation. Goodbye!",
            "Dhanyawad! Aapka din achha rahe!"
        ]
        
        # Select appropriate response based on emotion tone
        if self.product_data.get('emotion_tone') == 'friendly':
            return responses[0]
        else:
            return responses[1]
    
    def _handle_objection(self, objection_type: str) -> str:
        """Handle user objections"""
        objection_responses = self.product_data.get('objection_responses', {}).get(objection_type, [])
        
        if objection_responses:
            # Use product-specific objection response
            response = objection_responses[0]  # Use first response for now
        else:
            # Fallback responses
            fallback_responses = {
                'price': "I understand your concern about cost. Let me explain the value you'll get.",
                'timing': "I know you're busy. This will actually save you time in the long run.",
                'authority': "I'd be happy to speak with your decision maker about this.",
                'need': "Let me help you understand how this could benefit you.",
                'competition': "I'd love to show you what makes us different."
            }
            response = fallback_responses.get(objection_type, "I understand your concern. Let me address that.")
        
        logger.info(f"🚫 Handling objection: {objection_type}")
        return response
    
    def _handle_stage_transition(self, intent: IntentType):
        """Handle transition to next AIDA stage"""
        current_stage = self.aida_context.get_current_stage()
        
        if current_stage == AIDAStage.ATTENTION and intent in [IntentType.POSITIVE, IntentType.INQUIRY]:
            self.aida_context.transition_to_stage(AIDAStage.INTEREST, f"User showed {intent.value} intent")
            
        elif current_stage == AIDAStage.INTEREST and intent in [IntentType.POSITIVE, IntentType.AGREEMENT]:
            self.aida_context.transition_to_stage(AIDAStage.DESIRE, f"User showed {intent.value} intent")
            
        elif current_stage == AIDAStage.DESIRE and intent in [IntentType.AGREEMENT, IntentType.POSITIVE]:
            self.aida_context.transition_to_stage(AIDAStage.ACTION, f"User showed {intent.value} intent")
    
    def _generate_stage_response(self, intent: IntentType, user_input: str) -> str:
        """Generate response appropriate for current AIDA stage"""
        current_stage = self.aida_context.get_current_stage()
        
        # Get stage-specific content
        stage_content = self._get_stage_content(current_stage)
        
        # Generate dynamic prompt
        prompt = self._generate_stage_prompt(current_stage, stage_content, user_input, intent)
        
        # Get AI response
        try:
            response = self._get_ai_response(prompt)
            logger.info(f"🎯 Generated {current_stage.value} stage response")
            return response
        except Exception as e:
            logger.error(f"❌ Error generating AI response: {e}")
            return self._get_fallback_response(current_stage)
    
    def _get_stage_content(self, stage: AIDAStage) -> Dict:
        """Get content specific to current stage"""
        stage_content = {
            AIDAStage.ATTENTION: {
                'hooks': self.product_data.get('attention_hooks', []),
                'tagline': self.product_data.get('offer_tagline', ''),
                'brand': self.product_data.get('brand_name', ''),
                'product': self.product_data.get('product_name', '')
            },
            AIDAStage.INTEREST: {
                'questions': self.product_data.get('interest_questions', []),
                'features': self.product_data.get('features', []),
                'category': self.product_data.get('category', '')
            },
            AIDAStage.DESIRE: {
                'statements': self.product_data.get('desire_statements', []),
                'benefits': self.product_data.get('benefits', []),
                'emotion_tone': self.product_data.get('emotion_tone', 'friendly')
            },
            AIDAStage.ACTION: {
                'prompts': self.product_data.get('action_prompts', []),
                'call_to_action': self.product_data.get('call_to_action', ''),
                'urgency': True
            }
        }
        
        return stage_content.get(stage, {})
    
    def _generate_stage_prompt(self, stage: AIDAStage, stage_content: Dict, user_input: str, intent: IntentType) -> str:
        """Generate dynamic prompt for current stage"""
        
        # Base system prompt
        base_prompt = f"""You are a professional sales assistant using the AIDA framework. You're currently in the {stage.value.upper()} stage.

Product Information:
- Brand: {self.product_data.get('brand_name', 'Unknown')}
- Product: {self.product_data.get('product_name', 'Unknown')}
- Category: {self.product_data.get('category', 'Unknown')}
- Tone: {self.product_data.get('emotion_tone', 'friendly')}

Current Stage: {stage.value.upper()}
User Intent: {intent.value}
User Input: "{user_input}"

"""
        
        # Add stage-specific instructions
        if stage == AIDAStage.ATTENTION:
            stage_prompt = f"""ATTENTION STAGE GOALS:
- Capture attention within 1-2 sentences
- Use energetic, friendly tone
- Introduce brand and value proposition
- Create curiosity

Available hooks: {stage_content.get('hooks', [])}
Tagline: {stage_content.get('tagline', '')}

Generate a short, attention-grabbing response that introduces the product and creates interest."""
            
        elif stage == AIDAStage.INTEREST:
            stage_prompt = f"""INTEREST STAGE GOALS:
- Build curiosity and uncover relevance
- Ask open-ended questions about needs
- Be conversational and inquisitive
- Listen for pain points

Available questions: {stage_content.get('questions', [])}
Features: {stage_content.get('features', [])}

Generate a response that asks about their current situation or needs, building on their interest."""
            
        elif stage == AIDAStage.DESIRE:
            stage_prompt = f"""DESIRE STAGE GOALS:
- Create emotional or logical desire
- Connect benefits to their needs
- Use confident, reassuring tone
- Address any concerns

Available statements: {stage_content.get('statements', [])}
Benefits: {stage_content.get('benefits', [])}

Generate a response that creates desire by connecting the product benefits to their specific needs."""
            
        elif stage == AIDAStage.ACTION:
            stage_prompt = f"""ACTION STAGE GOALS:
- Convert or get commitment
- Present clear next steps
- Be direct but friendly
- Create urgency if appropriate

Available prompts: {stage_content.get('prompts', [])}
Call to action: {stage_content.get('call_to_action', '')}

Generate a response that presents a clear next step and asks for commitment."""
        
        else:
            stage_prompt = "Generate an appropriate response for the current stage."
        
        # Add conversation context
        context_prompt = f"""

Conversation Context:
{self.aida_context._get_conversation_summary()}

Guidelines:
- Keep responses short and conversational (1-2 sentences)
- Match the emotion tone: {self.product_data.get('emotion_tone', 'friendly')}
- Be natural and human-like
- Don't sound robotic or scripted
- Use appropriate language (English/Hindi based on user input)

Generate your response:"""
        
        return base_prompt + stage_prompt + context_prompt
    
    def _get_ai_response(self, prompt: str) -> str:
        """Get AI response using OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional sales assistant using the AIDA framework. Be conversational, natural, and helpful."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ OpenAI API error: {e}")
            raise
    
    def _get_fallback_response(self, stage: AIDAStage) -> str:
        """Get fallback response if AI fails"""
        fallback_responses = {
            AIDAStage.ATTENTION: "Hi! I have something exciting to share with you.",
            AIDAStage.INTEREST: "That's interesting! Tell me more about your current situation.",
            AIDAStage.DESIRE: "I can see how this would really help you.",
            AIDAStage.ACTION: "Would you like to move forward with this?"
        }
        
        return fallback_responses.get(stage, "I understand. Let me help you with that.")
    
    def get_aida_context(self) -> Optional[AidaContextManager]:
        """Get the AIDA context manager"""
        return self.aida_context
    
    def get_stage_progress(self) -> Dict:
        """Get current stage progress"""
        if self.aida_context:
            return self.aida_context.get_stage_progress()
        return {'current_stage': 'unknown', 'progress_percentage': 0}
    
    def get_conversation_summary(self) -> Dict:
        """Get comprehensive conversation summary"""
        if self.aida_context:
            return self.aida_context.get_conversation_summary()
        return {'error': 'AIDA context not initialized'}

