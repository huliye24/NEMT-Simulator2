"""
IPC - 进程间通信

提供多种进程间通信机制:
- ZeroMQ 消息队列
- gRPC RPC
- 共享内存
"""

import json
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

__all__ = [
    "IPCMessage",
    "IPCBus",
    "IPCBusType",
    "RPCClient",
    "RPCServer",
]


class IPCBusType(Enum):
    """IPC 总线类型"""

    IN_MEMORY = "in_memory"
    ZEROMQ = "zeromq"
    GRPC = "grpc"


@dataclass
class IPCMessage:
    """IPC 消息"""

    msg_id: str
    msg_type: str
    source: str
    target: str
    payload: Any
    timestamp: float
    correlation_id: str = ""
    reply_to: str = ""

    def to_json(self) -> str:
        return json.dumps(
            {
                "msg_id": self.msg_id,
                "msg_type": self.msg_type,
                "source": self.source,
                "target": self.target,
                "payload": self.payload,
                "timestamp": self.timestamp,
                "correlation_id": self.correlation_id,
                "reply_to": self.reply_to,
            }
        )

    @classmethod
    def from_json(cls, data: str) -> "IPCMessage":
        obj = json.loads(data)
        return cls(**obj)


class IPCBus:
    """
    IPC 总线

    提供进程间通信的统一接口。

    示例:
    ```python
    # 创建总线
    bus = IPCBus(bus_type=IPCBusType.IN_MEMORY)

    # 注册处理器
    bus.register_handler("capsule.exec", handle_exec)

    # 发送消息
    bus.send("target_capsule", "capsule.exec", {"cmd": "status"})

    # 接收消息（异步）
    bus.subscribe("capsule.*", handler)
    ```
    """

    def __init__(
        self,
        bus_type: IPCBusType = IPCBusType.IN_MEMORY,
        address: str = None,
        port: int = 5555,
    ):
        self.bus_type = bus_type
        self.address = address
        self.port = port
        self._logger = logging.getLogger(f"IPCBus.{bus_type.value}")

        self._handlers: dict[str, list[Callable]] = {}
        self._pattern_handlers: list[tuple] = []
        self._running = False
        self._thread: threading.Thread | None = None

        # ZeroMQ (预留)
        self._zmq_context = None
        self._zmq_socket = None

        # gRPC (预留)
        self._grpc_server = None
        self._grpc_channel = None

    def start(self) -> bool:
        """启动总线"""
        if self._running:
            return True

        try:
            if self.bus_type == IPCBusType.ZEROMQ:
                return self._start_zeromq()
            elif self.bus_type == IPCBusType.GRPC:
                return self._start_grpc()
            else:
                self._running = True
                return True

        except Exception as e:
            self._logger.error(f"启动失败: {e}")
            return False

    def stop(self) -> None:
        """停止总线"""
        self._running = False

        if self._thread:
            self._thread.join(timeout=5)

        if self._zmq_socket:
            self._zmq_socket.close()
        if self._zmq_context:
            self._zmq_context.term()

    def _start_zeromq(self) -> bool:
        """启动 ZeroMQ"""
        try:
            import zmq

            self._zmq_context = zmq.Context()
            self._zmq_socket = self._zmq_context.socket(zmq.ROUTER)
            self._zmq_socket.bind(f"tcp://*:{self.port}")
            self._running = True

            self._thread = threading.Thread(target=self._zmq_recv_loop, daemon=True)
            self._thread.start()

            return True

        except ImportError:
            self._logger.warning("ZeroMQ 未安装，使用内存模式")
            self.bus_type = IPCBusType.IN_MEMORY
            return self.start()

    def _start_grpc(self) -> bool:
        """启动 gRPC"""
        self._logger.warning("gRPC 模式尚未实现")
        return False

    def _zmq_recv_loop(self) -> None:
        """ZeroMQ 接收循环"""
        import zmq

        while self._running:
            try:
                msg = self._zmq_socket.recv_string(zmq.NOBLOCK)
                self._handle_message(msg)
            except zmq.Again:
                time.sleep(0.01)
            except Exception as e:
                self._logger.error(f"接收错误: {e}")

    def _handle_message(self, data: str) -> None:
        """处理消息"""
        try:
            msg = IPCMessage.from_json(data)
            handlers = self._handlers.get(msg.msg_type, [])

            for handler in handlers:
                try:
                    handler(msg)
                except Exception as e:
                    self._logger.error(f"处理消息错误: {e}")

            # 模式匹配
            for pattern, handler in self._pattern_handlers:
                import fnmatch

                if fnmatch.fnmatch(msg.msg_type, pattern):
                    try:
                        handler(msg)
                    except Exception as e:
                        self._logger.error(f"处理消息错误: {e}")

        except Exception as e:
            self._logger.error(f"解析消息错误: {e}")

    def register_handler(self, msg_type: str, handler: Callable[[IPCMessage], None]) -> None:
        """注册消息处理器"""
        if msg_type not in self._handlers:
            self._handlers[msg_type] = []
        self._handlers[msg_type].append(handler)

    def unregister_handler(self, msg_type: str, handler: Callable) -> None:
        """取消注册"""
        if msg_type in self._handlers:
            self._handlers[msg_type].remove(handler)

    def subscribe_pattern(self, pattern: str, handler: Callable[[IPCMessage], None]) -> None:
        """订阅模式匹配"""
        self._pattern_handlers.append((pattern, handler))

    def send(
        self,
        target: str,
        msg_type: str,
        payload: Any,
        source: str = "default",
        correlation_id: str = "",
    ) -> bool:
        """
        发送消息

        Args:
            target: 目标
            msg_type: 消息类型
            payload: 负载
            source: 来源
            correlation_id: 关联 ID

        Returns:
            是否发送成功
        """
        msg = IPCMessage(
            msg_id=self._generate_id(),
            msg_type=msg_type,
            source=source,
            target=target,
            payload=payload,
            timestamp=time.time(),
            correlation_id=correlation_id,
        )

        return self._send_message(msg)

    def _send_message(self, msg: IPCMessage) -> bool:
        """发送消息（具体实现）"""
        if self.bus_type == IPCBusType.IN_MEMORY:
            return self._send_in_memory(msg)
        elif self.bus_type == IPCBusType.ZEROMQ:
            return self._send_zeromq(msg)
        return False

    def _send_in_memory(self, msg: IPCMessage) -> bool:
        """内存模式发送"""
        self._handle_message(msg.to_json())
        return True

    def _send_zeromq(self, msg: IPCMessage) -> bool:
        """ZeroMQ 发送"""
        try:
            self._zmq_socket.send_string(msg.target, zmq.SNDMORE)
            self._zmq_socket.send_string(msg.to_json())
            return True
        except Exception as e:
            self._logger.error(f"ZeroMQ 发送失败: {e}")
            return False

    def _generate_id(self) -> str:
        """生成消息 ID"""
        import uuid

        return str(uuid.uuid4())


