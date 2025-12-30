# === deploy.sh (Deployment Script) ===
#!/bin/bash

# Mental Health Crisis Monitor - Deployment Script
# This script deploys to Google Cloud Run (Free Tier)

set -e

echo "🚀 Mental Health Crisis Monitor - Deployment"
echo "=============================================="

# Check required environment variables
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "❌ Error: GOOGLE_CLOUD_PROJECT not set"
    exit 1
fi

if [ -z "$DD_API_KEY" ]; then
    echo "❌ Error: DD_API_KEY not set"
    exit 1
fi

# Build and push Docker image
echo "📦 Building Docker image..."
docker build -t gcr.io/$GOOGLE_CLOUD_PROJECT/mental-health-bot:latest .

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
    --min-instances=1 \
    --max-instances=10 \
    --set-env-vars=DD_API_KEY=$DD_API_KEY,DD_APP_KEY=$DD_APP_KEY,DD_SERVICE=mental-health-bot,DD_ENV=production

# Get the deployed URL
SERVICE_URL=$(gcloud run services describe mental-health-bot --region=us-central1 --format='value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "Next steps:"
echo "1. Visit $SERVICE_URL to test the application"
echo "2. Check Datadog dashboard for metrics"
echo "3. Run traffic generator to test detection rules"
echo ""
