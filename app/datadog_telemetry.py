"""
Datadog Telemetry Module
Custom events, metrics, and incident creation
"""
import datadog_api_client
from datadog import api, initialize, statsd
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.case_management_api import CaseManagementApi
from datadog_api_client.v2.model.case_create_request import CaseCreateRequest
from datadog_api_client.v2.model.case_create import CaseCreate
from datadog_api_client.v2.model.case_type import CaseType
from datadog_api_client.v2.model.case_priority import CasePriority
from datadog_api_client.v2.model.case_attributes import CaseAttributes

import os
import logging
from datetime import datetime
from typing import Dict, Optional
import json

logger = logging.getLogger(__name__)

class DatadogTelemetry:
    """Custom Datadog integration for mental health monitoring"""
    
    def __init__(self):
        # Initialize Datadog API
        options = {
            'api_key': os.environ.get('DD_API_KEY'),
            'app_key': os.environ.get('DD_APP_KEY')
        }
        initialize(**options)
        
        # Setup API client for Case Management
        self.configuration = Configuration()
        self.configuration.api_key['apiKeyAuth'] = os.environ.get('DD_API_KEY')
        self.configuration.api_key['appKeyAuth'] = os.environ.get('DD_APP_KEY')
        
        logger.info("Datadog telemetry initialized")
    
    def create_crisis_event(
        self,
        session_id: str,
        crisis_analysis: Dict,
        user_message: str,
        session_context: Dict
    ):
        """Create a Datadog event for crisis detection"""
        
        risk_level = crisis_analysis['risk_level']
        crisis_score = crisis_analysis['crisis_score']
        
        # Anonymize user message for privacy (keep first/last 3 words)
        words = user_message.split()
        if len(words) > 10:
            anonymized = f"{' '.join(words[:3])} [...] {' '.join(words[-3:])}"
        else:
            anonymized = "[Content anonymized for privacy]"
        
        event_title = f"🚨 {risk_level} Risk Crisis Detected - Session {session_id[:8]}"
        
        event_text = f"""
**Crisis Alert**: {risk_level} risk detected (score: {crisis_score})

**Session Context**:
- Session ID: `{session_id}`
- Message Count: {len(session_context.get('messages', []))}
- Session Duration: {self._calculate_duration(session_context.get('created_at'))}
- Total Tokens Used: {session_context.get('total_tokens', 0)}
- Total Cost: ${session_context.get('total_cost', 0):.4f}

**Detected Signals**:
{self._format_signals(crisis_analysis.get('detected_signals', []))}

**Behavioral Flags**:
{self._format_behavioral_flags(crisis_analysis.get('behavioral_flags', {}))}

**Recommended Action**: {crisis_analysis.get('recommended_action', 'UNKNOWN')}

**Crisis Resources Provided**: {'Yes' if crisis_analysis.get('resources') else 'No'}

**Anonymized Message Preview**: {anonymized}

---
**IMMEDIATE ACTIONS REQUIRED**:
1. Review full conversation transcript (available in session logs)
2. Verify crisis resources were provided
3. Consider human intervention
4. Document response actions taken
        """
        
        # Determine alert level
        alert_type = 'error' if risk_level == 'HIGH' else 'warning'
        priority = 'normal'
        
        try:
            # Create Datadog event
            api.Event.create(
                title=event_title,
                text=event_text,
                tags=[
                    f"session_id:{session_id}",
                    f"risk_level:{risk_level}",
                    f"crisis_score:{crisis_score}",
                    "service:mental-health-bot",
                    "event_type:crisis_detection",
                    f"action:{crisis_analysis.get('recommended_action')}"
                ],
                alert_type=alert_type,
                priority=priority,
                source_type_name='mental-health-monitor'
            )
            
            logger.info(f"Created Datadog event for {risk_level} risk crisis")
            
            # If HIGH risk, also create a Case for incident management
            if risk_level == 'HIGH':
                self._create_case(
                    session_id=session_id,
                    crisis_analysis=crisis_analysis,
                    session_context=session_context,
                    anonymized_message=anonymized
                )
            
        except Exception as e:
            logger.error(f"Failed to create Datadog event: {str(e)}", exc_info=True)
    
    def _create_case(
        self,
        session_id: str,
        crisis_analysis: Dict,
        session_context: Dict,
        anonymized_message: str
    ):
        """Create a Case in Datadog for high-risk incidents"""
        
        try:
            with ApiClient(self.configuration) as api_client:
                api_instance = CaseManagementApi(api_client)
                
                # Build case description
                case_description = f"""
# High-Risk Crisis Detected

## Session Information
- **Session ID**: `{session_id}`
- **Detection Time**: {datetime.now().isoformat()}
- **Crisis Score**: {crisis_analysis['crisis_score']}
- **Risk Level**: {crisis_analysis['risk_level']}

## Crisis Indicators
{self._format_signals(crisis_analysis.get('detected_signals', []))}

## Behavioral Analysis
{self._format_behavioral_flags(crisis_analysis.get('behavioral_flags', {}))}

## Session Metrics
- Messages: {len(session_context.get('messages', []))}
- Duration: {self._calculate_duration(session_context.get('created_at'))}
- Tokens: {session_context.get('total_tokens', 0)}

## Action Items

### Immediate (Within 5 minutes)
- [ ] Review full conversation transcript in Datadog logs
- [ ] Verify crisis resources (988 Lifeline) were provided to user
- [ ] Assess if emergency services notification needed
- [ ] Document initial assessment

### Follow-up (Within 1 hour)
- [ ] Attempt to maintain connection with user if possible
- [ ] Review conversation patterns for systemic insights
- [ ] Update crisis detection algorithms if needed
- [ ] Notify on-call mental health professional (if available)

### Resolution
- [ ] Document outcome and actions taken
- [ ] Update incident response procedures if needed
- [ ] Add learnings to crisis response playbook

## Resources
- [Crisis Response Runbook](https://docs.example.com/crisis-runbook)
- [Session Logs in Datadog](https://app.datadoghq.com/logs?query=session_id:{session_id})
- [National Suicide Prevention Lifeline](https://988lifeline.org/)

---
**Last Message (Anonymized)**: {anonymized_message}
                """
                
                case_title = f"CRISIS: High Risk Detected - {session_id[:12]}"
                
                body = CaseCreateRequest(
                    data=CaseCreate(
                        attributes=CaseAttributes(
                            title=case_title,
                            type=CaseType.STANDARD,
                            priority=CasePriority.P1,  # Highest priority
                            description=case_description
                        ),
                        type="case"
                    )
                )
                
                response = api_instance.create_case(body=body)
                
                case_id = response.data.id
                logger.info(f"Created Datadog Case {case_id} for high-risk crisis")
                
                # Add metric for case creation
                statsd.increment('cases.created', tags=[
                    'priority:p1',
                    'type:crisis'
                ])
                
        except Exception as e:
            logger.error(f"Failed to create Datadog case: {str(e)}", exc_info=True)
    
    def _format_signals(self, signals: list) -> str:
        """Format detected crisis signals for display"""
        if not signals:
            return "- No specific crisis keywords detected"
        
        formatted = []
        for signal in signals:
            signal_type = signal.get('type', 'unknown')
            weight = signal.get('weight', 0)
            formatted.append(f"- **{signal_type}** (weight: {weight})")
        
        return "\n".join(formatted)
    
    def _format_behavioral_flags(self, flags: dict) -> str:
        """Format behavioral flags for display"""
        if not flags:
            return "- No behavioral concerns"
        
        formatted = []
        for flag, value in flags.items():
            status = "⚠️ YES" if value else "✓ No"
            flag_name = flag.replace('_', ' ').title()
            formatted.append(f"- {flag_name}: {status}")
        
        return "\n".join(formatted)
    
    def _calculate_duration(self, created_at) -> str:
        """Calculate session duration"""
        if not created_at:
            return "Unknown"
        
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except:
                return "Unknown"
        
        duration = datetime.now() - created_at
        minutes = int(duration.total_seconds() / 60)
        
        if minutes < 1:
            return "< 1 minute"
        elif minutes == 1:
            return "1 minute"
        else:
            return f"{minutes} minutes"
    
    def record_custom_metric(self, metric_name: str, value: float, tags: list = None):
        """Record a custom metric to Datadog"""
        try:
            statsd.gauge(metric_name, value, tags=tags or [])
        except Exception as e:
            logger.error(f"Failed to record metric {metric_name}: {str(e)}")