class RPCClient:
    """
    RPC 客户端

    提供同步 RPC 调用。

    示例:
    ```python
    client = RPCClient("tcp://localhost:5555")
    result = client.call("add", {"a": 1, "b": 2})
    ```
    """

    def __init__(self, address: str):
        self.address = address
        self._connected = False
        self._logger = logging.getLogger("RPCClient")

    def call(self, method: str, params: dict[str, Any] = None, timeout: float = 30.0) -> Any:
        """
        调用 RPC 方法

        Args:
            method: 方法名
            params: 参数
            timeout: 超时

        Returns:
            结果

        Raises:
            Exception: 调用失败
        """
        raise NotImplementedError("RPC 调用需要实现")

    def close(self) -> None:
        """关闭连接"""
        self._connected = False


class RPCServer:
    """
    RPC 服务器

    提供 RPC 服务。

    示例:
    ```python
    def add(a, b):
        return a + b

    server = RPCServer("tcp://*:5555")
    server.register("add", add)
    server.start()
    ```
    """

    def __init__(self, address: str):
        self.address = address
        self._handlers: dict[str, Callable] = {}
        self._running = False
        self._logger = logging.getLogger("RPCServer")

    def register(self, name: str, handler: Callable) -> None:
        """注册处理方法"""
        self._handlers[name] = handler

    def start(self) -> None:
        """启动服务器"""
        self._running = True

    def stop(self) -> None:
        """停止服务器"""
        self._running = False
