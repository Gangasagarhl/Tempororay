<#
Every 2 minutes: if the keep-going watchdog is not running, start it again.
  Run:  powershell -ExecutionPolicy Bypass -File tools\supervise.ps1
#>
$Root = Split-Path -Parent $PSScriptRoot
$Log = Join-Path $Root "logs\keep_going.log"
$TaskName = "LangChain Lab keep going"
while ($true) {
    $lock = Join-Path $Root "logs\keep_going.lock"
    $owner = if (Test-Path $lock) { Get-Content $lock -ErrorAction SilentlyContinue } else { $null }
    $alive = $owner -and (Get-Process -Id $owner -ErrorAction SilentlyContinue)
    if (-not $alive) {
        Add-Content -Path $Log -Encoding utf8 -Value ("{0}  Supervisor: the watchdog was not running, so it was started again." -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
        try { Start-ScheduledTask -TaskName $TaskName -ErrorAction Stop }
        catch { Start-Process powershell.exe -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", (Join-Path $Root "tools\keep_going.ps1") -WindowStyle Hidden }
    }
    Start-Sleep -Seconds 120
}
