"""
Prompt Manager for Context-Aware Personality Templates
====================================================

This module manages loading and combining different prompt templates
based on conversation context (sales, booking, support).
"""

import os
from pathlib import Path
from typing import Dict, Optional


class PromptManager:
    """Manages prompt templates and context-aware prompt loading."""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self._cache = {}
        
    def load_prompt(self, template_name: str) -> str:
        """Load a prompt template from file."""
        if template_name in self._cache:
            return self._cache[template_name]
            
        template_path = self.prompts_dir / f"{template_name}.txt"
        
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template '{template_name}' not found at {template_path}")
            
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                self._cache[template_name] = content
                return content
        except Exception as e:
            raise RuntimeError(f"Failed to load prompt template '{template_name}': {e}")
    
    def get_context_prompt(self, context: str = "booking") -> str:
        """
        Get a complete prompt combining core persona with context-specific behavior.
        
        Args:
            context: The conversation context ('sales', 'booking', 'support')
            
        Returns:
            Combined prompt string
        """
        # Load core persona
        core_persona = self.load_prompt("core_persona")
        
        # Load context-specific prompt
        context_prompt = self.load_prompt(f"{context}_prompt")
        
        # Combine them
        combined_prompt = f"{core_persona}\n\n{context_prompt}"
        
        return combined_prompt
    
    def get_available_contexts(self) -> list:
        """Get list of available conversation contexts."""
        contexts = []
        for file_path in self.prompts_dir.glob("*_prompt.txt"):
            context_name = file_path.stem.replace("_prompt", "")
            contexts.append(context_name)
        return contexts
    
    def clear_cache(self):
        """Clear the prompt cache."""
        self._cache.clear()
    
    def reload_prompts(self):
        """Reload all prompts from files."""
        self.clear_cache()
        # Preload core persona
        self.load_prompt("core_persona")
        # Preload all context prompts
        for context in self.get_available_contexts():
            self.load_prompt(f"{context}_prompt")


# Global prompt manager instance
_prompt_manager = None

def get_prompt_manager() -> PromptManager:
    """Get the global prompt manager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager

def get_context_prompt(context: str = "booking") -> str:
    """Convenience function to get context-aware prompt."""
    manager = get_prompt_manager()
    return manager.get_context_prompt(context)

def load_prompt_template(template_name: str) -> str:
    """Convenience function to load a specific prompt template."""
    manager = get_prompt_manager()
    return manager.load_prompt(template_name)


