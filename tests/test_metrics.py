"""指标单元/集成测试：Counter、Histogram、错误计数、/metrics 输出与标签基数约束。"""

import re

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _metrics_text() -> str:
    resp = client.get("/metrics")
    assert resp.status_code == 200
    return resp.text


def _count_metric(text: str, metric: str, route: str, status: str | None = None) -> float:
    pattern = rf'{metric}\{{[^}}]*route="{re.escape(route)}"[^}}]*'
    if status:
        pattern += rf'status="{status}"'
    pattern += r'[^}}]*\}\s+([0-9.]+)'
    matches = re.findall(pattern, text)
    return sum(float(v) for v in matches)


def test_root_endpoint_ok():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_metrics_endpoint_content_type():
    resp = client.get("/metrics")
    assert "text/plain" in resp.headers["content-type"]
    assert "version=0.0.4" in resp.headers["content-type"]


def test_counter_increments_after_request():
    before = _count_metric(_metrics_text(), "http_requests_total", "/api/items")
    for _ in range(3):
        assert client.get("/api/items").status_code == 200
    after = _count_metric(_metrics_text(), "http_requests_total", "/api/items")
    assert after - before == 3


def test_histogram_bucket_recorded():
    client.get("/api/items")
    text = _metrics_text()
    assert "http_request_duration_seconds_bucket" in text
    assert re.search(r'http_request_duration_seconds_bucket\{[^}]*route="/api/items"', text)


def test_error_endpoint_records_500():
    resp = client.get("/api/error")
    assert resp.status_code == 500
    text = _metrics_text()
    assert _count_metric(text, "http_requests_total", "/api/error", status="500") >= 1


def test_labels_use_bounded_values_only():
    client.get("/api/items")
    text = _metrics_text()
    # 请求指标只允许 method / route / status 三个标签
    for line in text.splitlines():
        if line.startswith("http_requests_total{"):
            labels = set(re.findall(r'([a-z_]+)="', line))
            assert labels <= {"method", "route", "status"}, f"出现越界标签: {labels}"
            # 路由标签必须是模板路径，不能带具体资源 ID
            route = re.search(r'route="([^"]*)"', line).group(1)
            assert not re.search(r"/\d+$", route), f"高基数路由: {route}"


def test_process_memory_metric_present():
    text = _metrics_text()
    assert "process_resident_memory_bytes" in text
