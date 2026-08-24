"""
Metrics - 指标系统

提供完整的指标采集、聚合和导出能力。
"""

import json
import logging
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "MetricType",
    "Metric",
    "Counter",
    "Gauge",
    "Histogram",
    "Summary",
    "MetricsRegistry",
    "MetricsCollector",
]


class MetricType(Enum):
    """指标类型"""

    COUNTER = "counter"  # 计数器
    GAUGE = "gauge"  # 仪表
    HISTOGRAM = "histogram"  # 直方图
    SUMMARY = "summary"  # 摘要


@dataclass
class Metric:
    """指标基类"""

    name: str
    description: str = ""
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def get_value(self) -> float:
        raise NotImplementedError

    def to_prometheus(self) -> str:
        raise NotImplementedError


class Counter(Metric):
    """
    计数器

    示例:
    ```python
    counter = Counter("requests_total", "Total requests", ["method", "status"])

    counter.inc()                    # +1
    counter.inc(5)                   # +5
    counter.inc(labels={"method": "GET", "status": "200"})
    ```
    """

    def __init__(self, name: str, description: str = "", labels: list[str] = None):
        super().__init__(name, description, {})
        self._labels = labels or []
        self._values: dict[tuple, float] = defaultdict(float)
        self._lock = threading.RLock()

    @property
    def labels(self) -> list[str]:
        return self._labels

    def inc(self, value: float = 1, labels: dict[str, str] = None) -> None:
        """增加计数"""
        with self._lock:
            key = self._make_key(labels)
            self._values[key] += value

    def get(self, labels: dict[str, str] = None) -> float:
        """获取当前值"""
        with self._lock:
            key = self._make_key(labels)
            return self._values.get(key, 0)

    def get_value(self) -> float:
        return sum(self._values.values())

    def _make_key(self, labels: dict[str, str]) -> tuple:
        """生成标签键"""
        if not self._labels:
            return ()
        if labels:
            return tuple(labels.get(l, "") for l in self._labels)
        return tuple("" for _ in self._labels)

    def to_prometheus(self) -> str:
        lines = []
        with self._lock:
            for key, value in self._values.items():
                label_str = ""
                if key and self._labels:
                    label_parts = [f'{l}="{v}"' for l, v in zip(self._labels, key, strict=False)]
                    label_str = "," + ",".join(label_parts)

                lines.append(f"{self.name}{label_str} {value}")
        return "\n".join(lines)


class Gauge(Metric):
    """
    仪表

    示例:
    ```python
    gauge = Gauge("memory_usage_bytes", "Memory usage in bytes")

    gauge.set(1024)              # 设置为 1024
    gauge.inc(10)                # +10
    gauge.dec(5)                # -5
    ```
    """

    def __init__(self, name: str, description: str = "", labels: list[str] = None):
        super().__init__(name, description, {})
        self._labels = labels or []
        self._values: dict[tuple, float] = defaultdict(float)
        self._lock = threading.RLock()

    def set(self, value: float, labels: dict[str, str] = None) -> None:
        """设置值"""
        with self._lock:
            key = self._make_key(labels)
            self._values[key] = value

    def inc(self, value: float = 1, labels: dict[str, str] = None) -> None:
        """增加"""
        with self._lock:
            key = self._make_key(labels)
            self._values[key] += value

    def dec(self, value: float = 1, labels: dict[str, str] = None) -> None:
        """减少"""
        self.inc(-value, labels)

    def get(self, labels: dict[str, str] = None) -> float:
        """获取当前值"""
        with self._lock:
            key = self._make_key(labels)
            return self._values.get(key, 0)

    def get_value(self) -> float:
        return sum(self._values.values()) if self._values else 0

    def _make_key(self, labels: dict[str, str]) -> tuple:
        if not self._labels:
            return ()
        if labels:
            return tuple(labels.get(l, "") for l in self._labels)
        return tuple("" for _ in self._labels)

    def to_prometheus(self) -> str:
        lines = []
        with self._lock:
            for key, value in self._values.items():
                label_str = ""
                if key and self._labels:
                    label_parts = [f'{l}="{v}"' for l, v in zip(self._labels, key, strict=False)]
                    label_str = "," + ",".join(label_parts)
                lines.append(f"{self.name}{label_str} {value}")
        return "\n".join(lines)


