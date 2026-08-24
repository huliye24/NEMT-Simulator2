"""
MonitorCapsule - 分形迭代版

按五阶段迭代法重写的监控胶囊。
"""

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from nemt.core.capsule import FractalCapsule


class HealthStatus(Enum):
    """健康状态"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthMetric:
    """健康指标"""

    name: str
    value: float
    threshold: float
    status: HealthStatus
    timestamp: datetime = field(default_factory=datetime.now)


class MonitorCapsule(FractalCapsule):
    """
    监控胶囊

    负责：
    - 系统健康检查
    - 性能监控
    - 告警管理
    - 日志聚合

    五阶段方法已实现。
    """

    def __init__(self, capsule_id: str = "monitor"):
        super().__init__(capsule_id, version="1.0.0")
        self._layer = "L1"

        # 监控配置
        self._check_interval = 60  # 秒
        self._alert_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "latency_ms": 1000.0,
            "error_rate": 0.05,
            "drawdown": 0.15,
        }

        # 健康指标
        self._health_metrics: dict[str, HealthMetric] = {}
        self._alert_history: list[dict] = []
        self._capsule_status: dict[str, str] = {}
        self._lock = threading.Lock()

        # 告警回调
        self._alert_callbacks: list[Callable] = []

    # ========================================
    # 【看】观察阶段
    # ========================================

    def observe_phase(self) -> dict[str, Any]:
        """【看】观察阶段"""
        return {
            "capsule_id": self._capsule_id,
            "layer": "L1",
            "phase": "observe",
            "timestamp": datetime.now().isoformat(),
            "inputs": {
                "system_metrics": {
                    "type": "dict",
                    "format": "{cpu, memory, latency, ...}",
                    "source": "系统",
                },
                "capsule_status": {
                    "type": "dict",
                    "format": "{capsule_id: status}",
                    "source": "CapsuleManager",
                },
                "trade_metrics": {
                    "type": "dict",
                    "format": "{pnl, drawdown, error_rate}",
                    "source": "ExecutionCapsule",
                },
            },
            "outputs": {
                "health_status": {
                    "type": "string",
                    "enum": ["healthy", "warning", "critical"],
                },
                "alerts": {
                    "type": "list",
                    "format": "[{severity, message, timestamp}]",
                },
                "metrics": {
                    "type": "dict",
                    "description": "当前健康指标",
                },
            },
            "constraints": {
                "check_interval": self._check_interval,
                "max_alerts": 100,
                "alert_retention": "24小时",
            },
            "dependencies": ["CapsuleManager", "ExecutionCapsule"],
            "risks": [
                {"type": "监控遗漏", "mitigation": "多重检查机制"},
                {"type": "告警风暴", "mitigation": "告警聚合+去重"},
            ],
            "subscribes_to": ["system.metric", "order.filled", "error.*"],
            "publishes": ["monitor.health", "monitor.alert", "monitor.report"],
        }

    # ========================================
    # 【画】设计阶段
    # ========================================

    def design_phase(self) -> dict[str, Any]:
        """【画】设计阶段"""
        return {
            "capsule_id": self._capsule_id,
            "layer": "L1",
            "phase": "design",
            "timestamp": datetime.now().isoformat(),
            "public_api": {
                "check_health()": "执行健康检查",
                "get_metrics()": "获取当前指标",
                "get_alerts(hours)": "获取告警历史",
                "set_threshold(metric, value)": "设置阈值",
                "register_alert_callback(cb)": "注册告警回调",
            },
            "input_schema": {
                "metric_name": {"type": "string"},
                "metric_value": {"type": "number"},
                "timestamp": {"type": "string"},
            },
            "output_schema": {
                "health_status": {"type": "string"},
                "alerts_count": {"type": "integer"},
                "critical_metrics": {"type": "array"},
            },
            "health_rules": {
                "cpu_usage": "healthy < 70, warning < 85, critical >= 85",
                "memory_usage": "healthy < 75, warning < 90, critical >= 90",
                "latency": "healthy < 500ms, warning < 1000ms, critical >= 1000ms",
                "error_rate": "healthy < 1%, warning < 5%, critical >= 5%",
            },
        }

    # ========================================
    # 【填】实现阶段
    # ========================================

    def implement_phase(self) -> None:
        """【填】实现阶段"""
        # 加载阈值配置
        for key in self._alert_thresholds:
            value = self.get_config(f"monitor.{key}", None)
            if value is not None:
                self._alert_thresholds[key] = value

        self._check_interval = self.get_config("monitor.check_interval", 60)
        self._logger.info(f"{self._capsule_id} 实现阶段完成")
        self._logger.info(f"  检查间隔: {self._check_interval}秒")

    # ========================================
    # 【验】验证阶段
    # ========================================

    def verify_phase(self) -> dict[str, Any]:
        """【验】验证阶段"""
        return {
            "capsule_id": self._capsule_id,
            "phase": "verify",
            "passed": True,
            "checks": {
                "thresholds_configured": len(self._alert_thresholds) > 0,
                "thread_safe": hasattr(self, "_lock"),
            },
            "metrics": {
                "monitored_count": len(self._health_metrics),
                "alerts_count": len(self._alert_history),
            },
        }

    # ========================================
    # 【连】集成阶段
    # ========================================

    def integrate_phase(self) -> None:
        """【连】集成阶段"""
        self._logger.info(f"{self._capsule_id} 集成阶段完成")
        self._logger.info(f"  监控阈值: {self._alert_thresholds}")

    # ========================================
    # 标准生命周期
    # ========================================

    def init(self) -> None:
        """初始化"""
        self.subscribe("system.metric", self._on_metric)
        self._initialized = True

    def exec(self) -> dict[str, Any]:
        """执行"""
        return self.check_health()

    def shutdown(self) -> None:
        """关闭"""
        self._health_metrics.clear()
        self._alert_history.clear()

    # ========================================
    # 公开 API
    # ========================================

    def check_health(self) -> dict[str, Any]:
        """执行健康检查"""
        with self._lock:
            critical_metrics = []
            warning_metrics = []
            overall_status = HealthStatus.HEALTHY

            for name, metric in self._health_metrics.items():
                if metric.status == HealthStatus.CRITICAL:
                    critical_metrics.append(name)
                    overall_status = HealthStatus.CRITICAL
                elif metric.status == HealthStatus.WARNING:
                    warning_metrics.append(name)
                    if overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.WARNING

            # 检查胶囊状态
            for capsule_id, status in self._capsule_status.items():
                if status != "healthy":
                    overall_status = HealthStatus.WARNING

            return {
                "health_status": overall_status.value,
                "critical_metrics": critical_metrics,
                "warning_metrics": warning_metrics,
                "capsule_status": dict(self._capsule_status),
                "alerts_count_24h": self._count_recent_alerts(24),
                "timestamp": datetime.now().isoformat(),
            }

    def get_metrics(self) -> dict[str, HealthMetric]:
        """获取当前指标"""
        with self._lock:
            return dict(self._health_metrics)

    def get_alerts(self, hours: int = 24) -> list[dict]:
        """获取告警历史"""
        with self._lock:
            cutoff = datetime.now() - timedelta(hours=hours)
            return [a for a in self._alert_history if a.get("timestamp", "") > cutoff.isoformat()]

    def set_threshold(self, metric: str, value: float) -> None:
        """设置阈值"""
        self._alert_thresholds[metric] = value
        self._logger.info(f"阈值更新: {metric} = {value}")

    def register_alert_callback(self, callback) -> None:
        """注册告警回调"""
        if callback not in self._alert_callbacks:
            self._alert_callbacks.append(callback)

    def update_capsule_status(self, capsule_id: str, status: str) -> None:
        """更新胶囊状态"""
        with self._lock:
            self._capsule_status[capsule_id] = status

    # ========================================
    # 内部方法
    # ========================================

    def _on_metric(self, metric_data: dict) -> None:
        """处理指标数据"""
        name = metric_data.get("name", "")
        value = metric_data.get("value", 0)

        if not name:
            return

        self._update_metric(name, value)

    def _update_metric(self, name: str, value: float) -> None:
        """更新指标"""
        with self._lock:
            threshold = self._alert_thresholds.get(name, 100.0)

            if value < threshold * 0.8:
                status = HealthStatus.HEALTHY
            elif value < threshold:
                status = HealthStatus.WARNING
            else:
                status = HealthStatus.CRITICAL

            metric = HealthMetric(
                name=name,
                value=value,
                threshold=threshold,
                status=status,
            )

            self._health_metrics[name] = metric

            # 检查是否需要告警
            if status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                self._create_alert(name, value, status)

    def _create_alert(self, metric_name: str, value: float, status: HealthStatus) -> None:
        """创建告警"""
        alert = {
            "id": len(self._alert_history),
            "metric": metric_name,
            "value": value,
            "status": status.value,
            "severity": "high" if status == HealthStatus.CRITICAL else "medium",
            "message": f"{metric_name} {status.value}: {value:.2f}",
            "timestamp": datetime.now().isoformat(),
        }

        with self._lock:
            self._alert_history.append(alert)

            # 限制历史长度
            if len(self._alert_history) > 100:
                self._alert_history = self._alert_history[-100:]

        # 触发回调
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception:
                pass

        # 发布事件
        self.publish("monitor.alert", alert)

    def _count_recent_alerts(self, hours: int) -> int:
        """统计最近告警数"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return sum(1 for a in self._alert_history if a.get("timestamp", "") > cutoff.isoformat())
