# 启动 Grafana OSS 13.2.1（原生 Windows 路线）
# 前置：下载 Grafana OSS Windows ZIP 解压，并把解压目录路径写入环境变量 GRAFANA_HOME，
# 例如 D:\tools\grafana-13.2.1（目录内含 bin\grafana.exe）。
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

if (-not $env:GRAFANA_HOME) {
    throw "未设置环境变量 GRAFANA_HOME，请指向 Grafana 解压目录。"
}

$env:GF_SERVER_HTTP_ADDR = "127.0.0.1"
$env:GF_SERVER_HTTP_PORT = "3000"
$env:GF_PATHS_PROVISIONING = Join-Path $root "grafana\provisioning"

& (Join-Path $env:GRAFANA_HOME "bin\grafana.exe") server --homepath $env:GRAFANA_HOME
