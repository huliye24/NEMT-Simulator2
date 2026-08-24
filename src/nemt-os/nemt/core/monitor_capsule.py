"""
MonitorCapsule - 监控胶囊

系统健康监控:
- 性能监控
- 错误率监控
- 延迟监控
- 告警管理
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import time
from nemt.core.capsule import ModuleCapsule
from nemt.core.event_bus import Event

__all__ = ["MonitorCapsule", "AlertLevel", "Alert"]


class AlertLevel(Enum):
    """告警级别"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """告警"""

    level: AlertLevel
    message: str
    source: str
    timestamp: float
    metadata: Dict[str, Any]


class MonitorCapsule(ModuleCapsule):
    """
    监控胶囊

    订阅事件:
    - nemt.signal: 信号生成
    - nemt.order_filled: 订单成交
    - nemt.risk_warning: 风险警告
    - nemt.risk_violation: 风险违规

    发布事件:
    - nemt.alert: 系统告警
    - nemt.health_check: 健康检查结果
    """

    def __init__(self):
        super().__init__("monitor")

        # 性能指标
        self._events_processed: int = 0
        self._errors_count: int = 0
        self._warnings_count: int = 0
        self._start_time: float = 0

        # 延迟跟踪
        self._latencies: List[float] = []
        self._max_latencies: int = 1000

        # 告警
        self._alerts: List[Alert] = []
        self._max_alerts: int = 100
        self._alert_thresholds: Dict[str, float] = {
            "error_rate": 0.05,  # 5% 错误率阈值
            "latency_p99": 1.0,  # P99 延迟阈值 (秒)
            "queue_size": 1000,  # 队列大小阈值
        }

        # 健康状态
        self._health_status: Dict[str, str] = {
            "event_bus": "healthy",
            "config": "healthy",
            "memory": "healthy",
        }

        # 事件处理统计
        self._event_types: Dict[str, int] = {}

    def init(self) -> None:
        """初始化"""
        self._start_time = self._get_time()

        # 订阅事件
        self.subscribe("nemt.signal", self._on_any_event)
        self.subscribe("nemt.order_filled", self._on_any_event)
        self.subscribe("nemt.risk_warning", self._on_risk_warning)
        self.subscribe("nemt.risk_violation", self._on_risk_violation)
        self.subscribe("system.*", self._on_any_event)

    def exec(self) -> Dict[str, Any]:
        """
        执行 - 返回监控状态

        Returns:
            监控状态字典
        """
        uptime = self._get_time() - self._start_time

        # 计算错误率
        error_rate = self._errors_count / max(self._events_processed, 1)

        # 计算 P99 延迟
        p99_latency = self._calculate_percentile(0.99)

        # 健康检查
        health = self._check_health()

        return {
            # 性能指标
            "uptime": uptime,
            "events_processed": self._events_processed,
            "events_per_second": self._events_processed / max(uptime, 1),
            # 错误统计
            "errors_count": self._errors_count,
            "warnings_count": self._warnings_count,
            "error_rate": error_rate,
            # 延迟统计
            "avg_latency": sum(self._latencies) / max(len(self._latencies), 1),
            "p99_latency": p99_latency,
            "max_latency": max(self._latencies) if self._latencies else 0,
            # 事件统计
            "event_types": self._event_types.copy(),
            "event_type_count": len(self._event_types),
            # 告警
            "alert_count": len(self._alerts),
            "recent_alerts": [self._alert_to_dict(a) for a in self._alerts[-5:]],
            # 健康状态
            "health": health,
            "is_healthy": health["status"] == "healthy",
        }

    def _on_any_event(self, event: Event) -> None:
        """处理任意事件"""
        self._events_processed += 1

        # 记录事件类型
        event_type = event.type
        self._event_types[event_type] = self._event_types.get(event_type, 0) + 1

        # 记录延迟
        latency = self._get_time() - event.timestamp
        self._latencies.append(latency)
        if len(self._latencies) > self._max_latencies:
            self._latencies.pop(0)

    def _on_risk_warning(self, event: Event) -> None:
        """处理风险警告"""
        self._warnings_count += 1
        self._events_processed += 1

        data = event.data or {}
        self._create_alert(AlertLevel.WARNING, data.get("message", "Risk warning"), "risk", data)

    def _on_risk_violation(self, event: Event) -> None:
        """处理风险违规"""
        self._errors_count += 1
        self._events_processed += 1

        data = event.data or {}
        self._create_alert(AlertLevel.ERROR, data.get("reason", "Risk violation"), "risk", data)

    def _create_alert(self, level: AlertLevel, message: str, source: str, metadata: Dict[str, Any]) -> None:
        """创建告警"""
        alert = Alert(level=level, message=message, source=source, timestamp=self._get_time(), metadata=metadata)

        self._alerts.append(alert)
        if len(self._alerts) > self._max_alerts:
            self._alerts.pop(0)

        # 发布告警事件
        self.publish(
            "nemt.alert",
            {
                "level": level.value,
                "message": message,
                "source": source,
                "timestamp": alert.timestamp,
            },
        )

    def _calculate_percentile(self, percentile: float) -> float:
        """计算延迟百分位"""
        if not self._latencies:
            return 0.0

        sorted_latencies = sorted(self._latencies)
        index = int(len(sorted_latencies) * percentile)
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]

    def _check_health(self) -> Dict[str, Any]:
        """健康检查"""
        uptime = self._get_time() - self._start_time
        error_rate = self._errors_count / max(self._events_processed, 1)
        p99_latency = self._calculate_percentile(0.99)

        issues = []

        # 检查错误率
        if error_rate > self._alert_thresholds["error_rate"]:
            issues.append(f"High error rate: {error_rate:.2%}")

        # 检查延迟
        if p99_latency > self._alert_thresholds["latency_p99"]:
            issues.append(f"High latency: {p99_latency:.3f}s")

        # 检查运行时长
        if uptime < 10:
            issues.append("System just started")

        status = "healthy" if not issues else "degraded"
        if len(issues) > 2:
            status = "unhealthy"

        return {
            "status": status,
            "issues": issues,
            "checks": {
                "error_rate": error_rate <= self._alert_thresholds["error_rate"],
                "latency": p99_latency <= self._alert_thresholds["latency_p99"],
                "uptime": uptime > 0,
            },
        }

    def _alert_to_dict(self, alert: Alert) -> Dict[str, Any]:
        """告警转字典"""
        return {
            "level": alert.level.value,
            "message": alert.message,
            "source": alert.source,
            "timestamp": alert.timestamp,
        }

    def set_threshold(self, key: str, value: float) -> None:
        """设置阈值"""
        if key in self._alert_thresholds:
            self._alert_thresholds[key] = value

    def get_alerts(self, level: AlertLevel = None, limit: int = 10) -> List[Dict[str, Any]]:
        """获取告警列表"""
        alerts = self._alerts

        if level:
            alerts = [a for a in alerts if a.level == level]

        return [self._alert_to_dict(a) for a in alerts[-limit:]]

    def clear_alerts(self) -> None:
        """清除告警"""
        self._alerts.clear()

    def record_error(self, error: Exception, source: str) -> None:
        """记录错误"""
        self._errors_count += 1
        self._create_alert(AlertLevel.ERROR, str(error), source, {"type": type(error).__name__})

    def shutdown(self) -> None:
        """关闭"""
        self.unsubscribe("nemt.signal", self._on_any_event)
        self.unsubscribe("nemt.order_filled", self._on_any_event)
        self.unsubscribe("nemt.risk_warning", self._on_risk_warning)
        self.unsubscribe("nemt.risk_violation", self._on_risk_violation)
        self.unsubscribe("system.*", self._on_any_event)

    @staticmethod
    def _get_time() -> float:
        """获取当前时间"""
        return time.time()
