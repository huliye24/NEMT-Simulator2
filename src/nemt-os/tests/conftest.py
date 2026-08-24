"""
Test Framework - 测试框架

提供测试环境搭建和测试工具。
"""

import os
import shutil
import sys
import tempfile
from collections.abc import Callable
from typing import Any

import pytest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

__all__ = [
    "TestEnvironment",
    "MockEventBus",
    "MockConfigCenter",
    "MockStorage",
    "create_test_container",
    "pytest_configure",
]


# ========================================================================
# 测试环境
# ========================================================================


class TestEnvironment:
    """
    测试环境管理器

    示例:
    ```python
    def test_my_feature():
        with TestEnvironment() as env:
            # 测试代码
            result = env.capsule.exec()
            assert result is not None
    ```
    """

    def __init__(self):
        self.temp_dir = None
        self.event_bus = None
        self.config_center = None
        self.storage = None
        self.container = None
        self._cleanup_callbacks: list[Callable] = []

    def __enter__(self):
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()

        # 初始化组件
        self._init_components()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 执行清理回调
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception:
                pass

        # 清理临时目录
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _init_components(self):
        """初始化测试组件"""
        from nemt.core.config_center import ConfigCenter
        from nemt.core.di import DIContainer
        from nemt.core.event_bus import EventBus
        from nemt.core.storage.sqlite_storage import SQLiteStorage

        # EventBus
        self.event_bus = EventBus()

        # ConfigCenter
        self.config_center = ConfigCenter()

        # Storage
        db_path = os.path.join(self.temp_dir, "test.db")
        self.storage = SQLiteStorage(db_path=db_path)

        # DI Container
        self.container = DIContainer()
        self.container.register_instance(type(self.event_bus), self.event_bus)
        self.container.register_instance(type(self.config_center), self.config_center)
        self.container.register_instance(type(self.storage), self.storage)

    def cleanup(self, callback: Callable) -> None:
        """添加清理回调"""
        self._cleanup_callbacks.append(callback)


# ========================================================================
# Mock 对象
# ========================================================================


class MockEventBus:
    """Mock EventBus"""

    def __init__(self):
        self.events: list[dict[str, Any]] = []
        self.subscriptions: dict[str, list[Callable]] = {}
        self.published_count = 0

    def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = []
        self.subscriptions[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        if event_type in self.subscriptions:
            self.subscriptions[event_type].remove(handler)

    def publish(self, event_type: str, data: Any = None, source: str = "", priority=None) -> None:
        self.published_count += 1
        event = {"type": event_type, "data": data, "source": source}
        self.events.append(event)

        # 通知订阅者
        if event_type in self.subscriptions:
            for handler in self.subscriptions[event_type]:
                handler(event)

    def clear(self, event_type: str = None) -> None:
        if event_type:
            self.events = [e for e in self.events if e["type"] != event_type]
        else:
            self.events.clear()
            self.subscriptions.clear()

    def get_events(self, event_type: str = None) -> list[dict]:
        if event_type:
            return [e for e in self.events if e["type"] == event_type]
        return self.events

    def get_stats(self) -> dict[str, Any]:
        return {
            "published_count": self.published_count,
            "events_count": len(self.events),
            "subscriptions_count": len(self.subscriptions),
        }


class MockConfigCenter:
    """Mock ConfigCenter"""

    def __init__(self, initial_config: dict[str, Any] = None):
        self._config: dict[str, Any] = initial_config or {}
        self._watchers: dict[str, list[Callable]] = {}
        self._history: list[dict[str, Any]] = []

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any, notify: bool = True, validate: bool = True) -> bool:
        old_value = self._config.get(key)
        self._config[key] = value

        self._history.append(
            {
                "key": key,
                "old_value": old_value,
                "new_value": value,
            }
        )

        if notify and key in self._watchers:
            for callback in self._watchers[key]:
                callback(key, old_value, value)

        return True

    def has(self, key: str) -> bool:
        return key in self._config

    def delete(self, key: str) -> bool:
        if key in self._config:
            del self._config[key]
            return True
        return False

    def get_keys(self, pattern: str = None) -> list[str]:
        if pattern is None:
            return list(self._config.keys())
        import fnmatch

        return [k for k in self._config.keys() if fnmatch.fnmatch(k, pattern)]

    def get_all(self) -> dict[str, Any]:
        return self._config.copy()

    def watch(self, key: str, callback: Callable) -> None:
        if key not in self._watchers:
            self._watchers[key] = []
        self._watchers[key].append(callback)

    def clear(self) -> None:
        self._config.clear()
        self._history.clear()

    def get_history(self) -> list[dict]:
        return self._history.copy()


