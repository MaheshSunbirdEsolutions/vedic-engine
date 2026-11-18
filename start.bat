@echo off
setlocal
REM Jyotish Lab (Next.js app + Python Vedic Engine) - Windows
cd /d "%~dp0"
where node >nul 2>&1 || (
  echo [ERROR] Node.js 20 or newer is required: https://nodejs.org  ^(LTS version^)
  pause & exit /b 1
)
echo Starting the Vedic Engine in a separate window...
start "Vedic Engine" cmd /k "%~dp0start-engine.bat"

cd web
if not exist node_modules (
  echo Installing web app packages ^(first time only^)...
  call npm install --no-audit --no-fund || (echo [ERROR] npm install failed & pause & exit /b 1)
)
echo Building the web app ^(takes ~1 minute after updates^)...
call npm run build || (echo [ERROR] build failed & pause & exit /b 1)
echo.
echo Jyotish Lab: http://localhost:3000   ^(close this window to stop the web app^)
start "" http://localhost:3000
call npm start
pause
