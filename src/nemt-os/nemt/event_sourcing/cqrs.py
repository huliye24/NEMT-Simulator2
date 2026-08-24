"""
CQRS - 命令查询职责分离

提供 CQRS 模式实现。
"""

import logging
import time
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "Command",
    "Query",
    "CommandHandler",
    "QueryHandler",
    "CommandBus",
    "QueryBus",
    "CQRSMediator",
]


@dataclass
class Command:
    """命令"""

    command_id: str
    command_type: str
    payload: dict
    timestamp: float
    metadata: dict = field(default_factory=dict)

    def __init__(self, command_type: str, payload: dict, metadata: dict = None):
        self.command_id = str(uuid.uuid4())
        self.command_type = command_type
        self.payload = payload
        self.timestamp = time.time()
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "command_id": self.command_id,
            "command_type": self.command_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class Query:
    """查询"""

    query_id: str
    query_type: str
    params: dict
    timestamp: float

    def __init__(self, query_type: str, params: dict):
        self.query_id = str(uuid.uuid4())
        self.query_type = query_type
        self.params = params
        self.timestamp = time.time()


@dataclass
class CommandResult:
    """命令结果"""

    success: bool
    data: Any
    error: str = ""
    command_id: str = ""


@dataclass
class QueryResult:
    """查询结果"""

    data: Any
    cached: bool = False
    query_id: str = ""


class CommandHandler(ABC):
    """命令处理器基类"""

    @abstractmethod
    def handle(self, command: Command) -> CommandResult:
        """处理命令"""
        pass


class QueryHandler(ABC):
    """查询处理器基类"""

    @abstractmethod
    def handle(self, query: Query) -> QueryResult:
        """处理查询"""
        pass


class CommandBus:
    """
    命令总线

    分发命令到对应的处理器。

    示例:
    ```python
    bus = CommandBus()

    @bus.register("CreateOrder")
    class CreateOrderHandler(CommandHandler):
        def handle(self, command):
            # 处理命令
            return CommandResult(success=True, data={"order_id": "123"})

    # 发送命令
    result = bus.send(Command("CreateOrder", {"product": "BTC"}))
    ```
    """

    def __init__(self):
        self._handlers: dict[str, CommandHandler] = {}
        self._middleware: list[Callable] = []
        self._logger = logging.getLogger("CommandBus")

    def register(self, command_type: str) -> Callable:
        """装饰器注册命令处理器"""

        def decorator(handler_class: type[CommandHandler]) -> type[CommandHandler]:
            self._handlers[command_type] = handler_class()
            return handler_class

        return decorator

    def register_handler(self, command_type: str, handler: CommandHandler) -> None:
        """注册命令处理器"""
        self._handlers[command_type] = handler

    def add_middleware(self, middleware: Callable) -> None:
        """添加中间件"""
        self._middleware.append(middleware)

    def send(self, command: Command) -> CommandResult:
        """发送命令"""
        command.command_id = command.command_id or str(uuid.uuid4())

        # 调用中间件（前置）
        for mw in self._middleware:
            result = mw(command)
            if result is not None:
                return result

        handler = self._handlers.get(command.command_type)
        if handler is None:
            self._logger.error(f"未找到命令处理器: {command.command_type}")
            return CommandResult(
                success=False,
                data=None,
                error=f"Unknown command: {command.command_type}",
                command_id=command.command_id,
            )

        try:
            result = handler.handle(command)
            result.command_id = command.command_id
            return result
        except Exception as e:
            self._logger.error(f"命令执行失败: {command.command_type}: {e}")
            return CommandResult(
                success=False,
                data=None,
                error=str(e),
                command_id=command.command_id,
            )

    def unregister(self, command_type: str) -> bool:
        """注销命令处理器"""
        if command_type in self._handlers:
            del self._handlers[command_type]
            return True
        return False


class QueryBus:
    """
    查询总线

    分发查询到对应的处理器。

    示例:
    ```python
    bus = QueryBus()

    @bus.register("GetOrder")
    class GetOrderHandler(QueryHandler):
        def handle(self, query):
            return QueryResult(data={"order": {...}})

    # 发送查询
    result = bus.send(Query("GetOrder", {"order_id": "123"}))
    ```
    """

    def __init__(self):
        self._handlers: dict[str, QueryHandler] = {}
        self._cache: dict[str, Any] = {}
        self._cache_ttl: int = 60
        self._logger = logging.getLogger("QueryBus")

    def register(self, query_type: str) -> Callable:
        """装饰器注册查询处理器"""

        def decorator(handler_class: type[QueryHandler]) -> type[QueryHandler]:
            self._handlers[query_type] = handler_class()
            return handler_class

        return decorator

    def register_handler(self, query_type: str, handler: QueryHandler) -> None:
        """注册查询处理器"""
        self._handlers[query_type] = handler

    def send(self, query: Query) -> QueryResult:
        """发送查询"""
        query.query_id = query.query_id or str(uuid.uuid4())

        # 检查缓存
        cache_key = self._get_cache_key(query)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            return QueryResult(data=cached, cached=True, query_id=query.query_id)

        handler = self._handlers.get(query.query_type)
        if handler is None:
            self._logger.error(f"未找到查询处理器: {query.query_type}")
            return QueryResult(data=None, query_id=query.query_id)

        try:
            result = handler.handle(query)
            result.query_id = query.query_id

            # 缓存结果
            self._cache[cache_key] = result.data

            return result
        except Exception as e:
            self._logger.error(f"查询执行失败: {query.query_type}: {e}")
            return QueryResult(data=None, query_id=query.query_id)

    def _get_cache_key(self, query: Query) -> str:
        """生成缓存键"""
        return f"{query.query_type}:{query.query_id}"

    def invalidate_cache(self, query_type: str = None) -> None:
        """清除缓存"""
        if query_type is None:
            self._cache.clear()
        else:
            keys_to_remove = [k for k in self._cache if k.startswith(f"{query_type}:")]
            for key in keys_to_remove:
                del self._cache[key]


class CQRSMediator:
    """
    CQRS 中介者

    统一管理命令和查询。

    示例:
    ```python
    mediator = CQRSMediator()

    # 发送命令
    cmd_result = mediator.execute(Command("CreateOrder", {"product": "BTC"}))

    # 发送查询
    query_result = mediator.query(Query("GetOrders", {}))
    ```
    """

    def __init__(self):
        self.command_bus = CommandBus()
        self.query_bus = QueryBus()
        self._logger = logging.getLogger("CQRSMediator")

    def execute(self, command: Command) -> CommandResult:
        """执行命令"""
        return self.command_bus.send(command)

    def query(self, query: Query) -> QueryResult:
        """执行查询"""
        return self.query_bus.send(query)

    def register_command(self, command_type: str, handler: CommandHandler) -> None:
        """注册命令处理器"""
        self.command_bus.register_handler(command_type, handler)

    def register_query(self, query_type: str, handler: QueryHandler) -> None:
        """注册查询处理器"""
        self.query_bus.register_handler(query_type, handler)