class MockStorage:
    """Mock Storage"""

    def __init__(self):
        self._klines: dict[str, list[dict]] = {}
        self._strategies: dict[str, dict] = {}
        self._backtests: dict[str, dict] = {}
        self._configs: dict[str, Any] = {}

    def save_klines(self, klines: list[Any]) -> int:
        for kline in klines:
            symbol = kline.get("symbol", "UNKNOWN")
            if symbol not in self._klines:
                self._klines[symbol] = []
            self._klines[symbol].append(kline)
        return len(klines)

    def get_klines(
        self, symbol: str, interval: str = "1h", start_time=None, end_time=None, limit: int = 1000
    ) -> list[Any]:
        klines = self._klines.get(symbol, [])
        if start_time:
            klines = [k for k in klines if k.get("timestamp", 0) >= start_time]
        if end_time:
            klines = [k for k in klines if k.get("timestamp", 0) <= end_time]
        return klines[-limit:]

    def save_strategy(
        self, strategy_id: str, name: str, strategy_type: str, params: dict, status: str = "alive"
    ) -> bool:
        self._strategies[strategy_id] = {
            "id": strategy_id,
            "name": name,
            "type": strategy_type,
            "params": params,
            "status": status,
        }
        return True

    def get_strategy(self, strategy_id: str) -> dict | None:
        return self._strategies.get(strategy_id)

    def list_strategies(self, status: str = None) -> list[dict]:
        if status:
            return [s for s in self._strategies.values() if s.get("status") == status]
        return list(self._strategies.values())

    def save_backtest(
        self,
        backtest_id: str,
        strategy_id: str | None,
        config: dict,
        metrics=None,
        equity_curve=None,
        trades=None,
        status: str = "completed",
    ) -> bool:
        self._backtests[backtest_id] = {
            "id": backtest_id,
            "strategy_id": strategy_id,
            "config": config,
            "metrics": metrics,
            "equity_curve": equity_curve,
            "trades": trades,
            "status": status,
        }
        return True

    def get_backtest(self, backtest_id: str) -> dict | None:
        return self._backtests.get(backtest_id)

    def set_config(self, key: str, value: Any) -> bool:
        self._configs[key] = value
        return True

    def get_config(self, key: str, default: Any = None) -> Any:
        return self._configs.get(key, default)

    def close(self) -> None:
        pass


# ========================================================================
# 测试容器
# ========================================================================


def create_test_container() -> Any:
    """创建测试容器"""
    from nemt.core.di import DIContainer

    container = DIContainer()

    # 注册 Mock 组件
    container.register_instance(MockEventBus, MockEventBus())
    container.register_instance(MockConfigCenter, MockConfigCenter())
    container.register_instance(MockStorage, MockStorage())

    return container


# ========================================================================
# Pytest 配置
# ========================================================================


def pytest_configure(config):
    """Pytest 配置钩子"""
    # 设置测试环境变量
    os.environ["NEMT_ENV"] = "test"
    os.environ["NEMT_LOG_LEVEL"] = "DEBUG"


@pytest.fixture
def test_env():
    """测试环境 fixture"""
    with TestEnvironment() as env:
        yield env


@pytest.fixture
def mock_event_bus():
    """Mock EventBus fixture"""
    return MockEventBus()


@pytest.fixture
def mock_config():
    """Mock ConfigCenter fixture"""
    return MockConfigCenter()


@pytest.fixture
def mock_storage():
    """Mock Storage fixture"""
    return MockStorage()


@pytest.fixture
def test_container():
    """测试容器 fixture"""
    return create_test_container()
