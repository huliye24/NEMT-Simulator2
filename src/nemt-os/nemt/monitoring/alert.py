"""
AlertManager - 告警管理

提供告警规则、告警触发和通知管理。
"""

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum

__all__ = [
    "AlertSeverity",
    "AlertStatus",
    "Alert",
    "AlertRule",
    "AlertManager",
    "NotificationChannel",
]


class AlertSeverity(Enum):
    """告警级别"""

    CRITICAL = "critical"  # 严重
    ERROR = "error"  # 错误
    WARNING = "warning"  # 警告
    INFO = "info"  # 信息


class AlertStatus(Enum):
    """告警状态"""

    PENDING = "pending"  # 待触发
    FIRING = "firing"  # 触发中
    RESOLVED = "resolved"  # 已解决


@dataclass
class Alert:
    """告警"""

    name: str
    message: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.PENDING
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)
    starts_at: float = field(default_factory=time.time)
    ends_at: float = field(default_factory=0)
    generator_url: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "message": self.message,
            "severity": self.severity.value,
            "status": self.status.value,
            "labels": self.labels,
            "annotations": self.annotations,
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
        }


@dataclass
class AlertRule:
    """告警规则"""

    name: str
    expr: str  # PromQL 表达式
    for_duration: float = 0  # 持续时间
    severity: AlertSeverity = AlertSeverity.WARNING
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)
    enabled: bool = True

    def evaluate(self, value: float) -> bool:
        """评估规则 - 使用安全的表达式解析"""
        import ast
        import operator

        ALLOWED_OPS = {
            ast.Gt: operator.gt,
            ast.Lt: operator.lt,
            ast.GtE: operator.ge,
            ast.LtE: operator.le,
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.USub: operator.neg,
        }

        try:
            expr = self.expr.replace("$value", str(value))
            tree = ast.parse(expr, mode="eval")

            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    if node.id not in ("True", "False", "None"):
                        self._logger.warning(f"不允许的变量: {node.id}")
                        return False
                elif isinstance(node, ast.Call):
                    self._logger.warning("不允许函数调用")
                    return False
                elif isinstance(node, ast.Attribute):
                    self._logger.warning("不允许属性访问")
                    return False
                elif isinstance(node, ast.BinOp) and type(node.op) not in ALLOWED_OPS:
                    self._logger.warning(f"不允许的运算符: {type(node.op).__name__}")
                    return False

            return eval(compile(tree, "<string>", "eval"), {"__builtins__": {}}, {})
        except Exception:
            return False


class NotificationChannel:
    """
    通知渠道

    示例:
    ```python
    class SlackChannel(NotificationChannel):
        async def send(self, alert: Alert):
            await slack_webhook.send(alert)

    class EmailChannel(NotificationChannel):
        async def send(self, alert: Alert):
            await send_email(alert)
    """

    def __init__(self, name: str):
        self.name = name
        self._logger = logging.getLogger(f"AlertChannel.{name}")

    async def send(self, alert: Alert) -> bool:
        """发送通知"""
        raise NotImplementedError

    async def resolve(self, alert: Alert) -> bool:
        """发送解决通知"""
        raise NotImplementedError


class SlackChannel(NotificationChannel):
    """Slack 通知"""

    def __init__(self, webhook_url: str, channel: str = None):
        super().__init__("slack")
        self.webhook_url = webhook_url
        self.channel = channel

    async def send(self, alert: Alert) -> bool:
        payload = {
            "text": f"[{alert.severity.value.upper()}] {alert.name}",
            "attachments": [
                {
                    "color": self._get_color(alert.severity),
                    "fields": [
                        {"title": "Message", "value": alert.message, "short": False},
                        {"title": "Status", "value": alert.status.value, "short": True},
                        {"title": "Severity", "value": alert.severity.value, "short": True},
                    ],
                }
            ],
        }
        if self.channel:
            payload["channel"] = self.channel

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload):
                    pass
            return True
        except Exception as e:
            self._logger.error(f"发送 Slack 通知失败: {e}")
            return False

    async def resolve(self, alert: Alert) -> bool:
        payload = {
            "text": f"[RESOLVED] {alert.name}",
        }
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload):
                    pass
            return True
        except Exception as e:
            self._logger.error(f"发送 Slack 解决通知失败: {e}")
            return False

    def _get_color(self, severity: AlertSeverity) -> str:
        colors = {
            AlertSeverity.CRITICAL: "danger",
            AlertSeverity.ERROR: "danger",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.INFO: "#36a64f",
        }
        return colors.get(severity, "#36a64f")


