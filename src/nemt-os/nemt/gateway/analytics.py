"""
APIAnalytics - API 分析统计

提供 API 使用统计、性能分析能力。
"""

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

__all__ = [
    "APIMetrics",
    "APIAnalytics",
]


@dataclass
class APIMetrics:
    """API 指标"""

    endpoint: str
    method: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0
    min_latency_ms: float = float("inf")
    max_latency_ms: float = 0
    p50_latency_ms: float = 0
    p95_latency_ms: float = 0
    p99_latency_ms: float = 0
    last_request_time: float = 0


class APIAnalytics:
    """
    API 分析统计

    示例:
    ```python
    analytics = APIAnalytics()

    # 记录请求
    analytics.record_request("/api/users", "GET", latency_ms=50, success=True)

    # 获取统计
    stats = analytics.get_endpoint_stats("/api/users", "GET")

    # 获取报告
    report = analytics.get_report()
    ```
    """

    def __init__(self):
        self._metrics: dict[str, dict[str, APIMetrics]] = defaultdict(dict)
        self._request_times: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        self._lock = threading.RLock()
        self._logger = logging.getLogger("APIAnalytics")

    def record_request(
        self,
        endpoint: str,
        method: str,
        latency_ms: float,
        success: bool,
        status_code: int = None,
        client_ip: str = None,
    ) -> None:
        """记录请求"""
        key = f"{method}:{endpoint}"

        with self._lock:
            if endpoint not in self._metrics:
                self._metrics[endpoint] = {}

            if method not in self._metrics[endpoint]:
                self._metrics[endpoint][method] = APIMetrics(endpoint=endpoint, method=method)

            metrics = self._metrics[endpoint][method]

            # 更新指标
            metrics.total_requests += 1
            if success:
                metrics.successful_requests += 1
            else:
                metrics.failed_requests += 1

            metrics.total_latency_ms += latency_ms
            metrics.min_latency_ms = min(metrics.min_latency_ms, latency_ms)
            metrics.max_latency_ms = max(metrics.max_latency_ms, latency_ms)
            metrics.last_request_time = time.time()

            # 记录延迟用于计算分位数
            self._request_times[endpoint][method].append(latency_ms)
            times = self._request_times[endpoint][method]

            # 保持最近 10000 条记录
            if len(times) > 10000:
                times[:] = times[-10000:]

            # 计算分位数
            if len(times) >= 10:
                sorted_times = sorted(times)
                n = len(sorted_times)
                metrics.p50_latency_ms = sorted_times[int(n * 0.5)]
                metrics.p95_latency_ms = sorted_times[int(n * 0.95)]
                metrics.p99_latency_ms = sorted_times[int(n * 0.99)]

    def get_endpoint_stats(self, endpoint: str, method: str = None) -> APIMetrics | None:
        """获取端点统计"""
        with self._lock:
            if method:
                return self._metrics.get(endpoint, {}).get(method)
            else:
                # 汇总所有方法
                methods = self._metrics.get(endpoint, {})
                if not methods:
                    return None

                total = APIMetrics(endpoint=endpoint, method="ALL")
                for m in methods.values():
                    total.total_requests += m.total_requests
                    total.successful_requests += m.successful_requests
                    total.failed_requests += m.failed_requests
                    total.total_latency_ms += m.total_latency_ms
                    total.min_latency_ms = min(total.min_latency_ms, m.min_latency_ms)
                    total.max_latency_ms = max(total.max_latency_ms, m.max_latency_ms)
                    total.last_request_time = max(total.last_request_time, m.last_request_time)

                if total.total_requests > 0:
                    total.total_latency_ms /= total.total_requests
                return total

    def get_all_stats(self) -> list[APIMetrics]:
        """获取所有统计"""
        with self._lock:
            result = []
            for endpoint, methods in self._metrics.items():
                for method, metrics in methods.items():
                    result.append(metrics)
            return result

    def get_report(self) -> dict[str, Any]:
        """生成分析报告"""
        with self._lock:
            total_requests = sum(m.total_requests for methods in self._metrics.values() for m in methods.values())

            total_errors = sum(m.failed_requests for methods in self._metrics.values() for m in methods.values())

            # 找出最慢的端点
            slowest = []
            for endpoint, methods in self._metrics.items():
                for method, m in methods.items():
                    avg_latency = m.total_latency_ms / m.total_requests if m.total_requests > 0 else 0
                    slowest.append((f"{method}:{endpoint}", avg_latency, m.total_requests))

            slowest.sort(key=lambda x: x[1], reverse=True)

            return {
                "total_requests": total_requests,
                "total_errors": total_errors,
                "error_rate": total_errors / total_requests if total_requests > 0 else 0,
                "slowest_endpoints": [{"endpoint": e, "avg_latency_ms": l, "requests": r} for e, l, r in slowest[:10]],
                "endpoints": len(self._metrics),
                "generated_at": time.time(),
            }

    def get_top_endpoints(self, limit: int = 10) -> list[dict]:
        """获取请求量最高的端点"""
        with self._lock:
            endpoint_counts = []
            for endpoint, methods in self._metrics.items():
                total = sum(m.total_requests for m in methods.values())
                endpoint_counts.append((endpoint, total))

            endpoint_counts.sort(key=lambda x: x[1], reverse=True)

            return [{"endpoint": e, "requests": r} for e, r in endpoint_counts[:limit]]

    def get_error_endpoints(self, limit: int = 10) -> list[dict]:
        """获取错误率最高的端点"""
        with self._lock:
            endpoint_errors = []
            for endpoint, methods in self._metrics.items():
                total = sum(m.total_requests for m in methods.values())
                errors = sum(m.failed_requests for m in methods.values())
                if total > 0:
                    endpoint_errors.append((endpoint, errors, total, errors / total))

            endpoint_errors.sort(key=lambda x: x[3], reverse=True)

            return [
                {"endpoint": e, "errors": err, "total": t, "error_rate": r} for e, err, t, r in endpoint_errors[:limit]
            ]

    def clear(self) -> None:
        """清除统计数据"""
        with self._lock:
            self._metrics.clear()
            self._request_times.clear()
