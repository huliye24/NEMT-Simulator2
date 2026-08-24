"""
NEMT Python SDK

提供 Python 客户端 SDK。
"""

from dataclasses import dataclass

import requests

__all__ = ["NEMTClient", "NEMTConfig"]


@dataclass
class NEMTConfig:
    """NEMT 配置"""

    api_url: str = "http://localhost:8080"
    api_key: str = ""
    timeout: float = 30.0


class NEMTClient:
    """
    NEMT Python 客户端

    示例:
    ```python
    client = NEMTClient(
        api_url="http://localhost:8080",
        api_key="your-api-key"
    )

    # 获取胶囊列表
    capsules = client.get_capsules()

    # 获取策略列表
    strategies = client.get_strategies()

    # 创建策略
    strategy = client.create_strategy({
        "name": "My Strategy",
        "type": "trend",
        "params": {"threshold": 0.5}
    })

    # 运行回测
    result = client.run_backtest(strategy["strategy_id"], {
        "symbol": "BTC",
        "interval": "1h",
        "start_time": "2024-01-01",
        "end_time": "2024-12-31"
    })
    ```
    """

    def __init__(self, config: NEMTConfig = None):
        self.config = config or NEMTConfig()
        self._session = requests.Session()
        if self.config.api_key:
            self._session.headers["X-API-Key"] = self.config.api_key

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """发送请求"""
        url = f"{self.config.api_url}{path}"
        kwargs.setdefault("timeout", self.config.timeout)

        response = self._session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    # ========================================================================
    # 系统
    # ========================================================================

    def health(self) -> dict:
        """健康检查"""
        return self._request("GET", "/health")

    def ready(self) -> dict:
        """就绪检查"""
        return self._request("GET", "/ready")

    # ========================================================================
    # 胶囊
    # ========================================================================

    def get_capsules(self) -> list[dict]:
        """获取所有胶囊"""
        return self._request("GET", "/api/v1/capsules")

    def get_capsule(self, capsule_id: str) -> dict:
        """获取胶囊详情"""
        return self._request("GET", f"/api/v1/capsules/{capsule_id}")

    def start_capsule(self, capsule_id: str) -> dict:
        """启动胶囊"""
        return self._request("POST", f"/api/v1/capsules/{capsule_id}/start")

    def stop_capsule(self, capsule_id: str) -> dict:
        """停止胶囊"""
        return self._request("POST", f"/api/v1/capsules/{capsule_id}/stop")

    def get_capsule_metrics(self, capsule_id: str) -> dict:
        """获取胶囊指标"""
        return self._request("GET", f"/api/v1/capsules/{capsule_id}/metrics")

    # ========================================================================
    # 策略
    # ========================================================================

    def get_strategies(self) -> list[dict]:
        """获取所有策略"""
        return self._request("GET", "/api/v1/strategies")

    def get_strategy(self, strategy_id: str) -> dict:
        """获取策略详情"""
        return self._request("GET", f"/api/v1/strategies/{strategy_id}")

    def create_strategy(self, data: dict) -> dict:
        """创建策略"""
        return self._request("POST", "/api/v1/strategies", json=data)

    def update_strategy(self, strategy_id: str, data: dict) -> dict:
        """更新策略"""
        return self._request("PUT", f"/api/v1/strategies/{strategy_id}", json=data)

    def delete_strategy(self, strategy_id: str) -> dict:
        """删除策略"""
        return self._request("DELETE", f"/api/v1/strategies/{strategy_id}")

    def run_backtest(self, strategy_id: str, config: dict) -> dict:
        """运行回测"""
        return self._request("POST", f"/api/v1/strategies/{strategy_id}/backtest", json=config)

    # ========================================================================
    # 市场数据
    # ========================================================================

    def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
        start_time: str = None,
        end_time: str = None,
    ) -> list[dict]:
        """获取K线数据"""
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        return self._request("GET", "/api/v1/market/klines", params=params)

    def get_ticker(self, symbol: str) -> dict:
        """获取行情"""
        return self._request("GET", "/api/v1/market/ticker", params={"symbol": symbol})

    def get_orderbook(self, symbol: str, limit: int = 20) -> dict:
        """获取订单簿"""
        return self._request("GET", "/api/v1/market/orderbook", params={"symbol": symbol, "limit": limit})

    # ========================================================================
    # 回测
    # ========================================================================

    def get_backtests(self) -> list[dict]:
        """获取回测列表"""
        return self._request("GET", "/api/v1/backtests")

    def get_backtest(self, backtest_id: str) -> dict:
        """获取回测结果"""
        return self._request("GET", f"/api/v1/backtests/{backtest_id}")

    def delete_backtest(self, backtest_id: str) -> dict:
        """删除回测"""
        return self._request("DELETE", f"/api/v1/backtests/{backtest_id}")

    # ========================================================================
    # 指标
    # ========================================================================

    def get_metrics(self) -> str:
        """获取 Prometheus 指标"""
        response = self._session.get(f"{self.config.api_url}/metrics", timeout=self.config.timeout)
        return response.text


# 便捷函数
def create_client(api_url: str = None, api_key: str = None) -> NEMTClient:
    """创建客户端"""
    config = NEMTConfig(api_url=api_url or "http://localhost:8080", api_key=api_key or "")
    return NEMTClient(config)
