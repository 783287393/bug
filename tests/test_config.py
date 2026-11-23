"""配置测试：Prometheus 抓取配置与告警规则可解析、目标与窗口正确。"""

import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_prometheus_config_parses():
    cfg = yaml.safe_load((ROOT / "prometheus" / "prometheus.yml").read_text(encoding="utf-8"))
    assert cfg["global"]["scrape_interval"] == "15s"
    jobs = cfg["scrape_configs"]
    assert len(jobs) == 1
    assert jobs[0]["job_name"] == "demo-app"
    assert jobs[0]["static_configs"][0]["targets"] == ["127.0.0.1:8000"]


def test_alert_rules_parse():
    rules = yaml.safe_load((ROOT / "prometheus" / "alerts.yml").read_text(encoding="utf-8"))
    groups = rules["groups"]
    assert len(groups) == 1
    alerts = groups[0]["rules"]
    names = {a["alert"] for a in alerts}
    assert {"AppInstanceDown", "HighLatencyP95"} <= names
    for alert in alerts:
        assert alert["for"], "告警必须设置 for 持续时间，避免尖峰抖动误报"


def test_grafana_datasource_provisioning():
    ds = yaml.safe_load(
        (ROOT / "grafana" / "provisioning" / "datasources" / "prometheus.yml").read_text(encoding="utf-8")
    )
    datasource = ds["datasources"][0]
    assert datasource["type"] == "prometheus"
    # 原生本机路线访问 127.0.0.1；Compose 路线经服务名 prometheus 访问，两者均合法。
    assert datasource["url"] in {"http://127.0.0.1:9090", "http://prometheus:9090"}
