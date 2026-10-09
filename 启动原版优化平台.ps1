$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$pythonPath = Join-Path $env:USERPROFILE 'miniforge3\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { $pythonPath = (Get-Command python).Source }
$runDirectory = Join-Path $projectRoot '.run'
New-Item -ItemType Directory -Path $runDirectory -Force | Out-Null
$running = Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
if ($running) { Write-Output '8501 端口已有服务，请在浏览器查看 http://127.0.0.1:8501'; exit 0 }
$previousReviewMode = $env:ARCTIC_ENABLE_LOCAL_REVIEW
try {
    # This launcher binds only to loopback. Public deployments default to read-only review.
    $env:ARCTIC_ENABLE_LOCAL_REVIEW = '1'
    $process = Start-Process -FilePath $pythonPath -ArgumentList @('-m','streamlit','run','app.py','--server.address','127.0.0.1','--server.port','8501','--server.headless','true','--server.fileWatcherType','none') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runDirectory 'streamlit.stdout.log') -RedirectStandardError (Join-Path $runDirectory 'streamlit.stderr.log') -PassThru
} finally { $env:ARCTIC_ENABLE_LOCAL_REVIEW = $previousReviewMode }
$process.Id | Set-Content -LiteralPath (Join-Path $runDirectory 'streamlit.pid')
$ready = $false
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    try {
        $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8501/_stcore/health' -UseBasicParsing -TimeoutSec 1
        if ($response.StatusCode -eq 200) { $ready = $true; break }
    } catch { }
    $process.Refresh()
    if ($process.HasExited) { throw '平台启动失败，请查看 .run/streamlit.stderr.log。' }
    Start-Sleep -Milliseconds 500
}
if ($ready) { Write-Output '原版优化平台：http://127.0.0.1:8501' }
else { Write-Output '平台仍在启动，可稍后打开 http://127.0.0.1:8501；启动记录保存在 .run 文件夹。' }
