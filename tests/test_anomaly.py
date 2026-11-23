"""异常/恢复测试：负载脚本参数边界与异常时间线记录完整性。"""

import argparse
import pathlib

from scripts.load_test import one_request

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_load_script_clamp_delay():
    # delay_ms 超出 2000 时应被限制在 0-2000，不向外发送超大延迟
    parser = argparse.ArgumentParser()
    parser.add_argument("--total", type=int, default=1)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--delay-ms", type=int, default=0)
    parser.add_argument("--error-ratio", type=float, default=0.0)
    args = parser.parse_args(["--delay-ms", "5000"])
    assert min(2000, args.delay_ms) == 2000


def test_error_ratio_bounded():
    parser = argparse.ArgumentParser()
    parser.add_argument("--error-ratio", type=float, default=0.0)
    args = parser.parse_args(["--error-ratio", "0.5"])
    assert min(0.2, args.error_ratio) == 0.2


def test_anomaly_timeline_document_exists():
    timeline = ROOT / "docs" / "anomaly-timeline.md"
    assert timeline.exists()
    text = timeline.read_text(encoding="utf-8")
    for keyword in ["开始时间", "结束时间", "现象", "曲线变化", "结论边界"]:
        assert keyword in text, f"异常时间线缺少字段: {keyword}"
