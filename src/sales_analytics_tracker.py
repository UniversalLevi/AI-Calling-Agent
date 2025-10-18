"""
Sales Analytics Tracker - Real-time Sales Metrics Tracking
=========================================================

This module tracks real-time sales metrics during calls including sentiment analysis,
talk-listen ratio, keyword extraction, and post-call analytics aggregation.
"""

import time
import re
import requests
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import os


class SalesAnalyticsTracker:
    """Tracks real-time sales analytics during calls"""
    
    def __init__(self, call_id: str):
        self.call_id = call_id
        self.start_time = time.time()
        
        # Real-time tracking data
        self.sentiment_history = []
        self.talk_listen_data = {
            'ai_talk_time': 0,
            'user_talk_time': 0,
            'ai_word_count': 0,
            'user_word_count': 0,
            'exchanges': []
        }
        self.key_phrases = []
        self.objections_detected = []
        self.techniques_used = []
        self.stage_progression = []
        self.conversion_stage = 'greeting'
        
        # Analytics configuration
        self.target_talk_ratio = float(os.getenv('TALK_LISTEN_TARGET_RATIO', '0.4'))
        self.sentiment_analysis_enabled = os.getenv('SENTIMENT_ANALYSIS_ENABLED', 'true').lower() == 'true'
        self.dashboard_url = os.getenv('SALES_API_URL', 'http://localhost:5000')
        
        print(f"📊 Sales Analytics Tracker initialized for call: {call_id}")
    
    def track_exchange(self, user_input: str, ai_response: str, language: str = 'en'):
        """Track a complete user-AI exchange"""
        exchange_start = time.time()
        
        # Analyze user input
        user_analysis = self._analyze_user_input(user_input, language)
        
        # Analyze AI response
        ai_analysis = self._analyze_ai_response(ai_response, language)
        
        # Update talk-listen ratio
        self._update_talk_listen_ratio(user_input, ai_response)
        
        # Track sentiment
        if self.sentiment_analysis_enabled:
            self._track_sentiment(user_input, ai_response, language)
        
        # Track key phrases
        self._track_key_phrases(user_input, ai_response, language)
        
        # Track objections
        objections = self._detect_objections(user_input, language)
        if objections:
            self.objections_detected.extend(objections)
        
        # Record exchange
        exchange_data = {
            'timestamp': exchange_start,
            'user_input': user_input,
            'ai_response': ai_response,
            'language': language,
            'user_word_count': len(user_input.split()),
            'ai_word_count': len(ai_response.split()),
            'user_sentiment': user_analysis.get('sentiment', 0),
            'ai_sentiment': ai_analysis.get('sentiment', 0),
            'objections': objections,
            'buying_signals': user_analysis.get('buying_signals', []),
            'duration': time.time() - exchange_start
        }
        
        self.talk_listen_data['exchanges'].append(exchange_data)
        
        return exchange_data
    
    def _analyze_user_input(self, user_input: str, language: str) -> Dict:
        """Analyze user input for various metrics"""
        user_lower = user_input.lower()
        
        # Sentiment analysis
        sentiment = self._analyze_sentiment(user_input)
        
        # Buying signals detection
        buying_signals = self._detect_buying_signals(user_lower)
        
        # Urgency detection
        urgency_level = self._detect_urgency_level(user_lower)
        
        # Competitor mentions
        competitor_mentions = self._detect_competitor_mentions(user_lower)
        
        return {
            'sentiment': sentiment,
            'buying_signals': buying_signals,
            'urgency_level': urgency_level,
            'competitor_mentions': competitor_mentions,
            'word_count': len(user_input.split()),
            'character_count': len(user_input)
        }
    
    def _analyze_ai_response(self, ai_response: str, language: str) -> Dict:
        """Analyze AI response for various metrics"""
        response_lower = ai_response.lower()
        
        # Sentiment analysis
        sentiment = self._analyze_sentiment(ai_response)
        
        # Technique detection
        techniques = self._detect_techniques_used(response_lower)
        
        # Question analysis
        question_count = response_lower.count('?')
        
        return {
            'sentiment': sentiment,
            'techniques_used': techniques,
            'question_count': question_count,
            'word_count': len(ai_response.split()),
            'character_count': len(ai_response)
        }
    
    def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text using keyword-based approach"""
        positive_keywords = [
            'good', 'great', 'excellent', 'amazing', 'perfect', 'love', 'wonderful',
            'achha', 'badhiya', 'perfect', 'excellent', 'nice', 'awesome'
        ]
        negative_keywords = [
            'bad', 'terrible', 'awful', 'hate', 'disappointed', 'angry', 'frustrated',
            'bura', 'kharab', 'hate', 'disappointed', 'not good', 'worst'
        ]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_keywords if word in text_lower)
        negative_count = sum(1 for word in negative_keywords if word in text_lower)
        
        if positive_count > negative_count:
            return 0.5
        elif negative_count > positive_count:
            return -0.5
        else:
            return 0.0
    
    def _detect_buying_signals(self, text_lower: str) -> List[str]:
        """Detect buying signals in text"""
        buying_signals = []
        
        signal_patterns = {
            'agreement': ['yes', 'okay', 'sure', 'haan', 'theek hai', 'bilkul'],
            'interest': ['interested', 'tell me more', 'aur batao', 'explain'],
            'commitment': ['book', 'buy', 'purchase', 'book karo', 'le lo'],
            'positive': ['good', 'great', 'sounds good', 'achha', 'badhiya'],
            'urgency': ['urgent', 'immediate', 'asap', 'jaldi', 'urgent']
        }
        
        for signal_type, keywords in signal_patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    buying_signals.append(f"{signal_type}:{keyword}")
        
        return buying_signals
    
    def _detect_urgency_level(self, text_lower: str) -> str:
        """Detect urgency level in text"""
        urgent_keywords = ['urgent', 'immediate', 'asap', 'quick', 'fast', 'jaldi', 'urgent']
        if any(keyword in text_lower for keyword in urgent_keywords):
            return 'high'
        
        moderate_keywords = ['soon', 'this week', 'month', 'jaldi', 'jald']
        if any(keyword in text_lower for keyword in moderate_keywords):
            return 'medium'
        
        return 'low'
    
    def _detect_competitor_mentions(self, text_lower: str) -> List[str]:
        """Detect competitor mentions in text"""
        competitors = []
        
        competitor_keywords = [
            'competitor', 'other company', 'alternative', 'different provider',
            'dusra company', 'alternative', 'competitor'
        ]
        
        for keyword in competitor_keywords:
            if keyword in text_lower:
                competitors.append(keyword)
        
        return competitors
    
    def _detect_techniques_used(self, response_lower: str) -> List[str]:
        """Detect sales techniques used in AI response"""
        techniques = []
        
        # SPIN technique detection
        spin_patterns = {
            'situation': ['tell me about', 'current situation', 'currently using'],
            'problem': ['challenges', 'problems', 'issues', 'difficulties'],
            'implication': ['how does that affect', 'impact', 'consequences'],
            'need_payoff': ['what would it mean', 'benefits', 'advantages']
        }
        
        for technique, patterns in spin_patterns.items():
            if any(pattern in response_lower for pattern in patterns):
                techniques.append(f"SPIN:{technique}")
        
        # Consultative technique detection
        consultative_patterns = ['i understand', 'that makes sense', 'i can see why']
        if any(pattern in response_lower for pattern in consultative_patterns):
            techniques.append('Consultative:empathy')
        
        # Challenger technique detection
        challenger_patterns = ['limited time', 'only few', 'many customers', 'urgent']
        if any(pattern in response_lower for pattern in challenger_patterns):
            techniques.append('Challenger:urgency')
        
        return techniques
    
    def _detect_objections(self, user_input: str, language: str) -> List[str]:
        """Detect objections in user input"""
        objections = []
        user_lower = user_input.lower()
        
        objection_patterns = {
            'price': ['expensive', 'cost', 'price', 'budget', 'mahanga', 'paisa', 'costly'],
            'timing': ['later', 'think', 'decide', 'busy', 'baad mein', 'soch', 'time'],
            'competition': ['already have', 'other company', 'competitor', 'pehle se', 'dusra'],
            'trust': ['trust', 'believe', 'sure', 'bharosa', 'yakeen', 'reliable'],
            'authority': ['boss', 'manager', 'decision', 'approve', 'boss', 'manager'],
            'need': ['need', 'want', 'require', 'zaroorat', 'chahiye', 'important']
        }
        
        for objection_type, keywords in objection_patterns.items():
            if any(keyword in user_lower for keyword in keywords):
                objections.append(objection_type)
        
        return objections
    
    def _update_talk_listen_ratio(self, user_input: str, ai_response: str):
        """Update talk-listen ratio data"""
        user_word_count = len(user_input.split())
        ai_word_count = len(ai_response.split())
        
        self.talk_listen_data['user_word_count'] += user_word_count
        self.talk_listen_data['ai_word_count'] += ai_word_count
        
        # Estimate talk time (rough approximation: 150 words per minute)
        user_talk_time = (user_word_count / 150) * 60
        ai_talk_time = (ai_word_count / 150) * 60
        
        self.talk_listen_data['user_talk_time'] += user_talk_time
        self.talk_listen_data['ai_talk_time'] += ai_talk_time
    
    def _track_sentiment(self, user_input: str, ai_response: str, language: str):
        """Track sentiment over time"""
        user_sentiment = self._analyze_sentiment(user_input)
        ai_sentiment = self._analyze_sentiment(ai_response)
        
        self.sentiment_history.append({
            'timestamp': time.time(),
            'user_sentiment': user_sentiment,
            'ai_sentiment': ai_sentiment,
            'combined_sentiment': (user_sentiment + ai_sentiment) / 2,
            'user_text': user_input[:100],  # First 100 chars
            'ai_text': ai_response[:100]
        })
    
    def _track_key_phrases(self, user_input: str, ai_response: str, language: str):
        """Track key phrases and their categories"""
        # Extract key phrases from user input
        user_phrases = self._extract_key_phrases(user_input, 'user')
        self.key_phrases.extend(user_phrases)
        
        # Extract key phrases from AI response
        ai_phrases = self._extract_key_phrases(ai_response, 'ai')
        self.key_phrases.extend(ai_phrases)
    
    def _extract_key_phrases(self, text: str, source: str) -> List[Dict]:
        """Extract key phrases from text"""
        phrases = []
        text_lower = text.lower()
        
        # Define phrase categories
        phrase_categories = {
            'buying_signal': ['yes', 'okay', 'book', 'interested', 'haan', 'theek hai'],
            'objection': ['expensive', 'cost', 'think', 'later', 'mahanga', 'soch'],
            'urgency': ['urgent', 'immediate', 'asap', 'jaldi', 'urgent'],
            'competitor': ['competitor', 'other company', 'alternative', 'dusra'],
            'authority': ['boss', 'manager', 'decision', 'approve', 'boss'],
            'budget': ['budget', 'price', 'cost', 'paisa', 'budget'],
            'timeline': ['when', 'timeline', 'schedule', 'jaldi', 'urgent']
        }
        
        for category, keywords in phrase_categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    phrases.append({
                        'phrase': keyword,
                        'category': category,
                        'timestamp': time.time(),
                        'context': text[:50],  # First 50 chars for context
                        'source': source
                    })
        
        return phrases
    
    def update_conversion_stage(self, stage: str):
        """Update conversion stage"""
        if stage != self.conversion_stage:
            self.stage_progression.append({
                'from_stage': self.conversion_stage,
                'to_stage': stage,
                'timestamp': time.time()
            })
            self.conversion_stage = stage
            print(f"📈 Stage progression: {self.conversion_stage}")
    
    def get_talk_listen_ratio(self) -> float:
        """Calculate current talk-listen ratio"""
        total_words = self.talk_listen_data['ai_word_count'] + self.talk_listen_data['user_word_count']
        if total_words == 0:
            return 0.0
        
        return self.talk_listen_data['ai_word_count'] / total_words
    
    def get_sentiment_trend(self) -> Dict:
        """Get sentiment trend analysis"""
        if not self.sentiment_history:
            return {'trend': 'neutral', 'average': 0.0, 'volatility': 0.0}
        
        sentiments = [entry['combined_sentiment'] for entry in self.sentiment_history]
        average_sentiment = sum(sentiments) / len(sentiments)
        
        # Calculate trend
        if len(sentiments) >= 2:
            recent_avg = sum(sentiments[-3:]) / min(3, len(sentiments))
            if recent_avg > average_sentiment + 0.1:
                trend = 'improving'
            elif recent_avg < average_sentiment - 0.1:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        # Calculate volatility
        volatility = sum(abs(s - average_sentiment) for s in sentiments) / len(sentiments)
        
        return {
            'trend': trend,
            'average': average_sentiment,
            'volatility': volatility,
            'current': sentiments[-1] if sentiments else 0.0
        }
    
    def get_keyword_analysis(self) -> Dict:
        """Get keyword analysis"""
        keyword_counts = defaultdict(int)
        category_counts = defaultdict(int)
        
        for phrase in self.key_phrases:
            keyword_counts[phrase['phrase']] += 1
            category_counts[phrase['category']] += 1
        
        # Get top keywords
        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'top_keywords': top_keywords,
            'category_distribution': dict(category_counts),
            'total_phrases': len(self.key_phrases)
        }
    
    def get_call_quality_score(self) -> int:
        """Calculate overall call quality score"""
        score = 0
        
        # Talk-listen ratio score (25 points)
        ratio = self.get_talk_listen_ratio()
        ratio_diff = abs(ratio - self.target_talk_ratio)
        ratio_score = max(0, 25 - (ratio_diff * 100))
        score += ratio_score
        
        # Sentiment trend score (25 points)
        sentiment_trend = self.get_sentiment_trend()
        if sentiment_trend['trend'] == 'improving':
            score += 25
        elif sentiment_trend['trend'] == 'stable':
            score += 15
        else:
            score += 5
        
        # Objection resolution score (25 points)
        if self.objections_detected:
            # Simple heuristic: fewer objections = better score
            objection_score = max(0, 25 - len(self.objections_detected) * 5)
            score += objection_score
        else:
            score += 25  # No objections is good
        
        # Buying signals score (25 points)
        buying_signals = [p for p in self.key_phrases if p['category'] == 'buying_signal']
        signal_score = min(25, len(buying_signals) * 5)
        score += signal_score
        
        return min(100, max(0, score))
    
    def get_analytics_summary(self) -> Dict:
        """Get comprehensive analytics summary"""
        duration = time.time() - self.start_time
        
        return {
            'call_id': self.call_id,
            'duration': duration,
            'conversion_stage': self.conversion_stage,
            'stage_progression': self.stage_progression,
            'talk_listen_ratio': {
                'ai_ratio': self.get_talk_listen_ratio(),
                'target_ratio': self.target_talk_ratio,
                'ai_talk_time': self.talk_listen_data['ai_talk_time'],
                'user_talk_time': self.talk_listen_data['user_talk_time'],
                'ai_word_count': self.talk_listen_data['ai_word_count'],
                'user_word_count': self.talk_listen_data['user_word_count']
            },
            'sentiment_analysis': self.get_sentiment_trend(),
            'objections_detected': self.objections_detected,
            'techniques_used': self.techniques_used,
            'keyword_analysis': self.get_keyword_analysis(),
            'call_quality_score': self.get_call_quality_score(),
            'total_exchanges': len(self.talk_listen_data['exchanges'])
        }
    
    def save_analytics_to_dashboard(self) -> bool:
        """Save analytics data to dashboard"""
        try:
            analytics_data = self.get_analytics_summary()
            
            response = requests.post(
                f"{self.dashboard_url}/api/analytics/save",
                json=analytics_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Analytics saved to dashboard for call: {self.call_id}")
                return True
            else:
                print(f"❌ Failed to save analytics: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error saving analytics: {e}")
            return False
