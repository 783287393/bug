# 启动被监控的 FastAPI 演示应用（单 uvicorn worker，避免多进程指标聚合问题）
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    .\.venv\Scripts\Activate.ps1
}

uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
