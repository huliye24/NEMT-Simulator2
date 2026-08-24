"""
IStorage - 存储接口定义

定义数据存储的标准接口。
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IStorage(Protocol):
    """
    存储接口

    定义数据存储的标准操作。
    """

    def save_klines(self, klines: list[Any]) -> int:
        """
        保存K线数据

        Args:
            klines: K线数据列表

        Returns:
            保存的记录数
        """
        ...

    def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        start_time: Any = None,
        end_time: Any = None,
        limit: int = 1000,
    ) -> list[Any]:
        """
        获取K线数据

        Args:
            symbol: 交易对
            interval: K线周期
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制

        Returns:
            K线数据列表
        """
        ...

    def save_strategy(
        self,
        strategy_id: str,
        name: str,
        strategy_type: str,
        params: dict[str, Any],
        status: str = "alive",
    ) -> bool:
        """
        保存策略配置

        Args:
            strategy_id: 策略ID
            name: 策略名称
            strategy_type: 策略类型
            params: 策略参数
            status: 状态

        Returns:
            是否成功
        """
        ...

    def get_strategy(self, strategy_id: str) -> dict[str, Any] | None:
        """
        获取策略配置

        Args:
            strategy_id: 策略ID

        Returns:
            策略配置字典
        """
        ...

    def list_strategies(self, status: str = None) -> list[dict[str, Any]]:
        """
        列出所有策略

        Args:
            status: 过滤状态

        Returns:
            策略列表
        """
        ...

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
        """
        保存回测结果

        Args:
            backtest_id: 回测ID
            strategy_id: 策略ID
            config: 配置
            metrics: 指标
            equity_curve: 权益曲线
            trades: 交易列表
            status: 状态

        Returns:
            是否成功
        """
        ...

    def get_backtest(self, backtest_id: str) -> dict[str, Any] | None:
        """
        获取回测结果

        Args:
            backtest_id: 回测ID

        Returns:
            回测结果字典
        """
        ...

    def set_config(self, key: str, value: Any) -> bool:
        """
        设置系统配置

        Args:
            key: 配置键
            value: 配置值

        Returns:
            是否成功
        """
        ...

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取系统配置

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        ...

    def close(self) -> None:
        """关闭存储"""
        ...


class IKVStorage(Protocol):
    """键值存储接口"""

    def set(self, key: str, value: Any) -> bool:
        """设置值"""
        ...

    def get(self, key: str, default: Any = None) -> Any:
        """获取值"""
        ...

    def delete(self, key: str) -> bool:
        """删除键"""
        ...

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        ...

    def keys(self, pattern: str = "*") -> list[str]:
        """获取所有键"""
        ...


class IDocumentStorage(Protocol):
    """文档存储接口"""

    def insert(self, collection: str, document: dict[str, Any]) -> str:
        """插入文档"""
        ...

    def find(self, collection: str, query: dict[str, Any]) -> list[dict[str, Any]]:
        """查询文档"""
        ...

    def update(self, collection: str, query: dict[str, Any], update: dict[str, Any]) -> int:
        """更新文档"""
        ...

    def delete(self, collection: str, query: dict[str, Any]) -> int:
        """删除文档"""
        ...
