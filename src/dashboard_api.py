"""
Simple Dashboard API Endpoints
==============================

Clean API endpoints for dashboard integration.
"""

from flask import Blueprint, jsonify, request
from src.simple_dashboard_integration import simple_dashboard
from datetime import datetime

# Create blueprint
dashboard_api = Blueprint('dashboard_api', __name__)

@dashboard_api.route('/api/calls/active', methods=['GET'])
def get_active_calls():
    """Get all active calls"""
    try:
        active_calls = simple_dashboard.get_active_calls()
        return jsonify({
            'success': True,
            'data': active_calls,
            'count': len(active_calls)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_api.route('/api/calls/history', methods=['GET'])
def get_call_history():
    """Get call history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        history = simple_dashboard.get_call_history(limit)
        return jsonify({
            'success': True,
            'data': history,
            'count': len(history)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_api.route('/api/calls/stats', methods=['GET'])
def get_call_stats():
    """Get call statistics"""
    try:
        stats = simple_dashboard.get_call_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_api.route('/api/calls/<call_sid>/status', methods=['PUT'])
def update_call_status(call_sid):
    """Update call status"""
    try:
        data = request.get_json() or {}
        status = data.get('status')
        metadata = data.get('metadata', {})
        
        if not status:
            return jsonify({
                'success': False,
                'error': 'Status is required'
            }), 400
        
        success = simple_dashboard.update_call_status(call_sid, status, metadata)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Call {call_sid} status updated to {status}'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Call {call_sid} not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_api.route('/api/calls', methods=['POST'])
def log_call():
    """Log a call (start or end)"""
    try:
        data = request.get_json() or {}
        call_type = data.get('type', 'start')  # 'start' or 'end'
        
        if call_type == 'start':
            success = simple_dashboard.log_call_start(data)
        elif call_type == 'end':
            success = simple_dashboard.log_call_end(data)
        else:
            return jsonify({
                'success': False,
                'error': 'Type must be "start" or "end"'
            }), 400
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Call {call_type} logged successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to log call {call_type}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

