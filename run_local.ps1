# Project Atlas: Local Runner Script
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "   Starting Project Atlas: Report Copilot        " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# 1. Ingest reports into vector store
Write-Host "`n[1/3] Ingesting reports into ChromaDB..." -ForegroundColor Yellow
python -m backend.app.services.ingest

# 2. Run automated test suite
Write-Host "`n[2/3] Running automated evaluation harness (25 questions)..." -ForegroundColor Yellow
python -m backend.tests.eval_harness

# 3. Check for PHP and start frontend if available
$wingetPhp = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\PHP.PHP.8.1_Microsoft.Winget.Source_8wekyb3d8bbwe\php.exe"
$phpExe = if (Get-Command php -ErrorAction SilentlyContinue) { "php" } elseif (Test-Path $wingetPhp) { $wingetPhp } else { $null }

if ($phpExe) {
    Write-Host "PHP detected ($phpExe). Starting CodeIgniter 3 portal on http://localhost:8080" -ForegroundColor Green
    Start-Process -FilePath $phpExe -ArgumentList "-S 127.0.0.1:8080 -t frontend" -NoNewWindow
} else {
    Write-Host "PHP not detected. Frontend can be run via Docker Compose: 'docker compose up --build'" -ForegroundColor Yellow
}

# 4. Start FastAPI Backend
Write-Host "`nStarting FastAPI backend server on http://localhost:8000..." -ForegroundColor Green
Write-Host "Interactive Swagger Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
