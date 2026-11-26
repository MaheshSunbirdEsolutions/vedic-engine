@echo off
setlocal
REM Vedic Engine (Python API) - Windows
REM Needs Python 3.12 or 3.11: these have ready-made packages for pysweph/pyyaml (newer Pythons need a C++ compiler).
cd /d "%~dp0"

set "PY="
py -3.12 -c "import sys" >nul 2>&1 && set "PY=py -3.12"
if not defined PY py -3.11 -c "import sys" >nul 2>&1 && set "PY=py -3.11"
if not defined PY py -3.13 -c "import sys" >nul 2>&1 && set "PY=py -3.13"

if not defined PY (
  echo Python 3.12 not found - trying to install it with the Python install manager...
  py install 3.12 >nul 2>&1
  py -3.12 -c "import sys" >nul 2>&1 && set "PY=py -3.12"
)
if not defined PY (
  echo.
  echo [ERROR] Python 3.12 is required ^(you may have only a newer version such as 3.13-3.15^).
  echo   Option A: open Command Prompt and run:   py install 3.12
  echo   Option B: download "Python 3.12.x Windows installer" from https://www.python.org/downloads/windows/
  echo Then delete the .venv folder and run this file again.
  pause & exit /b 1
)
echo Using: %PY%
%PY% --version

REM recreate .venv if it was made with another Python version
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info[:2] in ((3,11),(3,12),(3,13)) else 1)" || (
    echo Removing old .venv made with a different Python...
    rmdir /s /q .venv
  )
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  %PY% -m venv .venv || (echo [ERROR] could not create .venv & pause & exit /b 1)
)

echo Installing / checking libraries...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install --only-binary=pysweph,pyyaml -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Library installation failed - see the messages above.
  pause & exit /b 1
)

echo.
echo Vedic Engine running at https://vedic-engine-eight.vercel.app/engine  (keep this window open; close it to stop)
".venv\Scripts\python.exe" -m uvicorn vedic_engine.api:app --host 127.0.0.1 --port 8000
pause
