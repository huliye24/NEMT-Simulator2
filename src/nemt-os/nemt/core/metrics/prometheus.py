"""
Metrics - 指标采集系统

提供 Prometheus 指标采集功能:
- Counter: 计数器
- Gauge: 仪表
- Histogram: 直方图
- Summary: 摘要
"""

import threading
import time
from dataclasses import dataclass
from typing import Any

__all__ = ["MetricsCollector", "Counter", "Gauge", "Histogram", "Summary", "get_metrics_collector"]


@dataclass
class MetricSample:
    """指标样本"""

    name: str
    value: float
    labels: dict[str, str]
    timestamp: float
    metric_type: str


class Counter:
    """计数器指标"""

    def __init__(self, name: str, description: str = "", labels: list[str] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: dict[tuple, float] = {}
        self._lock = threading.Lock()

    def inc(self, value: float = 1, **labels) -> None:
        """增加计数"""
        key = self._make_key(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0) + value

    def get(self, **labels) -> float:
        """获取当前值"""
        key = self._make_key(labels)
        with self._lock:
            return self._values.get(key, 0)

    def _make_key(self, labels: dict[str, str]) -> tuple:
        return tuple(labels.get(l, "") for l in self.labels)

    def collect(self) -> list[MetricSample]:
        """采集指标"""
        samples = []
        with self._lock:
            for key, value in self._values.items():
                label_dict = dict(zip(self.labels, key, strict=False))
                samples.append(
                    MetricSample(
                        name=self.name,
                        value=value,
                        labels=label_dict,
                        timestamp=time.time(),
                        metric_type="counter",
                    )
                )
        return samples


class Gauge:
    """仪表指标"""

    def __init__(self, name: str, description: str = "", labels: list[str] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: dict[tuple, float] = {}
        self._lock = threading.Lock()

    def set(self, value: float, **labels) -> None:
        """设置值"""
        key = self._make_key(labels)
        with self._lock:
            self._values[key] = value

    def inc(self, value: float = 1, **labels) -> None:
        """增加"""
        key = self._make_key(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0) + value

    def dec(self, value: float = 1, **labels) -> None:
        """减少"""
        key = self._make_key(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0) - value

    def get(self, **labels) -> float:
        """获取当前值"""
        key = self._make_key(labels)
        with self._lock:
            return self._values.get(key, 0)

    def _make_key(self, labels: dict[str, str]) -> tuple:
        return tuple(labels.get(l, "") for l in self.labels)

    def collect(self) -> list[MetricSample]:
        """采集指标"""
        samples = []
        with self._lock:
            for key, value in self._values.items():
                label_dict = dict(zip(self.labels, key, strict=False))
                samples.append(
                    MetricSample(
                        name=self.name,
                        value=value,
                        labels=label_dict,
                        timestamp=time.time(),
                        metric_type="gauge",
                    )
                )
        return samples


class Histogram:
    """直方图指标"""

    def __init__(
        self,
        name: str,
        description: str = "",
        labels: list[str] = None,
        buckets: list[float] = None,
    ):
        self.name = name
        self.description = description
        self.labels = labels or []
        self.buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
        self._counts: dict[tuple, dict[float, int]] = {}
        self._sums: dict[tuple, float] = {}
        self._totals: dict[tuple, int] = {}
        self._lock = threading.Lock()

    def observe(self, value: float, **labels) -> None:
        """观察值"""
        key = self._make_key(labels)
        with self._lock:
            if key not in self._counts:
                self._counts[key] = {b: 0 for b in self.buckets}
                self._sums[key] = 0
                self._totals[key] = 0

            self._counts[key][float("inf")] += 1
            for bucket in self.buckets:
                if value <= bucket:
                    self._counts[key][bucket] += 1
            self._sums[key] += value
            self._totals[key] += 1

    def _make_key(self, labels: dict[str, str]) -> tuple:
        return tuple(labels.get(l, "") for l in self.labels)

    def collect(self) -> list[MetricSample]:
        """采集指标"""
        samples = []
        with self._lock:
            for key, counts in self._counts.items():
                label_dict = dict(zip(self.labels, key, strict=False))
                total = self._totals.get(key, 0)
                for bucket, count in counts.items():
                    bucket_labels = {**label_dict, "le": str(bucket)}
                    samples.append(
                        MetricSample(
                            name=f"{self.name}_bucket",
                            value=count,
                            labels=bucket_labels,
                            timestamp=time.time(),
                            metric_type="histogram",
                        )
                    )
                # Sum and count
                samples.append(
                    MetricSample(
                        name=f"{self.name}_sum",
                        value=self._sums.get(key, 0),
                        labels=label_dict,
                        timestamp=time.time(),
                        metric_type="histogram",
                    )
                )
                samples.append(
                    MetricSample(
                        name=f"{self.name}_count",
                        value=total,
                        labels=label_dict,
                        timestamp=time.time(),
                        metric_type="histogram",
                    )
                )
        return samples


class Summary:
    """摘要指标"""

    def __init__(
        self,
        name: str,
        description: str = "",
        labels: list[str] = None,
        objectives: dict[float, float] = None,
    ):
        self.name = name
        self.description = description
        self.labels = labels or []
        self.objectives = objectives or {0.5: 0.05, 0.9: 0.05, 0.99: 0.05}
        self._values: dict[tuple, list[float]] = {}
        self._lock = threading.Lock()

    def observe(self, value: float, **labels) -> None:
        """观察值"""
        key = self._make_key(labels)
        with self._lock:
            if key not in self._values:
                self._values[key] = []
            self._values[key].append(value)

    def _make_key(self, labels: dict[str, str]) -> tuple:
        return tuple(labels.get(l, "") for l in self.labels)

    def _quantile(self, values: list[float], q: float) -> float:
        if not values:
            return 0
        sorted_vals = sorted(values)
        idx = int(len(sorted_vals) * q)
        return sorted_vals[min(idx, len(sorted_vals) - 1)]

    def collect(self) -> list[MetricSample]:
        """采集指标"""
        samples = []
        with self._lock:
            for key, values in self._values.items():
                label_dict = dict(zip(self.labels, key, strict=False))
                # Quantiles
                for q in self.objectives.keys():
                    samples.append(
                        MetricSample(
                            name=f"{self.name}",
                            value=self._quantile(values, q),
                            labels={**label_dict, "quantile": str(q)},
                            timestamp=time.time(),
                            metric_type="summary",
                        )
                    )
                # Sum and count
                samples.append(
                    MetricSample(
                        name=f"{self.name}_sum",
                        value=sum(values),
                        labels=label_dict,
                        timestamp=time.time(),
                        metric_type="summary",
                    )
                )
                samples.append(
                    MetricSample(
                        name=f"{self.name}_count",
                        value=len(values),
                        labels=label_dict,
                        timestamp=time.time(),
                        metric_type="summary",
                    )
                )
        return samples


class MetricsCollector:
    """
    指标采集器

    管理所有指标并提供 Prometheus 格式输出。

    示例:
    ```python
    collector = MetricsCollector()

    # 创建指标
    requests_total = collector.counter("requests_total", "Total requests", ["method", "status"])
    request_duration = collector.histogram("request_duration_seconds", "Request duration")

    # 使用指标
    requests_total.inc(method="GET", status="200")
    request_duration.observe(0.123)

    # 导出 Prometheus 格式
    print(collector.export())
    ```
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}
        self._summaries: dict[str, Summary] = {}
        self._lock = threading.Lock()
        self._initialized = True

    def counter(self, name: str, description: str = "", labels: list[str] = None) -> Counter:
        """创建或获取计数器"""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, description, labels)
            return self._counters[name]

    def gauge(self, name: str, description: str = "", labels: list[str] = None) -> Gauge:
        """创建或获取仪表"""
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name, description, labels)
            return self._gauges[name]

    def histogram(
        self, name: str, description: str = "", labels: list[str] = None, buckets: list[float] = None
    ) -> Histogram:
        """创建或获取直方图"""
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name, description, labels, buckets)
            return self._histograms[name]

    def summary(
        self, name: str, description: str = "", labels: list[str] = None, objectives: dict[float, float] = None
    ) -> Summary:
        """创建或获取摘要"""
        with self._lock:
            if name not in self._summaries:
                self._summaries[name] = Summary(name, description, labels, objectives)
            return self._summaries[name]

    def collect(self) -> list[MetricSample]:
        """采集所有指标"""
        samples = []
        samples.extend(sum((c.collect() for c in self._counters.values()), []))
        samples.extend(sum((g.collect() for g in self._gauges.values()), []))
        samples.extend(sum((h.collect() for h in self._histograms.values()), []))
        samples.extend(sum((s.collect() for s in self._summaries.values()), []))
        return samples

    def export(self) -> str:
        """导出 Prometheus 格式"""
        lines = []
        for sample in self.collect():
            label_str = ",".join(f'{k}="{v}"' for k, v in sample.labels.items())
            if label_str:
                lines.append(f"{sample.name}{{{label_str}}} {sample.value}")
            else:
                lines.append(f"{sample.name} {sample.value}")
        return "\n".join(lines)

    def export_dict(self) -> dict[str, Any]:
        """导出字典格式"""
        samples = self.collect()
        result = {}
        for sample in samples:
            key = f"{sample.name}:{sample.labels}"
            result[key] = sample.value
        return result

    def clear(self) -> None:
        """清除所有指标"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._summaries.clear()


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标采集器"""
    return MetricsCollector()


# ============================================================================
# 预置指标
# ============================================================================


# 请求相关
def get_request_metrics():
    """获取请求相关指标"""
    collector = get_metrics_collector()
    return {
        "requests_total": collector.counter("nemt_requests_total", "Total requests", ["method", "status"]),
        "request_duration": collector.histogram("nemt_request_duration_seconds", "Request duration"),
        "requests_in_flight": collector.gauge("nemt_requests_in_flight", "Requests in flight"),
    }


# Capsule 相关
def get_capsule_metrics():
    """获取 Capsule 相关指标"""
    collector = get_metrics_collector()
    return {
        "capsule_exec_total": collector.counter("nemt_capsule_exec_total", "Capsule executions", ["capsule_id"]),
        "capsule_exec_duration": collector.histogram(
            "nemt_capsule_exec_duration_seconds", "Capsule execution duration", ["capsule_id"]
        ),
        "capsule_errors": collector.counter("nemt_capsule_errors", "Capsule errors", ["capsule_id"]),
        "capsule_state": collector.gauge("nemt_capsule_state", "Capsule state", ["capsule_id"]),
    }


# 事件相关
def get_event_metrics():
    """获取事件相关指标"""
    collector = get_metrics_collector()
    return {
        "events_published": collector.counter("nemt_events_published", "Events published", ["event_type"]),
        "events_consumed": collector.counter("nemt_events_consumed", "Events consumed", ["event_type"]),
        "event_processing_duration": collector.histogram(
            "nemt_event_processing_duration_seconds", "Event processing duration", ["event_type"]
        ),
    }
