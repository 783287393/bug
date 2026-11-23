"""
实验 08 · 软件运行监控与可观测性平台 —— 被监控的 FastAPI 演示应用。

职责：
1. 暴露 HTTP 请求计数（Counter）与延迟分布（Histogram）指标；
2. 暴露当前应用进程的 CPU / 内存指标（原生 Windows 下 ProcessCollector 不自动提供，
   因此在 win32 平台注册自定义 Collector，Linux 上由默认 ProcessCollector 提供）；
3. 提供受控延迟端点 /api/work 与错误端点 /api/error，用于异常模拟实验；
4. 在 /metrics 输出 Prometheus 文本格式指标，排除 /metrics 自身的流量统计。

指标标签只使用有界集合：method、route（模板路径）、status；
不使用用户 ID、原始 URL、查询参数或异常消息作为标签，避免高基数。
"""

import sys
from time import perf_counter

import psutil
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    REGISTRY,
    generate_latest,
)
from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily

app = FastAPI(title="observability-lab demo app", version="1.0.0")

# ---------------------------------------------------------------------------
# 指标定义（名称 / 类型 / 单位 / 标签见 metrics_design.md）
# ---------------------------------------------------------------------------

REQUESTS = Counter(
    "http_requests_total",
    "Total number of HTTP requests.",
    ["method", "route", "status"],
)

LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "route"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
)

# 仅在原生 Windows 下注册自定义进程指标；Linux 上默认 ProcessCollector 已提供
# process_cpu_seconds_total / process_resident_memory_bytes，避免重名重复注册。
if sys.platform == "win32":

    class WindowsProcessMetrics:
        """采集当前应用进程（非整机）的 CPU 秒数与常驻内存字节数。"""

        def collect(self):
            proc = psutil.Process()
            cpu = proc.cpu_times()
            yield CounterMetricFamily(
                "process_cpu_seconds_total",
                "Process CPU time in seconds (user + system).",
                value=cpu.user + cpu.system,
            )
            yield GaugeMetricFamily(
                "process_resident_memory_bytes",
                "Process resident set size in bytes.",
                value=proc.memory_info().rss,
            )

    REGISTRY.register(WindowsProcessMetrics())


def _template_route(request: Request) -> str:
    """取模板路由路径作为标签；中间件阶段 scope 可能尚未写入 route，
    回退到已注册路由表按路径匹配，避免把原始路径（潜在高基数）写入标签。"""
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    path = request.url.path
    for registered in app.routes:
        if getattr(registered, "path", None) == path:
            return registered.path
    return "unmatched"


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """记录请求计数与延迟；/metrics 自身不计入业务流量指标。"""
    route = _template_route(request)
    if route == "/metrics":
        return await call_next(request)

    start = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        status_code = 500
        raise
    finally:
        elapsed = perf_counter() - start
        REQUESTS.labels(request.method, route, str(status_code)).inc()
        LATENCY.labels(request.method, route).observe(elapsed)


# ---------------------------------------------------------------------------
# 业务演示端点
# ---------------------------------------------------------------------------


@app.get("/", include_in_schema=False)
def root():
    return {"service": "observability-lab", "status": "ok"}


@app.get("/api/items")
def list_items():
    """普通业务端点：返回固定列表，作为背景流量。"""
    return [{"id": i, "name": f"item-{i}"} for i in range(10)]


@app.get("/api/work")
def work(delay_ms: int = 0):
    """受控延迟端点：delay_ms 限制在 0-2000ms，用于观察 p95 抬升。"""
    delay_ms = max(0, min(2000, int(delay_ms)))
    # 用短休眠模拟处理耗时；delay_ms 来自查询参数，不作为指标标签。
    import time

    time.sleep(delay_ms / 1000.0)
    return {"delay_ms": delay_ms, "status": "done"}


@app.get("/api/error")
def trigger_error():
    """受控错误端点：返回 500，用于观察错误率指标。"""
    return PlainTextResponse("internal error demo", status_code=500)


@app.get("/metrics", include_in_schema=False)
def metrics():
    """Prometheus 抓取入口。"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
