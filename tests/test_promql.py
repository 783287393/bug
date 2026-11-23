"""PromQL 测试：核对查询的指标名、聚合函数、时间窗口与单位口径。"""

import re

QUERIES = {
    "up": 'up{job="demo-app"}',
    "request_rate": 'sum(rate(http_requests_total{job="demo-app"}[1m]))',
    "status_rate": 'sum by (status) (rate(http_requests_total{job="demo-app"}[1m]))',
    "error_rate": 'sum(rate(http_requests_total{job="demo-app",status=~"5.."}[1m])) / sum(rate(http_requests_total{job="demo-app"}[1m]))',
    "p95": 'histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{job="demo-app"}[5m])))',
    "cpu_rate": 'rate(process_cpu_seconds_total{job="demo-app"}[1m])',
    "memory": 'process_resident_memory_bytes{job="demo-app"}',
}


def test_up_query_uses_state_metric():
    assert "up" in QUERIES["up"]
    assert "job=" in QUERIES["up"]


def test_request_rate_uses_rate_with_window():
    q = QUERIES["request_rate"]
    assert "rate(" in q and "[1m]" in q
    assert "http_requests_total" in q


def test_status_rate_groups_by_status():
    q = QUERIES["status_rate"]
    assert "by (status)" in q and "[1m]" in q


def test_error_rate_filters_5xx():
    q = QUERIES["error_rate"]
    assert 'status=~"5.." ' in q or 'status=~"5.."' in q
    assert "/" in q  # 错误率为两个速率之比


def test_p95_uses_histogram_quantile_and_le():
    q = QUERIES["p95"]
    assert "histogram_quantile(0.95" in q
    assert "by (le)" in q and "_bucket" in q and "[5m]" in q


def test_resource_queries_have_unit_consistency():
    cpu = QUERIES["cpu_rate"]
    mem = QUERIES["memory"]
    assert "rate(" in cpu and "process_cpu_seconds_total" in cpu
    assert "process_resident_memory_bytes" in mem
    # CPU 速率单位为 核数（每秒 CPU 秒）；内存单位为字节
    assert not re.search(r"sum\(", cpu)
