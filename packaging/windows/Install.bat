@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Job Profile Management - Installer

if exist "%~dp0payload\python\python.exe" goto payload_ok
echo.
echo  The installer files were not found next to Install.bat.
echo  Please extract the whole zip first (right-click the zip ^> Extract All),
echo  then run Install.bat from the extracted folder.
echo.
pause
exit /b 1
:payload_ok

set "MODE=%~1"
if /i "%MODE%"=="personal" goto mode_ok
if /i "%MODE%"=="server" goto mode_ok

echo.
echo  =====================================================
echo    MTN Irancell - Job Profile Management System
echo  =====================================================
echo.
echo    1  Personal  - install for me; runs on this PC only
echo    2  Server    - shared server; colleagues open it in their
echo                   browser (asks for administrator permission)
echo.
choice /c 12 /n /m "  Choose 1 or 2: "
if errorlevel 2 (set "MODE=server") else (set "MODE=personal")
:mode_ok

if /i not "%MODE%"=="server" goto install_dir
net session >nul 2>&1
if not errorlevel 1 goto install_dir
echo.
echo  Server mode needs administrator permission - asking Windows...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -ArgumentList 'server' -Verb RunAs"
exit /b 0

:install_dir
set "INSTALL=%LOCALAPPDATA%\JobProfile"
if /i "%MODE%"=="server" set "INSTALL=%ProgramData%\JobProfile"
echo.
echo  Mode:        %MODE%
echo  Installing:  %INSTALL%
echo.

if exist "%INSTALL%\stop-server.bat" call "%INSTALL%\stop-server.bat"

echo  [1/5] Copying files...
robocopy "%~dp0payload" "%INSTALL%" /E /R:2 /W:2 /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto copy_failed

if not exist "%INSTALL%\userdata" mkdir "%INSTALL%\userdata"
if not exist "%INSTALL%\logs" mkdir "%INSTALL%\logs"
if not exist "%INSTALL%\userdata\jobprofile.db" copy /y "%INSTALL%\seed\jobprofile.db" "%INSTALL%\userdata\jobprofile.db" >nul
> "%INSTALL%\install-mode.txt" echo %MODE%

echo  [2/5] Writing settings...
set "NEWCONFIG=0"
if exist "%INSTALL%\config.bat" goto config_done
set "NEWCONFIG=1"
set "HOST=127.0.0.1"
if /i "%MODE%"=="server" set "HOST=0.0.0.0"
for /f "delims=" %%i in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%INSTALL%\new-secret.ps1" 48') do set "SECRET=%%i"
> "%INSTALL%\config.bat" echo @rem Job Profile server settings. Edit, then restart the server (stop-server.bat).
>> "%INSTALL%\config.bat" echo @rem If you change the port, also update the Windows Firewall rule "Job Profile Server".
>> "%INSTALL%\config.bat" echo set "JP_HOST=%HOST%"
>> "%INSTALL%\config.bat" echo set "JP_PORT=8000"
>> "%INSTALL%\config.bat" echo set "JPMS_AUTH_SECRET=%SECRET%"
>> "%INSTALL%\config.bat" echo @rem Optional - enables full generative AI (drafting, rewriting, translation):
>> "%INSTALL%\config.bat" echo @rem set "JPMS_ANTHROPIC_API_KEY=sk-ant-..."
if /i not "%MODE%"=="server" goto config_done
for /f "delims=" %%i in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%INSTALL%\new-secret.ps1" 10') do set "PW_ADMIN=%%i"
for /f "delims=" %%i in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%INSTALL%\new-secret.ps1" 10') do set "PW_HR=%%i"
for /f "delims=" %%i in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%INSTALL%\new-secret.ps1" 10') do set "PW_MGR=%%i"
>> "%INSTALL%\config.bat" echo set "JPMS_PASSWORD_ADMIN=%PW_ADMIN%"
>> "%INSTALL%\config.bat" echo set "JPMS_PASSWORD_HR=%PW_HR%"
>> "%INSTALL%\config.bat" echo set "JPMS_PASSWORD_MANAGER=%PW_MGR%"
>> "%INSTALL%\config.bat" echo @rem The "employee" login is read-only and keeps the password: demo
:config_done

echo  [3/5] Creating shortcuts and start-up entry...
if /i "%MODE%"=="server" goto shortcuts_server
powershell -NoProfile -ExecutionPolicy Bypass -File "%INSTALL%\make-shortcuts.ps1" -InstallDir "%INSTALL%" -Startup
goto shortcuts_done
:shortcuts_server
powershell -NoProfile -ExecutionPolicy Bypass -File "%INSTALL%\make-shortcuts.ps1" -InstallDir "%INSTALL%" -AllUsers
netsh advfirewall firewall delete rule name="Job Profile Server" >nul 2>&1
netsh advfirewall firewall add rule name="Job Profile Server" dir=in action=allow protocol=TCP localport=8000 profile=private,domain >nul
schtasks /Create /TN "JobProfileServer" /TR "wscript.exe \"%INSTALL%\run-hidden.vbs\"" /SC ONSTART /RU SYSTEM /RL HIGHEST /F >nul
:shortcuts_done

echo  [4/5] Registering in Apps ^& features...
set "UKEY=HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\JobProfile"
if /i "%MODE%"=="server" set "UKEY=HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\JobProfile"
reg add "%UKEY%" /v DisplayName /d "Job Profile Management (MTN Irancell)" /f >nul
reg add "%UKEY%" /v DisplayIcon /d "%INSTALL%\jobprofile.ico" /f >nul
reg add "%UKEY%" /v InstallLocation /d "%INSTALL%" /f >nul
reg add "%UKEY%" /v UninstallString /d "\"%INSTALL%\Uninstall.bat\"" /f >nul
reg add "%UKEY%" /v NoModify /t REG_DWORD /d 1 /f >nul

echo  [5/5] Starting the server...
if /i "%MODE%"=="server" schtasks /Run /TN "JobProfileServer" >nul
if /i not "%MODE%"=="server" start "" wscript.exe "%INSTALL%\run-hidden.vbs"

set /a TRIES=0
:wait_up
curl.exe -s -m 2 http://localhost:8000/api/health >nul 2>&1
if not errorlevel 1 goto is_up
set /a TRIES+=1
if %TRIES% GEQ 40 goto not_up
timeout /t 1 /nobreak >nul
goto wait_up

:is_up
echo.
echo  =====================================================
echo    Installed and running.
echo  =====================================================
echo.
echo    Open it from the "Job Profiles" icon on your Desktop,
echo    or go to  http://localhost:8000
if /i "%MODE%"=="server" echo    Colleagues on your network open  http://%COMPUTERNAME%:8000
echo.
if "%NEWCONFIG%"=="0" goto login_hint
if /i "%MODE%"=="server" goto login_server
echo    Sign in as  hr / admin / manager / employee   password: demo
goto after_login
:login_server
echo    Sign in as:
echo        admin     %PW_ADMIN%
echo        hr        %PW_HR%
echo        manager   %PW_MGR%
echo        employee  demo  (read-only)
echo    These are saved in %INSTALL%\config.bat - keep them private.
goto after_login
:login_hint
echo    Existing settings and data were kept (see config.bat for passwords).
:after_login
echo.
if /i not "%MODE%"=="server" start "" http://localhost:8000
pause
exit /b 0

:not_up
echo.
echo  The files were installed but the server did not answer within 40 seconds.
echo  Check the log:  %INSTALL%\logs\server.log
pause
exit /b 1

:copy_failed
echo.
echo  Copying files failed. Close any running Job Profile window and try again.
pause
exit /b 1
