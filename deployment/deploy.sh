#!/bin/bash

# Mental Health Crisis Monitor - Deployment Script
# This script deploys to Google Cloud Run (Free Tier)

set -e

echo "🚀 Mental Health Crisis Monitor - Deployment"
echo "=============================================="

# Load environment variables from .env file
if [ -f .env ]; then
    echo "📄 Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ Error: .env file not found"
    exit 1
fi

# Check required environment variables
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "❌ Error: GOOGLE_CLOUD_PROJECT not set"
    exit 1
fi

if [ -z "$DD_API_KEY" ]; then
    echo "❌ Error: DD_API_KEY not set"
    exit 1
fi

if [ -z "$DD_APP_KEY" ]; then
    echo "❌ Error: DD_APP_KEY not set"
    exit 1
fi

echo "✅ Environment variables loaded"
echo "   Project: $GOOGLE_CLOUD_PROJECT"
echo "   Datadog API Key: ${DD_API_KEY:0:10}..."
echo ""

# Configure Docker for GCP
echo "🔐 Configuring Docker for Google Cloud..."
gcloud auth configure-docker gcr.io --quiet

# Build and push Docker image
echo "📦 Building Docker image..."
docker build -t gcr.io/$GOOGLE_CLOUD_PROJECT/mental-health-bot:latest -f deployment/Dockerfile .

echo "⬆️  Pushing to Google Container Registry..."
docker push gcr.io/$GOOGLE_CLOUD_PROJECT/mental-health-bot:latest

# Deploy to Cloud Run
echo "🌐 Deploying to Cloud Run..."
gcloud run deploy mental-health-bot \
    --image=gcr.io/$GOOGLE_CLOUD_PROJECT/mental-health-bot:latest \
    --region=us-central1 \
    --platform=managed \
    --allow-unauthenticated \
    --port=8080 \
    --memory=2Gi \
    --cpu=2 \
    --min-instances=0 \
    --max-instances=10 \
    --timeout=300 \
    --set-env-vars "DD_API_KEY=$DD_API_KEY,DD_APP_KEY=$DD_APP_KEY,DD_SERVICE=mental-health-bot,DD_ENV=production,DD_SITE=datadoghq.eu,DD_TRACE_ENABLED=true,DD_LOGS_INJECTION=true,GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=us-central1" \
    --project=$GOOGLE_CLOUD_PROJECT

# Get the deployed URL
echo ""
echo "📍 Getting service URL..."
SERVICE_URL=$(gcloud run services describe mental-health-bot \
    --region=us-central1 \
    --project=$GOOGLE_CLOUD_PROJECT \
    --format='value(status.url)')

echo ""
echo "=============================================="
echo "✅ Deployment Complete!"
echo "=============================================="
echo ""
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "📋 Next Steps:"
echo "1. Visit $SERVICE_URL to test the application"
echo "2. Check Datadog dashboard for metrics"
echo "3. Run traffic generator: python traffic_generator/generate_scenarios.py --url $SERVICE_URL"
echo ""
echo "📊 Monitoring:"
echo "   Datadog: https://app.datadoghq.eu/dashboard"
echo "   Cloud Run Logs: https://console.cloud.google.com/run/detail/us-central1/mental-health-bot/logs?project=$GOOGLE_CLOUD_PROJECT"
echo ""