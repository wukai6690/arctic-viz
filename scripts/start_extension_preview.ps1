$ErrorActionPreference = 'Stop'
$releaseRoot = Split-Path -Parent $PSScriptRoot
$outputPath = Join-Path $releaseRoot 'test-results/research-extension'
New-Item -ItemType Directory -Force -Path $outputPath | Out-Null
$listener = Get-NetTCPConnection -LocalPort 8502 -State Listen -ErrorAction SilentlyContinue
if ($listener) { throw 'Port 8502 is already in use; no process was changed.' }
$oldReview = $env:ARCTIC_ENABLE_LOCAL_REVIEW
try {
    $env:ARCTIC_ENABLE_LOCAL_REVIEW = '0'
    $pythonPath = (Get-Command python -ErrorAction Stop).Source
    $preview = Start-Process -FilePath $pythonPath -ArgumentList @('-m','streamlit','run','app.py','--server.address','127.0.0.1','--server.port','8502','--server.headless','true') -WorkingDirectory $releaseRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $outputPath 'preview.stdout.log') -RedirectStandardError (Join-Path $outputPath 'preview.stderr.log') -PassThru
    $preview.Id | Set-Content -LiteralPath (Join-Path $outputPath 'preview.pid')
    Write-Output "Preview started: $($preview.Id)"
} finally { $env:ARCTIC_ENABLE_LOCAL_REVIEW = $oldReview }
