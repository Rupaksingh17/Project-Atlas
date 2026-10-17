@echo off
title Project Atlas Launcher
echo ===================================================
echo Starting Project Atlas: Report Copilot
echo ===================================================

echo Starting FastAPI Backend on port 8000...
start "Atlas Backend (FastAPI)" cmd /k "uvicorn backend.app.main:app --port 8000"

echo Starting CodeIgniter 3 Portal on port 8080...
start "Atlas Frontend (CodeIgniter 3)" cmd /k "powershell -Command \"$php = if (Get-Command php -ErrorAction SilentlyContinue) { 'php' } else { '%LOCALAPPDATA%\Microsoft\WinGet\Packages\PHP.PHP.8.1_Microsoft.Winget.Source_8wekyb3d8bbwe\php.exe' }; & $php -S 127.0.0.1:8080 -t frontend\""

timeout /t 3 >nul

echo Opening browser windows...
start http://localhost:8080
start http://localhost:8000/docs

echo Services running!
