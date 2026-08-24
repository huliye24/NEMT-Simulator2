"""
MessageQueue - 消息队列

提供消息队列实现:
- 内存队列
- Redis 队列
- Kafka/RabbitMQ 适配器
"""

import json
import logging
import threading
import time
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "Message",
    "MessagePriority",
    "MessageQueue",
    "InMemoryQueue",
    "RedisQueue",
    "QueueConsumer",
]


class MessagePriority(Enum):
    """消息优先级"""

    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class Message:
    """消息"""

    msg_id: str
    topic: str
    payload: Any
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    headers: dict[str, str] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3

    def __init__(
        self,
        topic: str,
        payload: Any,
        priority: MessagePriority = MessagePriority.NORMAL,
        headers: dict = None,
        max_retries: int = 3,
    ):
        self.msg_id = str(uuid.uuid4())
        self.topic = topic
        self.payload = payload
        self.priority = priority
        self.timestamp = time.time()
        self.headers = headers or {}
        self.retry_count = 0
        self.max_retries = max_retries

    def to_dict(self) -> dict:
        return {
            "msg_id": self.msg_id,
            "topic": self.topic,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "headers": self.headers,
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        msg = cls(
            topic=data["topic"],
            payload=data["payload"],
            priority=MessagePriority(data["priority"]),
            headers=data.get("headers", {}),
            max_retries=data.get("max_retries", 3),
        )
        msg.msg_id = data["msg_id"]
        msg.timestamp = data["timestamp"]
        msg.retry_count = data.get("retry_count", 0)
        return msg


class QueueConsumer:
    """
    队列消费者

    示例:
    ```python
    def handle_message(msg):
        print(f"Received: {msg.payload}")

    consumer = QueueConsumer(queue, handler=handle_message)
    consumer.start()
    consumer.stop()
    ```
    """

    def __init__(
        self,
        queue: "MessageQueue",
        handler: Callable[[Message], Any],
        batch_size: int = 1,
        poll_interval: float = 0.1,
    ):
        self.queue = queue
        self.handler = handler
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self._running = False
        self._thread: threading.Thread | None = None
        self._logger = logging.getLogger("QueueConsumer")

    def start(self) -> None:
        """启动消费者"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._consume_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """停止消费者"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _consume_loop(self) -> None:
        """消费循环"""
        while self._running:
            try:
                if self.batch_size == 1:
                    msg = self.queue.get(timeout=self.poll_interval)
                    if msg:
                        self._process_message(msg)
                else:
                    messages = self.queue.get_batch(self.batch_size, timeout=self.poll_interval)
                    for msg in messages:
                        self._process_message(msg)

            except Exception as e:
                self._logger.error(f"消费消息失败: {e}")
                time.sleep(1)

    def _process_message(self, msg: Message) -> None:
        """处理消息"""
        try:
            result = self.handler(msg)
            if result is False:
                # 处理失败，重试
                self._handle_failure(msg)
            else:
                self.queue.ack(msg.msg_id)

        except Exception as e:
            self._logger.error(f"处理消息异常: {msg.msg_id}: {e}")
            self._handle_failure(msg)

    def _handle_failure(self, msg: Message) -> None:
        """处理失败"""
        msg.retry_count += 1
        if msg.retry_count < msg.max_retries:
            # 重新入队
            self.queue.put(msg)
        else:
            # 死信
            self.queue.dead_letter(msg)
            self._logger.error(f"消息处理失败，已进入死信队列: {msg.msg_id}")


class MessageQueue(ABC):
    """消息队列抽象"""

    @abstractmethod
    def put(self, message: Message) -> bool:
        """发送消息"""
        pass

    @abstractmethod
    def get(self, timeout: float = None) -> Message | None:
        """获取消息"""
        pass

    @abstractmethod
    def ack(self, msg_id: str) -> bool:
        """确认消息"""
        pass

    @abstractmethod
    def dead_letter(self, message: Message) -> None:
        """死信处理"""
        pass

    @abstractmethod
    def size(self) -> int:
        """队列大小"""
        pass


class InMemoryQueue(MessageQueue):
    """
    内存消息队列

    示例:
    ```python
    queue = InMemoryQueue()

    queue.put(Message("topic1", {"data": "test"}))

    msg = queue.get()
    if msg:
        print(msg.payload)
        queue.ack(msg.msg_id)
    ```
    """

    def __init__(self):
        self._queue: list[Message] = []
        self._processing: dict[str, Message] = {}
        self._dead_letter: list[Message] = []
        self._lock = threading.RLock()
        self._not_empty = threading.Condition(self._lock)

    def put(self, message: Message) -> bool:
        """发送消息"""
        with self._lock:
            # 按优先级插入
            inserted = False
            for i, msg in enumerate(self._queue):
                if message.priority.value < msg.priority.value:
                    self._queue.insert(i, message)
                    inserted = True
                    break
            if not inserted:
                self._queue.append(message)
            self._not_empty.notify()
            return True

    def get(self, timeout: float = None) -> Message | None:
        """获取消息"""
        with self._not_empty:
            if not self._queue:
                if timeout:
                    self._not_empty.wait(timeout)
                else:
                    return None

            if not self._queue:
                return None

            message = self._queue.pop(0)
            self._processing[message.msg_id] = message
            return message

    def get_batch(self, batch_size: int, timeout: float = None) -> list[Message]:
        """批量获取消息"""
        messages = []
        with self._not_empty:
            if not self._queue:
                if timeout:
                    self._not_empty.wait(timeout)

            while self._queue and len(messages) < batch_size:
                message = self._queue.pop(0)
                self._processing[message.msg_id] = message
                messages.append(message)

        return messages

    def ack(self, msg_id: str) -> bool:
        """确认消息"""
        with self._lock:
            if msg_id in self._processing:
                del self._processing[msg_id]
                return True
            return False

    def dead_letter(self, message: Message) -> None:
        """死信处理"""
        with self._lock:
            if message.msg_id in self._processing:
                del self._processing[message.msg_id]
            self._dead_letter.append(message)

    def size(self) -> int:
        """队列大小"""
        with self._lock:
            return len(self._queue)

    def get_dead_letters(self) -> list[Message]:
        """获取死信"""
        with self._lock:
            return self._dead_letter.copy()

    def clear_dead_letters(self) -> int:
        """清空死信"""
        with self._lock:
            count = len(self._dead_letter)
            self._dead_letter.clear()
            return count


class RedisQueue(MessageQueue):
    """
    Redis 消息队列

    示例:
    ```python
    queue = RedisQueue(host="localhost", port=6379)

    queue.put(Message("topic1", {"data": "test"}))
    msg = queue.get()
    queue.ack(msg.msg_id)
    ```
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str = None,
        queue_name: str = "default",
        dead_letter_name: str = "dead_letter",
    ):
        self.host = host
        self.port = port
        self.db = db
        self.queue_name = f"nemt:queue:{queue_name}"
        self.dead_letter_name = f"nemt:queue:{dead_letter_name}"
        self._client = None
        self._logger = logging.getLogger("RedisQueue")

    def _get_client(self):
        """获取 Redis 客户端"""
        if self._client is None:
            try:
                import redis

                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=password,
                    decode_responses=True,
                )
            except ImportError:
                self._logger.warning("Redis 未安装")
                return None
        return self._client

    def put(self, message: Message) -> bool:
        """发送消息"""
        client = self._get_client()
        if client is None:
            return False

        try:
            data = json.dumps(message.to_dict())
            client.rpush(self.queue_name, data)
            return True
        except Exception as e:
            self._logger.error(f"发送消息失败: {e}")
            return False

    def get(self, timeout: float = None) -> Message | None:
        """获取消息"""
        client = self._get_client()
        if client is None:
            return None

        try:
            if timeout:
                result = client.blpop(self.queue_name, timeout=int(timeout))
                if result:
                    _, data = result
                else:
                    return None
            else:
                data = client.lpop(self.queue_name)

            if data:
                return Message.from_dict(json.loads(data))
            return None

        except Exception as e:
            self._logger.error(f"获取消息失败: {e}")
            return None

    def ack(self, msg_id: str) -> bool:
        """确认消息"""
        # Redis 队列不需要显式确认
        return True

    def dead_letter(self, message: Message) -> None:
        """死信处理"""
        client = self._get_client()
        if client is None:
            return

        try:
            data = json.dumps(message.to_dict())
            client.rpush(self.dead_letter_name, data)
        except Exception as e:
            self._logger.error(f"死信处理失败: {e}")

    def size(self) -> int:
        """队列大小"""
        client = self._get_client()
        if client is None:
            return 0

        try:
            return client.llen(self.queue_name)
        except Exception:
            return 0


# 全局队列管理器
_queues: dict[str, MessageQueue] = {}


def get_queue(name: str = "default") -> MessageQueue:
    """获取命名队列"""
    if name not in _queues:
        _queues[name] = InMemoryQueue()
    return _queues[name]


def register_queue(name: str, queue: MessageQueue) -> None:
    """注册队列"""
    _queues[name] = queue
