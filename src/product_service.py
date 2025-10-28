"""
Product Service Module
======================

Fetches and caches active product from dashboard API.
Supports both Product and AidaProduct models with intelligent fallback.
"""

import requests
import time
from typing import Dict, Optional
from datetime import datetime, timedelta


class ProductService:
    """Service for fetching and caching active product from dashboard."""
    
    def __init__(self, dashboard_url: str = "http://localhost:5000"):
        self.dashboard_url = dashboard_url.rstrip('/')
        self.cache = {}
        self.cache_ttl = 60  # 60 seconds cache
        self.last_fetch_time = None
        
        print(f"🛍️ Product Service initialized: {self.dashboard_url}")
    
    def get_active_product(self) -> Optional[Dict]:
        """
        Get active product from dashboard API with caching.
        
        Returns:
            Product dict or None if unavailable
        """
        # Check cache first
        if self._is_cache_valid():
            print(f"📦 Using cached product: {self.cache.get('name', 'Unknown')}")
            return self.cache
        
        # Try to fetch fresh product
        product = self._fetch_from_dashboard()
        
        if product:
            self.cache = product
            self.last_fetch_time = datetime.now()
            print(f"✅ Fresh product fetched: {product.get('name', 'Unknown')}")
            return product
        
        # Fallback to cache even if expired
        if self.cache:
            print(f"⚠️ Using expired cache as fallback")
            return self.cache
        
        print(f"❌ No product available")
        return None
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self.cache or not self.last_fetch_time:
            return False
        
        age = (datetime.now() - self.last_fetch_time).total_seconds()
        return age < self.cache_ttl
    
    def _fetch_from_dashboard(self) -> Optional[Dict]:
        """Fetch active product from dashboard API."""
        
        # Try AIDA product first (more detailed)
        product = self._try_aida_endpoint()
        if product:
            return product
        
        # Fallback to regular product
        product = self._try_product_endpoint()
        if product:
            return product
        
        return None
    
    def _try_aida_endpoint(self) -> Optional[Dict]:
        """Try fetching from AIDA products endpoint."""
        try:
            url = f"{self.dashboard_url}/api/aida/active"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    return self._parse_aida_product(data['data'])
            
        except Exception as e:
            print(f"⚠️ AIDA endpoint failed: {e}")
        
        return None
    
    def _try_product_endpoint(self) -> Optional[Dict]:
        """Try fetching from regular products endpoint."""
        try:
            url = f"{self.dashboard_url}/api/sales/products/active"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    return self._parse_regular_product(data['data'])
            
        except Exception as e:
            print(f"⚠️ Product endpoint failed: {e}")
        
        return None
    
    def _parse_aida_product(self, data: Dict) -> Dict:
        """Parse AIDA product into standardized format."""
        
        # Build features list
        features = []
        if data.get('features'):
            features.extend(data['features'])
        if data.get('benefits'):
            features.extend(data['benefits'])
        
        # Build objections list
        objections = []
        objection_responses = data.get('objection_responses', {})
        for obj_type, responses in objection_responses.items():
            if responses:
                objections.append({
                    'type': obj_type,
                    'responses': responses
                })
        
        # Determine context type from category
        category_map = {
            'travel': 'booking',
            'food': 'booking',
            'service': 'support',
            'electronics': 'sales',
            'healthcare': 'sales',
            'education': 'sales',
            'finance': 'sales',
            'other': 'sales'
        }
        
        context_type = category_map.get(data.get('category', 'other'), 'sales')
        
        # Build custom greeting based on product
        product_name = data.get('product_name', 'our product')
        brand_name = data.get('brand_name', '')
        
        if brand_name:
            greeting = f"Namaste! Main Sara hun {brand_name} se. Aapko {product_name} ke baare mein bataun?"
        else:
            greeting = f"Namaste! Main Sara hun. Aapko {product_name} mein interest hai?"
        
        return {
            'product_id': str(data.get('_id', '')),
            'name': product_name,
            'brand': brand_name,
            'description': data.get('description', ''),
            'category': data.get('category', 'service'),
            'greeting': greeting,
            'tagline': data.get('offer_tagline', ''),
            'features': features,
            'objections': objections,
            'context_type': context_type,
            'emotion_tone': data.get('emotion_tone', 'friendly'),
            'call_to_action': data.get('call_to_action', 'Book now'),
            'attention_hooks': data.get('attention_hooks', []),
            'interest_questions': data.get('interest_questions', []),
            'desire_statements': data.get('desire_statements', []),
            'action_prompts': data.get('action_prompts', [])
        }
    
    def _parse_regular_product(self, data: Dict) -> Dict:
        """Parse regular product into standardized format."""
        
        # Build objections list
        objections = []
        if data.get('common_objections'):
            for obj in data['common_objections']:
                objections.append({
                    'type': 'general',
                    'objection': obj.get('objection', ''),
                    'response': obj.get('response', '')
                })
        
        # Simple greeting
        product_name = data.get('name', 'our product')
        greeting = f"Namaste! Main Sara hun. Aapko {product_name} ke baare mein bataun?"
        
        # Infer context from name/description
        name_lower = product_name.lower()
        desc_lower = (data.get('description', '')).lower()
        combined = name_lower + ' ' + desc_lower
        
        if any(word in combined for word in ['hotel', 'booking', 'travel', 'flight', 'vacation']):
            context_type = 'booking'
        elif any(word in combined for word in ['support', 'help', 'service', 'customer']):
            context_type = 'support'
        else:
            context_type = 'sales'
        
        return {
            'product_id': str(data.get('_id', '')),
            'name': product_name,
            'brand': '',
            'description': data.get('description', ''),
            'category': 'service',
            'greeting': greeting,
            'tagline': '',
            'features': data.get('key_features', []),
            'selling_points': data.get('selling_points', []),
            'objections': objections,
            'faqs': data.get('faqs', []),
            'context_type': context_type,
            'emotion_tone': 'friendly',
            'call_to_action': 'Get started',
            'attention_hooks': [],
            'interest_questions': [],
            'desire_statements': [],
            'action_prompts': []
        }
    
    def clear_cache(self):
        """Clear product cache (useful for testing)."""
        self.cache = {}
        self.last_fetch_time = None
        print("🧹 Product cache cleared")


# Global instance
_product_service = None

def get_product_service() -> ProductService:
    """Get global product service instance."""
    global _product_service
    if _product_service is None:
        _product_service = ProductService()
    return _product_service

