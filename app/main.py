"""
Mental Health Crisis Detection System - Main Application
Monitors LLM conversations for crisis signals with Datadog observability
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime
import uuid
import time
import os

# Datadog imports
from ddtrace import tracer, patch_all
from datadog import initialize, statsd
import logging

# Custom modules
from .vertex_ai_client import VertexAIClient
from .crisis_detector import CrisisDetector
from .datadog_telemetry import DatadogTelemetry

# Initialize Datadog
patch_all()

options = {
    'statsd_host': '127.0.0.1',
    'statsd_port': 8125,
}
initialize(**options)

# Setup logging with Datadog
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mental Health Support Bot")

# Initialize components
vertex_client = VertexAIClient()
crisis_detector = CrisisDetector()
dd_telemetry = DatadogTelemetry()

# In-memory session storage (use Redis in production)
sessions = {}

class Message(BaseModel):
    session_id: Optional[str] = None
    user_message: str
    user_metadata: Optional[dict] = {}

class SessionMetrics(BaseModel):
    session_id: str
    message_count: int
    crisis_score: float
    risk_level: str
    conversation_duration: float

@app.on_event("startup")
async def startup_event():
    logger.info("Mental Health Crisis Monitor starting up")
    statsd.increment('app.startup')

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the chat interface"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mental Health Support Chat</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            
            .chat-container {
                background: white;
                border-radius: 16px;
                padding: 30px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                width: 100%;
                max-width: 800px;
                height: 90vh;
                display: flex;
                flex-direction: column;
            }
            
            h1 {
                color: #667eea;
                margin-bottom: 20px;
                font-size: 28px;
                font-weight: 600;
            }
            
            .crisis-banner {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                padding: 16px 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                display: none;
                animation: slideIn 0.3s ease-out;
            }
            
            @keyframes slideIn {
                from {
                    transform: translateY(-20px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }
            
            .crisis-banner strong {
                display: block;
                margin-bottom: 8px;
                font-size: 16px;
            }
            
            .crisis-banner a {
                color: white;
                text-decoration: underline;
            }
            
            .messages {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                border: 2px solid #f0f0f0;
                border-radius: 10px;
                margin-bottom: 20px;
                background: #fafafa;
            }
            
            .message {
                margin-bottom: 16px;
                padding: 12px 16px;
                border-radius: 12px;
                max-width: 80%;
                animation: messageSlide 0.2s ease-out;
                line-height: 1.6;
            }
            
            @keyframes messageSlide {
                from {
                    transform: translateY(10px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }
            
            .user {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin-left: auto;
                text-align: right;
                border-bottom-right-radius: 4px;
            }
            
            .bot {
                background: white;
                color: #333;
                border: 2px solid #e0e0e0;
                margin-right: auto;
                border-bottom-left-radius: 4px;
                white-space: pre-wrap;
            }
            
            .typing {
                display: none;
                background: white;
                border: 2px solid #e0e0e0;
                color: #666;
                font-style: italic;
                max-width: 100px;
            }
            
            .input-area {
                display: flex;
                gap: 12px;
            }
            
            input {
                flex: 1;
                padding: 14px 18px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                font-size: 15px;
                transition: border-color 0.2s;
            }
            
            input:focus {
                outline: none;
                border-color: #667eea;
            }
            
            button {
                padding: 14px 32px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                font-size: 15px;
                font-weight: 600;
                transition: transform 0.1s, box-shadow 0.2s;
            }
            
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            }
            
            button:active {
                transform: translateY(0);
            }
            
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .messages::-webkit-scrollbar {
                width: 8px;
            }
            
            .messages::-webkit-scrollbar-track {
                background: #f0f0f0;
                border-radius: 10px;
            }
            
            .messages::-webkit-scrollbar-thumb {
                background: #c0c0c0;
                border-radius: 10px;
            }
            
            .messages::-webkit-scrollbar-thumb:hover {
                background: #a0a0a0;
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <h1>🤝 Mental Health Support</h1>
            <div id="crisis-banner" class="crisis-banner">
                <strong>⚠️ Crisis Resources Available</strong>
                If you're in crisis: <a href="tel:988">988 Suicide & Crisis Lifeline</a> | 
                Text HOME to 741741
            </div>
            <div id="messages" class="messages">
                <div class="message bot">
                    Hello, I'm here to listen and support you. How are you feeling today?
                </div>
            </div>
            <div class="message typing" id="typing">Thinking...</div>
            <div class="input-area">
                <input type="text" id="userInput" placeholder="Type your message..." />
                <button onclick="sendMessage()" id="sendBtn">Send</button>
            </div>
        </div>
        
        <script>
            let sessionId = localStorage.getItem('session_id') || Math.random().toString(36).substr(2, 9);
            localStorage.setItem('session_id', sessionId);
            
            async function sendMessage() {
                const input = document.getElementById('userInput');
                const sendBtn = document.getElementById('sendBtn');
                const typing = document.getElementById('typing');
                const message = input.value.trim();
                
                if (!message) return;
                
                // Disable input while processing
                input.disabled = true;
                sendBtn.disabled = true;
                typing.style.display = 'block';
                
                addMessage('user', message);
                input.value = '';
                
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            session_id: sessionId,
                            user_message: message
                        })
                    });
                    
                    const data = await response.json();
                    
                    typing.style.display = 'none';
                    addMessage('bot', data.response);
                    
                    if (data.crisis_detected) {
                        document.getElementById('crisis-banner').style.display = 'block';
                    }
                } catch (error) {
                    typing.style.display = 'none';
                    addMessage('bot', 'I apologize, but I encountered an error. Please try again.');
                    console.error('Error:', error);
                } finally {
                    input.disabled = false;
                    sendBtn.disabled = false;
                    input.focus();
                }
            }
            
            function addMessage(sender, text) {
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}`;
                messageDiv.textContent = text;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            document.getElementById('userInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            
            // Focus input on load
            document.getElementById('userInput').focus();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/chat")
@tracer.wrap(service="mental-health-bot", resource="chat")
async def chat(message: Message):
    """Handle chat messages with full observability"""
    
    start_time = time.time()
    session_id = message.session_id or str(uuid.uuid4())
    
    # Initialize session if new
    if session_id not in sessions:
        sessions[session_id] = {
            "messages": [],
            "created_at": datetime.now(),
            "crisis_scores": [],
            "total_tokens": 0,
            "total_cost": 0.0
        }
        statsd.increment('sessions.created')
    
    session = sessions[session_id]
    user_message = message.user_message
    
    # Add span tags for Datadog APM
    span = tracer.current_span()
    if span:
        span.set_tag("session_id", session_id)
        span.set_tag("message_length", len(user_message))
        span.set_tag("message_count", len(session["messages"]))
    
    try:
        # Crisis detection BEFORE LLM call
        crisis_analysis = crisis_detector.analyze_message(
            user_message, 
            session["messages"]
        )
        
        # Log crisis metrics
        statsd.gauge('crisis.score', crisis_analysis['crisis_score'])
        statsd.gauge('crisis.risk_level', crisis_analysis['risk_level_numeric'])
        
        if span:
            span.set_tag("crisis_score", crisis_analysis['crisis_score'])
            span.set_tag("risk_level", crisis_analysis['risk_level'])
        
        # Generate response using Vertex AI
        llm_start = time.time()
        llm_response = await vertex_client.generate_response(
            user_message=user_message,
            conversation_history=session["messages"],
            crisis_context=crisis_analysis
        )
        llm_latency = time.time() - llm_start
        
        # Record LLM metrics
        statsd.histogram('llm.latency', llm_latency * 1000)  # in ms
        statsd.increment('llm.requests')
        statsd.gauge('llm.tokens.input', llm_response.get('input_tokens', 0))
        statsd.gauge('llm.tokens.output', llm_response.get('output_tokens', 0))
        statsd.gauge('llm.cost', llm_response.get('estimated_cost', 0))
        
        # Update session
        session["messages"].append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        session["messages"].append({
            "role": "assistant",
            "content": llm_response['text'],
            "timestamp": datetime.now().isoformat()
        })
        session["crisis_scores"].append(crisis_analysis['crisis_score'])
        session["total_tokens"] += llm_response.get('total_tokens', 0)
        session["total_cost"] += llm_response.get('estimated_cost', 0)
        
        # Create Datadog event if crisis detected
        if crisis_analysis['risk_level'] == 'HIGH':
            dd_telemetry.create_crisis_event(
                session_id=session_id,
                crisis_analysis=crisis_analysis,
                user_message=user_message,
                session_context=session
            )
            statsd.increment('crisis.high_risk_detected')
        
        # Calculate response time
        total_latency = time.time() - start_time
        statsd.histogram('request.latency', total_latency * 1000)
        
        # Log structured event
        logger.info(
            "Chat interaction processed",
            extra={
                "session_id": session_id,
                "crisis_score": crisis_analysis['crisis_score'],
                "risk_level": crisis_analysis['risk_level'],
                "llm_latency_ms": llm_latency * 1000,
                "total_latency_ms": total_latency * 1000,
                "tokens_used": llm_response.get('total_tokens', 0)
            }
        )
        
        return {
            "session_id": session_id,
            "response": llm_response['text'],
            "crisis_detected": crisis_analysis['risk_level'] in ['MEDIUM', 'HIGH'],
            "risk_level": crisis_analysis['risk_level'],
            "crisis_resources": crisis_analysis.get('resources', []) if crisis_analysis['risk_level'] == 'HIGH' else []
        }
        
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}", exc_info=True)
        statsd.increment('errors.chat_processing')
        if span:
            span.set_tag("error", True)
            span.set_tag("error.message", str(e))
        raise HTTPException(status_code=500, detail="Error processing message")

@app.get("/metrics")
async def get_metrics():
    """Endpoint for health checks and metrics"""
    total_sessions = len(sessions)
    high_risk_sessions = sum(
        1 for s in sessions.values() 
        if s['crisis_scores'] and max(s['crisis_scores']) > 0.7
    )
    
    return {
        "status": "healthy",
        "total_sessions": total_sessions,
        "high_risk_sessions": high_risk_sessions,
        "avg_session_length": sum(len(s['messages']) for s in sessions.values()) / max(total_sessions, 1)
    }

@app.get("/health")
async def health_check():
    """Health check for Cloud Run"""
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)