"""
Redis 事件总线 (Event Bus)
提供系统内各模块之间的异步事件通信
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from threading import Thread, Lock
from queue import Queue, Empty

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """事件类型枚举"""
    # 市场数据事件
    MARKET_TICK = "market.tick"
    MARKET_KLINE = "market.kline"
    MARKET_STATUS_CHANGE = "market.status_change"
    
    # 信号事件
    SIGNAL_GENERATED = "signal.generated"
    SIGNAL_EXECUTED = "signal.executed"
    SIGNAL_CANCELLED = "signal.cancelled"
    
    # 策略事件
    STRATEGY_CREATED = "strategy.created"
    STRATEGY_UPDATED = "strategy.updated"
    STRATEGY_EVALUATED = "strategy.evaluated"
    STRATEGY_EVICTED = "strategy.evicted"
    
    # 回测事件
    BACKTEST_STARTED = "backtest.started"
    BACKTEST_PROGRESS = "backtest.progress"
    BACKTEST_COMPLETED = "backtest.completed"
    BACKTEST_FAILED = "backtest.failed"
    
    # 系统事件
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    SYSTEM_ERROR = "system.error"
    SYSTEM_STATUS = "system.status"
    
    # 用户事件
    USER_ACTION = "user.action"
    USER_NOTIFICATION = "user.notification"


@dataclass
class Event:
    """事件数据类"""
    event_type: EventType
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = field(default=None)
    event_id: Optional[str] = field(default=None)
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.event_id is None:
            import uuid
            self.event_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type.value if isinstance(self.event_type, EventType) else self.event_type,
            'source': self.source,
            'data': self.data,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            'event_id': self.event_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        event_type = data.get('event_type')
        if isinstance(event_type, str):
            event_type = EventType(event_type)
        
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        return cls(
            event_type=event_type,
            source=data.get('source', ''),
            data=data.get('data', {}),
            timestamp=timestamp,
            event_id=data.get('event_id')
        )


class EventBus:
    """
    事件总线管理器
    
    功能:
    1. 本地事件订阅/发布（默认）
    2. Redis Pub/Sub 集成（可选）
    3. 事件历史记录
    4. 事件过滤
    """
    
    # 全局单例
    _instance: Optional['EventBus'] = None
    _lock = Lock()
    
    @classmethod
    def get_instance(cls) -> 'EventBus':
        """获取单例实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def __init__(self, redis_host: str = None, redis_port: int = 6379):
        self._subscribers: Dict[str, Set[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._history_lock = Lock()
        
        self._redis_host = redis_host
        self._redis_port = redis_port
        self._redis_client = None
        self._redis_pubsub = None
        self._use_redis = redis_host is not None
        
        self._event_queue: Queue = Queue()
        self._processing = False
        self._processor_thread: Optional[Thread] = None
        
        if self._use_redis:
            self._init_redis()
    
    def _init_redis(self) -> bool:
        """初始化 Redis 连接"""
        try:
            import redis
            self._redis_client = redis.Redis(
                host=self._redis_host,
                port=self._redis_port,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self._redis_client.ping()
            self._redis_pubsub = self._redis_client.pubsub()
            logger.info(f"[EventBus] Redis connected: {self._redis_host}:{self._redis_port}")
            return True
        except Exception as e:
            logger.warning(f"[EventBus] Redis connection failed: {e}, using local event bus")
            self._use_redis = False
            return False
    
    def start(self) -> None:
        """启动事件处理器"""
        if self._processing:
            return
        
        self._processing = True
        self._processor_thread = Thread(target=self._process_events, daemon=True)
        self._processor_thread.start()
        logger.info("[EventBus] Started event processor")
    
    def stop(self) -> None:
        """停止事件处理器"""
        self._processing = False
        if self._processor_thread:
            self._processor_thread.join(timeout=1)
        logger.info("[EventBus] Stopped event processor")
    
    def _process_events(self) -> None:
        """事件处理循环"""
        while self._processing:
            try:
                event = self._event_queue.get(timeout=0.1)
                self._handle_event(event)
            except Empty:
                continue
            except Exception as e:
                logger.error(f"[EventBus] Event processing error: {e}")
    
    def _handle_event(self, event: Event) -> None:
        """处理单个事件"""
        self._add_to_history(event)
        
        event_type_str = event.event_type.value if isinstance(event.event_type, EventType) else event.event_type
        subscribers = self._subscribers.get(event_type_str, set())
        
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"[EventBus] Subscriber callback error: {e}")
        
        if self._use_redis and self._redis_client:
            try:
                self._redis_client.publish(event_type_str, json.dumps(event.to_dict()))
            except Exception as e:
                logger.error(f"[EventBus] Redis publish error: {e}")
    
    def _add_to_history(self, event: Event) -> None:
        """添加事件到历史记录"""
        with self._history_lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]
    
    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """订阅事件"""
        event_type_str = event_type.value if isinstance(event_type, EventType) else event_type
        
        if event_type_str not in self._subscribers:
            self._subscribers[event_type_str] = set()
        
        self._subscribers[event_type_str].add(callback)
        logger.debug(f"[EventBus] Subscribed to {event_type_str}")
        
        if self._use_redis and self._redis_pubsub:
            try:
                self._redis_pubsub.subscribe(**{event_type_str: self._on_redis_message})
            except Exception as e:
                logger.error(f"[EventBus] Redis subscribe error: {e}")
    
    def _on_redis_message(self, message: Dict[str, Any]) -> None:
        """处理 Redis 消息"""
        try:
            if message['type'] == 'message':
                data = json.loads(message['data'])
                event = Event.from_dict(data)
                self._event_queue.put(event)
        except Exception as e:
            logger.error(f"[EventBus] Redis message processing error: {e}")
    
    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """取消订阅"""
        event_type_str = event_type.value if isinstance(event_type, EventType) else event_type
        
        if event_type_str in self._subscribers:
            self._subscribers[event_type_str].discard(callback)
            if not self._subscribers[event_type_str]:
                del self._subscribers[event_type_str]
        
        logger.debug(f"[EventBus] Unsubscribed from {event_type_str}")
    
    def publish(self, event: Event) -> None:
        """发布事件"""
        self._event_queue.put(event)
        logger.debug(f"[EventBus] Published: {event.event_type}")
    
    def emit(self, event_type: EventType, source: str, data: Dict[str, Any] = None) -> None:
        """快速发布事件"""
        event = Event(event_type=event_type, source=source, data=data or {})
        self.publish(event)
    
    def get_history(self, event_type: Optional[EventType] = None, limit: int = 100) -> List[Event]:
        """获取事件历史"""
        with self._history_lock:
            if event_type is None:
                return self._event_history[-limit:]
            
            event_type_str = event_type.value if isinstance(event_type, EventType) else event_type
            filtered = [e for e in self._event_history if e.event_type == event_type_str]
            return filtered[-limit:]
    
    def clear_history(self) -> None:
        """清空事件历史"""
        with self._history_lock:
            self._event_history.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """获取事件总线状态"""
        return {
            'redis_enabled': self._use_redis,
            'redis_host': self._redis_host,
            'redis_port': self._redis_port,
            'subscribers': {k: len(v) for k, v in self._subscribers.items()},
            'queue_size': self._event_queue.qsize(),
            'history_size': len(self._event_history)
        }


# ==================== 便捷函数 ====================

_bus: Optional[EventBus] = None


def get_event_bus(redis_host: str = None) -> EventBus:
    """获取或创建事件总线"""
    global _bus
    if _bus is None:
        _bus = EventBus(redis_host=redis_host)
        _bus.start()
    return _bus


def publish_event(event_type: EventType, source: str, data: Dict[str, Any] = None) -> None:
    """快速发布事件"""
    bus = get_event_bus()
    bus.emit(event_type, source, data)


def subscribe_event(event_type: EventType, callback: Callable) -> None:
    """快速订阅事件"""
    bus = get_event_bus()
    bus.subscribe(event_type, callback)


def unsubscribe_event(event_type: EventType, callback: Callable) -> None:
    """快速取消订阅"""
    bus = get_event_bus()
    bus.unsubscribe(event_type, callback)
