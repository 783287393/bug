# 一键复跑测试：指标单元/集成测试
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    .\.venv\Scripts\Activate.ps1
}

python -m pytest tests -q
if ($LASTEXITCODE -ne 0) { throw "测试未全部通过。" }