class Histogram(Metric):
    """
    直方图

    示例:
    ```python
    histogram = Histogram(
        "request_duration_seconds",
        "Request duration in seconds",
        buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
    )

    histogram.observe(0.123)  # 记录观测值
    ```
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        buckets: list[float] = None,
        labels: list[str] = None,
    ):
        super().__init__(name, description, {})
        self._labels = labels or []
        self._buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        self._values: dict[tuple, dict[str, float]] = defaultdict(
            lambda: {"sum": 0, "count": 0, **{b: 0 for b in self._buckets}}
        )
        self._lock = threading.RLock()

    def observe(self, value: float, labels: dict[str, str] = None) -> None:
        """记录观测值"""
        with self._lock:
            key = self._make_key(labels)
            bucket_data = self._values[key]

            bucket_data["sum"] += value
            bucket_data["count"] += 1

            for bound in self._buckets:
                if value <= bound:
                    bucket_data[bound] += 1

    def get_value(self) -> float:
        with self._lock:
            return sum(v["count"] for v in self._values.values())

    def _make_key(self, labels: dict[str, str]) -> tuple:
        if not self._labels:
            return ()
        if labels:
            return tuple(labels.get(l, "") for l in self._labels)
        return tuple("" for _ in self._labels)

    def to_prometheus(self) -> str:
        lines = []
        with self._lock:
            for key, data in self._values.items():
                label_str = ""
                if key and self._labels:
                    label_parts = [f'{l}="{v}"' for l, v in zip(self._labels, key, strict=False)]
                    label_str = "," + ",".join(label_parts)

                # 输出每个 bucket
                cumulative = 0
                for bound in self._buckets:
                    cumulative += data[bound]
                    bucket_line = f'{self.name}_bucket{{le="{bound}"{label_str}}} {cumulative}'
                    lines.append(bucket_line)

                # 输出 +Inf bucket
                lines.append(f"{self.name}_bucket{{le=\"+Inf\"{label_str}}} {data['count']}")

                # 输出 sum 和 count
                lines.append(f"{self.name}_sum{label_str} {data['sum']}")
                lines.append(f"{self.name}_count{label_str} {data['count']}")

        return "\n".join(lines)


class Summary(Metric):
    """
    摘要

    示例:
    ```python
    summary = Summary("request_size_bytes", "Request size in bytes")

    summary.observe(1024)
    ```
    """

    def __init__(self, name: str, description: str = "", labels: list[str] = None):
        super().__init__(name, description, {})
        self._labels = labels or []
        self._values: dict[tuple, dict[str, float]] = defaultdict(lambda: {"sum": 0, "count": 0, "quantiles": {}})
        self._quantiles = [0.5, 0.9, 0.95, 0.99]
        self._lock = threading.RLock()

    def observe(self, value: float, labels: dict[str, str] = None) -> None:
        """记录观测值"""
        with self._lock:
            key = self._make_key(labels)
            data = self._values[key]

            data["sum"] += value
            data["count"] += 1

            # 更新分位数（简化实现）
            if "values" not in data:
                data["values"] = []
            data["values"].append(value)
            data["values"] = data["values"][-1000:]  # 保留最近1000个

            # 计算分位数
            if len(data["values"]) >= 10:
                sorted_vals = sorted(data["values"])
                for q in self._quantiles:
                    idx = int(len(sorted_vals) * q)
                    data["quantiles"][q] = sorted_vals[min(idx, len(sorted_vals) - 1)]

    def get_value(self) -> float:
        with self._lock:
            return sum(v["count"] for v in self._values.values())

    def _make_key(self, labels: dict[str, str]) -> tuple:
        if not self._labels:
            return ()
        if labels:
            return tuple(labels.get(l, "") for l in self._labels)
        return tuple("" for _ in self._labels)

    def to_prometheus(self) -> str:
        lines = []
        with self._lock:
            for key, data in self._values.items():
                label_str = ""
                if key and self._labels:
                    label_parts = [f'{l}="{v}"' for l, v in zip(self._labels, key, strict=False)]
                    label_str = "," + ",".join(label_parts)

                for q, v in data.get("quantiles", {}).items():
                    lines.append(f'{self.name}{{quantile="{q}"{label_str}}} {v}')

                lines.append(f"{self.name}_sum{label_str} {data['sum']}")
                lines.append(f"{self.name}_count{label_str} {data['count']}")

        return "\n".join(lines)


class MetricsRegistry:
    """
    指标注册表

    示例:
    ```python
    registry = MetricsRegistry()

    # 注册指标
    counter = registry.counter("requests_total", "Total requests", ["method"])
    histogram = registry.histogram("request_duration", "Request duration")

    # 收集所有指标
    metrics = registry.collect()
    ```
    """

    def __init__(self, namespace: str = "nemt"):
        self.namespace = namespace
        self._metrics: dict[str, Metric] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger("MetricsRegistry")

    def _prefix_name(self, name: str) -> str:
        if self.namespace:
            return f"{self.namespace}_{name}"
        return name

    def counter(self, name: str, description: str = "", labels: list[str] = None) -> Counter:
        """创建计数器"""
        with self._lock:
            full_name = self._prefix_name(name)
            if full_name in self._metrics:
                return self._metrics[full_name]

            counter = Counter(full_name, description, labels)
            self._metrics[full_name] = counter
            return counter

    def gauge(self, name: str, description: str = "", labels: list[str] = None) -> Gauge:
        """创建仪表"""
        with self._lock:
            full_name = self._prefix_name(name)
            if full_name in self._metrics:
                return self._metrics[full_name]

            gauge = Gauge(full_name, description, labels)
            self._metrics[full_name] = gauge
            return gauge

    def histogram(
        self, name: str, description: str = "", buckets: list[float] = None, labels: list[str] = None
    ) -> Histogram:
        """创建直方图"""
        with self._lock:
            full_name = self._prefix_name(name)
            if full_name in self._metrics:
                return self._metrics[full_name]

            histogram = Histogram(full_name, description, buckets, labels)
            self._metrics[full_name] = histogram
            return histogram

    def summary(self, name: str, description: str = "", labels: list[str] = None) -> Summary:
        """创建摘要"""
        with self._lock:
            full_name = self._prefix_name(name)
            if full_name in self._metrics:
                return self._metrics[full_name]

            summary = Summary(full_name, description, labels)
            self._metrics[full_name] = summary
            return summary

    def get(self, name: str) -> Metric | None:
        """获取指标"""
        with self._lock:
            return self._metrics.get(self._prefix_name(name))

    def collect(self) -> str:
        """收集所有指标（Prometheus 格式）"""
        with self._lock:
            lines = []
            for metric in self._metrics.values():
                if isinstance(metric, (Counter, Gauge, Histogram, Summary)):
                    output = metric.to_prometheus()
                    if output:
                        lines.append(output)
            return "\n".join(lines)

    def list_metrics(self) -> list[dict[str, Any]]:
        """列出所有指标"""
        with self._lock:
            return [
                {
                    "name": m.name,
                    "type": m.__class__.__name__,
                    "description": m.description,
                }
                for m in self._metrics.values()
            ]


class MetricsCollector:
    """
    指标收集器

    示例:
    ```python
    collector = MetricsCollector()

    # 创建指标
    collector.create_counter("requests", labels=["method"])
    collector.create_histogram("latency")

    # 记录数据
    collector.get_counter("requests").inc(labels={"method": "GET"})
    collector.get_histogram("latency").observe(0.123)

    # HTTP 端点
    @app.route("/metrics")
    def metrics():
        return collector.export()
    ```
    """

    def __init__(self, namespace: str = "nemt"):
        self.registry = MetricsRegistry(namespace)
        self._collectors: list[Callable[[], None]] = []
        self._lock = threading.RLock()

    def create_counter(self, name: str, description: str = "", labels: list[str] = None) -> Counter:
        return self.registry.counter(name, description, labels)

    def create_gauge(self, name: str, description: str = "", labels: list[str] = None) -> Gauge:
        return self.registry.gauge(name, description, labels)

    def create_histogram(
        self, name: str, description: str = "", buckets: list[float] = None, labels: list[str] = None
    ) -> Histogram:
        return self.registry.histogram(name, description, buckets, labels)

    def create_summary(self, name: str, description: str = "", labels: list[str] = None) -> Summary:
        return self.registry.summary(name, description, labels)

    def get_counter(self, name: str) -> Counter | None:
        metric = self.registry.get(name)
        return metric if isinstance(metric, Counter) else None

    def get_gauge(self, name: str) -> Gauge | None:
        metric = self.registry.get(name)
        return metric if isinstance(metric, Gauge) else None

    def get_histogram(self, name: str) -> Histogram | None:
        metric = self.registry.get(name)
        return metric if isinstance(metric, Histogram) else None

    def get_summary(self, name: str) -> Summary | None:
        metric = self.registry.get(name)
        return metric if isinstance(metric, Summary) else None

    def export(self) -> str:
        """导出指标"""
        return self.registry.collect()

    def to_json(self) -> str:
        """导出 JSON 格式"""
        metrics = self.registry.list_metrics()
        return json.dumps(metrics, indent=2)


# 全局实例
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
