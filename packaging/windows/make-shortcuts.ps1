# Creates / removes the Desktop, Start Menu and (personal mode) Startup shortcuts.
param(
    [Parameter(Mandatory = $true)][string]$InstallDir,
    [switch]$AllUsers,
    [switch]$Startup,
    [switch]$Remove
)
$ErrorActionPreference = 'Stop'
$ws = New-Object -ComObject WScript.Shell

function Get-Paths([bool]$all) {
    if ($all) {
        return @{
            Desktop  = [Environment]::GetFolderPath('CommonDesktopDirectory')
            Programs = [Environment]::GetFolderPath('CommonPrograms')
            Startup  = [Environment]::GetFolderPath('CommonStartup')
        }
    }
    return @{
        Desktop  = [Environment]::GetFolderPath('Desktop')
        Programs = [Environment]::GetFolderPath('Programs')
        Startup  = [Environment]::GetFolderPath('Startup')
    }
}

if ($Remove) {
    foreach ($all in @($false, $true)) {
        $p = Get-Paths $all
        Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $p.Desktop 'Job Profiles.lnk')
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $p.Programs 'Job Profiles')
        Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $p.Startup 'Job Profile Server.lnk')
    }
    exit 0
}

function New-Link([string]$file, [string]$target, [string]$arguments, [string]$desc) {
    $lnk = $ws.CreateShortcut($file)
    $lnk.TargetPath = $target
    $lnk.Arguments = $arguments
    $lnk.WorkingDirectory = $InstallDir
    $lnk.IconLocation = (Join-Path $InstallDir 'jobprofile.ico') + ',0'
    $lnk.Description = $desc
    $lnk.Save()
}

$p = Get-Paths $AllUsers.IsPresent
$wscript = Join-Path $env:SystemRoot 'System32\wscript.exe'
$notepad = Join-Path $env:SystemRoot 'System32\notepad.exe'
$open = '"' + (Join-Path $InstallDir 'open-app.vbs') + '"'

New-Link (Join-Path $p.Desktop 'Job Profiles.lnk') $wscript $open 'Open Job Profile Management'

$menu = Join-Path $p.Programs 'Job Profiles'
New-Item -ItemType Directory -Force -Path $menu | Out-Null
New-Link (Join-Path $menu 'Job Profiles.lnk') $wscript $open 'Open Job Profile Management'
New-Link (Join-Path $menu 'Server settings.lnk') $notepad ('"' + (Join-Path $InstallDir 'config.bat') + '"') 'Edit port, passwords and AI key'
New-Link (Join-Path $menu 'Uninstall.lnk') (Join-Path $InstallDir 'Uninstall.bat') '' 'Uninstall Job Profile Management'

if ($Startup) {
    New-Link (Join-Path $p.Startup 'Job Profile Server.lnk') $wscript ('"' + (Join-Path $InstallDir 'run-hidden.vbs') + '"') 'Start the Job Profile server at sign-in'
}
