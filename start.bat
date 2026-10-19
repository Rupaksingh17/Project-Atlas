@echo off
title Project Atlas Launcher
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_local.ps1"
if errorlevel 1 pause
