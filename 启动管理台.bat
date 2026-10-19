@echo off
NET SESSION >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)
cd /d "%~dp0"
python job_dashboard.py
if errorlevel 1 pause
