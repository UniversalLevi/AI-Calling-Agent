"""
Script Integration Module
========================

Handles retrieval and integration of sales scripts from the dashboard database.
This module bridges the gap between the dashboard script management and bot responses.
"""

import os
import requests
import logging
import time
from typing import Optional, Dict, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class ConversationStage(Enum):
    """Conversation stages for script selection"""
    GREETING = "greeting"
    QUALIFICATION = "qualification"
    PRESENTATION = "presentation"
    OBJECTION = "objection"
    CLOSING = "closing"
    UPSELL = "upsell"

class ScriptIntegration:
    """Handles integration of sales scripts with bot responses"""
    
    def __init__(self):
        self.dashboard_url = os.getenv('SALES_API_URL', 'http://localhost:5000')
        self.api_timeout = 5
        self.script_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def get_active_scripts(self, product_id: str, language: str = 'en') -> List[Dict]:
        """Get all active scripts for a product"""
        cache_key = f"scripts_{product_id}_{language}"
        
        # Check cache first
        if cache_key in self.script_cache:
            cached_data, timestamp = self.script_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
        
        try:
            response = requests.get(
                f"{self.dashboard_url}/api/sales/scripts",
                params={'productId': product_id, 'language': language, 'isActive': 'true'},
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    scripts = data.get('data', [])
                    # Cache the results
                    self.script_cache[cache_key] = (scripts, time.time())
                    return scripts
            
            logger.warning(f"Failed to get scripts: {response.status_code}")
            return []
            
        except Exception as e:
            logger.error(f"Error getting scripts: {e}")
            return []
    
    def get_script_for_stage(self, product_id: str, stage: ConversationStage, 
                           language: str = 'en', user_input: str = "") -> Optional[Dict]:
        """Get the best script for a specific conversation stage"""
        scripts = self.get_active_scripts(product_id, language)
        
        if not scripts:
            return None
        
        # Filter scripts by stage
        stage_scripts = [s for s in scripts if s.get('scriptType') == stage.value]
        
        if not stage_scripts:
            return None
        
        # Sort by priority and success rate
        stage_scripts.sort(key=lambda x: (x.get('priority', 1), x.get('successRate', 0)), reverse=True)
        
        # Check for trigger keywords if user input provided
        if user_input:
            for script in stage_scripts:
                triggers = script.get('conditions', {}).get('triggers', [])
                if triggers and any(trigger.lower() in user_input.lower() for trigger in triggers):
                    return script
        
        # Return highest priority script
        return stage_scripts[0]
    
    def detect_conversation_stage(self, user_input: str, conversation_history: List[Dict] = None) -> ConversationStage:
        """Detect current conversation stage based on user input and history"""
        user_lower = user_input.lower()
        
        # Stage detection keywords
        stage_keywords = {
            ConversationStage.GREETING: ['hello', 'hi', 'namaste', 'kaise', 'start', 'begin'],
            ConversationStage.QUALIFICATION: ['who', 'what', 'where', 'when', 'why', 'how', 'tell me', 'about'],
            ConversationStage.PRESENTATION: ['show', 'explain', 'details', 'features', 'benefits', 'advantages'],
            ConversationStage.OBJECTION: ['expensive', 'costly', 'price', 'money', 'not sure', 'doubt', 'problem'],
            ConversationStage.CLOSING: ['buy', 'purchase', 'order', 'book', 'confirm', 'yes', 'agree'],
            ConversationStage.UPSELL: ['more', 'additional', 'extra', 'upgrade', 'premium', 'better']
        }
        
        # Check for stage keywords
        for stage, keywords in stage_keywords.items():
            if any(keyword in user_lower for keyword in keywords):
                return stage
        
        # Default to presentation if no clear stage detected
        return ConversationStage.PRESENTATION
    
    def format_script_content(self, script: Dict, product: Dict = None, user_name: str = None) -> str:
        """Format script content with product and user context"""
        content = script.get('content', '')
        
        if not content:
            return ""
        
        # Replace variables if product info available
        if product:
            content = content.replace('{product_name}', product.get('name', ''))
            content = content.replace('{product_price}', product.get('price', 'Contact for pricing'))
            content = content.replace('{product_description}', product.get('description', ''))
        
        # Replace user name if available
        if user_name:
            content = content.replace('{user_name}', user_name)
        
        return content
    
    def should_use_script(self, script: Dict, user_input: str, conversation_history: List[Dict] = None) -> bool:
        """Determine if a script should be used based on conditions"""
        conditions = script.get('conditions', {})
        
        # Check minimum qualification score
        min_score = conditions.get('minQualificationScore')
        if min_score and conversation_history:
            # Simple qualification scoring based on conversation length and engagement
            score = len(conversation_history) * 10
            if score < min_score:
                return False
        
        # Check call duration
        max_duration = conditions.get('maxCallDuration')
        if max_duration and conversation_history:
            # Estimate call duration (rough approximation)
            estimated_duration = len(conversation_history) * 30  # 30 seconds per exchange
            if estimated_duration > max_duration:
                return False
        
        return True
    
    def get_script_response(self, product_id: str, user_input: str, language: str = 'en',
                           conversation_history: List[Dict] = None, product: Dict = None) -> Optional[str]:
        """Get script-based response for user input"""
        try:
            # Detect conversation stage
            stage = self.detect_conversation_stage(user_input, conversation_history)
            
            # Get appropriate script
            script = self.get_script_for_stage(product_id, stage, language, user_input)
            
            if not script:
                return None
            
            # Check if script should be used
            if not self.should_use_script(script, user_input, conversation_history):
                return None
            
            # Format script content
            response = self.format_script_content(script, product)
            
            # Update usage count (async)
            self._update_script_usage(script['_id'], True)
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting script response: {e}")
            return None
    
    def _update_script_usage(self, script_id: str, success: bool):
        """Update script usage statistics"""
        try:
            requests.post(
                f"{self.dashboard_url}/api/sales/scripts/{script_id}/usage",
                json={'success': success},
                timeout=self.api_timeout
            )
        except Exception as e:
            logger.warning(f"Failed to update script usage: {e}")

# Global instance
script_integration = ScriptIntegration()
