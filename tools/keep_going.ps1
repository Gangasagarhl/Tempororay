<#
Keeps LangChain Lab complete and up to date, without stopping.

Every 2 minutes it checks, and fixes what it finds:
  1. API reference not downloaded       -> downloads it (resumes where it stopped)
  2. Lab older than its sources/tools   -> builds a new copy, checks every word, every link and the page in a browser,
                                           and only then swaps it in. A failed copy is thrown away and the old lab stays.
  3. Gemini key in .env                 -> rewrites the docs in simpler words, and resumes after each daily free limit
It waits while memory is low or while another build is running.

  Run now:            powershell -ExecutionPolicy Bypass -File tools\keep_going.ps1
  Start at logon:     powershell -ExecutionPolicy Bypass -File tools\keep_going.ps1 -Install
  Stop for good:      powershell -ExecutionPolicy Bypass -File tools\keep_going.ps1 -Uninstall
  Log:                logs\keep_going.log
#>
param([switch]$Install, [switch]$Uninstall, [switch]$Once)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root ".venv\Scripts\python.exe"
$Logs = Join-Path $Root "logs"
$Site = Join-Path $Root "site"
$Stage = Join-Path $Site "data.new"
$Live = Join-Path $Site "data"
$Old = Join-Path $Site "data.old"
$StateFile = Join-Path $Logs "keep_going_state.json"
$TaskName = "LangChain Lab keep going"
New-Item -ItemType Directory -Force $Logs | Out-Null

if ($Install) {
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$PSCommandPath`"" -WorkingDirectory $Root
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 99 -RestartInterval (New-TimeSpan -Minutes 5)
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
    Write-Output "Installed: it starts at every logon. Remove with -Uninstall."
    return
}
if ($Uninstall) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Output "Removed."
    return
}

function Log($text) {
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $text
    Add-Content -Path (Join-Path $Logs "keep_going.log") -Value $line -Encoding utf8
    Write-Host $line  # not Write-Output: that would leak into the pass/fail results of the checks
}

# One copy only.
$lockPath = Join-Path $Logs "keep_going.lock"
if (Test-Path $lockPath) {
    $other = Get-Content $lockPath -ErrorAction SilentlyContinue
    if ($other -and (Get-Process -Id $other -ErrorAction SilentlyContinue)) { Write-Output "Already running as process $other."; return }
}
Set-Content -Path $lockPath -Value $PID

function Get-State {
    if (Test-Path $StateFile) { return Get-Content -Raw $StateFile | ConvertFrom-Json }
    return [pscustomobject]@{ builtFrom = ""; failedFrom = ""; lastBuild = "2000-01-01"; rewriteWaitUntil = "2000-01-01" }
}
function Save-State($state) { $state | ConvertTo-Json | Set-Content -Path $StateFile -Encoding utf8 }

function Free-GB { [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1) }

function Other-Work {
    # Lab work started by someone else, such as a Claude session, counts as busy.
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match "build_site\.py|fetch_reference\.py|audit_words\.py|rewrite\.py" -and $_.ProcessId -ne $PID }
}

function Run-Python([string[]]$arguments, [string]$label) {
    $out = Join-Path $Logs "$label.out.txt"
    $err = Join-Path $Logs "$label.err.txt"
    $process = Start-Process -FilePath $Py -ArgumentList (@("-I", "-X", "utf8", "-u") + $arguments) -WorkingDirectory $Root -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -PassThru -Wait
    return @{ code = $process.ExitCode; text = (Get-Content -Raw -Encoding utf8 $out -ErrorAction SilentlyContinue) }
}

function Inputs-Stamp {
    $paths = @("tools\build_site.py", "tools\textcheck.py", "content", "coverage.json", "source\reference\index.jsonl", "source\raw\openapi", "source\simple\done.jsonl")
    $newest = Get-Date "2000-01-01"
    foreach ($relative in $paths) {
        $full = Join-Path $Root $relative
        if (Test-Path $full) {
            Get-ChildItem $full -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object { if ($_.LastWriteTime -gt $newest) { $newest = $_.LastWriteTime } }
        }
    }
    return $newest.ToString("o")
}

function Browser-Test {
    $edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
    if (-not (Test-Path $edge)) { Log "Edge not found; skipping the browser test."; return $true }
    $page = Join-Path $Site "selftest.html"
    Copy-Item (Join-Path $Root "tools\selftest.html") $page -Force
    $dom = Join-Path $Logs "selftest.dom.txt"
    $profile = Join-Path $Logs "edge-profile"
    Start-Process -FilePath $edge -ArgumentList "--headless", "--disable-gpu", "--no-first-run", "--user-data-dir=$profile", "--virtual-time-budget=180000", "--dump-dom", ("file:///" + ($page -replace '\\', '/')) -RedirectStandardOutput $dom -RedirectStandardError (Join-Path $Logs "selftest.err.txt") -Wait | Out-Null
    Remove-Item $page -Force
    $text = Get-Content -Raw -Encoding utf8 $dom -ErrorAction SilentlyContinue
    $result = ($text -replace '(?s).*<pre id="out">', '') -replace '(?s)</pre>.*', ''
    Log ("Browser test: " + (($result -split "`n" | Where-Object { $_ }) -join " / "))
    return ($result -match "DONE") -and -not ($result -match "ERROR|TIMEOUT")
}

