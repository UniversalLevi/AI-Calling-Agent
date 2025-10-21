"""
AIDA Analytics Tracker
Tracks metrics and performance for AIDA sales framework
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

class AidaAnalyticsTracker:
    """
    Tracks AIDA sales framework analytics and performance metrics
    """
    
    def __init__(self):
        self.metrics = {
            'stage_completion_rates': defaultdict(int),
            'stage_durations': defaultdict(list),
            'conversion_rates': defaultdict(float),
            'objection_frequency': defaultdict(int),
            'intent_distribution': defaultdict(int),
            'product_performance': defaultdict(dict),
            'call_outcomes': defaultdict(int),
            'drop_off_points': defaultdict(int)
        }
        
        self.session_data = []
        self.start_time = time.time()
        
        logger.info("📊 AIDA Analytics Tracker initialized")
    
    def track_stage_entry(self, call_id: str, stage: str, product_id: str = None):
        """Track when a call enters a new AIDA stage"""
        entry = {
            'call_id': call_id,
            'stage': stage,
            'product_id': product_id,
            'timestamp': time.time(),
            'event': 'stage_entry'
        }
        
        self.session_data.append(entry)
        self.metrics['stage_completion_rates'][stage] += 1
        
        logger.info(f"📈 Stage entry tracked: {stage} for call {call_id}")
    
    def track_stage_exit(self, call_id: str, stage: str, duration: float, 
                        next_stage: str = None, reason: str = None):
        """Track when a call exits an AIDA stage"""
        entry = {
            'call_id': call_id,
            'stage': stage,
            'duration': duration,
            'next_stage': next_stage,
            'reason': reason,
            'timestamp': time.time(),
            'event': 'stage_exit'
        }
        
        self.session_data.append(entry)
        self.metrics['stage_durations'][stage].append(duration)
        
        # Track drop-off points
        if not next_stage:  # Call ended without progressing
            self.metrics['drop_off_points'][stage] += 1
        
        logger.info(f"📈 Stage exit tracked: {stage} (duration: {duration:.1f}s)")
    
    def track_intent(self, call_id: str, intent: str, confidence: float, stage: str):
        """Track user intent classification"""
        entry = {
            'call_id': call_id,
            'intent': intent,
            'confidence': confidence,
            'stage': stage,
            'timestamp': time.time(),
            'event': 'intent'
        }
        
        self.session_data.append(entry)
        self.metrics['intent_distribution'][intent] += 1
        
        logger.info(f"📈 Intent tracked: {intent} (confidence: {confidence:.2f})")
    
    def track_objection(self, call_id: str, objection_type: str, stage: str, 
                       resolved: bool = False, resolution_time: float = None):
        """Track objections raised during calls"""
        entry = {
            'call_id': call_id,
            'objection_type': objection_type,
            'stage': stage,
            'resolved': resolved,
            'resolution_time': resolution_time,
            'timestamp': time.time(),
            'event': 'objection'
        }
        
        self.session_data.append(entry)
        self.metrics['objection_frequency'][objection_type] += 1
        
        logger.info(f"📈 Objection tracked: {objection_type} in {stage}")
    
    def track_call_outcome(self, call_id: str, outcome: str, final_stage: str, 
                          total_duration: float, product_id: str = None):
        """Track final call outcome"""
        entry = {
            'call_id': call_id,
            'outcome': outcome,
            'final_stage': final_stage,
            'total_duration': total_duration,
            'product_id': product_id,
            'timestamp': time.time(),
            'event': 'call_outcome'
        }
        
        self.session_data.append(entry)
        self.metrics['call_outcomes'][outcome] += 1
        
        # Update conversion rates
        if outcome == 'converted':
            self.metrics['conversion_rates'][final_stage] += 1
        
        logger.info(f"📈 Call outcome tracked: {outcome} (final stage: {final_stage})")
    
    def track_product_performance(self, product_id: str, stage: str, 
                                success: bool, duration: float):
        """Track performance metrics by product"""
        if product_id not in self.metrics['product_performance']:
            self.metrics['product_performance'][product_id] = {
                'total_calls': 0,
                'conversions': 0,
                'stage_performance': defaultdict(dict),
                'avg_duration': 0
            }
        
        product_metrics = self.metrics['product_performance'][product_id]
        product_metrics['total_calls'] += 1
        
        if success:
            product_metrics['conversions'] += 1
        
        # Update stage performance
        if stage not in product_metrics['stage_performance']:
            product_metrics['stage_performance'][stage] = {
                'attempts': 0,
                'successes': 0,
                'avg_duration': 0
            }
        
        stage_perf = product_metrics['stage_performance'][stage]
        stage_perf['attempts'] += 1
        if success:
            stage_perf['successes'] += 1
        
        # Update average duration
        current_avg = product_metrics['avg_duration']
        total_calls = product_metrics['total_calls']
        product_metrics['avg_duration'] = ((current_avg * (total_calls - 1)) + duration) / total_calls
        
        logger.info(f"📈 Product performance tracked: {product_id} - {stage}")
    
    def get_stage_completion_rates(self) -> Dict:
        """Get stage completion rates"""
        total_calls = sum(self.metrics['stage_completion_rates'].values())
        if total_calls == 0:
            return {}
        
        rates = {}
        for stage, count in self.metrics['stage_completion_rates'].items():
            rates[stage] = (count / total_calls) * 100
        
        return rates
    
    def get_average_stage_durations(self) -> Dict:
        """Get average duration for each stage"""
        durations = {}
        for stage, duration_list in self.metrics['stage_durations'].items():
            if duration_list:
                durations[stage] = sum(duration_list) / len(duration_list)
            else:
                durations[stage] = 0
        
        return durations
    
    def get_conversion_rates(self) -> Dict:
        """Get conversion rates by stage"""
        conversion_rates = {}
        for stage, conversions in self.metrics['conversion_rates'].items():
            total_stage_calls = self.metrics['stage_completion_rates'].get(stage, 0)
            if total_stage_calls > 0:
                conversion_rates[stage] = (conversions / total_stage_calls) * 100
            else:
                conversion_rates[stage] = 0
        
        return conversion_rates
    
    def get_objection_analysis(self) -> Dict:
        """Get objection frequency and resolution analysis"""
        total_objections = sum(self.metrics['objection_frequency'].values())
        if total_objections == 0:
            return {}
        
        objection_rates = {}
        for objection_type, count in self.metrics['objection_frequency'].items():
            objection_rates[objection_type] = (count / total_objections) * 100
        
        return {
            'frequency': objection_rates,
            'total_objections': total_objections,
            'most_common': max(self.metrics['objection_frequency'].items(), key=lambda x: x[1])[0] if self.metrics['objection_frequency'] else None
        }
    
    def get_intent_analysis(self) -> Dict:
        """Get intent distribution analysis"""
        total_intents = sum(self.metrics['intent_distribution'].values())
        if total_intents == 0:
            return {}
        
        intent_rates = {}
        for intent, count in self.metrics['intent_distribution'].items():
            intent_rates[intent] = (count / total_intents) * 100
        
        return {
            'distribution': intent_rates,
            'total_intents': total_intents,
            'most_common': max(self.metrics['intent_distribution'].items(), key=lambda x: x[1])[0] if self.metrics['intent_distribution'] else None
        }
    
    def get_product_performance_summary(self) -> Dict:
        """Get performance summary by product"""
        summary = {}
        for product_id, metrics in self.metrics['product_performance'].items():
            conversion_rate = 0
            if metrics['total_calls'] > 0:
                conversion_rate = (metrics['conversions'] / metrics['total_calls']) * 100
            
            summary[product_id] = {
                'total_calls': metrics['total_calls'],
                'conversions': metrics['conversions'],
                'conversion_rate': conversion_rate,
                'avg_duration': metrics['avg_duration'],
                'stage_performance': dict(metrics['stage_performance'])
            }
        
        return summary
    
    def get_drop_off_analysis(self) -> Dict:
        """Get analysis of where calls drop off"""
        total_drop_offs = sum(self.metrics['drop_off_points'].values())
        if total_drop_offs == 0:
            return {}
        
        drop_off_rates = {}
        for stage, count in self.metrics['drop_off_points'].items():
            drop_off_rates[stage] = (count / total_drop_offs) * 100
        
        return {
            'rates': drop_off_rates,
            'total_drop_offs': total_drop_offs,
            'biggest_drop_off': max(self.metrics['drop_off_points'].items(), key=lambda x: x[1])[0] if self.metrics['drop_off_points'] else None
        }
    
    def get_session_summary(self, hours: int = 24) -> Dict:
        """Get summary of recent session data"""
        cutoff_time = time.time() - (hours * 3600)
        recent_data = [entry for entry in self.session_data if entry['timestamp'] >= cutoff_time]
        
        summary = {
            'total_events': len(recent_data),
            'time_period': f"{hours} hours",
            'events_by_type': defaultdict(int),
            'calls_tracked': set(),
            'stages_reached': set(),
            'objections_raised': set()
        }
        
        for entry in recent_data:
            summary['events_by_type'][entry['event']] += 1
            summary['calls_tracked'].add(entry.get('call_id', 'unknown'))
            
            if 'stage' in entry:
                summary['stages_reached'].add(entry['stage'])
            
            if entry.get('event') == 'objection':
                summary['objections_raised'].add(entry.get('objection_type', 'unknown'))
        
        # Convert sets to lists for JSON serialization
        summary['calls_tracked'] = list(summary['calls_tracked'])
        summary['stages_reached'] = list(summary['stages_reached'])
        summary['objections_raised'] = list(summary['objections_raised'])
        
        return summary
    
    def get_comprehensive_report(self) -> Dict:
        """Get comprehensive analytics report"""
        return {
            'session_info': {
                'start_time': self.start_time,
                'uptime': time.time() - self.start_time,
                'total_events': len(self.session_data)
            },
            'stage_metrics': {
                'completion_rates': self.get_stage_completion_rates(),
                'avg_durations': self.get_average_stage_durations(),
                'conversion_rates': self.get_conversion_rates(),
                'drop_off_analysis': self.get_drop_off_analysis()
            },
            'user_behavior': {
                'intent_analysis': self.get_intent_analysis(),
                'objection_analysis': self.get_objection_analysis()
            },
            'product_performance': self.get_product_performance_summary(),
            'call_outcomes': dict(self.metrics['call_outcomes']),
            'recent_activity': self.get_session_summary(24)
        }
    
    def export_data(self, filepath: str = None) -> str:
        """Export analytics data to JSON file"""
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"aida_analytics_{timestamp}.json"
        
        report = self.get_comprehensive_report()
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📊 Analytics data exported to: {filepath}")
        return filepath
    
    def reset_metrics(self):
        """Reset all metrics (use with caution)"""
        self.metrics = {
            'stage_completion_rates': defaultdict(int),
            'stage_durations': defaultdict(list),
            'conversion_rates': defaultdict(float),
            'objection_frequency': defaultdict(int),
            'intent_distribution': defaultdict(int),
            'product_performance': defaultdict(dict),
            'call_outcomes': defaultdict(int),
            'drop_off_points': defaultdict(int)
        }
        
        self.session_data = []
        self.start_time = time.time()
        
        logger.info("📊 Analytics metrics reset")

