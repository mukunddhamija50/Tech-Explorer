@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if errorlevel 1 (
  echo Python 3 was not found. Install Python, then run this file again.
  pause
  exit /b 1
)

py -3 -c "import fastapi, uvicorn, pydantic, requests, multipart, pypdf; import main" >nul 2>&1
if errorlevel 1 (
  echo Installing SkillMatch requirements...
  py -3 -m pip install -r "%~dp0requirements.txt"
  if errorlevel 1 (
    echo Dependency installation failed. Check your internet connection and try again.
    pause
    exit /b 1
  )
)

start "SkillMatch API" /min py -3 -m uvicorn main:app --app-dir "%~dp0" --host 127.0.0.1 --port 8000

for /L %%i in (1,1,30) do (
  py -3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=1)" >nul 2>&1
  if not errorlevel 1 goto server_ready
  timeout /t 1 /nobreak >nul
)

echo SkillMatch did not start. Install dependencies with: py -3 -m pip install -r requirements.txt
pause
exit /b 1

:server_ready
start "" "http://127.0.0.1:8000/indexr.html"
exit /b 0