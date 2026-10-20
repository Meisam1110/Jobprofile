MTN Irancell - Job Profile Management System  (Windows installer)
==================================================================

Nothing else needs to be installed: Python and every library are included.
No internet connection is required.

INSTALL
  1. Unzip this folder anywhere (right-click the zip > Extract All).
  2. Double-click  Install.bat
  3. Choose:
       1  Personal  - for you only. Installs under your user profile, adds a
                      "Job Profiles" icon to your Desktop and Start menu, and
                      starts the server automatically when you sign in.
       2  Server    - shared server. Installs for all users (administrator
                      permission), starts automatically when Windows boots,
                      opens port 8000 in Windows Firewall for Private and
                      Domain networks, and creates random passwords.
                      Colleagues open  http://<this-computer-name>:8000

  The database with all 1,446 job profiles is included - no import step.

USE
  Double-click the "Job Profiles" desktop icon. If the server is not running
  it is started for you, then your browser opens.
  Personal install default logins: hr, manager, employee, admin - password: demo

SETTINGS
  Start menu > Job Profiles > Server settings (opens config.bat in Notepad).
  There you can change the port, passwords and add an Anthropic API key to
  enable full generative AI. After editing, restart: run stop-server.bat in
  the install folder, then open the app again.

UPGRADE
  Run the new Install.bat over the old install. Your database and settings
  (userdata\ and config.bat) are kept.

UNINSTALL
  Settings > Apps > "Job Profile Management", or Start menu > Job Profiles >
  Uninstall. You can keep or delete your data.

WHERE THINGS ARE
  Personal:  %LOCALAPPDATA%\JobProfile
  Server:    %ProgramData%\JobProfile
    userdata\jobprofile.db   your database (back this file up)
    logs\server.log          server log
    config.bat               settings

SECURITY NOTES (server mode)
  - Logins and passwords travel over plain HTTP on your network. Use it on a
    trusted internal network only, or put it behind an HTTPS reverse proxy.
  - Windows SmartScreen may warn about Install.bat because it is downloaded
    and unsigned: choose "More info" > "Run anyway" if you trust the source.
    Antivirus tools sometimes pause the bundled python.exe on first start.
