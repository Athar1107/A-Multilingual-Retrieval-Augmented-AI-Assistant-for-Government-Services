@echo off
title Government AI Assistant - API Server

echo ============================================================
echo   Government AI Assistant - API Server
echo ============================================================
echo.

:: Kill anything already on port 8000
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000.*LISTENING"') do (
    echo Killing old process %%a on port 8000...
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 2 /nobreak >nul

:: Use the full venv Python path — no activation needed
set PYTHON="%~dp0.venv\Scripts\python.exe"
set BACKEND=%~dp0backend

:: Set all required environment variables
:: ⚠️  Set HF_TOKEN in backend/.env — do not hardcode your real token here
set HF_TOKEN=YOUR_HF_TOKEN_HERE
set TRANSLATION_MODEL=indictrans2
set PYTHONIOENCODING=utf-8
set HF_HUB_OFFLINE=0
set TRANSFORMERS_OFFLINE=0
set OLLAMA_URL=http://localhost:11434
set OLLAMA_MODEL=llama3.2

echo Python   : %PYTHON%
echo Backend  : %BACKEND%
echo.
echo Server   : http://127.0.0.1:8000
echo Swagger  : http://127.0.0.1:8000/docs
echo Health   : http://127.0.0.1:8000/health
echo.
echo Press Ctrl+C to stop.
echo ============================================================
echo.

cd /d "%BACKEND%"
%PYTHON% -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info

echo.
echo Server stopped.
pause
