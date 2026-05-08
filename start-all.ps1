# Verit — start all 4 services in separate PowerShell windows
# Usage:  Right-click → Run with PowerShell    OR    .\start-all.ps1

Write-Host "Starting Verit AI Detection App..." -ForegroundColor Cyan
Write-Host ""

# 1. DeepSafe image service (port 5001)
Write-Host "[1/4] Starting Image AI service on port 5001..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList '-NoExit', '-Command', @"
`$Host.UI.RawUI.WindowTitle = 'Verit - Image AI (5001)'
cd e:\deepmedia\DeepSafe
.venv\Scripts\activate
deepsafe serve --manifest models\image\npr_deepfakedetection\model.yaml
"@

Start-Sleep -Seconds 2

# 2. Video AI service (port 5005)
Write-Host "[2/4] Starting Video AI service on port 5005..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList '-NoExit', '-Command', @"
`$Host.UI.RawUI.WindowTitle = 'Verit - Video AI (5005)'
cd e:\deepmedia\ai-detection-app\video-service
`$env:DETECTOR_PATH = 'e:\deepmedia\AI-Generated-Video-Detector'
python -m uvicorn server:app --host 0.0.0.0 --port 5005
"@

Start-Sleep -Seconds 2

# 3. Orchestrator backend (port 8080)
Write-Host "[3/4] Starting Orchestrator backend on port 8080..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList '-NoExit', '-Command', @"
`$Host.UI.RawUI.WindowTitle = 'Verit - Backend (8080)'
cd e:\deepmedia\ai-detection-app\backend
.venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8080
"@

Start-Sleep -Seconds 2

# 4. Frontend (port 3000)
Write-Host "[4/4] Starting Frontend on port 3000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList '-NoExit', '-Command', @"
`$Host.UI.RawUI.WindowTitle = 'Verit - Frontend (3000)'
cd e:\deepmedia\ai-detection-app\frontend
npm run dev
"@

Write-Host ""
Write-Host "All 4 services launching..." -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend:     http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:      http://localhost:8080" -ForegroundColor White
Write-Host "  Image AI:     http://localhost:5001" -ForegroundColor White
Write-Host "  Video AI:     http://localhost:5005" -ForegroundColor White
Write-Host ""
Write-Host "Wait ~30 seconds for AI services to load models, then open:" -ForegroundColor Cyan
Write-Host "  http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Health check:  http://localhost:8080/health" -ForegroundColor DarkGray
Write-Host ""
Write-Host "To stop everything: close all 4 PowerShell windows (or press Ctrl+C in each)." -ForegroundColor DarkGray

# Optional: auto-open browser after 30 seconds
$openBrowser = Read-Host "Open browser automatically when ready? (y/n)"
if ($openBrowser -eq 'y') {
    Write-Host "Waiting for backend to be ready..." -ForegroundColor Cyan
    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        try {
            $r = Invoke-WebRequest -Uri 'http://localhost:8080/health' -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            $data = $r.Content | ConvertFrom-Json
            if ($data.services.orchestrator -eq 'healthy' -and $data.services.deepsafe -eq 'healthy' -and $data.services.video -eq 'healthy') {
                $ready = $true
                break
            }
        } catch { }
        Start-Sleep -Seconds 2
    }
    if ($ready) {
        Write-Host "All services healthy. Opening browser..." -ForegroundColor Green
        Start-Process "http://localhost:3000"
    } else {
        Write-Host "Services taking longer than expected. Open http://localhost:3000 manually when ready." -ForegroundColor Yellow
    }
}
