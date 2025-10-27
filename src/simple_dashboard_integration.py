"""
Simple Dashboard Integration
============================

A clean, simple dashboard integration for live calls without complex dependencies.
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import threading
import time

class SimpleDashboardIntegration:
    """Simple dashboard integration for live calls"""
    
    def __init__(self, dashboard_url: str = "http://localhost:3001"):
        self.dashboard_url = dashboard_url.rstrip('/')
        self.api_timeout = 10
        self.active_calls = {}  # Store active calls in memory
        self.call_history = []  # Store call history
        self.max_history = 100  # Keep last 100 calls
        
        print(f"🔗 Simple Dashboard Integration initialized: {self.dashboard_url}")
    
    def log_call_start(self, call_data: Dict) -> bool:
        """Log call start - simple in-memory storage"""
        try:
            call_sid = call_data.get('call_sid') or call_data.get('callId')
            if not call_sid:
                print("⚠️ No call_sid provided")
                return False
            
            # Store in active calls
            self.active_calls[call_sid] = {
                'call_sid': call_sid,
                'phone_number': call_data.get('phone_number', 'Unknown'),
                'start_time': datetime.now().isoformat(),
                'status': 'active',
                'language': call_data.get('language', 'mixed'),
                'metadata': call_data.get('metadata', {})
            }
            
            print(f"✅ Call logged as active: {call_sid}")
            return True
            
        except Exception as e:
            print(f"⚠️ Call start logging failed: {e}")
            return False
    
    def log_call_end(self, call_data: Dict) -> bool:
        """Log call end - move from active to history"""
        try:
            call_sid = call_data.get('call_sid') or call_data.get('callId')
            if not call_sid:
                print("⚠️ No call_sid provided")
                return False
            
            # Get call from active calls
            call_info = self.active_calls.get(call_sid, {})
            
            # Calculate duration
            start_time = call_info.get('start_time')
            duration = 0
            if start_time:
                try:
                    # start_time is already a datetime object, not ISO string
                    if isinstance(start_time, datetime):
                        duration = int((datetime.now() - start_time).total_seconds())
                    else:
                        start_dt = datetime.fromisoformat(start_time)
                        duration = int((datetime.now() - start_dt).total_seconds())
                except Exception as e:
                    print(f"⚠️ Duration calculation error: {e}")
                    duration = call_data.get('duration', 0)
            
            # Create call record
            call_record = {
                'call_sid': call_sid,
                'phone_number': call_info.get('phone_number', 'Unknown'),
                'start_time': start_time,
                'end_time': datetime.now().isoformat(),
                'duration': duration,
                'status': call_data.get('status', 'completed'),
                'language': call_info.get('language', 'mixed'),
                'transcript': call_data.get('transcript', ''),
                'satisfaction': call_data.get('satisfaction', 'neutral'),
                'metadata': call_data.get('metadata', {})
            }
            
            # Move to history
            self.call_history.append(call_record)
            
            # Remove from active calls
            if call_sid in self.active_calls:
                del self.active_calls[call_sid]
            
            # Keep only last 100 calls
            if len(self.call_history) > self.max_history:
                self.call_history = self.call_history[-self.max_history:]
            
            print(f"✅ Call logged as completed: {call_sid} (Duration: {duration}s)")
            return True
            
        except Exception as e:
            print(f"⚠️ Call end logging failed: {e}")
            return False
    
    def get_active_calls(self) -> List[Dict]:
        """Get all active calls"""
        return list(self.active_calls.values())
    
    def get_call_history(self, limit: int = 50) -> List[Dict]:
        """Get call history"""
        return self.call_history[-limit:] if limit else self.call_history
    
    def get_call_stats(self) -> Dict:
        """Get call statistics"""
        total_calls = len(self.call_history)
        active_calls = len(self.active_calls)
        
        # Calculate success rate
        completed_calls = [c for c in self.call_history if c.get('status') == 'completed']
        success_rate = (len(completed_calls) / total_calls * 100) if total_calls > 0 else 0
        
        # Calculate average duration
        durations = [c.get('duration', 0) for c in completed_calls]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            'total_calls': total_calls,
            'active_calls': active_calls,
            'success_rate': round(success_rate, 2),
            'average_duration': round(avg_duration, 2),
            'last_updated': datetime.now().isoformat()
        }
    
    def update_call_status(self, call_sid: str, status: str, metadata: Dict = None) -> bool:
        """Update call status"""
        try:
            if call_sid in self.active_calls:
                self.active_calls[call_sid]['status'] = status
                if metadata:
                    self.active_calls[call_sid]['metadata'].update(metadata)
                print(f"✅ Call status updated: {call_sid} -> {status}")
                return True
            else:
                print(f"⚠️ Call not found in active calls: {call_sid}")
                return False
        except Exception as e:
            print(f"⚠️ Call status update failed: {e}")
            return False

# Global instance
simple_dashboard = SimpleDashboardIntegration()
