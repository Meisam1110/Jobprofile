@echo off
setlocal
cd /d "%~dp0"
set "JP_HOST=127.0.0.1"
set "JP_PORT=8000"
if exist "%~dp0config.bat" call "%~dp0config.bat"
set "DB=%~dp0userdata\jobprofile.db"
set "JPMS_DATABASE_URL=sqlite:///%DB:\=/%"
if not exist "%~dp0logs" mkdir "%~dp0logs"
"%~dp0python\python.exe" -m uvicorn app.main:app --host %JP_HOST% --port %JP_PORT% >> "%~dp0logs\server.log" 2>&1
