"""
Storage 适配器

将现有的 SQLiteStorage 类适配到 IStorage 接口。
"""

from collections.abc import Iterator
from typing import Any

from nemt.core.interfaces.storage import IStorage
from nemt.core.storage.sqlite_storage import SQLiteStorage as OriginalSQLiteStorage


class SQLiteStorageAdapter(IStorage):
    """
    SQLiteStorage 适配器

    将原有 SQLiteStorage 实现适配到 IStorage 接口。
    """

    def __init__(self, original: OriginalSQLiteStorage):
        self._original = original

    def save_klines(self, klines: list[Any]) -> int:
        return self._original.save_klines(klines)

    def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        start_time: Any = None,
        end_time: Any = None,
        limit: int = 1000,
    ) -> list[Any]:
        return self._original.get_klines(symbol, interval, start_time, end_time, limit)

    def save_strategy(
        self,
        strategy_id: str,
        name: str,
        strategy_type: str,
        params: dict[str, Any],
        status: str = "alive",
    ) -> bool:
        return self._original.save_strategy(strategy_id, name, strategy_type, params, status)

    def get_strategy(self, strategy_id: str) -> dict[str, Any] | None:
        return self._original.get_strategy(strategy_id)

    def list_strategies(self, status: str = None) -> list[dict[str, Any]]:
        return self._original.list_strategies(status)

    def save_backtest(
        self,
        backtest_id: str,
        strategy_id: str | None,
        config: dict[str, Any],
        metrics: dict[str, Any] | None = None,
        equity_curve: list[float] | None = None,
        trades: list[dict[str, Any]] | None = None,
        status: str = "completed",
    ) -> bool:
        return self._original.save_backtest(backtest_id, strategy_id, config, metrics, equity_curve, trades, status)

    def get_backtest(self, backtest_id: str) -> dict[str, Any] | None:
        return self._original.get_backtest(backtest_id)

    def set_config(self, key: str, value: Any) -> bool:
        return self._original.set_config(key, value)

    def get_config(self, key: str, default: Any = None) -> Any:
        return self._original.get_config(key, default)

    def close(self) -> None:
        self._original.close()

    # ========================================================================
    # 便捷方法 (原有功能)
    # ========================================================================

    def get_klines_iterator(
        self,
        symbol: str,
        interval: str = "1h",
        start_time: Any = None,
        end_time: Any = None,
        batch_size: int = 1000,
    ) -> Iterator[list[Any]]:
        """分批获取 K线数据"""
        return self._original.get_klines_iterator(symbol, interval, start_time, end_time, batch_size)

    def list_backtests(self, limit: int = 100) -> list[dict[str, Any]]:
        """列出回测结果"""
        return self._original.list_backtests(limit)

    def update_strategy_status(self, strategy_id: str, status: str) -> bool:
        """更新策略状态"""
        return self._original.update_strategy_status(strategy_id, status)

    def save_signal(
        self,
        signal_id: str,
        signal_type: str,
        direction: str,
        symbol: str,
        confidence: float,
        reason: str,
        price: float,
        metadata: dict[str, Any] | None = None,
        timestamp: Any = None,
    ) -> bool:
        """保存信号"""
        return self._original.save_signal(
            signal_id, signal_type, direction, symbol, confidence, reason, price, metadata, timestamp
        )

    def get_signals(self, symbol: str = None, signal_type: str = None, limit: int = 100) -> list[dict[str, Any]]:
        """获取信号历史"""
        return self._original.get_signals(symbol, signal_type, limit)

    def get_all_configs(self) -> dict[str, Any]:
        """获取所有系统配置"""
        return self._original.get_all_configs()
