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
        # Optional JWT for protected endpoints (fixes 401 in dev/prod)
        self.jwt_token = os.getenv('DASHBOARD_JWT') or os.getenv('DASHBOARD_API_TOKEN') or os.getenv('DASHBOARD_AUTH_TOKEN')
        
        print(f"🔗 Sales Dashboard Integration initialized: {self.dashboard_url}")
    def _auth_headers(self) -> Dict[str, str]:
        """Return Authorization header if JWT token is configured."""
        if self.jwt_token:
            return { 'Authorization': f'Bearer {self.jwt_token}' }
        return {}

        # Optional: subscribe to websocket updates for instant voice settings
        try:
            if websocket_client:
                websocket_client.subscribe('system:voice-settings', self._on_voice_settings_update)
        except Exception:
            pass
    
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

    def _on_voice_settings_update(self, data: Any):
        try:
            # Invalidate voice cache so next call fetches fresh values
            if 'voice_settings' in self.cache:
                del self.cache['voice_settings']
                del self.cache_timestamps['voice_settings']
        except Exception:
            pass
    
    def _send_call_update(self, event_type: str, call_data: Dict) -> None:
        """Send real-time call update via WebSocket"""
        try:
            if websocket_client and websocket_client.is_connected():
                websocket_client.emit(event_type, call_data)
                print(f"📡 Sent {event_type} update via WebSocket")
        except Exception as e:
            print(f"⚠️ WebSocket update failed: {e}")

    def get_voice_settings(self) -> Dict:
        """Fetch TTS voice settings from dashboard with simple caching."""
        cache_key = "voice_settings"
        cached = self._get_cached_data(cache_key)
        if cached:
            return cached
        try:
            response = requests.get(
                f"{self.dashboard_url}/api/system/voice-settings",
                headers=self._auth_headers(),
                timeout=self.api_timeout
            )
            if response.status_code == 200:
                data = response.json().get('data', {})
                self._cache_data(cache_key, data)
                return data
        except Exception as e:
            print(f"❌ Error fetching voice settings: {e}")
        # Defaults
        return {"tts_voice_english": "nova", "tts_voice_hindi": "shimmer", "tts_language_preference": "auto"}
    
    def get_active_campaign(self, product_id: str) -> Optional[Dict]:
        """Get active sales campaign configuration"""
        cache_key = f"campaign_{product_id}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            response = requests.get(
                f"{self.dashboard_url}/api/sales/active-campaign/{product_id}",
                headers=self._auth_headers(),
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
                headers=self._auth_headers(),
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
                headers=self._auth_headers(),
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
                headers=self._auth_headers(),
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
                headers=self._auth_headers(),
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
    
    def save_sales_analytics(self, analytics_data: Dict) -> bool:
        """Save sales analytics data"""
        try:
            response = requests.post(
                f"{self.dashboard_url}/api/analytics/save",
                json=analytics_data,
                headers=self._auth_headers(),
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
                headers=self._auth_headers(),
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
                headers=self._auth_headers(),
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
                headers=self._auth_headers(),
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
                headers=self._auth_headers(),
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
        """Log call start to dashboard with fallback"""
        try:
            # Ensure required fields for CallLog model
            if 'callId' not in call_data:
                call_data['callId'] = call_data.get('call_sid', 'unknown')
            if 'type' not in call_data:
                call_data['type'] = 'outbound'
            if 'caller' not in call_data:
                call_data['caller'] = call_data.get('from', 'unknown')
            if 'receiver' not in call_data:
                call_data['receiver'] = call_data.get('to', 'unknown')
            if 'startTime' not in call_data:
                call_data['startTime'] = datetime.utcnow().isoformat()
            if 'status' not in call_data:
                call_data['status'] = 'in-progress'
            
            response = requests.post(
                f"{self.dashboard_url}/api/calls/",
                json=call_data,
                headers=self._auth_headers(),
                timeout=self.api_timeout
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Call start logged: {call_data.get('callId', 'unknown')}")
                
                # Send real-time update via WebSocket
                self._send_call_update('callStarted', call_data)
                
                return True
            else:
                print(f"⚠️ Dashboard call log failed: {response.status_code}")
                if response.status_code == 400:
                    print(f"📝 Request data: {call_data}")
                    print(f"📝 Response: {response.text}")
                return False
        except Exception as e:
            print(f"⚠️ Dashboard unavailable: {e}")
            return False
    
    def log_call_end(self, call_data: Dict) -> bool:
        """Log call end to dashboard"""
        try:
            call_sid = call_data.get('call_sid', 'unknown')
            response = requests.patch(
                f"{self.dashboard_url}/api/calls/{call_sid}",
                json=call_data,
                headers=self._auth_headers(),
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                print(f"✅ Call end logged: {call_data.get('call_sid', 'unknown')}")
                
                # Send real-time update via WebSocket
                self._send_call_update('callTerminated', call_data)
                
                return True
            else:
                print(f"❌ Failed to log call end: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error logging call end: {e}")
            return False
    
    def get_active_aida_product(self) -> Optional[Dict]:
        """Get active AIDA product from dashboard"""
        try:
            response = requests.get(
                f"{self.dashboard_url}/api/aida/active",
                headers=self._auth_headers(),
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    print(f"✅ Active AIDA product loaded: {data['data'].get('product_name', 'Unknown')}")
                    return data['data']
                else:
                    print("⚠️ No active AIDA product found")
                    return None
            else:
                print(f"⚠️ Failed to fetch active AIDA product: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️ Error fetching active AIDA product: {e}")
            return None
    
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
        """Log call start - redirect to sales integration"""
        return self.sales_integration.log_call_start(call_data)
    
    def log_call_end(self, call_data: Dict) -> bool:
        """Log call end - redirect to sales integration"""
        return self.sales_integration.log_call_end(call_data)
    
    def log_call_update(self, call_data: Dict) -> bool:
        """Log call update during conversation"""
        try:
            call_sid = call_data.get('call_sid', 'unknown')
            response = requests.patch(
                f"{self.dashboard_url}/api/calls/{call_sid}",
                json=call_data,
                headers=self._auth_headers(),
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                # Send real-time update via WebSocket
                self._send_call_update('callUpdated', call_data)
                return True
            else:
                print(f"❌ Failed to log call update: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error logging call update: {e}")
            return False


# Global instance
dashboard = DashboardIntegration()
sales_dashboard = SalesDashboardIntegration()