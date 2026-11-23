"""
受控负载脚本：仅对本机 127.0.0.1:8000 发请求，限制并发与总次数。
禁止对非本人或未授权系统压测。

用法示例：
  python scripts/load_test.py --total 200 --concurrency 4 --delay-ms 0
  python scripts/load_test.py --total 200 --concurrency 4 --delay-ms 300 --error-ratio 0.1
"""

import argparse
import concurrent.futures
import re
import time

import requests

DEFAULT_BASE = "http://127.0.0.1:8000"
BASE = DEFAULT_BASE


def one_request(index: int, delay_ms: int, error_ratio: float) -> int:
    try:
        if (index % 100) < int(error_ratio * 100):
            resp = requests.get(f"{BASE}/api/error", timeout=5)
        else:
            resp = requests.get(f"{BASE}/api/work", params={"delay_ms": delay_ms}, timeout=5)
        return resp.status_code
    except requests.RequestException as exc:
        print(f"[{index}] request failed: {exc}")
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="受控负载脚本（仅本机演示应用）")
    parser.add_argument("--total", type=int, default=100, help="总请求次数")
    parser.add_argument("--concurrency", type=int, default=4, help="并发数（不超过 8）")
    parser.add_argument("--delay-ms", type=int, default=0, help="每请求附加延迟 0-2000ms")
    parser.add_argument("--error-ratio", type=float, default=0.0, help="错误请求占比 0-0.2")
    parser.add_argument("--base", default=DEFAULT_BASE, help="应用基础地址，容器路线映射到 8001 时传 http://127.0.0.1:8001")
    args = parser.parse_args()
    global BASE
    BASE = args.base

    concurrency = min(args.concurrency, 8)
    delay_ms = max(0, min(2000, args.delay_ms))
    error_ratio = max(0.0, min(0.2, args.error_ratio))

    print(f"开始负载：total={args.total}, concurrency={concurrency}, delay_ms={delay_ms}, "
          f"error_ratio={error_ratio}")
    start = time.perf_counter()
    status_counter: dict[int, int] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(one_request, i, delay_ms, error_ratio) for i in range(args.total)]
        for future in concurrent.futures.as_completed(futures):
            code = future.result()
            status_counter[code] = status_counter.get(code, 0) + 1

    elapsed = time.perf_counter() - start
    print(f"完成：耗时 {elapsed:.2f}s，状态码分布 {dict(sorted(status_counter.items()))}")


if __name__ == "__main__":
    main()
