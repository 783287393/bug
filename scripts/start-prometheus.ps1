# 启动 Prometheus 3.14.0（原生 Windows 路线）
# 前置：从官方 Release 下载 windows-amd64 ZIP 解压，并把解压目录路径写入环境变量 PROMETHEUS_HOME，
# 例如 D:\tools\prometheus-3.14.0.windows-amd64（目录内含 prometheus.exe、promtool.exe）。
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

if (-not $env:PROMETHEUS_HOME) {
    throw "未设置环境变量 PROMETHEUS_HOME，请指向 Prometheus 解压目录。"
}

$dataDir = Join-Path $root "data\prometheus"
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

& (Join-Path $env:PROMETHEUS_HOME "promtool.exe") check config (Join-Path $root "prometheus\prometheus.yml")
if ($LASTEXITCODE -ne 0) { throw "prometheus.yml 配置校验未通过。" }

& (Join-Path $env:PROMETHEUS_HOME "prometheus.exe") `
    --config.file=(Join-Path $root "prometheus\prometheus.yml") `
    --storage.tsdb.path=$dataDir `
    --web.listen-address=127.0.0.1:9090
