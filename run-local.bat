@echo off
REM One-click local launcher for Windows: sets up Python + Node deps on first run,
REM seeds the database from data\job_profiles_master.xlsm, builds the UI, starts the app.
setlocal
cd /d "%~dp0"

where py >nul 2>nul && (set PY=py -3) || (set PY=python)

if not exist .venv (
  echo Creating Python virtual environment...
  %PY% -m venv .venv || goto :error
)
call .venv\Scripts\activate.bat

echo Installing backend dependencies...
pip install -q -r backend\requirements.txt || goto :error

if not exist backend\jobprofile.db (
  echo Importing the master workbook ^(about 30 seconds^)...
  python scripts\import_excel.py || goto :error
)

if not exist frontend\dist (
  echo Building the frontend...
  pushd frontend
  call npm install || (popd & goto :error)
  call npm run build || (popd & goto :error)
  popd
)

echo.
echo Starting at http://localhost:8000   (login: hr / demo)   -- Ctrl+C to stop
start "" http://localhost:8000
cd backend
uvicorn app.main:app --port 8000
goto :eof

:error
echo.
echo Setup failed - see the message above. Requires Python 3.11+ and Node 20+ on PATH.
pause
exit /b 1
