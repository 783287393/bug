# 指标设计表（metrics-design）

## 1. 指标清单

| 指标名 | 类型 | 单位 | 标签（有界集合） | 含义 | 回答的问题 |
|---|---|---|---|---|---|
| `http_requests_total` | Counter | 次 | `method`、`route`、`status` | 累计 HTTP 请求数，只增不减，重启后由 PromQL `rate()` 处理重置 | 服务接收了多少请求？按方法/路由/状态如何分布？ |
| `http_request_duration_seconds` | Histogram | 秒 | `method`、`route` | 请求延迟分布，桶：0.01 / 0.025 / 0.05 / 0.1 / 0.25 / 0.5 / 1.0 / 2.0 | 延迟集中在什么水平？p50 / p95 是多少？ |
| `process_cpu_seconds_total` | Counter | 秒 | 无 | 当前应用进程 CPU 用户态 + 内核态时间（非整机） | 进程消耗了多少 CPU？速率换算为占用核数 |
| `process_resident_memory_bytes` | Gauge | 字节 | 无 | 当前应用进程常驻内存（RSS） | 进程内存是否持续增长？ |
| `up`（Prometheus 内置） | Gauge | 0/1 | `job` | 目标抓取是否成功 | 服务实例是否存活？ |

## 2. 标签基数审查（高基数约束）

- 允许的标签：`method`（GET/POST 等有限方法）、`route`（FastAPI 模板路径，如 `/api/items`）、`status`（200/500 等状态码）。
- **禁止**作为标签：用户 ID、原始 URL（如 `/users/123`）、查询参数、异常消息文本、订单号等取值无限的字段。
- `/metrics` 自身请求不计入业务流量指标，避免抓取行为污染业务曲线。
- 自定义进程指标仅在 `win32` 平台注册；Linux 上使用默认 ProcessCollector，避免指标重名。

## 3. 问题 — 指标 — PromQL — 面板 — 阈值 — 预期动作

| 运维问题 | 指标 | PromQL（窗口） | 面板 | 阈值/口径 | 预期动作 |
|---|---|---|---|---|---|
| 服务是否存活 | `up` | `up{job="demo-app"}` | 服务状态 Stat | `up==0` 持续 1 分钟触发 `AppInstanceDown` | 检查进程与 8000 端口，恢复后告警 Resolved |
| 请求流量水平 | `http_requests_total` | `sum(rate(http_requests_total{job="demo-app"}[1m]))` | 请求速率折线 | 观察基线，不设固定告警 | 流量上涨时对照延迟与 CPU 判断容量 |
| 是否出现错误 | `http_requests_total` | `sum by (status) (rate(http_requests_total{job="demo-app"}[1m]))` | 状态码速率折线 | 5xx 占比单独观察 | 错误率抬升时查看应用日志定位接口 |
| 延迟是否恶化 | `http_request_duration_seconds_bucket` | `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{job="demo-app"}[5m])))` | p50/p95 延迟折线 | p95 > 1s 持续 2 分钟触发 `HighLatencyP95` | 结合负载、CPU 与慢接口排查 |
| CPU 是否紧张 | `process_cpu_seconds_total` | `rate(process_cpu_seconds_total{job="demo-app"}[1m])` | 进程 CPU 核数 | 口径为单核倍数，整机百分比需再除以逻辑核数 | CPU 与延迟同时升高时关注热点接口 |
| 内存是否泄漏 | `process_resident_memory_bytes` | `process_resident_memory_bytes{job="demo-app"}` | 进程内存折线 | 观察是否单调上升不回落 | 持续增长时检查缓存与对象生命周期 |

## 4. 口径说明

- CPU 速率单位是「每秒消耗的 CPU 秒」，可理解为占用的 CPU 核数；乘以 100 为相对单个逻辑核的百分比。
- 进程指标测量的是当前应用进程，不是整机；Windows 进程指标、Linux 容器指标与整机 exporter 不能混为同一口径。
- Counter 是累计值，面板必须用 `rate()` / `increase()` 计算速率，不能直接画原始累计值。