function Checks-Pass($folder) {
    $verify = Run-Python @("tools\verify_site.py", $folder) "verify"
    $audit = Run-Python @("tools\audit_words.py", $folder) "audit"
    Log ("Checks: " + (($verify.text -split "`n" | Select-Object -First 5) -join " / "))
    $ok = $verify.code -eq 0 -and $audit.code -eq 0
    foreach ($pattern in "docs pages missing: 0 ", "REST operations missing: 0", "structure problems: 0 ", "pointing nowhere: 0") {
        if ($verify.text -notmatch [regex]::Escape($pattern)) { $ok = $false; Log "Check failed: expected '$pattern'" }
    }
    $report = Join-Path $folder "audit_report.json"
    if (Test-Path $report) {
        $counts = (Get-Content -Raw -Encoding utf8 $report | ConvertFrom-Json).counts
        foreach ($property in $counts.PSObject.Properties) {
            if ($property.Name -match "missing" -and $property.Value -gt 0) { $ok = $false; Log ("Word check failed: {0} = {1}" -f $property.Name, $property.Value) }
        }
    } else { $ok = $false; Log "Word check made no report." }
    return $ok
}

function Build-And-Swap($state, $stamp) {
    Log "Building a new copy of the lab."
    $env:LAB_OUT = $Stage
    $build = Run-Python @("tools\build_site.py") "build"
    Remove-Item Env:LAB_OUT
    if ($build.code -ne 0) {
        Log ("Build failed; the current lab stays. " + ((Get-Content (Join-Path $Logs "build.err.txt") -Tail 3) -join " "))
        $state.failedFrom = $stamp; Save-State $state; return
    }
    if (-not (Checks-Pass $Stage)) {
        Log "The new copy failed a check, so the current lab stays. Details: logs\verify.out.txt and logs\audit.out.txt"
        $state.failedFrom = $stamp; Save-State $state; return
    }
    if (Test-Path $Old) { Remove-Item $Old -Recurse -Force }
    Copy-Item (Join-Path $Site "app.js") (Join-Path $Logs "app.js.before") -Force
    if (Test-Path $Live) { Rename-Item $Live "data.old" }
    Rename-Item $Stage "data"
    Run-Python @("tools\patch_app.py") "patch" | Out-Null
    if (Browser-Test) {
        if (Test-Path $Old) { Remove-Item $Old -Recurse -Force }
        Run-Python @("tools\copy_pictures.py") "pictures" | Out-Null
        $state.builtFrom = $stamp; $state.failedFrom = ""; $state.lastBuild = (Get-Date).ToString("o"); Save-State $state
        Log "The lab is updated and passed every check."
    } else {
        Log "The browser test failed, so the previous lab is put back."
        Remove-Item $Live -Recurse -Force
        if (Test-Path $Old) { Rename-Item $Old "data" }
        Copy-Item (Join-Path $Logs "app.js.before") (Join-Path $Site "app.js") -Force
        $state.failedFrom = $stamp; Save-State $state
    }
}

function Has-GeminiKey {
    $envFile = Join-Path $Root ".env"
    return (Test-Path $envFile) -and (Select-String -Path $envFile -Pattern '^GEMINI_API_KEY=\S+' -Quiet)
}

Log "Keep-going started (process $PID)."
try {
    while ($true) {
        $state = Get-State
        if (Other-Work) { Log "Other lab work is running; waiting." }
        elseif ((Free-GB) -lt 1.0) { Log ("Only {0} GB of memory free; waiting." -f (Free-GB)) }  # above this, Windows moves overflow to disk and work goes on
        elseif (-not (Test-Path (Join-Path $Root "source\reference\crawl_report.json"))) {
            Log "Downloading the API reference (it resumes where it stopped)."
            $crawl = Run-Python @("tools\fetch_reference.py") "crawl"
            Log ("Download finished with code {0}." -f $crawl.code)
        }
        else {
            $stamp = Inputs-Stamp
            $onlyRewrites = $state.builtFrom -and ((Get-Item (Join-Path $Root "source\simple\done.jsonl") -ErrorAction SilentlyContinue).LastWriteTime -gt [datetime]$state.builtFrom)
            $tooSoon = $onlyRewrites -and ((Get-Date) - [datetime]$state.lastBuild).TotalHours -lt 6
            $built = Test-Path (Join-Path $Live "build_report.json")
            if ((-not $built -or $stamp -ne $state.builtFrom) -and $stamp -ne $state.failedFrom -and -not $tooSoon) {
                Build-And-Swap $state $stamp
            }
            elseif ((Has-GeminiKey) -and (Get-Date) -gt [datetime]$state.rewriteWaitUntil) {
                $units = Join-Path $Root "source\simple\units.jsonl"
                if (-not (Test-Path $units) -or (Get-Item $units).LastWriteTime -lt [datetime]$state.lastBuild) {
                    Log "Listing the passages to rewrite."
                    $collect = Run-Python @("tools\rewrite.py", "collect") "rewrite-collect"
                    Log $collect.text.Trim()
                }
                Log "Rewriting in simpler words."
                $rewrite = Run-Python @("tools\rewrite.py", "run") "rewrite"
                $last = ($rewrite.text -split "`n" | Where-Object { $_.Trim() } | Select-Object -Last 1)
                Log "Rewrite: $last"
                if ($rewrite.text -match "Free limit reached") {
                    $state.rewriteWaitUntil = (Get-Date).AddHours(1).ToString("o"); Save-State $state
                }
            }
        }
        if ($Once) { break }
        Start-Sleep -Seconds 120
    }
}
finally {
    Remove-Item $lockPath -Force -ErrorAction SilentlyContinue
}
