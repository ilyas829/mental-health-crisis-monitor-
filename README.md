# Mental Health Crisis Detection & Monitoring System

> An AI-powered mental health support chatbot with real-time crisis detection, powered by Vertex AI Gemini and monitored through Datadog's observability platform.

## 🎯 The Problem We're Solving

**Global Crisis**: Every 40 seconds, someone dies by suicide globally (WHO). Crisis helplines are overwhelmed, and people increasingly turn to AI chatbots for mental health support.

**Current Gap**: Existing LLM applications lack real-time safety monitoring, crisis detection capabilities, and actionable escalation protocols that could save lives.

**Our Innovation**: A multi-layered observability system that monitors conversations for crisis signals in real-time, automatically escalates high-risk situations, and provides comprehensive operational insights—all while being completely free to deploy.

---

## 🌟 Unique Features

### 1. **Multi-Signal Crisis Detection**
- **Textual Analysis**: Pattern matching for suicide ideation, self-harm, hopelessness
- **Behavioral Anomalies**: Late-night usage, rapid message frequency, conversation escalation
- **Conversation Flow Analysis**: Topic changes, help-seeking language, protective factors
- **Risk Scoring**: 0-1 scale with LOW/MEDIUM/HIGH categorization

### 2. **Three-Tier Alert System**
- **🟢 GREEN (Low Risk)**: Normal monitoring, standard support
- **🟡 YELLOW (Medium Risk)**: Enhanced monitoring, proactive resource offering
- **🔴 RED (High Risk)**: Immediate escalation, automatic case creation, crisis resources

### 3. **Comprehensive Observability**
- **Crisis Metrics**: Real-time risk scores, detection patterns, behavioral flags
- **LLM Performance**: Latency, token usage, costs, response quality
- **Operational Health**: Error rates, availability, session metrics
- **SLO Tracking**: 6 critical service levels with error budgets

### 4. **Actionable Incident Management**
Every high-risk detection automatically creates a Datadog Case with:
- Full conversation context (anonymized)
- Risk assessment breakdown
- Recommended interventions
- Historical pattern data
- Local crisis resources
- Action item checklist

---

## 🏗️ Architecture

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│   FastAPI Application           │
│   ┌─────────────────────┐       │
│   │  Crisis Detector    │───────┼──► Datadog Events
│   │  (Multi-Signal)     │       │
│   └─────────────────────┘       │
│            │                    │
│            ▼                    │
│   ┌─────────────────────┐       │
│   │  Vertex AI Client   │───────┼──► Gemini API
│   │  (Gemini 1.5 Flash) │       │
│   └─────────────────────┘       │
│            │                    │
│            ▼                    │
│   ┌─────────────────────┐       │
│   │ Datadog Telemetry   │───────┼──► Datadog APM/Logs
│   │  (Metrics, Traces)  │       │
│   └─────────────────────┘       │
└─────────────────────────────────┘
                │
                ▼
        ┌───────────────┐
        │   Datadog     │
        │  ┌─────────┐  │
        │  │Monitors │  │──► Alerts
        │  └─────────┘  │
        │  ┌─────────┐  │
        │  │  SLOs   │  │──► Error Budgets
        │  └─────────┘  │
        │  ┌─────────┐  │
        │  │  Cases  │  │──► Incident Mgmt
        │  └─────────┘  │
        └───────────────┘
```

---

## 🚀 Quick Start Deployment

### Prerequisites
- Google Cloud Platform account (free tier)
- Datadog account (30-day free trial)
- Docker installed locally

### Step 1: Clone Repository
```bash
git clone https://github.com/ilyas829/mental-health-crisis-monitor.git
cd mental-health-crisis-monitor
```

### Step 2: Set Up Google Cloud

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize and authenticate
gcloud init
gcloud auth login

# Create project (free tier)
gcloud projects create mental-health-monitor --name="Mental Health Crisis Monitor"
gcloud config set project mental-health-monitor

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    aiplatform.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com

# Enable Vertex AI
gcloud ai models list --region=us-central1
```

### Step 3: Set Up Vertex AI Service Account

```bash
# Create service account
gcloud iam service-accounts create vertex-ai-user \
    --display-name="Vertex AI User"

# Grant permissions
gcloud projects add-iam-policy-binding mental-health-monitor \
    --member="serviceAccount:vertex-ai-user@mental-health-monitor.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create credentials.json \
    --iam-account=vertex-ai-user@mental-health-monitor.iam.gserviceaccount.com
```

### Step 4: Configure Datadog

