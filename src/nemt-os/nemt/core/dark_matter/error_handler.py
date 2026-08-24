"""
Error Handler - 集中式错误处理器

提供统一的错误处理接口:
- 错误处理器注册和路由
- 错误上下文管理
- 错误统计
- 错误告警

参考: Notion 暗物质框架 第二章「错误即信号，处理即恢复」
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

from nemt.core.dark_matter.error_types import (
    ErrorContext,
    NEMTError,
    RecoveryStrategy,
)

# ============================================================================
# 全局错误处理器实例（模块级单例）
# ============================================================================


class ErrorHandler:
    """
    集中式错误处理器

    提供统一的错误处理接口，支持:
    - 错误处理器注册和路由
    - 错误上下文管理
    - 错误统计
    - 错误告警

    Usage:
        handler = ErrorHandler()
        handler.register(InsufficientBalanceError, handle_balance_error)
        handler.handle(error, context)
    """

    def __init__(self, max_history: int = 1000, enable_alert: bool = True):
        """
        初始化错误处理器

        Args:
            max_history: 最大历史记录数
            enable_alert: 是否启用告警
        """
        self._handlers: dict[type[Exception], Callable] = {}
        self._default_handler: Callable | None = None
        self._context_source: str | None = None

        # 统计
        self._error_count: int = 0
        self._error_history: deque = deque(maxlen=max_history)
        self._error_stats: dict[str, int] = defaultdict(int)

        # 告警
        self._enable_alert = enable_alert
        self._alert_callbacks: list[Callable] = []

        # 线程安全
        self._lock = threading.RLock()

        # 恢复策略映射
        self._recovery_strategies: dict[type[Exception], RecoveryStrategy] = {}

        # 事件总线（延迟导入避免循环依赖）
        self._event_bus = None

        self._logger = logging.getLogger("ErrorHandler")

    # ========================================================================
    # 处理器注册
    # ========================================================================

    def register(self, error_type: type[Exception], handler: Callable[[Exception, ErrorContext], Any]) -> None:
        """
        注册错误处理器

        Args:
            error_type: 异常类型（可以是基类，匹配时优先精确匹配）
            handler: 处理函数，签名: (error: Exception, context: ErrorContext) -> Any
        """
        with self._lock:
            # 不允许重复注册
            if error_type not in self._handlers:
                self._handlers[error_type] = handler
                self._logger.debug(f"Registered error handler for {error_type.__name__}")

    def register_default(self, handler: Callable[[Exception, ErrorContext], Any]) -> None:
        """
        注册默认错误处理器

        Args:
            handler: 默认处理函数
        """
        with self._lock:
            self._default_handler = handler

    def set_default_handler(self) -> None:
        """设置默认处理行为（记录日志 + 记录统计）"""

        def default_handler(error: Exception, context: ErrorContext) -> None:
            self._logger.error(f"Unhandled error in {context.source}: {type(error).__name__}: {error}")

        self.register_default(default_handler)

    def unregister(self, error_type: type[Exception]) -> None:
        """
        注销错误处理器

        Args:
            error_type: 异常类型
        """
        with self._lock:
            if error_type in self._handlers:
                del self._handlers[error_type]
                self._logger.debug(f"Unregistered error handler for {error_type.__name__}")

    # ========================================================================
    # 错误处理核心
    # ========================================================================

    def handle(self, error: Exception, context: ErrorContext | None = None) -> Any:
        """
        处理错误

        Args:
            error: 异常对象
            context: 错误上下文

        Returns:
            处理结果
        """
        # 填充上下文
        if context is None:
            context = ErrorContext(error=error, source=self._context_source or "unknown")

        # 更新统计
        self._record_error(error, context)

        # 记录历史
        self._record_history(error, context)

        # 查找处理器
        handler = self._find_handler(type(error))

        if handler is not None:
            try:
                return handler(error, context)
            except Exception as e:
                # 处理器自身出错，调用默认处理器
                self._logger.error(f"Error handler raised exception: {e}")
                if self._default_handler:
                    return self._default_handler(error, context)
                return None
        elif self._default_handler:
            return self._default_handler(error, context)

        return None

    def _find_handler(self, error_type: type[Exception]) -> Callable | None:
        """
        查找错误处理器

        策略：
        1. 精确匹配
        2. 基类匹配（按 MRO 顺序）

        Args:
            error_type: 异常类型

        Returns:
            处理函数或 None
        """
        with self._lock:
            # 精确匹配
            if error_type in self._handlers:
                return self._handlers[error_type]

            # 基类匹配
            for cls in error_type.__mro__:
                if cls in self._handlers and cls != Exception and cls != BaseException:
                    return self._handlers[cls]

            return None

    def _record_error(self, error: Exception, context: ErrorContext) -> None:
        """记录错误到统计"""
        with self._lock:
            self._error_count += 1
            error_type = type(error).__name__
            self._error_stats[error_type] += 1

    def _record_history(self, error: Exception, context: ErrorContext) -> None:
        """记录错误到历史"""
        record = {
            "timestamp": time.time(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "source": context.source,
            "attempt": context.attempt,
        }

        if isinstance(error, NEMTError):
            record["error_code"] = error.code
            record["retryable"] = error.retryable
            record["severity"] = error.severity.value

        with self._lock:
            self._error_history.append(record)

    # ========================================================================
    # 错误上下文管理
    # ========================================================================

    @contextmanager
    def error_context(self, source: str):
        """
        错误上下文管理器

        Usage:
            with error_handler.error_context(source="execution"):
                risky_operation()

        Args:
            source: 错误来源
        """
        old_source = self._context_source
        self._context_source = source
        try:
            yield
        finally:
            self._context_source = old_source

    def get_current_source(self) -> str | None:
        """获取当前错误来源"""
        return self._context_source

    # ========================================================================
    # 恢复策略
    # ========================================================================

    def set_recovery_strategy(self, error_type: type[Exception], strategy: RecoveryStrategy) -> None:
        """
        设置错误恢复策略

        Args:
            error_type: 异常类型
            strategy: 恢复策略
        """
        with self._lock:
            self._recovery_strategies[error_type] = strategy

    def get_recovery_strategy(self, error: Exception) -> RecoveryStrategy:
        """
        获取错误恢复策略

        Args:
            error: 异常对象

        Returns:
            恢复策略
        """
        # 优先从 NEMTError 获取
        if isinstance(error, NEMTError):
            return error.get_recovery_strategy()

        # 从映射表获取
        with self._lock:
            for cls in type(error).__mro__:
                if cls in self._recovery_strategies:
                    return self._recovery_strategies[cls]

        # 默认：可重试的异常使用 RETRY
        if isinstance(error, (ConnectionError, TimeoutError)):
            return RecoveryStrategy.RETRY

        return RecoveryStrategy.PROPAGATE

    def is_retryable(self, error: Exception) -> bool:
        """
        判断错误是否可重试

        Args:
            error: 异常对象

        Returns:
            是否可重试
        """
        strategy = self.get_recovery_strategy(error)
        return strategy in (RecoveryStrategy.RETRY, RecoveryStrategy.FALLBACK)

    # ========================================================================
    # 告警
    # ========================================================================

    def register_alert_callback(self, callback: Callable[[NEMTError, ErrorContext], None]) -> None:
        """
        注册告警回调

        Args:
            callback: 告警回调函数
        """
        with self._lock:
            if callback not in self._alert_callbacks:
                self._alert_callbacks.append(callback)

    def unregister_alert_callback(self, callback: Callable) -> None:
        """
        注销告警回调

        Args:
            callback: 告警回调函数
        """
        with self._lock:
            if callback in self._alert_callbacks:
                self._alert_callbacks.remove(callback)

    def notify_alert(self, error: NEMTError, context: ErrorContext) -> None:
        """
        触发告警

        Args:
            error: NEMT 错误
            context: 错误上下文
        """
        if not self._enable_alert:
            return

        # 发送告警回调
        with self._lock:
            callbacks = list(self._alert_callbacks)

        for callback in callbacks:
            try:
                callback(error, context)
            except Exception as e:
                self._logger.error(f"Alert callback raised exception: {e}")

        # 发布到事件总线
        if self._event_bus is not None:
            try:
                self._event_bus.publish(
                    "system.alert",
                    {
                        "error": error.to_dict(),
                        "context": context.to_dict(),
                        "severity": error.severity.value,
                    },
                )
            except Exception as e:
                self._logger.error(f"Failed to publish alert event: {e}")

    def set_event_bus(self, event_bus) -> None:
        """
        设置事件总线（用于发布告警事件）

        Args:
            event_bus: EventBus 实例
        """
        self._event_bus = event_bus

    # ========================================================================
    # 统计和历史
    # ========================================================================

    def get_error_stats(self) -> dict[str, Any]:
        """
        获取错误统计

        Returns:
            错误统计字典
        """
        with self._lock:
            return {
                "total_errors": self._error_count,
                "error_stats": dict(self._error_stats),
                "history_size": len(self._error_history),
                "history_max": self._error_history.maxlen,
            }

    def get_error_history(self, error_type: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """
        获取错误历史

        Args:
            error_type: 按错误类型过滤（可选）
            limit: 返回数量限制

        Returns:
            错误历史列表
        """
        with self._lock:
            history = list(self._error_history)

        if error_type:
            history = [r for r in history if r.get("error_type") == error_type]

        return history[-limit:]

    def clear_history(self) -> None:
        """清除错误历史"""
        with self._lock:
            self._error_history.clear()

    def reset_stats(self) -> None:
        """重置统计"""
        with self._lock:
            self._error_count = 0
            self._error_stats.clear()

    # ========================================================================
    # 便捷方法
    # ========================================================================

    def __call__(self, error: Exception, context: ErrorContext | None = None) -> Any:
        """
        便捷调用接口

        Usage:
            handler = ErrorHandler.get_instance()
            handler(error)  # 等价于 handler.handle(error)
        """
        return self.handle(error, context)

    def __repr__(self) -> str:
        return (
            f"ErrorHandler("
            f"errors={self._error_count}, "
            f"handlers={len(self._handlers)}, "
            f"history={len(self._error_history)}"
            f")"
        )


# ============================================================================
# 模块级错误处理器实例
# ============================================================================

_default_handler: ErrorHandler | None = None
_default_handler_lock = threading.Lock()


# ============================================================================
# 便捷函数
# ============================================================================


def get_error_handler() -> ErrorHandler:
    """获取模块级错误处理器实例"""
    global _default_handler
    if _default_handler is None:
        with _default_handler_lock:
            if _default_handler is None:
                _default_handler = ErrorHandler()
    return _default_handler


def reset_error_handler() -> None:
    """重置模块级错误处理器（用于测试）"""
    global _default_handler
    with _default_handler_lock:
        _default_handler = None


@contextmanager
def error_context(source: str):
    """
    便捷错误上下文管理器

    Usage:
        with error_context("my_module"):
            risky_operation()
    """
    handler = get_error_handler()
    with handler.error_context(source):
        yield


def handle_error(error: Exception, source: str | None = None) -> Any:
    """
    便捷错误处理

    Usage:
        try:
            risky_operation()
        except Exception as e:
            handle_error(e, source="my_module")

    Args:
        error: 异常对象
        source: 错误来源

    Returns:
        处理结果
    """
    handler = get_error_handler()
    context = ErrorContext(error=error, source=source or "unknown")
    return handler.handle(error, context)
