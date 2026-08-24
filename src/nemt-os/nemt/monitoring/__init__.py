"""
Monitoring Module - 监控模块

提供可观测性能力:
- 指标采集 (Metrics)
- 告警管理 (AlertManager)
- 健康检查 (HealthCheck)
"""

from nemt.monitoring.alert import (
    Alert,
    AlertManager,
    AlertRule,
    AlertSeverity,
    AlertStatus,
    NotificationChannel,
    SlackChannel,
    get_alert_manager,
)
from nemt.monitoring.health import (
    HealthCheck,
    HealthCheckRegistry,
    HealthCheckResult,
    HealthStatus,
    LambdaHealthCheck,
    LivenessProbe,
    ReadinessProbe,
    get_health_registry,
)
from nemt.monitoring.metrics import (
    Counter,
    Gauge,
    Histogram,
    Metric,
    MetricsCollector,
    MetricsRegistry,
    MetricType,
    Summary,
    get_metrics_collector,
)

__all__ = [
    # 指标
    "MetricType",
    "Metric",
    "Counter",
    "Gauge",
    "Histogram",
    "Summary",
    "MetricsRegistry",
    "MetricsCollector",
    "get_metrics_collector",
    # 告警
    "AlertSeverity",
    "AlertStatus",
    "Alert",
    "AlertRule",
    "AlertManager",
    "NotificationChannel",
    "SlackChannel",
    "get_alert_manager",
    # 健康检查
    "HealthStatus",
    "HealthCheckResult",
    "HealthCheck",
    "HealthCheckRegistry",
    "LambdaHealthCheck",
    "LivenessProbe",
    "ReadinessProbe",
    "get_health_registry",
]
