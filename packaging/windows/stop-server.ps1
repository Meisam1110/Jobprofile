# Stops the Job Profile server (only the python.exe that lives in this install folder).
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $dir 'python\python.exe'
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.ExecutablePath -eq $py } |
    ForEach-Object {
        try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch { }
    }
Start-Sleep -Milliseconds 800
