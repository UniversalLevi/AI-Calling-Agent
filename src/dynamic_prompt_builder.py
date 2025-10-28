"""
Dynamic Prompt Builder
======================

Builds AI prompts dynamically based on active product data.
Integrates with existing PromptManager and adds product-specific context.
"""

from typing import Dict, List, Optional
from src.prompt_manager import PromptManager


class DynamicPromptBuilder:
    """Builds dynamic AI prompts with product context."""
    
    def __init__(self):
        self.prompt_manager = PromptManager()
        print("🔨 Dynamic Prompt Builder initialized")
    
    def build_prompt(
        self, 
        product: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None,
        detected_language: str = 'mixed'
    ) -> str:
        """
        Build complete AI prompt with product context.
        
        Args:
            product: Active product data from ProductService
            conversation_history: List of previous messages
            detected_language: Detected language of conversation
            
        Returns:
            Complete system prompt string
        """
        
        if not product:
            # No product - use generic persona
            return self._build_generic_prompt(detected_language)
        
        # Build product-aware prompt
        return self._build_product_prompt(product, conversation_history, detected_language)
    
    def _build_generic_prompt(self, language: str) -> str:
        """Build generic prompt when no product is active."""
        try:
            core_persona = self.prompt_manager.load_prompt("core_persona")
            return f"{core_persona}\n\nRespond naturally and conversationally in {language}. Be warm, helpful, and empathetic."
        except Exception as e:
            print(f"⚠️ Failed to load core persona: {e}")
            return f"You are Sara, a helpful AI assistant. Respond naturally in {language}. Be warm and helpful."
    
    def _build_product_prompt(
        self, 
        product: Dict, 
        conversation_history: Optional[List[Dict]],
        language: str
    ) -> str:
        """Build product-aware prompt with scope control."""
        
        # Load base prompts
        try:
            core_persona = self.prompt_manager.load_prompt("core_persona")
            context_type = product.get('context_type', 'sales')
            context_prompt = self.prompt_manager.get_context_prompt(context_type)
        except Exception as e:
            print(f"⚠️ Prompt loading error: {e}")
            core_persona = "You are Sara, a helpful AI assistant."
            context_prompt = ""
        
        # Build product context section
        product_context = self._build_product_context(product)
        
        # Build scope control rules
        scope_rules = self._build_scope_rules(product)
        
        # Build conversation context
        conv_context = self._build_conversation_context(conversation_history)
        
        # Combine all parts
        full_prompt = f"""{core_persona}

{product_context}

{context_prompt}

{scope_rules}

{conv_context}

LANGUAGE: Respond in {language}. Use Romanized Hinglish for Hindi (Latin script, not Devanagari).

REMEMBER: You are Sara, warm and helpful. Stay focused on {product.get('name', 'the product')} while being flexible with general questions.
"""
        
        return full_prompt.strip()
    
    def _build_product_context(self, product: Dict) -> str:
        """Build product-specific context section."""
        
        name = product.get('name', 'our product')
        brand = product.get('brand', '')
        description = product.get('description', '')
        category = product.get('category', 'service')
        tagline = product.get('tagline', '')
        
        # Build features section
        features_text = ""
        features = product.get('features', [])
        selling_points = product.get('selling_points', [])
        all_features = features + selling_points
        
        if all_features:
            features_list = '\n'.join(f"  - {f}" for f in all_features[:5])  # Top 5
            features_text = f"\n\nKEY FEATURES:\n{features_list}"
        
        # Build objections section
        objections_text = ""
        objections = product.get('objections', [])
        if objections:
            obj_list = []
            for obj in objections[:3]:  # Top 3
                if isinstance(obj, dict):
                    obj_type = obj.get('type', 'general')
                    responses = obj.get('responses', [])
                    if responses:
                        obj_list.append(f"  - {obj_type.title()}: {responses[0]}")
                    elif obj.get('response'):
                        obj_list.append(f"  - {obj.get('objection', '')}: {obj.get('response', '')}")
            
            if obj_list:
                objections_text = f"\n\nCOMMON OBJECTIONS:\n" + '\n'.join(obj_list)
        
        # Build AIDA content if available
        aida_text = ""
        attention_hooks = product.get('attention_hooks', [])
        if attention_hooks:
            aida_text += f"\n\nATTENTION HOOKS:\n" + '\n'.join(f"  - {h}" for h in attention_hooks[:2])
        
        interest_questions = product.get('interest_questions', [])
        if interest_questions:
            aida_text += f"\n\nINTEREST QUESTIONS:\n" + '\n'.join(f"  - {q}" for q in interest_questions[:3])
        
        desire_statements = product.get('desire_statements', [])
        if desire_statements:
            aida_text += f"\n\nDESIRE STATEMENTS:\n" + '\n'.join(f"  - {s}" for s in desire_statements[:2])
        
        action_prompts = product.get('action_prompts', [])
        if action_prompts:
            aida_text += f"\n\nACTION PROMPTS:\n" + '\n'.join(f"  - {p}" for p in action_prompts[:2])
        
        # Combine product context
        brand_text = f" from {brand}" if brand else ""
        tagline_text = f"\nTagline: {tagline}" if tagline else ""
        desc_text = f"\nDescription: {description}" if description else ""
        
        context = f"""
╔══════════════════════════════════════════════════════╗
║           ACTIVE PRODUCT CONTEXT                     ║
╚══════════════════════════════════════════════════════╝

Product: {name}{brand_text}
Category: {category}{tagline_text}{desc_text}

YOUR PRIMARY GOAL: Help users with {name}.{features_text}{objections_text}{aida_text}
"""
        
        return context.strip()
    
    def _build_scope_rules(self, product: Dict) -> str:
        """Build flexible scope control rules."""
        
        product_name = product.get('name', 'this product')
        
        rules = f"""
╔══════════════════════════════════════════════════════╗
║       CONVERSATION SCOPE & FLEXIBILITY               ║
╚══════════════════════════════════════════════════════╝

HANDLING OFF-TOPIC QUESTIONS:

Rule 1: GENERAL KNOWLEDGE (weather, time, small talk)
- Answer naturally and warmly
- Blend seamlessly into product topic
- Make it feel like natural conversation flow

Examples:
  User: "What time is it?"
  Sara: "Abhi 3 baje hain ji. Perfect time for planning! Waise, aapko {product_name} book karna hai kya?"
  
  User: "Kaisa chal raha hai?"
  Sara: "Bahut achha, thank you! Main aaj kaafi logon ki help kar rahi hun {product_name} mein. Aapko bhi chahiye?"
  
  User: "Weather kaisa hai?"
  Sara: "Aaj to garmi hai! Waise {product_name} ki planning kar rahe ho kya?"

Rule 2: RELATED BUT DIFFERENT SERVICE
- Show understanding and empathy
- Explain your specialty warmly
- Offer gentle alternative or redirect

Examples:
  User: "Can you help with [other service]?"
  Sara: "Wo service to main directly nahi karti, but {product_name} mein expert hun! Main aapki wahan madad kar sakti hun. Interested?"
  
  User: "[Different product] chahiye?"
  Sara: "[Different product] ke liye main help nahi kar sakti, lekin {product_name} mein zaroor help karungi. Sochiye?"

Rule 3: COMPLETELY UNRELATED (still friendly)
- Light, warm acknowledgment
- Gentle humor if appropriate
- Soft boundary with smile in voice
- Keep door open

Examples:
  User: "Tell me a joke"
  Sara: "Haha! Main jokes kam, {product_name} zyada better karti hun. But seriously, agar interested ho to bataiye. Chahiye?"
  
  User: "Sing a song"
  Sara: "Arre, singing to nahi aati mujhe! {product_name} mein gaana gaati hun main haha. Waise planning hai kya?"
  
  User: "Random unrelated question"
  Sara: "Interesting question! Agar aapko {product_name} chahiye to main help kar sakti hun. Interested?"

Rule 4: PERSISTENT OFF-TOPIC (2-3 redirects failed)
- Show understanding without judgment
- Respectful closure
- Leave door open for future
- Warm goodbye

Examples:
  (After 2-3 redirects)
  Sara: "Main dekh rahi hun aapko abhi {product_name} nahi chahiye. Koi baat nahi! Jab bhi zarurat ho, mujhe call kar lena. Main hamesha ready hun help karne ke liye. Take care!"
  
  OR (if user getting frustrated)
  Sara: "Achha ji, lagta hai aaj {product_name} ka plan nahi hai. No problem at all! Jab zarurat ho, tab baat karte hain. Have a great day!"

IMPORTANT TONE PRINCIPLES:
- Never sound robotic or scripted
- Match user's energy (but stay professional)
- Use filler words naturally: "achha", "haan ji", "dekho", "waise"
- Let redirects feel conversational, not forced
- If user is polite, be extra warm
- If user is curt, be efficient but friendly
- Always end positively
"""
        
        return rules.strip()
    
    def _build_conversation_context(self, history: Optional[List[Dict]]) -> str:
        """Build conversation history context."""
        
        if not history or len(history) == 0:
            return "CONVERSATION STATUS: This is the first interaction with the user."
        
        # Count redirects for scope control
        redirect_count = 0
        for msg in history:
            if isinstance(msg, dict):
                content = msg.get('content', '').lower()
                if any(word in content for word in ['waise', 'but', 'lekin', 'main sirf', 'nahi kar sakti']):
                    redirect_count += 1
        
        redirect_warning = ""
        if redirect_count >= 2:
            redirect_warning = "\n⚠️ WARNING: User has been redirected 2+ times. Consider polite closure if they continue off-topic."
        
        # Build recent context
        recent_messages = history[-3:] if len(history) > 3 else history
        context_lines = []
        for msg in recent_messages:
            if isinstance(msg, dict):
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                context_lines.append(f"  {role.title()}: {content[:100]}...")
        
        history_text = '\n'.join(context_lines)
        
        return f"""
CONVERSATION HISTORY (Last {len(recent_messages)} messages):
{history_text}{redirect_warning}
"""


# Global instance
_prompt_builder = None

def get_prompt_builder() -> DynamicPromptBuilder:
    """Get global prompt builder instance."""
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = DynamicPromptBuilder()
    return _prompt_builder

