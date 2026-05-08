# Start all AI Detection App services locally
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$deepmedia = Split-Path -Parent $root

# Install deepsafe-sdk if not already installed
if (-not (pip show deepsafe-sdk 2>&1 | Select-String "^Name:")) {
    Write-Host "Installing DeepSafe SDK..." -ForegroundColor Cyan
    pip install -e "$deepmedia\DeepSafe\sdk" -q
}

$manifest    = "$deepmedia\DeepSafe\models\image\npr_deepfakedetection\model.yaml"
$videoDetect = "$deepmedia\AI-Generated-Video-Detector"

# 1. DeepSafe image model — port 5001
Start-Process cmd -ArgumentList "/k title DeepSafe-Image && deepsafe serve --manifest `"$manifest`""

# 2. Video service — port 5005
Start-Process cmd -ArgumentList "/k title VideoService && set DETECTOR_PATH=$videoDetect && cd /d `"$root\video-service`" && python -m uvicorn server:app --host 0.0.0.0 --port 5005"

# 3. Backend orchestrator — port 8080
Start-Process cmd -ArgumentList "/k title Backend && cd /d `"$root\backend`" && python -m uvicorn main:app --host 0.0.0.0 --port 8080"

# 4. Frontend — port 3000
Start-Process cmd -ArgumentList "/k title Frontend && cd /d `"$root\frontend`" && npm run dev"

Write-Host ""
Write-Host "All services launching in separate windows:" -ForegroundColor Green
Write-Host "  Frontend  ->  http://localhost:3000"
Write-Host "  Backend   ->  http://localhost:8080"
Write-Host "  DeepSafe  ->  http://localhost:5001"
Write-Host "  Video     ->  http://localhost:5005"
