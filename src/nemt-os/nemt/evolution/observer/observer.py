"""
L-State: 状态管理层 - 状态观测系统

状态观测系统是自演化系统的感知神经。
它持续监控系统状态，收集指标，检测异常，为自演化提供输入。

核心概念:
- StateObserver: 状态观测器
- Metric: 指标定义
- AnomalyDetector: 异常检测器
- AlertManager: 告警管理器
"""

from __future__ import annotations

import logging
import statistics
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import (
    Any,
)

logger = logging.getLogger(__name__)

# =============================================================================
# 类型定义
# =============================================================================

MetricId = str
AlertId = str


class MetricType(Enum):
    """指标类型"""

    COUNTER = auto()  # 计数器
    GAUGE = auto()  # 仪表值
    HISTOGRAM = auto()  # 直方图
    SUMMARY = auto()  # 摘要
    RATE = auto()  # 比率


class AlertLevel(Enum):
    """告警级别"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AnomalyType(Enum):
    """异常类型"""

    SPIKE = auto()  # 尖峰
    DROP = auto()  # 骤降
    TREND = auto()  # 趋势异常
    LEVEL_SHIFT = auto()  # 水平位移
    OUTLIER = auto()  # 离群点


# =============================================================================
# 指标定义
# =============================================================================


@dataclass
class Metric:
    """指标定义"""

    id: MetricId
    name: str
    type: MetricType
    description: str = ""

    # 值
    value: float = 0.0
    unit: str = ""

    # 统计
    count: int = 0
    sum: float = 0.0
    min_value: float = float("inf")
    max_value: float = float("-inf")

    # 历史
    values: deque = field(default_factory=lambda: deque(maxlen=1000))

    # 标签
    tags: dict[str, str] = field(default_factory=dict)

    # 时间
    timestamp: datetime = field(default_factory=datetime.now)

    def record(self, value: float) -> None:
        """记录值"""
        self.value = value
        self.count += 1
        self.sum += value
        self.min_value = min(self.min_value, value)
        self.max_value = max(self.max_value, value)
        self.values.append(value)
        self.timestamp = datetime.now()

    def get_stats(self) -> dict[str, float]:
        """获取统计信息"""
        if not self.values:
            return {}

        vals = list(self.values)
        return {
            "count": self.count,
            "sum": self.sum,
            "mean": statistics.mean(vals),
            "median": statistics.median(vals),
            "std": statistics.stdev(vals) if len(vals) > 1 else 0,
            "min": self.min_value,
            "max": self.max_value,
            "p50": statistics.median(vals),
            "p95": self._percentile(vals, 0.95),
            "p99": self._percentile(vals, 0.99),
        }

    def _percentile(self, values: list[float], p: float) -> float:
        """计算百分位数"""
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        idx = int(len(sorted_vals) * p)
        return sorted_vals[min(idx, len(sorted_vals) - 1)]


@dataclass
class Alert:
    """告警"""

    id: AlertId
    level: AlertLevel
    message: str
    metric_id: MetricId
    metric_name: str
    value: float
    threshold: float
    anomaly_type: AnomalyType | None = None

    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def resolve(self):
        """解决告警"""
        self.resolved = True
        self.resolved_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "level": self.level.value,
            "message": self.message,
            "metric_id": self.metric_id,
            "metric_name": self.metric_name,
            "value": self.value,
            "threshold": self.threshold,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
        }


# =============================================================================
# 异常检测器
# =============================================================================


class AnomalyDetector:
    """
    异常检测器

    支持多种异常检测算法:
    - 阈值检测
    - 统计检测 (z-score)
    - 趋势检测
    - 移动平均检测
    """

    def __init__(self):
        self._threshold_rules: dict[str, dict[str, Any]] = {}
        self._baseline_stats: dict[str, dict[str, float]] = {}

    def add_threshold_rule(
        self,
        metric_id: str,
        threshold: float,
        comparison: str = "gt",  # gt, lt, eq, gte, lte
        level: AlertLevel = AlertLevel.WARNING,
    ):
        """添加阈值规则"""
        self._threshold_rules[metric_id] = {
            "threshold": threshold,
            "comparison": comparison,
            "level": level,
        }

    def detect_threshold(
        self,
        metric_id: str,
        value: float,
    ) -> Alert | None:
        """阈值检测"""
        rule = self._threshold_rules.get(metric_id)
        if not rule:
            return None

        threshold = rule["threshold"]
        comparison = rule["comparison"]

        is_anomaly = False
        if comparison == "gt" and value > threshold:
            is_anomaly = True
        elif comparison == "lt" and value < threshold:
            is_anomaly = True
        elif comparison == "gte" and value >= threshold:
            is_anomaly = True
        elif comparison == "lte" and value <= threshold:
            is_anomaly = True
        elif comparison == "eq" and value == threshold:
            is_anomaly = True

        if is_anomaly:
            return Alert(
                id=f"alert_{metric_id}_{int(time.time())}",
                level=rule["level"],
                message=f"{metric_id} value {value} {comparison} threshold {threshold}",
                metric_id=metric_id,
                metric_name=metric_id,
                value=value,
                threshold=threshold,
                anomaly_type=AnomalyType.SPIKE if comparison == "gt" else AnomalyType.DROP,
            )

        return None

    def detect_zscore(
        self,
        values: list[float],
        threshold: float = 3.0,
    ) -> list[int]:
        """Z-score 异常检测

        Returns:
            异常值的索引列表
        """
        if len(values) < 3:
            return []

        mean = statistics.mean(values)
        std = statistics.stdev(values)

        if std == 0:
            return []

        anomalies = []
        for i, v in enumerate(values):
            z_score = abs((v - mean) / std)
            if z_score > threshold:
                anomalies.append(i)

        return anomalies

    def detect_trend(
        self,
        values: list[float],
        window: int = 10,
        threshold: float = 0.5,
    ) -> AnomalyType | None:
        """趋势异常检测"""
        if len(values) < window * 2:
            return None

        recent = values[-window:]
        previous = values[-window * 2 : -window]

        recent_mean = statistics.mean(recent)
        previous_mean = statistics.mean(previous)

        change_ratio = (recent_mean - previous_mean) / (previous_mean + 1e-6)

        if change_ratio > threshold:
            return AnomalyType.SPIKE
        elif change_ratio < -threshold:
            return AnomalyType.DROP

        return None


# =============================================================================
# 状态观测器
# =============================================================================


class StateObserver:
    """
    状态观测器

    负责:
    - 指标采集
    - 异常检测
    - 告警管理
    - 状态发布
    """

    def __init__(self, name: str = "default"):
        self.name = name

        # 指标存储
        self._metrics: dict[MetricId, Metric] = {}

        # 异常检测器
        self._detector = AnomalyDetector()

        # 告警
        self._alerts: list[Alert] = []
        self._alert_handlers: list[Callable[[Alert], None]] = []

        # 订阅者
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

        self._logger = logging.getLogger(f"{__name__}.Observer.{name}")

    def register_metric(
        self,
        metric_id: MetricId,
        name: str,
        metric_type: MetricType,
        description: str = "",
        unit: str = "",
        tags: dict[str, str] | None = None,
    ) -> Metric:
        """注册指标"""
        metric = Metric(
            id=metric_id,
            name=name,
            type=metric_type,
            description=description,
            unit=unit,
            tags=tags or {},
        )
        self._metrics[metric_id] = metric
        return metric

    def record(
        self,
        metric_id: MetricId,
        value: float,
        tags: dict[str, str] | None = None,
    ):
        """记录指标值"""
        metric = self._metrics.get(metric_id)
        if not metric:
            metric = self.register_metric(metric_id, metric_id, MetricType.GAUGE)

        metric.record(value)

        if tags:
            metric.tags.update(tags)

        # 检测异常
        alert = self._detector.detect_threshold(metric_id, value)
        if alert:
            self._add_alert(alert)

        # 通知订阅者
        self._notify(
            f"metric_{metric_id}",
            {
                "metric_id": metric_id,
                "value": value,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def get_metric(self, metric_id: MetricId) -> Metric | None:
        """获取指标"""
        return self._metrics.get(metric_id)

    def get_metrics(
        self,
        tag_filter: dict[str, str] | None = None,
    ) -> list[Metric]:
        """获取指标列表"""
        metrics = list(self._metrics.values())

        if tag_filter:
            metrics = [m for m in metrics if all(m.tags.get(k) == v for k, v in tag_filter.items())]

        return metrics

    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """添加告警处理器"""
        self._alert_handlers.append(handler)

    def _add_alert(self, alert: Alert):
        """添加告警"""
        self._alerts.append(alert)
        self._logger.warning(f"Alert: {alert.message}")

        # 调用处理器
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self._logger.error(f"Alert handler error: {e}")

    def get_active_alerts(
        self,
        level: AlertLevel | None = None,
    ) -> list[Alert]:
        """获取活跃告警"""
        alerts = [a for a in self._alerts if not a.resolved]

        if level:
            alerts = [a for a in alerts if a.level == level]

        return alerts

    def resolve_alert(self, alert_id: AlertId) -> bool:
        """解决告警"""
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.resolve()
                return True
        return False

    def subscribe(self, event_type: str, handler: Callable):
        """订阅事件"""
        self._subscribers[event_type].append(handler)

    def _notify(self, event_type: str, data: Any):
        """通知订阅者"""
        for handler in self._subscribers.get(event_type, []):
            try:
                handler(data)
            except Exception as e:
                self._logger.error(f"Subscriber error: {e}")

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "metrics_count": len(self._metrics),
            "active_alerts_count": len(self.get_active_alerts()),
            "total_alerts_count": len(self._alerts),
            "alerts_by_level": {
                level.value: len([a for a in self._alerts if a.level == level]) for level in AlertLevel
            },
        }

    def export_metrics(self) -> dict[str, Any]:
        """导出指标"""
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                mid: {
                    "name": m.name,
                    "value": m.value,
                    "stats": m.get_stats(),
                    "tags": m.tags,
                }
                for mid, m in self._metrics.items()
            },
        }


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    # 类型别名
    "MetricId",
    "AlertId",
    # 枚举
    "MetricType",
    "AlertLevel",
    "AnomalyType",
    # 数据类
    "Metric",
    "Alert",
    # 核心类
    "AnomalyDetector",
    "StateObserver",
]
