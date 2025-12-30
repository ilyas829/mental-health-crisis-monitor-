"""
Vertex AI / Gemini Client
Handles LLM interactions with safety controls and cost tracking
"""

import os
import logging
from typing import List, Dict, Optional
import time
import json

# Vertex AI imports
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel, GenerationConfig
from vertexai.generative_models import SafetySetting, HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)

class VertexAIClient:
    """Client for Vertex AI Gemini models with observability"""
    
    def __init__(self):
        # Initialize Vertex AI
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'mental-health-monitor-482612')
        location = os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')
        
        aiplatform.init(project=project_id, location=location)
        
        # Use Gemini 1.5 Flash for cost efficiency
        self.model_name = "gemini-2.0-flash-lite-001"
        self.model = GenerativeModel(self.model_name)
        
        # Pricing (approximate, as of Dec 2024)
        self.pricing = {
            'input_per_1k_tokens': 0.00001875,  # $0.01875 per 1M tokens
            'output_per_1k_tokens': 0.000075    # $0.075 per 1M tokens
        }
        
        # Safety settings - be permissive for mental health context
        # but block genuinely harmful content
        self.safety_settings = [
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
        ]
        
        # Generation config
        self.generation_config = GenerationConfig(
            temperature=0.8,
            top_p=0.9,
            top_k=40,
            max_output_tokens=1004,
        )
        
        logger.info(f"Vertex AI client initialized with model: {self.model_name}")
    
    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict],
        crisis_context: Optional[Dict] = None
    ) -> Dict:
        """
        Generate response using Gemini with crisis-aware context
        
        Returns:
            {
                'text': str,
                'input_tokens': int,
                'output_tokens': int,
                'total_tokens': int,
                'estimated_cost': float,
                'latency_ms': float,
                'safety_ratings': dict,
                'finish_reason': str
            }
        """
        start_time = time.time()
        
        try:
            # Build system instruction based on crisis level
            system_instruction = self._build_system_instruction(crisis_context)
            
            # Format conversation history for Gemini
            chat_history = self._format_history(conversation_history)
            
            # Create chat session
            chat = self.model.start_chat(history=chat_history)
            
            # Generate response
            response = chat.send_message(
                user_message,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings,
                stream=False
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract usage metadata
            usage_metadata = response.usage_metadata if hasattr(response, 'usage_metadata') else None
            
            input_tokens = usage_metadata.prompt_token_count if usage_metadata else self._estimate_tokens(user_message + str(chat_history))
            output_tokens = usage_metadata.candidates_token_count if usage_metadata else self._estimate_tokens(response.text)
            total_tokens = input_tokens + output_tokens
            
            # Calculate cost
            estimated_cost = (
                (input_tokens / 1000) * self.pricing['input_per_1k_tokens'] +
                (output_tokens / 1000) * self.pricing['output_per_1k_tokens']
            )
            
            # Extract safety ratings
            safety_ratings = {}
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'safety_ratings'):
                    for rating in candidate.safety_ratings:
                        safety_ratings[rating.category.name] = rating.probability.name
            
            # Get finish reason
            finish_reason = "STOP"
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = candidate.finish_reason.name
            
            result = {
                'text': response.text,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': total_tokens,
                'estimated_cost': estimated_cost,
                'latency_ms': latency_ms,
                'safety_ratings': safety_ratings,
                'finish_reason': finish_reason,
                'model': self.model_name
            }
            
            logger.info(
                f"LLM response generated: {total_tokens} tokens, "
                f"${estimated_cost:.6f} cost, {latency_ms:.2f}ms latency"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            
            # Return safe fallback response
            return {
                'text': self._get_fallback_response(crisis_context),
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'estimated_cost': 0.0,
                'latency_ms': (time.time() - start_time) * 1000,
                'safety_ratings': {},
                'finish_reason': 'ERROR',
                'error': str(e),
                'model': self.model_name
            }
    # async def generate_response(
    #     self, user_message: str, conversation_history: List[Dict], crisis_context: Optional[Dict] = None
    # ) -> Dict:
    #     """Generate response using Gemini - NO HISTORY (challenge demo)"""
    #     start_time = time.time()

    #     try:
    #         # Build crisis-aware prompt (no chat session)
    #         system_instruction = self._build_system_instruction(crisis_context)
    #         full_prompt = f"{system_instruction}\n\nUser: {user_message}"

    #         # Single-shot generation (bulletproof)
    #         response = self.model.generate_content(
    #             full_prompt,
    #             generation_config=self.generation_config,
    #             safety_settings=self.safety_settings
    #         )

    #         latency_ms = (time.time() - start_time) * 1000

    #         # Extract response data
    #         text = response.text if hasattr(response, 'text') else str(response)
    #         input_tokens = getattr(response, 'usage_metadata', {}).prompt_token_count if hasattr(response, 'usage_metadata') else self._estimate_tokens(full_prompt)
    #         output_tokens = getattr(response, 'usage_metadata', {}).candidates_token_count if hasattr(response, 'usage_metadata') else self._estimate_tokens(text)
    #         total_tokens = input_tokens + output_tokens

    #         # Cost calculation
    #         estimated_cost = (
    #             (input_tokens / 1000) * self.pricing['input_per_1k_tokens'] +
    #             (output_tokens / 1000) * self.pricing['output_per_1k_tokens']
    #         )

    #         result = {
    #             'text': text,
    #             'input_tokens': input_tokens,
    #             'output_tokens': output_tokens,
    #             'total_tokens': total_tokens,
    #             'estimated_cost': estimated_cost,
    #             'latency_ms': latency_ms,
    #             'safety_ratings': {},
    #             'finish_reason': 'STOP',
    #             'model': self.model_name
    #         }

    #         logger.info(f"LLM response: {total_tokens} tokens, ${estimated_cost:.6f}")
    #         return result

    #     except Exception as e:
    #         logger.error(f"Error generating response: {str(e)}")
    #         return {
    #             'text': self._get_fallback_response(crisis_context),
    #             'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0,
    #             'estimated_cost': 0.0, 'latency_ms': (time.time() - start_time) * 1000,
    #             'safety_ratings': {}, 'finish_reason': 'ERROR', 'error': str(e)
    #         }

    
    def _build_system_instruction(self, crisis_context: Optional[Dict]) -> str:
        """Build context-aware system instruction"""
        
        base_instruction = """You are a compassionate mental health support assistant. Your role is to:
        
    1. Listen empathetically and validate feelings
    2. Provide brief, focused responses (2-3 paragraphs maximum)
    3. Use natural, conversational language - not lists or bullet points
    4. Never provide medical advice or diagnoses
    5. Encourage professional help when appropriate
    6. Maintain a supportive, non-judgmental tone
    7. Be honest about your limitations as an AI

    IMPORTANT FORMATTING RULES:
    - Keep responses concise (under 150 words)
    - Use short paragraphs (2-3 sentences each)
    - No bullet points or numbered lists
    - Natural conversation flow
    - One question per response maximum"""
        
        if not crisis_context:
            return base_instruction
        
        risk_level = crisis_context.get('risk_level', 'LOW')
        
        if risk_level == 'HIGH':
            return base_instruction + """
            
    CRISIS MODE - CRITICAL:
    This person may be in immediate danger. Your response MUST:
    1. Acknowledge their pain with empathy
    2. Immediately provide crisis resources in your first paragraph:
    "I'm deeply concerned about your safety. Please reach out for immediate help:
    • Call or text 988 (Suicide & Crisis Lifeline) - available 24/7
    • Text HOME to 741741 (Crisis Text Line)
    These counselors are trained to help and want to support you."
    3. Encourage staying connected
    4. Express genuine care
    5. DO NOT end the conversation abruptly
    6. Keep your full response under 100 words

    Example structure:
    "I hear that you're in tremendous pain right now, and I'm truly concerned about your safety. [Crisis resources]. You don't have to face this alone. Would you be willing to reach out to one of these services? I'm here with you right now."
    """
        
        elif risk_level == 'MEDIUM':
            return base_instruction + """
            
    ELEVATED CONCERN MODE:
    This person is showing signs of significant distress. Your response should:
    1. Validate their feelings with empathy
    2. Gently explore their support system
    3. Suggest professional resources if appropriate (therapist, counselor)
    4. Stay engaged and supportive
    5. Keep response focused and under 120 words

    Example: "I can hear that you're going through a really difficult time. That kind of pain is real and valid. Have you been able to talk with anyone about how you're feeling? Sometimes having support - whether from friends, family, or a professional - can make things feel a little more manageable. I'm here to listen if you'd like to talk more about what's been going on."
    """
        
        return base_instruction
    
    def _format_history(self, history: List[Dict]) -> List[Dict]:
        """Format conversation history for Gemini API"""
        from vertexai.generative_models import Content, Part
        formatted = []
        
        for msg in history:
            role = msg.get('role')
            content = msg.get('content', '')
            
            # if role == 'user':
            #     formatted.append({
            #         'role': 'user',
            #         'parts': [{'text': content}]
            #     })
            # elif role == 'assistant':
            #     formatted.append({
            #         'role': 'model',
            #         'parts': [{'text': content}]
            #     })
            if role == 'user':
                formatted.append(Content(role="user", parts=[Part.from_text(content)]))
            elif role == 'assistant':
                formatted.append(Content(role="model", parts=[Part.from_text(content)]))
        
        return formatted
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters for English)"""
        return max(1, len(text) // 4)
    
    def _get_fallback_response(self, crisis_context: Optional[Dict]) -> str:
        """Safe fallback response if LLM fails"""
        
        if crisis_context and crisis_context.get('risk_level') == 'HIGH':
            return """I'm experiencing a technical difficulty, but I want you to know that help is available right now. 
            
            Please reach out to:
            - 112 Suicide & Crisis Lifeline (call or text 112)
            - Crisis Text Line (text HOME to 741741)
            
            You don't have to go through this alone. These trained counselors are available 24/7 and want to help."""
        
        return """I'm having trouble processing your message right now, but I'm here to listen. 
        Could you try rephrasing what you'd like to talk about?"""