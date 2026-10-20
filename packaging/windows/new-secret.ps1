# Prints a random alphanumeric string of the requested length (default 32).
param([int]$Length = 32)
$chars = 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'.ToCharArray()
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$bytes = New-Object byte[] $Length
$rng.GetBytes($bytes)
$out = New-Object System.Text.StringBuilder
foreach ($b in $bytes) { [void]$out.Append($chars[$b % $chars.Length]) }
Write-Output $out.ToString()
