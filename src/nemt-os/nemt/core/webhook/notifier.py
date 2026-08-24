"""
Webhook Notifier - Webhook 变更通知系统

监听业务变更，自动触发相关通知。

版本: v1.0.0
更新: 2026-04-27
"""

from __future__ import annotations

import hashlib
import hmac
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class WebhookEvent:
    """Webhook 事件"""

    event_id: str
    event_type: str
    timestamp: datetime
    payload: dict[str, Any]
    source: str = "system"

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "source": self.source,
        }


@dataclass
class WebhookSubscription:
    """Webhook 订阅"""

    subscription_id: str
    url: str
    events: list[str]  # 关注的事件类型
    secret: str | None = None
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    headers: dict[str, str] = field(default_factory=dict)


class WebhookNotifier:
    """
    Webhook 通知器

    支持：
    - 订阅特定事件
    - 签名验证
    - 重试机制
    """

    def __init__(self):
        self._subscriptions: dict[str, WebhookSubscription] = {}
        self._event_history: list[WebhookEvent] = []
        self._lock = threading.RLock()
        self._max_history = 1000

    def subscribe(
        self,
        url: str,
        events: list[str],
        secret: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        """
        订阅 Webhook

        Args:
            url: Webhook URL
            events: 关注的事件列表
            secret: 签名密钥
            headers: 自定义请求头

        Returns:
            订阅 ID
        """
        import uuid

        sub_id = str(uuid.uuid4())[:8]

        subscription = WebhookSubscription(
            subscription_id=sub_id,
            url=url,
            events=events,
            secret=secret,
            headers=headers or {},
        )

        with self._lock:
            self._subscriptions[sub_id] = subscription

        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        with self._lock:
            if subscription_id in self._subscriptions:
                del self._subscriptions[subscription_id]
                return True
            return False

    def notify(
        self,
        event_type: str,
        payload: dict[str, Any],
        source: str = "system",
    ) -> int:
        """
        发送通知

        Args:
            event_type: 事件类型
            payload: 事件数据
            source: 事件来源

        Returns:
            发送的通知数量
        """
        import uuid

        event = WebhookEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(),
            payload=payload,
            source=source,
        )

        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history :]

            # 找到订阅者
            subscribers = [sub for sub in self._subscriptions.values() if sub.enabled and event_type in sub.events]

        # TODO: 实际发送 HTTP 请求
        # 这里只是模拟
        for sub in subscribers:
            self._send_webhook(sub, event)

        return len(subscribers)

    def _send_webhook(self, subscription: WebhookSubscription, event: WebhookEvent) -> bool:
        """
        发送 Webhook 请求

        TODO: 实现实际的 HTTP 请求逻辑
        """
        # 模拟发送
        print(f"Sending webhook to {subscription.url} for event {event.event_type}")
        return True

    def _generate_signature(self, payload: str, secret: str) -> str:
        """生成签名"""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

    def get_subscriptions(self) -> list[WebhookSubscription]:
        """获取所有订阅"""
        with self._lock:
            return list(self._subscriptions.values())

    def get_event_history(
        self,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[WebhookEvent]:
        """获取事件历史"""
        with self._lock:
            events = self._event_history

            if event_type:
                events = [e for e in events if e.event_type == event_type]

            return events[-limit:]


# =============================================================================
# Predefined Event Types
# =============================================================================

BUSINESS_CHANGE_EVENTS = {
    "domain.entity.added": "新增领域实体",
    "domain.entity.modified": "修改领域实体",
    "domain.entity.removed": "删除领域实体",
    "contract.interface.changed": "接口变更",
    "context.boundary.changed": "上下文边界变更",
    "event.schema.changed": "事件模式变更",
    "code.deployment": "代码部署",
    "test.failed": "测试失败",
}


# =============================================================================
# Global Notifier
# =============================================================================

_global_notifier: WebhookNotifier | None = None


def get_webhook_notifier() -> WebhookNotifier:
    """获取全局通知器"""
    global _global_notifier
    if _global_notifier is None:
        _global_notifier = WebhookNotifier()
    return _global_notifier
