"""
Dashboard Integration - Extended for Sales AI System
===================================================

This module handles integration with the Sara Dashboard for sales data,
analytics tracking, and real-time updates.
"""

import os
import requests
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# WebSocket client for real-time updates
try:
    from .websocket_client import DashboardWebSocketClient
    websocket_client = DashboardWebSocketClient()
except ImportError:
    websocket_client = None

logger = logging.getLogger(__name__)

class SalesDashboardIntegration:
    """Extended dashboard integration for sales AI system"""
    
    def __init__(self):
        self.dashboard_url = os.getenv('SALES_API_URL', 'http://localhost:5000')
        self.api_timeout = 10
        self.cache_duration = int(os.getenv('SALES_CACHE_DURATION', '300'))  # 5 minutes
        self.cache = {}
        self.cache_timestamps = {}
        
        print(f"🔗 Sales Dashboard Integration initialized: {self.dashboard_url}")
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.cache_timestamps:
            return False
        
        cache_time = self.cache_timestamps[key]
        return time.time() - cache_time < self.cache_duration
    
    def _get_cached_data(self, key: str) -> Optional[Any]:
        """Get cached data if valid"""
        if self._is_cache_valid(key):
            return self.cache.get(key)
        return None
    
    def _cache_data(self, key: str, data: Any):
        """Cache data with timestamp"""
        self.cache[key] = data
        self.cache_timestamps[key] = time.time()
    
    def get_active_campaign(self, product_id: str) -> Optional[Dict]:
        """Get active sales campaign configuration"""
        cache_key = f"campaign_{product_id}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            response = requests.get(
                f"{self.dashboard_url}/api/sales/active-campaign/{product_id}",
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                data = response.json()['data']
                self._cache_data(cache_key, data)
                return data
            else:
                print(f"❌ Failed to get active campaign: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting active campaign: {e}")
            return None
    
    def get_sales_scripts(self, product_id: str, script_type: str = None, language: str = 'en') -> List[Dict]:
        """Get sales scripts for a product"""
        cache_key = f"scripts_{product_id}_{script_type}_{language}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            params = {'productId': product_id, 'language': language}
            if script_type:
                params['scriptType'] = script_type
            
            response = requests.get(
                f"{self.dashboard_url}/api/sales/scripts",
                params=params,
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                data = response.json()['data']
                self._cache_data(cache_key, data)
                return data
            else:
                print(f"❌ Failed to get sales scripts: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting sales scripts: {e}")
            return []
    
    def get_objection_handlers(self, objection_type: str = None, language: str = 'en') -> List[Dict]:
        """Get objection handlers"""
        cache_key = f"objections_{objection_type}_{language}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            params = {'language': language}
            if objection_type:
                params['objectionType'] = objection_type
            
            response = requests.get(
                f"{self.dashboard_url}/api/sales/objections",
                params=params,
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                data = response.json()['data']
                self._cache_data(cache_key, data)
                return data
            else:
                print(f"❌ Failed to get objection handlers: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting objection handlers: {e}")
            return []
    
    def detect_objection(self, user_input: str, language: str = 'en') -> List[str]:
        """Detect objections in user input"""
        try:
            response = requests.post(
                f"{self.dashboard_url}/api/sales/objections/detect",
                json={'userInput': user_input, 'language': language},
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                return response.json()['data']['objectionTypes']
            else:
                print(f"❌ Failed to detect objections: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error detecting objections: {e}")
            return []
    
    def get_objection_response(self, objection_type: str, language: str = 'en') -> Optional[Dict]:
        """Get response for specific objection type"""
        try:
            response = requests.get(
                f"{self.dashboard_url}/api/sales/objections/{objection_type}/{language}",
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                return response.json()['data']
            else:
                print(f"❌ Failed to get objection response: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting objection response: {e}")
            return None
    
    def update_lead_qualification(self, call_id: str, bant_data: Dict) -> bool:
        """Update lead qualification data"""
        try:
            response = requests.put(
                f"{self.dashboard_url}/api/sales/qualification/{call_id}",
                json=bant_data,
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                print(f"✅ Lead qualification updated for call: {call_id}")
                return True
            else:
                print(f"❌ Failed to update lead qualification: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error updating lead qualification: {e}")
            return False
    
    def save_sales_analytics(self, analytics_data: Dict) -> bool:
        """Save sales analytics data"""
        try:
            response = requests.post(
                f"{self.dashboard_url}/api/analytics/save",
                json=analytics_data,
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                print(f"✅ Sales analytics saved for call: {analytics_data.get('call_id', 'unknown')}")
                return True
            else:
                print(f"❌ Failed to save sales analytics: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error saving sales analytics: {e}")
            return False
    
    def get_conversion_funnel(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get conversion funnel data"""
        try:
            params = {}
            if start_date:
                params['startDate'] = start_date
            if end_date:
                params['endDate'] = end_date
            
            response = requests.get(
                f"{self.dashboard_url}/api/analytics/conversion-funnel",
                params=params,
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                return response.json()['data']
            else:
                print(f"❌ Failed to get conversion funnel: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting conversion funnel: {e}")
            return []
    
    def get_objection_analysis(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get objection analysis data"""
        try:
            params = {}
            if start_date:
                params['startDate'] = start_date
            if end_date:
                params['endDate'] = end_date
            
            response = requests.get(
                f"{self.dashboard_url}/api/analytics/objection-analysis",
                params=params,
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                return response.json()['data']
            else:
                print(f"❌ Failed to get objection analysis: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting objection analysis: {e}")
            return []
    
    def get_technique_performance(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get technique performance data"""
        try:
            params = {}
            if start_date:
                params['startDate'] = start_date
            if end_date:
                params['endDate'] = end_date
            
            response = requests.get(
                f"{self.dashboard_url}/api/analytics/technique-performance",
                params=params,
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                return response.json()['data']
            else:
                print(f"❌ Failed to get technique performance: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting technique performance: {e}")
            return []
    
    def get_dashboard_summary(self, start_date: str = None, end_date: str = None) -> Optional[Dict]:
        """Get comprehensive dashboard summary"""
        try:
            params = {}
            if start_date:
                params['startDate'] = start_date
            if end_date:
                params['endDate'] = end_date
            
            response = requests.get(
                f"{self.dashboard_url}/api/analytics/dashboard-summary",
                params=params,
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                return response.json()['data']
            else:
                print(f"❌ Failed to get dashboard summary: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting dashboard summary: {e}")
            return None
    
    def log_call_start(self, call_data: Dict) -> bool:
        """Log call start to dashboard"""
        try:
            response = requests.post(
                f"{self.dashboard_url}/api/calls/start",
                json=call_data,
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                print(f"✅ Call start logged: {call_data.get('call_sid', 'unknown')}")
                return True
            else:
                print(f"❌ Failed to log call start: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error logging call start: {e}")
            return False
    
    def log_call_end(self, call_data: Dict) -> bool:
        """Log call end to dashboard"""
        try:
            response = requests.post(
                f"{self.dashboard_url}/api/calls/end",
                json=call_data,
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                print(f"✅ Call end logged: {call_data.get('call_sid', 'unknown')}")
                return True
            else:
                print(f"❌ Failed to log call end: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error logging call end: {e}")
            return False
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        self.cache_timestamps.clear()
        print("🧹 Dashboard integration cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'cache_size': len(self.cache),
            'cache_keys': list(self.cache.keys()),
            'cache_duration': self.cache_duration
        }


# Legacy compatibility
class DashboardIntegration:
    """Legacy dashboard integration for backward compatibility"""
    
    def __init__(self):
        self.sales_integration = SalesDashboardIntegration()
    
    def log_call_start(self, call_data: Dict) -> bool:
        return self.sales_integration.log_call_start(call_data)
    
    def log_call_end(self, call_data: Dict) -> bool:
        return self.sales_integration.log_call_end(call_data)
    
    def log_call_update(self, call_data: Dict) -> bool:
        # Legacy method - redirect to call end
        return self.sales_integration.log_call_end(call_data)


# Global instance
dashboard = DashboardIntegration()
sales_dashboard = SalesDashboardIntegration()