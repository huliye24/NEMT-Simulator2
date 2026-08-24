"""
Monitor Domain Models - 监控领域模型

定义监控上下文中所有业务实体：
- HealthMetric: 健康指标聚合根
- Alert: 告警实体
- CapsuleStatus: 胶囊状态值对象

版本: v1.0.0
更新: 2026-04-27
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class HealthStatus(Enum):
    """健康状态枚举"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value

    def to_level(self) -> int:
        """转换为数值级别"""
        levels = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.WARNING: 1,
            HealthStatus.CRITICAL: 2,
            HealthStatus.UNKNOWN: -1,
        }
        return levels.get(self, -1)


class AlertSeverity(Enum):
    """告警严重程度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    def __str__(self) -> str:
        return self.value


@dataclass
class CapsuleStatus:
    """
    胶囊状态值对象

    表示单个胶囊的运行状态。

    INVARIANTS:
    - status 是 HealthStatus 枚举
    """

    capsule_id: str
    status: HealthStatus
    last_check: datetime = field(default_factory=datetime.now)

    # 可选信息
    error_message: str = ""
    metrics: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.status, HealthStatus):
            self.status = HealthStatus(self.status)

    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY

    @property
    def is_stale(self) -> bool:
        """是否超时（超过2分钟未更新）"""
        return datetime.now() - self.last_check > timedelta(minutes=2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "capsule_id": self.capsule_id,
            "status": self.status.value,
            "last_check": self.last_check.isoformat(),
            "error_message": self.error_message,
            "metrics": self.metrics,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CapsuleStatus:
        last_check = data.get("last_check")
        if isinstance(last_check, str):
            last_check = datetime.fromisoformat(last_check)
        elif last_check is None:
            last_check = datetime.now()

        status = data.get("status", "unknown")
        if isinstance(status, str):
            status = HealthStatus(status)

        return cls(
            capsule_id=data.get("capsule_id", ""),
            status=status,
            last_check=last_check,
            error_message=data.get("error_message", ""),
            metrics=data.get("metrics", {}),
        )


@dataclass
class HealthMetric:
    """
    健康指标聚合根

    表示系统或业务层面的健康状态指标。
    聚合根：外部只能通过此类访问指标数据。

    INVARIANTS:
    - value 是实数
    - threshold > 0
    """

    name: str
    value: float
    threshold: float

    # 状态
    status: HealthStatus = HealthStatus.UNKNOWN

    # 元数据
    timestamp: datetime = field(default_factory=datetime.now)
    metric_type: str = "system"  # "system" or "business"
    unit: str = ""  # "ms", "%", "count"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.threshold <= 0:
            raise ValueError("threshold must be positive")
        if not isinstance(self.status, HealthStatus):
            self.status = HealthStatus(self.status)
        # 自动计算状态
        self._update_status()

    def _update_status(self) -> None:
        """根据阈值更新状态"""
        if self.metric_type == "system":
            # 系统指标：越接近阈值越严重
            ratio = self.value / self.threshold if self.threshold > 0 else 0
            if ratio < 0.8:
                self.status = HealthStatus.HEALTHY
            elif ratio < 1.0:
                self.status = HealthStatus.WARNING
            else:
                self.status = HealthStatus.CRITICAL
        else:
            # 业务指标：超过阈值越严重
            if self.value < self.threshold:
                self.status = HealthStatus.HEALTHY
            elif self.value <= self.threshold * 1.2:
                self.status = HealthStatus.WARNING
            else:
                self.status = HealthStatus.CRITICAL

    def update(self, value: float) -> None:
        """更新指标值"""
        self.value = value
        self.timestamp = datetime.now()
        self._update_status()

    @property
    def ratio(self) -> float:
        """当前值 / 阈值"""
        return self.value / self.threshold if self.threshold > 0 else 0

    @property
    def is_critical(self) -> bool:
        return self.status == HealthStatus.CRITICAL

    @property
    def is_warning(self) -> bool:
        return self.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "threshold": self.threshold,
            "ratio": self.ratio,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "metric_type": self.metric_type,
            "unit": self.unit,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HealthMetric:
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        elif ts is None:
            ts = datetime.now()

        status = data.get("status", "unknown")
        if isinstance(status, str):
            status = HealthStatus(status)

        return cls(
            name=data.get("name", ""),
            value=float(data.get("value", 0)),
            threshold=float(data.get("threshold", 100)),
            status=status,
            timestamp=ts,
            metric_type=data.get("metric_type", "system"),
            unit=data.get("unit", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Alert:
    """
    告警实体

    表示系统异常事件记录。

    INVARIANTS:
    - severity 是 AlertSeverity 枚举
    """

    alert_id: int
    metric: str
    value: float
    threshold: float
    status: HealthStatus
    severity: AlertSeverity

    # 告警内容
    message: str = ""

    # 时间戳
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
    acknowledged_by: str = ""

    # 元数据
    capsule_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.status, HealthStatus):
            self.status = HealthStatus(self.status)
        if not isinstance(self.severity, AlertSeverity):
            self.severity = AlertSeverity(self.severity)

    def acknowledge(self, acknowledged_by: str = "") -> None:
        """确认告警"""
        self.acknowledged = True
        self.acknowledged_at = datetime.now()
        self.acknowledged_by = acknowledged_by

    def is_expired(self, hours: int = 24) -> bool:
        """是否过期"""
        return datetime.now() - self.timestamp > timedelta(hours=hours)

    @property
    def is_active(self) -> bool:
        """是否活跃（未确认且未过期）"""
        return not self.acknowledged and not self.is_expired(hours=24)

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "metric": self.metric,
            "value": self.value,
            "threshold": self.threshold,
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by,
            "capsule_id": self.capsule_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Alert:
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        elif ts is None:
            ts = datetime.now()

        ack_at = data.get("acknowledged_at")
        if isinstance(ack_at, str):
            ack_at = datetime.fromisoformat(ack_at)

        status = data.get("status", "unknown")
        if isinstance(status, str):
            status = HealthStatus(status)

        severity = data.get("severity", "medium")
        if isinstance(severity, str):
            severity = AlertSeverity(severity)

        return cls(
            alert_id=int(data.get("alert_id", 0)),
            metric=data.get("metric", ""),
            value=float(data.get("value", 0)),
            threshold=float(data.get("threshold", 0)),
            status=status,
            severity=severity,
            message=data.get("message", ""),
            timestamp=ts,
            acknowledged=data.get("acknowledged", False),
            acknowledged_at=ack_at,
            acknowledged_by=data.get("acknowledged_by", ""),
            capsule_id=data.get("capsule_id", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class HealthReport:
    """
    健康报告值对象

    表示系统的综合健康状态报告。
    """

    health_status: HealthStatus
    critical_metrics: list[str]
    warning_metrics: list[str]
    healthy_metrics: list[str]
    capsule_statuses: dict[str, CapsuleStatus]

    # 统计数据
    total_metrics: int = 0
    alerts_count: int = 0
    uptime_seconds: float = 0.0

    # 时间戳
    timestamp: datetime = field(default_factory=datetime.now)
    report_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "health_status": self.health_status.value,
            "critical_metrics": self.critical_metrics,
            "warning_metrics": self.warning_metrics,
            "healthy_metrics": self.healthy_metrics,
            "capsule_statuses": {k: v.to_dict() for k, v in self.capsule_statuses.items()},
            "total_metrics": self.total_metrics,
            "alerts_count": self.alerts_count,
            "uptime_seconds": self.uptime_seconds,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# Factory Methods
# =============================================================================


def create_health_metric(
    name: str,
    value: float,
    threshold: float,
    metric_type: str = "system",
    unit: str = "",
) -> HealthMetric:
    """
    工厂方法：创建健康指标

    Args:
        name: 指标名称
        value: 当前值
        threshold: 阈值
        metric_type: 指标类型 ("system" or "business")
        unit: 单位

    Returns:
        HealthMetric 实例
    """
    return HealthMetric(
        name=name,
        value=value,
        threshold=threshold,
        metric_type=metric_type,
        unit=unit,
    )


def create_alert(
    alert_id: int,
    metric: str,
    value: float,
    threshold: float,
    severity: AlertSeverity,
    message: str,
    capsule_id: str = "",
) -> Alert:
    """
    工厂方法：创建告警

    Args:
        alert_id: 告警 ID
        metric: 指标名
        value: 触发值
        threshold: 阈值
        severity: 严重程度
        message: 告警消息
        capsule_id: 胶囊 ID

    Returns:
        Alert 实例
    """
    status = HealthStatus.CRITICAL if severity == AlertSeverity.CRITICAL else HealthStatus.WARNING

    return Alert(
        alert_id=alert_id,
        metric=metric,
        value=value,
        threshold=threshold,
        status=status,
        severity=severity,
        message=message,
        capsule_id=capsule_id,
    )


def create_capsule_status(
    capsule_id: str,
    status: HealthStatus,
) -> CapsuleStatus:
    """
    工厂方法：创建胶囊状态

    Args:
        capsule_id: 胶囊 ID
        status: 健康状态

    Returns:
        CapsuleStatus 实例
    """
    return CapsuleStatus(
        capsule_id=capsule_id,
        status=status,
    )


# =============================================================================
# Domain Services
# =============================================================================


def determine_overall_status(metrics: list[HealthMetric]) -> HealthStatus:
    """
    根据多个指标确定总体状态

    Args:
        metrics: 健康指标列表

    Returns:
        总体健康状态
    """
    if not metrics:
        return HealthStatus.UNKNOWN

    statuses = [m.status for m in metrics]

    if any(s == HealthStatus.CRITICAL for s in statuses):
        return HealthStatus.CRITICAL
    elif any(s == HealthStatus.WARNING for s in statuses):
        return HealthStatus.WARNING
    elif any(s == HealthStatus.UNKNOWN for s in statuses):
        return HealthStatus.UNKNOWN
    else:
        return HealthStatus.HEALTHY


def calculate_alert_severity(value: float, threshold: float) -> AlertSeverity:
    """
    根据值与阈值的比例确定告警严重程度

    Args:
        value: 当前值
        threshold: 阈值

    Returns:
        告警严重程度
    """
    if threshold <= 0:
        return AlertSeverity.MEDIUM

    ratio = value / threshold

    if ratio >= 1.5:
        return AlertSeverity.CRITICAL
    elif ratio >= 1.2:
        return AlertSeverity.HIGH
    elif ratio >= 1.0:
        return AlertSeverity.MEDIUM
    else:
        return AlertSeverity.LOW


def filter_active_alerts(alerts: list[Alert], hours: int = 24) -> list[Alert]:
    """
    过滤活跃告警

    Args:
        alerts: 告警列表
        hours: 过期小时数

    Returns:
        活跃告警列表
    """
    return [a for a in alerts if a.is_active or (not a.acknowledged and not a.is_expired(hours))]