class AlertManager:
    """
    告警管理器

    示例:
    ```python
    manager = AlertManager()

    # 添加告警规则
    manager.add_rule(AlertRule(
        name="HighCPU",
        expr="$value > 80",
        severity=AlertSeverity.WARNING,
    ))

    # 添加通知渠道
    manager.add_channel(SlackChannel("https://hooks.slack.com/..."))

    # 评估告警
    manager.evaluate("HighCPU", cpu_usage)

    # 获取告警
    alerts = manager.get_firing_alerts()
    ```
    """

    def __init__(self):
        self._rules: dict[str, AlertRule] = {}
        self._alerts: dict[str, Alert] = {}
        self._channels: dict[str, NotificationChannel] = {}
        self._lock = threading.RLock()
        self._evaluation_history: list[dict] = []
        self._logger = logging.getLogger("AlertManager")

    def add_rule(self, rule: AlertRule) -> None:
        """添加告警规则"""
        with self._lock:
            self._rules[rule.name] = rule

    def remove_rule(self, name: str) -> bool:
        """移除告警规则"""
        with self._lock:
            if name in self._rules:
                del self._rules[name]
                return True
            return False

    def get_rule(self, name: str) -> AlertRule | None:
        """获取告警规则"""
        with self._lock:
            return self._rules.get(name)

    def list_rules(self) -> list[AlertRule]:
        """列出所有规则"""
        with self._lock:
            return list(self._rules.values())

    def add_channel(self, channel: NotificationChannel) -> None:
        """添加通知渠道"""
        with self._lock:
            self._channels[channel.name] = channel

    def remove_channel(self, name: str) -> bool:
        """移除通知渠道"""
        with self._lock:
            if name in self._channels:
                del self._channels[name]
                return True
            return False

    def evaluate(self, rule_name: str, value: float) -> Alert | None:
        """评估告警规则"""
        with self._lock:
            rule = self._rules.get(rule_name)
            if not rule:
                return None

            # 记录评估历史
            self._evaluation_history.append(
                {
                    "rule": rule_name,
                    "value": value,
                    "timestamp": time.time(),
                }
            )

            # 保持最近1000条记录
            if len(self._evaluation_history) > 1000:
                self._evaluation_history = self._evaluation_history[-1000:]

            triggered = rule.evaluate(value)

            if triggered:
                return self._fire_alert(rule)
            else:
                return self._resolve_alert(rule_name)

        return None

    def _fire_alert(self, rule: AlertRule) -> Alert:
        """触发告警"""
        if rule.name in self._alerts:
            alert = self._alerts[rule.name]
            if alert.status == AlertStatus.FIRING:
                return alert

        alert = Alert(
            name=rule.name,
            message=rule.annotations.get("description", f"Alert {rule.name} triggered"),
            severity=rule.severity,
            status=AlertStatus.FIRING,
            labels=rule.labels,
            annotations=rule.annotations,
            starts_at=time.time(),
        )

        self._alerts[rule.name] = alert
        self._logger.warning(f"告警触发: {rule.name} [{rule.severity.value}]")

        # 发送通知
        self._send_notifications(alert)

        return alert

    def _resolve_alert(self, rule_name: str) -> Alert | None:
        """解决告警"""
        if rule_name not in self._alerts:
            return None

        alert = self._alerts[rule_name]
        if alert.status == AlertStatus.RESOLVED:
            return alert

        alert.status = AlertStatus.RESOLVED
        alert.ends_at = time.time()

        self._logger.info(f"告警解决: {rule_name}")

        # 发送解决通知
        self._send_resolved_notifications(alert)

        return alert

    async def _send_notifications(self, alert: Alert) -> None:
        """发送告警通知"""
        for channel in self._channels.values():
            try:
                await channel.send(alert)
            except Exception as e:
                self._logger.error(f"通知发送失败: {channel.name}: {e}")

    async def _send_resolved_notifications(self, alert: Alert) -> None:
        """发送解决通知"""
        for channel in self._channels.values():
            try:
                await channel.resolve(alert)
            except Exception as e:
                self._logger.error(f"解决通知发送失败: {channel.name}: {e}")

    def get_alert(self, name: str) -> Alert | None:
        """获取告警"""
        with self._lock:
            return self._alerts.get(name)

    def get_firing_alerts(self) -> list[Alert]:
        """获取触发中的告警"""
        with self._lock:
            return [a for a in self._alerts.values() if a.status == AlertStatus.FIRING]

    def get_all_alerts(self) -> list[Alert]:
        """获取所有告警"""
        with self._lock:
            return list(self._alerts.values())

    def get_alerts_by_severity(self, severity: AlertSeverity) -> list[Alert]:
        """按级别获取告警"""
        with self._lock:
            return [a for a in self._alerts.values() if a.severity == severity]

    def clear_alerts(self) -> int:
        """清除所有告警"""
        with self._lock:
            count = len(self._alerts)
            self._alerts.clear()
            return count

    def export(self) -> str:
        """导出告警（Prometheus AlertManager 格式）"""
        with self._lock:
            alerts = []
            for alert in self._alerts.values():
                if alert.status == AlertStatus.FIRING:
                    alerts.append(alert.to_dict())
            return json.dumps(alerts, indent=2)


# 全局实例
_alert_manager: AlertManager | None = None


def get_alert_manager() -> AlertManager:
    """获取全局告警管理器"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
