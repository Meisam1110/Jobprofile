@echo off
setlocal EnableExtensions
set "INSTALL=%~dp0"
if "%INSTALL:~-1%"=="\" set "INSTALL=%INSTALL:~0,-1%"
title Job Profile Management - Uninstall
cd /d "%TEMP%"

set "MODE=personal"
if exist "%INSTALL%\install-mode.txt" set /p MODE=<"%INSTALL%\install-mode.txt"

if /i not "%MODE%"=="server" goto confirm
net session >nul 2>&1
if not errorlevel 1 goto confirm
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
exit /b 0

:confirm
echo.
echo  This removes Job Profile Management from this PC.
echo  Install folder: %INSTALL%
echo.
choice /c YN /n /m "  Also DELETE the database and all profile data? (Y = delete everything, N = keep data) "
if errorlevel 2 (set "DELDATA=N") else (set "DELDATA=Y")

echo.
echo  Stopping the server...
call "%INSTALL%\stop-server.bat"
schtasks /Delete /TN "JobProfileServer" /F >nul 2>&1
netsh advfirewall firewall delete rule name="Job Profile Server" >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -File "%INSTALL%\make-shortcuts.ps1" -InstallDir "%INSTALL%" -Remove
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\JobProfile" /f >nul 2>&1
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\JobProfile" /f >nul 2>&1

set "H=%TEMP%\jobprofile-uninstall.cmd"
> "%H%" echo @echo off
>> "%H%" echo ping -n 4 127.0.0.1 ^>nul
if /i "%DELDATA%"=="Y" goto del_all
>> "%H%" echo rd /s /q "%INSTALL%\python"
>> "%H%" echo rd /s /q "%INSTALL%\jpms"
>> "%H%" echo rd /s /q "%INSTALL%\seed"
>> "%H%" echo rd /s /q "%INSTALL%\logs"
>> "%H%" echo del /q "%INSTALL%\*.bat" "%INSTALL%\*.vbs" "%INSTALL%\*.ps1" "%INSTALL%\*.ico" "%INSTALL%\*.txt"
goto del_helper
:del_all
>> "%H%" echo rd /s /q "%INSTALL%"
:del_helper
>> "%H%" echo del "%%~f0"
start "" /min cmd /c "%H%"

echo.
if /i "%DELDATA%"=="Y" goto msg_all
echo  Removed. Your data was kept in %INSTALL%\userdata
goto msg_end
:msg_all
echo  Everything was removed.
:msg_end
echo.
pause
exit /b 0