1. Sign up at [Datadog](https://www.datadoghq.com/) (30-day free trial)
2. Get your API keys:
   - Navigate to: Organization Settings → API Keys
   - Create new API Key
   - Create new Application Key
3. Note your Datadog organization name

### Step 5: Set Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your values
nano .env
```

```bash
# Required variables
DD_API_KEY=your_datadog_api_key
DD_APP_KEY=your_datadog_app_key
GOOGLE_CLOUD_PROJECT=mental-health-monitor
GOOGLE_APPLICATION_CREDENTIALS=./credentials.json
```

### Step 6: Deploy to Cloud Run

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The script will:
1. Build Docker image
2. Push to Google Container Registry
3. Deploy to Cloud Run (free tier: 2M requests/month)
4. Configure Datadog integration
5. Output the public URL

### Step 7: Import Datadog Configurations

```bash
# Install Datadog CLI
npm install -g @datadog/datadog-ci

# Export Datadog credentials
export DATADOG_API_KEY=your_api_key
export DATADOG_APP_KEY=your_app_key

# Import monitors
datadog-ci synthetics upload-application \
    --config datadog_configs/monitors.json

# Import dashboard
# (Manual: Go to Datadog UI → Dashboards → Import JSON)
```

### Step 8: Test the System

```bash
# Install dependencies for traffic generator
pip install requests

# Run traffic generator
python traffic_generator/generate_scenarios.py --all

# Or test specific scenario
python traffic_generator/generate_scenarios.py --scenario high_risk_immediate
```

---

## 📊 Monitoring & Detection Rules

### Detection Rule #1: High-Risk Crisis Detection
**Trigger**: `crisis.risk_level >= 3` (HIGH)
**Severity**: P1 - CRITICAL
**Action**: 
- Create Datadog Case immediately
- Page on-call crisis team
- Provide full conversation context
- Verify crisis resources delivered

**Rationale**: High-risk conversations indicate immediate danger. Human intervention must occur within 5 minutes to potentially save lives.

### Detection Rule #2: Elevated Distress Monitoring
**Trigger**: `avg(crisis.score) >= 0.4` over 10 minutes
**Severity**: P2 - HIGH
**Action**:
- Enhanced monitoring
- Alert monitoring team
- Track for escalation

**Rationale**: Sustained elevated distress across multiple sessions may indicate systemic issues or patterns requiring attention.

### Detection Rule #3: Cost Anomaly Detection
**Trigger**: Token usage or costs exceed 2σ from baseline
**Severity**: P3 - MEDIUM
**Action**:
- Investigate usage patterns
- Check for stuck sessions
- Verify model selection logic

**Rationale**: Unexpected cost spikes could indicate technical issues (retry storms, inefficient prompts) or abuse attempts. Crisis conversations may naturally use more tokens, so context is important.

### Detection Rule #4: Performance Degradation
**Trigger**: `avg(llm.latency) > 3000ms`
**Severity**: P2 - HIGH
**Action**:
- Check Vertex AI status
- Review application logs
- Consider model failover

**Rationale**: Slow responses during crisis conversations increase abandonment risk and delay critical resource delivery.

### Detection Rule #5: High Error Rate
**Trigger**: `sum(errors) > 10` in 5 minutes
**Severity**: P2 - HIGH
**Action**:
- Review error logs
- Check dependency health
- Activate fallback mode if needed

**Rationale**: Errors during crisis conversations are unacceptable. System must maintain 99.5%+ reliability.

### Detection Rule #6: Late-Night Crisis Pattern
**Trigger**: `sum(crisis.high_risk) > 3` in 1 hour during 11 PM - 5 AM
**Severity**: P2 - HIGH
**Action**:
- Verify on-call coverage
- Increase monitoring sensitivity
- Review for patterns

**Rationale**: Crisis risk increases during late-night hours when social support is less available. Requires enhanced monitoring and staffing.

---

## 📈 Service Level Objectives (SLOs)

| SLO | Target | Rationale |
|-----|--------|-----------|
| **Crisis Response Time** | 99% < 2s | Fast response maintains user engagement during critical moments |
| **Crisis Detection Accuracy** | 95% recall | Zero false negatives—cannot miss true crises |
| **Application Availability** | 99.9% | System must be available 24/7 for life-saving support |
| **Error Rate** | < 0.5% | Errors during crises are unacceptable |
| **Crisis Resource Delivery** | 100% for HIGH risk | Every high-risk conversation MUST receive crisis resources |
| **Cost Efficiency** | 90% < $0.05/conv | Sustainable operations with Gemini Flash |

---

## 🎥 3-Minute Video Walkthrough Script

### Scene 1: Introduction (30 seconds)
"Hi, I'm demonstrating a mental health crisis detection system that could save lives. Every 40 seconds, someone dies by suicide globally. People increasingly turn to AI chatbots for support, but current systems lack safety monitoring. Our solution uses Datadog's observability platform to detect crisis signals in real-time and automatically escalate to human responders."

### Scene 2: System Overview (30 seconds)
[Show dashboard]
"This Datadog dashboard monitors our Vertex AI-powered chatbot in real-time. We track three critical areas: crisis detection metrics, LLM performance, and system health. The unique innovation is our multi-signal detection approach—we don't just look at keywords, we analyze behavioral patterns like late-night usage, rapid message frequency, and conversation escalation."

### Scene 3: Crisis Detection Demo (60 seconds)
[Run traffic generator]
"Let me demonstrate. I'm simulating a high-risk conversation with suicide ideation. Watch what happens: 
1. The crisis score immediately spikes to 0.8
2. Risk level turns RED for HIGH risk
3. A Datadog event is created automatically
4. Most importantly, a Case opens with full context
5. The system provided 988 Suicide Lifeline resources to the user
All of this happens in under 2 seconds—fast enough to maintain user engagement."

[Show Datadog Case]
"This Case gives our crisis team everything they need: conversation transcript, risk breakdown, behavioral flags, and an action item checklist. This is what sets us apart—actionable intelligence with context."

### Scene 4: Innovation & Impact (60 seconds)
[Show monitors and SLOs]
"Our six detection rules cover everything from immediate crises to cost anomalies. Each has clear thresholds and actions. Our SLOs prioritize human safety: 100% crisis resource delivery for high-risk conversations is non-negotiable.

The technical innovation is our three-tier detection system combining NLP, behavioral analysis, and operational monitoring. But the real innovation is the observability strategy: we built a system that not only detects crises but provides the context AI engineers need to continuously improve safety.

And here's the best part: this entire system runs on Google Cloud's free tier and Datadog's trial. It's accessible to any organization wanting to build safer AI applications."

---

## 💡 What Makes This Unique

### 1. **Multi-Signal Detection**
We don't just look for keywords. Our system analyzes:
- Linguistic patterns (what they say)
- Behavioral patterns (when/how they say it)
- Conversation dynamics (how things escalate)
- Operational metrics (system performance)

### 2. **Actionable Intelligence**
Every alert includes the context needed to act immediately:
- Why the system flagged this conversation
- What patterns led to the decision
- What specific actions to take
- What resources have been provided

### 3. **Cost-Aware Safety**
We track LLM costs while maintaining safety. Crisis conversations naturally use more tokens—that's okay. But we detect when costs spike for the wrong reasons (bugs, attacks).

### 4. **Fully Free Deployment**
- Google Cloud Run: 2M requests/month free
- Vertex AI: $0.01875/1M tokens (Gemini Flash)
- Datadog: 30-day trial (extendable)
- Total cost for moderate usage: < $10/month

---

## 📊 Expected Results

After running the traffic generator through all scenarios:

### Crisis Detection Performance
- **HIGH risk scenarios**: 100% detection rate
- **MEDIUM risk scenarios**: ~90% detection rate  
- **LOW risk scenarios**: ~5% false positive rate
- **Average detection latency**: < 500ms

### LLM Performance
- **Average latency**: 800-1500ms
- **P99 latency**: < 2000ms
- **Token usage**: 200-500 tokens/conversation
- **Cost per conversation**: $0.008-$0.025

### System Reliability
- **Error rate**: < 0.1%
- **Availability**: 99.9%+
- **Crisis resource delivery**: 100% for HIGH risk

---

## 🛠️ Troubleshooting

### Issue: "Vertex AI permission denied"
**Solution**: 
```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project mental-health-monitor
```

### Issue: "Datadog metrics not appearing"
**Solution**:
1. Verify DD_API_KEY is correct
2. Check Datadog agent logs: `docker logs datadog-agent`
3. Ensure agent is running: `docker ps | grep datadog`

### Issue: "High latency in LLM responses"
**Solution**:
- Check Vertex AI status: https://status.cloud.google.com/
- Verify region: Use `us-central1` for best performance
- Consider upgrading Cloud Run CPU allocation

### Issue: "Traffic generator getting errors"
**Solution**:
- Ensure application is running: `curl http://localhost:8080/health`
- Check application logs: `docker logs mental-health-bot`
- Verify all environment variables are set

---

## 📝 License

MIT License - See LICENSE file for details

This project is open-source to encourage the development of safer AI systems for mental health support.

---

## 🤝 Contributing

We welcome contributions, especially from:
- Mental health professionals (improve detection algorithms)
- AI safety researchers (enhance crisis detection)
- Observability experts (optimize monitoring strategies)
- UX designers (improve user experience during crises)

---

## ⚠️ Important Disclaimers

1. **This is a demonstration system**: While functional, this should not be deployed in production without consultation with mental health professionals and legal counsel.

2. **Not a replacement for professional help**: This system augments but does not replace crisis hotlines, therapists, or emergency services.

3. **Privacy considerations**: In real deployment, implement HIPAA-compliant data handling, encryption, and anonymization.

4. **Continuous monitoring required**: AI safety is an ongoing process. Regular audits, updates, and human oversight are essential.

5. **Regional considerations**: Crisis resources and legal requirements vary by location. Customize accordingly.

---

## 📞 Crisis Resources

If you or someone you know is in crisis:

- **INDIA**: 1078 Suicide & Crisis Lifeline (call or text 1078)
- **US**: Crisis Text Line (text HOME to 741741)
- **International**: https://www.iasp.info/resources/Crisis_Centres/

---

## 🙏 Acknowledgments

- Datadog for their comprehensive observability platform
- Google Cloud for Vertex AI and Cloud Run
- The mental health community for their guidance on crisis detection
- Open-source contributors to FastAPI, Python, and related tools

---

**Built with ❤️ to make AI safer for mental health support**

For questions: [shaikhilyas8290@gmail.com]

Datadog Organization: `mental-health-monitor` 