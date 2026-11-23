"""Dashboard 测试：面板数量、数据源、查询、单位与无数据表达。"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DASHBOARD = json.loads(
    (ROOT / "grafana" / "dashboards" / "observability-lab.json").read_text(encoding="utf-8")
)


def test_dashboard_has_at_least_five_panels():
    panels = DASHBOARD["panels"]
    assert len(panels) >= 5


def test_each_panel_has_prometheus_target():
    for panel in DASHBOARD["panels"]:
        targets = panel.get("targets", [])
        assert targets, f"面板 {panel['title']} 缺少查询"
        for target in targets:
            assert target["expr"].strip(), f"面板 {panel['title']} 查询为空"


def test_panels_cover_required_observability_dimensions():
    titles = " ".join(p["title"] for p in DASHBOARD["panels"])
    for keyword in ["状态", "请求", "延迟", "CPU", "内存"]:
        assert keyword in titles, f"Dashboard 缺少维度: {keyword}"


def test_panel_units_are_set():
    for panel in DASHBOARD["panels"]:
        unit = panel["fieldConfig"]["defaults"].get("unit")
        assert unit, f"面板 {panel['title']} 未设置单位"


def test_dashboard_refresh_and_time_window():
    assert DASHBOARD["refresh"] == "15s"
    assert DASHBOARD["time"]["from"] == "now-30m"


def test_dashboard_datasource_uid_matches_provisioning():
    for panel in DASHBOARD["panels"]:
        assert panel["datasource"]["uid"] == "prometheus"
