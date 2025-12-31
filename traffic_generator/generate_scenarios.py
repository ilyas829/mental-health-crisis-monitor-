"""
Traffic Generator for Mental Health Crisis Monitor
Simulates various conversation scenarios to test detection rules
"""

import requests
import time
import random
import json
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScenarioGenerator:
    """Generate realistic conversation scenarios"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.scenarios = self._define_scenarios()
    
    def _define_scenarios(self) -> Dict[str, List[str]]:
        """Define test scenarios with varying risk levels"""
        
        return {
            # LOW RISK - Normal support seeking
            'low_risk_general': [
                "Hi, I've been feeling a bit down lately",
                "I'm struggling with work stress",
                "I had a bad day today",
                "Can you help me feel better?",
                "Thank you, that helps"
            ],
            
            'low_risk_anxiety': [
                "I've been feeling anxious about my job interview",
                "I can't stop worrying about everything",
                "My anxiety has been high this week",
                "I'm seeing a therapist which helps",
                "Thanks for listening"
            ],
            
            # MEDIUM RISK - Elevated distress
            'medium_risk_hopeless': [
                "I don't know what to do anymore",
                "Everything feels hopeless",
                "I feel like giving up on everything",
                "Nobody really understands what I'm going through",
                "I just need someone to talk to"
            ],
            
            'medium_risk_isolation': [
                "I feel so alone all the time",
                "No one really cares about me",
                "I'm completely isolated from everyone",
                "I don't have anyone I can talk to",
                "It's been getting worse lately"
            ],
            
            # HIGH RISK - Crisis indicators
            'high_risk_suicidal': [
                "I've been thinking about suicide",
                "I don't want to live anymore",
                "I can't take this pain anymore",
                "I've been planning how to end it",
                "There's no point in going on"
            ],
            
            'high_risk_immediate': [
                "I want to kill myself tonight",
                "I have everything planned out",
                "Nobody will miss me when I'm gone",
                "I'm going to end it all",
                "This is too much to handle"
            ],
            
            # ESCALATION - Conversation that worsens
            'escalating_crisis': [
                "I'm feeling really stressed",
                "Things are getting worse",
                "I can't handle this anymore",
                "I'm thinking of ending it all",
                "I don't want to be here anymore"
            ],
            
            # RAPID FIRE - High frequency messages (behavioral flag)
            'rapid_fire_distress': [
                "Help",
                "Please help me",
                "I need help now",
                "Can someone please help",
                "I'm scared"
            ],
            
            # LATE NIGHT - Time-based risk factor
            'late_night_crisis': [
                "Can't sleep, feeling terrible",
                "3am and I'm thinking dark thoughts",
                "Everyone's asleep and I'm alone with these thoughts",
                "I don't know if I can make it through the night",
                "Please help"
            ],
            
            # PROTECTIVE FACTORS PRESENT
            'low_risk_with_support': [
                "I'm feeling down but my family is supportive",
                "I'm in therapy and it's helping",
                "I have friends I can talk to",
                "Things are tough but I'm getting help",
                "Thank you for the resources"
            ]
        }
    
    def run_scenario(self, scenario_name: str, delay: float = 2.0) -> Dict:
        """
        Run a specific scenario
        
        Args:
            scenario_name: Name of scenario to run
            delay: Delay between messages in seconds
            
        Returns:
            Summary of the scenario execution
        """
        
        if scenario_name not in self.scenarios:
            logger.error(f"Unknown scenario: {scenario_name}")
            return {}
        
        messages = self.scenarios[scenario_name]
        session_id = f"test_{scenario_name}_{int(time.time())}"
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Running scenario: {scenario_name}")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"{'='*60}\n")
        
        results = []
        crisis_detected = False
        max_risk_level = "LOW"
        max_crisis_score = 0.0
        
        for i, message in enumerate(messages):
            logger.info(f"[Message {i+1}/{len(messages)}] User: {message}")
            
            try:
                response = requests.post(
                    f"{self.base_url}/chat",
                    json={
                        "session_id": session_id,
                        "user_message": message
                    },
                    timeout=30
                )
                
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"[Response] Bot: {data['response'][:100]}...")
                logger.info(f"[Risk] Level: {data['risk_level']}, Score: {data.get('crisis_score', 'N/A')}")
                
                if data.get('crisis_detected'):
                    crisis_detected = True
                    logger.warning("⚠️  CRISIS DETECTED!")
                
                # Track highest risk
                risk_level = data['risk_level']
                if risk_level == 'HIGH':
                    max_risk_level = 'HIGH'
                elif risk_level == 'MEDIUM' and max_risk_level != 'HIGH':
                    max_risk_level = 'MEDIUM'
                
                results.append({
                    'message': message,
                    'response': data['response'],
                    'risk_level': risk_level,
                    'crisis_detected': data.get('crisis_detected', False)
                })
                
                # Wait before next message (except for rapid-fire scenarios)
                if 'rapid' not in scenario_name.lower() and i < len(messages) - 1:
                    time.sleep(delay)
                elif 'rapid' in scenario_name.lower():
                    time.sleep(0.5)  # Faster for rapid-fire
                
            except requests.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                results.append({
                    'message': message,
                    'error': str(e)
                })
        
        summary = {
            'scenario': scenario_name,
            'session_id': session_id,
            'total_messages': len(messages),
            'crisis_detected': crisis_detected,
            'max_risk_level': max_risk_level,
            'results': results
        }
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Scenario Complete: {scenario_name}")
        logger.info(f"Crisis Detected: {crisis_detected}")
        logger.info(f"Max Risk Level: {max_risk_level}")
        logger.info(f"{'='*60}\n")
        
        return summary
    
    def run_all_scenarios(self, delay_between_scenarios: float = 5.0):
        """Run all defined scenarios"""
        
        logger.info(f"\n{'#'*60}")
        logger.info(f"Starting Full Scenario Test Suite")
        logger.info(f"Total Scenarios: {len(self.scenarios)}")
        logger.info(f"{'#'*60}\n")
        
        all_results = []
        
        for scenario_name in self.scenarios.keys():
            result = self.run_scenario(scenario_name)
            all_results.append(result)
            
            # Wait between scenarios
            if scenario_name != list(self.scenarios.keys())[-1]:
                logger.info(f"Waiting {delay_between_scenarios}s before next scenario...\n")
                time.sleep(delay_between_scenarios)
        
        # Print summary
        self._print_summary(all_results)
        
        return all_results
    
    def run_stress_test(self, duration_seconds: int = 60):
        """
        Run a stress test with random scenarios
        
        Args:
            duration_seconds: How long to run the stress test
        """
        
        logger.info(f"\n{'#'*60}")
        logger.info(f"Starting Stress Test - Duration: {duration_seconds}s")
        logger.info(f"{'#'*60}\n")
        
        start_time = time.time()
        request_count = 0
        
        while time.time() - start_time < duration_seconds:
            # Pick random scenario
            scenario_name = random.choice(list(self.scenarios.keys()))
            messages = self.scenarios[scenario_name]
            
            # Pick random message from scenario
            message = random.choice(messages)
            session_id = f"stress_{int(time.time())}_{request_count}"
            
            try:
                requests.post(
                    f"{self.base_url}/chat",
                    json={
                        "session_id": session_id,
                        "user_message": message
                    },
                    timeout=10
                )
                request_count += 1
                
                if request_count % 10 == 0:
                    logger.info(f"Stress test: {request_count} requests sent...")
                
            except Exception as e:
                logger.error(f"Stress test request failed: {str(e)}")
            
            # Small delay
            time.sleep(random.uniform(0.1, 0.5))
        
        elapsed = time.time() - start_time
        rps = request_count / elapsed
        
        logger.info(f"\n{'#'*60}")
        logger.info(f"Stress Test Complete")
        logger.info(f"Total Requests: {request_count}")
        logger.info(f"Duration: {elapsed:.2f}s")
        logger.info(f"Requests/Second: {rps:.2f}")
        logger.info(f"{'#'*60}\n")
    
    def _print_summary(self, results: List[Dict]):
        """Print summary of all scenario results"""
        
        logger.info(f"\n{'#'*60}")
        logger.info(f"TEST SUITE SUMMARY")
        logger.info(f"{'#'*60}\n")
        
        total = len(results)
        crisis_detected = sum(1 for r in results if r.get('crisis_detected'))
        high_risk = sum(1 for r in results if r.get('max_risk_level') == 'HIGH')
        medium_risk = sum(1 for r in results if r.get('max_risk_level') == 'MEDIUM')
        
        logger.info(f"Total Scenarios: {total}")
        logger.info(f"Crisis Detected: {crisis_detected}")
        logger.info(f"High Risk: {high_risk}")
        logger.info(f"Medium Risk: {medium_risk}")
        logger.info(f"\nDetailed Results:")
        
        for result in results:
            status = "🚨 CRISIS" if result.get('crisis_detected') else "✓ Normal"
            logger.info(f"  {status} | {result['scenario']} | Risk: {result['max_risk_level']}")


def main():
    """Main function to run traffic generation"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate traffic for mental health crisis monitor')
    parser.add_argument('--url', default='http://localhost:8080', help='Base URL of the application')
    parser.add_argument('--scenario', help='Run specific scenario')
    parser.add_argument('--all', action='store_true', help='Run all scenarios')
    parser.add_argument('--stress', action='store_true', help='Run stress test')
    parser.add_argument('--duration', type=int, default=60, help='Stress test duration (seconds)')
    
    args = parser.parse_args()
    
    generator = ScenarioGenerator(base_url=args.url)
    
    if args.scenario:
        generator.run_scenario(args.scenario)
    elif args.all:
        generator.run_all_scenarios()
    elif args.stress:
        generator.run_stress_test(duration_seconds=args.duration)
    else:
        # Default: run a few key scenarios
        for scenario in ['low_risk_general', 'medium_risk_hopeless', 'high_risk_immediate']:
            generator.run_scenario(scenario)
            time.sleep(5)


if __name__ == "__main__":
    main()