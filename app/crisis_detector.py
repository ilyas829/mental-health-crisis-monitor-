"""
Crisis Detection Module
Multi-signal approach to detect mental health crisis indicators
"""

import re
from typing import List, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CrisisDetector:
    """Detects crisis signals in conversation using multiple indicators"""
    
    def __init__(self):
        # Crisis keyword patterns (with weights)
        self.crisis_patterns = {
            # Immediate danger - highest weight
            'suicide': {
                'patterns': [
                    r'\bsuicide\b', r'\bkill myself\b', r'\bend my life\b',
                    r'\bdon\'t want to live\b', r'\bwant to die\b',
                    r'\bending it all\b', r'\bnot worth living\b'
                ],
                'weight': 1.0
            },
            'self_harm': {
                'patterns': [
                    r'\bcut myself\b', r'\bhurt myself\b', r'\bself harm\b',
                    r'\bself-harm\b', r'\bburning myself\b'
                ],
                'weight': 0.9
            },
            'plan': {
                'patterns': [
                    r'\bplanned\b.*\b(suicide|death)\b',
                    r'\bhow to (kill|end)\b',
                    r'\bmethods (of|for)\b.*\b(suicide|death)\b'
                ],
                'weight': 1.0
            },
            # High concern - medium-high weight
            'hopelessness': {
                'patterns': [
                    r'\bno hope\b', r'\bhopeless\b', r'\bnothing matters\b',
                    r'\bno point\b', r'\bgive up\b', r'\bcan\'t go on\b'
                ],
                'weight': 0.7
            },
            'isolation': {
                'patterns': [
                    r'\bno one cares\b', r'\ball alone\b', r'\bcompletely alone\b',
                    r'\bnobody understands\b', r'\bbetter off without me\b'
                ],
                'weight': 0.6
            },
            'pain': {
                'patterns': [
                    r'\bcan\'t take it anymore\b', r'\btoo much pain\b',
                    r'\bcan\'t handle\b', r'\bso much pain\b'
                ],
                'weight': 0.5
            },
            # Medium concern
            'help_seeking': {
                'patterns': [
                    r'\bneed help\b', r'\bplease help\b', r'\bhelp me\b',
                    r'\bdon\'t know what to do\b'
                ],
                'weight': 0.4
            }
        }
        
        # Protective factors (reduce score)
        self.protective_patterns = [
            r'\bgetting help\b', r'\bin therapy\b', r'\bseeing therapist\b',
            r'\btalking to someone\b', r'\bfamily supports\b', r'\bfriends care\b'
        ]
        
        # Crisis resources
        self.crisis_resources = [
            {
                "name": "988 Suicide & Crisis Lifeline",
                "contact": "Call/Text 988",
                "available": "24/7"
            },
            {
                "name": "Crisis Text Line",
                "contact": "Text HOME to 741741",
                "available": "24/7"
            },
            {
                "name": "International Association for Suicide Prevention",
                "contact": "https://www.iasp.info/resources/Crisis_Centres/",
                "available": "Global directory"
            }
        ]
    
    def analyze_message(self, message: str, conversation_history: List[Dict]) -> Dict:
        """
        Analyze a message for crisis signals
        
        Returns:
            {
                'crisis_score': float (0-1),
                'risk_level': str (LOW/MEDIUM/HIGH),
                'risk_level_numeric': int (1-3),
                'detected_signals': list,
                'behavioral_flags': dict,
                'resources': list,
                'recommended_action': str
            }
        """
        message_lower = message.lower()
        detected_signals = []
        crisis_score = 0.0
        
        # 1. Keyword-based detection
        for category, config in self.crisis_patterns.items():
            for pattern in config['patterns']:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    detected_signals.append({
                        'type': category,
                        'weight': config['weight'],
                        'matched_pattern': pattern
                    })
                    crisis_score += config['weight']
                    logger.warning(f"Crisis signal detected: {category} in message")
        
        # 2. Check for protective factors
        protective_count = 0
        for pattern in self.protective_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                protective_count += 1
        
        # Reduce score based on protective factors
        if protective_count > 0:
            crisis_score *= (1 - (protective_count * 0.15))
        
        # 3. Behavioral analysis
        behavioral_flags = self._analyze_behavioral_patterns(
            message, 
            conversation_history
        )
        
        # Adjust score based on behavioral flags
        if behavioral_flags['rapid_escalation']:
            crisis_score += 0.2
        if behavioral_flags['late_night_distress']:
            crisis_score += 0.15
        if behavioral_flags['conversation_length_concern']:
            crisis_score += 0.1
        
        # 4. Normalize score to 0-1 range
        crisis_score = min(crisis_score, 1.0)
        
        # 5. Determine risk level
        if crisis_score >= 0.7:
            risk_level = "HIGH"
            risk_level_numeric = 3
            recommended_action = "IMMEDIATE_ESCALATION"
        elif crisis_score >= 0.4:
            risk_level = "MEDIUM"
            risk_level_numeric = 2
            recommended_action = "ENHANCED_MONITORING"
        else:
            risk_level = "LOW"
            risk_level_numeric = 1
            recommended_action = "STANDARD_SUPPORT"
        
        result = {
            'crisis_score': round(crisis_score, 3),
            'risk_level': risk_level,
            'risk_level_numeric': risk_level_numeric,
            'detected_signals': detected_signals,
            'behavioral_flags': behavioral_flags,
            'recommended_action': recommended_action,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add resources if high risk
        if risk_level in ['MEDIUM', 'HIGH']:
            result['resources'] = self.crisis_resources
        
        return result
    
    def _analyze_behavioral_patterns(
        self, 
        current_message: str, 
        history: List[Dict]
    ) -> Dict:
        """Analyze behavioral patterns in conversation"""
        
        flags = {
            'rapid_escalation': False,
            'late_night_distress': False,
            'conversation_length_concern': False,
            'message_frequency_spike': False
        }
        
        # Check conversation length
        if len(history) > 20:
            flags['conversation_length_concern'] = True
        
        # Check time of day (higher risk during late night/early morning)
        current_hour = datetime.now().hour
        if current_hour >= 23 or current_hour <= 5:
            flags['late_night_distress'] = True
        
        # Check for rapid escalation in recent messages
        if len(history) >= 4:
            recent_messages = history[-4:]
            # Simple heuristic: look for increasing negative sentiment
            negative_words = ['bad', 'worse', 'terrible', 'awful', 'can\'t', 'no']
            negative_counts = []
            
            for msg in recent_messages:
                if msg.get('role') == 'user':
                    content = msg.get('content', '').lower()
                    count = sum(1 for word in negative_words if word in content)
                    negative_counts.append(count)
            
            # Check if sentiment is worsening
            if len(negative_counts) >= 2:
                if negative_counts[-1] > negative_counts[0]:
                    flags['rapid_escalation'] = True
        
        # Check message frequency (messages within short time window)
        if len(history) >= 3:
            recent_messages = history[-3:]
            timestamps = []
            
            for msg in recent_messages:
                ts_str = msg.get('timestamp')
                if ts_str:
                    try:
                        timestamps.append(datetime.fromisoformat(ts_str))
                    except:
                        pass
            
            if len(timestamps) >= 2:
                time_diff = (timestamps[-1] - timestamps[0]).total_seconds()
                if time_diff < 60:  # 3+ messages in less than 1 minute
                    flags['message_frequency_spike'] = True
        
        return flags
    
    def get_intervention_guidance(self, analysis: Dict) -> str:
        """Get specific intervention guidance based on analysis"""
        
        risk_level = analysis['risk_level']
        signals = analysis['detected_signals']
        
        if risk_level == 'HIGH':
            return """
            IMMEDIATE ACTION REQUIRED:
            1. Human intervention needed within 5 minutes
            2. Offer crisis resources immediately
            3. Maintain connection - do not leave user alone
            4. Consider emergency services if imminent danger
            5. Document all interactions
            """
        elif risk_level == 'MEDIUM':
            return """
            ENHANCED MONITORING:
            1. Continue conversation with increased attention
            2. Gently suggest professional resources
            3. Monitor for escalation
            4. Follow up within 24 hours if possible
            """
        else:
            return """
            STANDARD SUPPORT:
            1. Provide empathetic, supportive responses
            2. Continue normal conversation flow
            3. Routine monitoring
            """