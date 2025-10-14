"""
WebSocket Client for Real-time Dashboard Integration
Connects to the dashboard's Socket.io server for instant updates
"""

import os
import socketio
import json
from datetime import datetime
from typing import Dict, Any, Optional

class DashboardWebSocketClient:
    """WebSocket client for real-time dashboard updates"""
    
    def __init__(self):
        self.dashboard_url = os.getenv('DASHBOARD_URL', 'http://localhost:5000')
        self.enabled = os.getenv('DASHBOARD_INTEGRATION', 'true').lower() == 'true'
        self.sio = None
        self.connected = False
        
        if self.enabled:
            self._initialize_socket()
    
    def _initialize_socket(self):
        """Initialize Socket.io client"""
        try:
            self.sio = socketio.Client()
            
            @self.sio.event
            def connect():
                print("🔌 Connected to dashboard WebSocket")
                self.connected = True
            
            @self.sio.event
            def disconnect():
                print("🔌 Disconnected from dashboard WebSocket")
                self.connected = False
            
            @self.sio.event
            def connect_error(data):
                print(f"❌ Dashboard WebSocket connection error: {data}")
                self.connected = False
            
            # Connect to dashboard
            self.sio.connect(self.dashboard_url)
            
        except Exception as e:
            print(f"❌ Failed to initialize WebSocket client: {e}")
            self.connected = False
    
    def emit_call_started(self, call_data: Dict[str, Any]) -> bool:
        """Emit call started event to dashboard"""
        if not self.enabled or not self.connected:
            return False
        
        try:
            event_data = {
                'callId': call_data.get('call_sid', ''),
                'type': call_data.get('direction', 'inbound'),
                'caller': call_data.get('from', ''),
                'receiver': call_data.get('to', ''),
                'startTime': datetime.now().isoformat(),
                'status': 'in-progress',
                'language': call_data.get('language', 'mixed'),
                'metadata': {
                    'userAgent': call_data.get('user_agent', ''),
                    'location': call_data.get('location', ''),
                    'deviceType': 'phone'
                }
            }
            
            self.sio.emit('call-started', event_data)
            print(f"📡 Emitted call-started event: {call_data.get('call_sid')}")
            return True
            
        except Exception as e:
            print(f"❌ Error emitting call-started: {e}")
            return False
    
    def emit_call_updated(self, call_sid: str, update_data: Dict[str, Any]) -> bool:
        """Emit call updated event to dashboard"""
        if not self.enabled or not self.connected:
            return False
        
        try:
            event_data = {
                'callId': call_sid,
                'timestamp': datetime.now().isoformat(),
                **update_data
            }
            
            self.sio.emit('call-updated', event_data)
            print(f"📡 Emitted call-updated event: {call_sid}")
            return True
            
        except Exception as e:
            print(f"❌ Error emitting call-updated: {e}")
            return False
    
    def emit_call_ended(self, call_data: Dict[str, Any]) -> bool:
        """Emit call ended event to dashboard"""
        if not self.enabled or not self.connected:
            return False
        
        try:
            event_data = {
                'callId': call_data.get('call_sid', ''),
                'status': call_data.get('status', 'success'),
                'duration': call_data.get('duration', 0),
                'endTime': datetime.now().isoformat(),
                'transcript': call_data.get('transcript', ''),
                'interruptionCount': call_data.get('interruption_count', 0),
                'satisfaction': call_data.get('satisfaction', 'unknown')
            }
            
            self.sio.emit('call-ended', event_data)
            print(f"📡 Emitted call-ended event: {call_data.get('call_sid')}")
            return True
            
        except Exception as e:
            print(f"❌ Error emitting call-ended: {e}")
            return False
    
    def emit_call_interrupted(self, call_sid: str, interruption_data: Dict[str, Any]) -> bool:
        """Emit call interrupted event to dashboard"""
        if not self.enabled or not self.connected:
            return False
        
        try:
            event_data = {
                'callId': call_sid,
                'timestamp': datetime.now().isoformat(),
                **interruption_data
            }
            
            self.sio.emit('call-interrupted', event_data)
            print(f"📡 Emitted call-interrupted event: {call_sid}")
            return True
            
        except Exception as e:
            print(f"❌ Error emitting call-interrupted: {e}")
            return False
    
    def emit_transcript_update(self, call_sid: str, speaker: str, text: str) -> bool:
        """Emit transcript update event to dashboard"""
        if not self.enabled or not self.connected:
            return False
        
        try:
            event_data = {
                'callId': call_sid,
                'speaker': speaker,
                'text': text,
                'timestamp': datetime.now().isoformat()
            }
            
            self.sio.emit('transcript-updated', event_data)
            return True
            
        except Exception as e:
            print(f"❌ Error emitting transcript-updated: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from WebSocket"""
        if self.sio and self.connected:
            self.sio.disconnect()
            self.connected = False

# Global instance
websocket_client = DashboardWebSocketClient()
