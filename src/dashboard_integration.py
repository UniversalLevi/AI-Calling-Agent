"""
Dashboard Integration Module
Sends call data to the Sara Dashboard in real-time
"""

import os
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional

class DashboardIntegration:
    """Integration with Sara Dashboard for real-time call logging"""
    
    def __init__(self):
        self.dashboard_url = os.getenv('DASHBOARD_URL', 'http://localhost:5000')
        self.api_key = os.getenv('DASHBOARD_API_KEY', '')
        self.enabled = os.getenv('DASHBOARD_INTEGRATION', 'true').lower() == 'true'
        
    def _get_headers(self):
        """Get request headers"""
        headers = {
            'Content-Type': 'application/json'
        }
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers
    
    def log_call_start(self, call_data: Dict[str, Any]) -> bool:
        """Log when a call starts"""
        if not self.enabled:
            return False
            
        try:
            payload = {
                'callId': call_data.get('call_sid', ''),
                'type': call_data.get('direction', 'inbound'),
                'caller': call_data.get('from', ''),
                'receiver': call_data.get('to', ''),
                'startTime': datetime.now().isoformat(),
                'status': 'in-progress',
                'language': call_data.get('language', 'mixed'),
                'transcript': '',
                'metadata': {
                    'userAgent': call_data.get('user_agent', ''),
                    'location': call_data.get('location', ''),
                    'deviceType': 'phone'
                }
            }
            
            response = requests.post(
                f'{self.dashboard_url}/api/calls',
                json=payload,
                headers=self._get_headers(),
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                print(f"📊 Call logged to dashboard: {call_data.get('call_sid')}")
                return True
            else:
                print(f"⚠️ Dashboard logging failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Dashboard integration error: {e}")
            return False
    
    def update_call_transcript(self, call_sid: str, speaker: str, text: str) -> bool:
        """Update call transcript in real-time"""
        if not self.enabled:
            return False
            
        try:
            payload = {
                'transcript': f"{speaker}: {text}\n"
            }
            
            response = requests.patch(
                f'{self.dashboard_url}/api/calls/{call_sid}/transcript',
                json=payload,
                headers=self._get_headers(),
                timeout=5
            )
            
            return response.status_code == 200
                
        except Exception as e:
            print(f"❌ Transcript update error: {e}")
            return False
    
    def log_call_end(self, call_data: Dict[str, Any]) -> bool:
        """Log when a call ends"""
        if not self.enabled:
            return False
            
        try:
            call_sid = call_data.get('call_sid', '')
            payload = {
                'endTime': datetime.now().isoformat(),
                'status': call_data.get('status', 'success'),
                'duration': call_data.get('duration', 0),
                'transcript': call_data.get('transcript', ''),
                'interruptionCount': call_data.get('interruption_count', 0),
                'satisfaction': call_data.get('satisfaction', 'unknown'),
                'metadata': call_data.get('metadata', {})
            }
            
            response = requests.patch(
                f'{self.dashboard_url}/api/calls/{call_sid}',
                json=payload,
                headers=self._get_headers(),
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"📊 Call completed and logged: {call_sid}")
                return True
            else:
                print(f"⚠️ Call end logging failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Call end logging error: {e}")
            return False
    
    def send_live_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Send live event to dashboard via WebSocket"""
        if not self.enabled:
            return False
            
        try:
            payload = {
                'type': event_type,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(
                f'{self.dashboard_url}/api/events',
                json=payload,
                headers=self._get_headers(),
                timeout=5
            )
            
            return response.status_code == 200
                
        except Exception as e:
            print(f"❌ Live event error: {e}")
            return False

# Global instance
dashboard = DashboardIntegration()

