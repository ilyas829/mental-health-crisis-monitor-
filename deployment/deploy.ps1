# Load .env
Get-Content ../.env | ForEach-Object { 
    if ($_ -match '^\s*#') { return }
    if ($_ -match '^\s*$') { return }
    $name, $value = $_.Split('=', 2)
    $value = $value.Trim('"')
    [System.Environment]::SetEnvironmentVariable($name.Trim(), $value, 'Process')
}

$project = $env:GOOGLE_CLOUD_PROJECT
$imageName = "mental-health-bot"
$image = "gcr.io/$project/$imageName`:latest"

Write-Host "🚀 Mental Health Crisis Monitor - Deployment"
Write-Host "=============================================="

Write-Host "📦 Building Docker image..."
docker build -t $image -f ../deployment/Dockerfile ../.

Write-Host "⬆️ Pushing to GCR..."
docker push $image

Write-Host "🌐 Deploying to Cloud Run..."
gcloud run deploy $imageName `
  --image=$image `
  --region=us-central1 --platform=managed --allow-unauthenticated `
  --port=8080 --memory=2Gi --cpu=2 --min-instances=1 --max-instances=10 `
  --set-env-vars "DD_API_KEY=$env:DD_API_KEY,DD_APP_KEY=$env:DD_APP_KEY,DD_SERVICE=mental-health-bot,DD_ENV=production,DD_SITE=datadoghq.eu,GOOGLE_CLOUD_PROJECT=$project,GOOGLE_CLOUD_LOCATION=us-central1"

$url = gcloud run services describe $imageName --region=us-central1 --format='value(status.url)'
Write-Host ""
Write-Host "✅ Deployment complete!"
Write-Host "🌐 Service URL: $url"
Write-Host "Test: curl $url/health"
