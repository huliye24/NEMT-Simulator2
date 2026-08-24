"""
Binance 市场数据提供者 (Binance Market Provider)
支持 REST API 历史数据 + WebSocket 实时数据流
"""

import requests
import json
import time
import threading
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Callable
from websocket import create_connection, WebSocketTimeoutException, WebSocketConnectionClosedException
import asyncio

from .base import BaseMarketProvider, MarketData, KLine


class BinanceMarketProvider(BaseMarketProvider):
    """
    Binance 市场数据提供者

    功能:
    - REST API 获取历史K线
    - WebSocket 获取实时K线
    - 自动重连机制
    - 多交易对订阅
    """

    REST_BASE_URL = "https://api.binance.com/api/v3"
    WS_BASE_URL = "wss://stream.binance.com:9443/ws"

    # 支持的K线周期
    INTERVALS = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "6h": "6h",
        "8h": "8h",
        "12h": "12h",
        "1d": "1d",
        "3d": "3d",
        "1w": "1w",
    }

    def __init__(
        self,
        name: str = "BinanceProvider",
        symbols: Optional[List[str]] = None,
        default_interval: str = "1h",
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Args:
            name: 提供者名称
            symbols: 默认交易对列表
            default_interval: 默认K线周期
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)
        """
        super().__init__(name)
        self._symbols = symbols or ["BTCUSDT", "ETHUSDT"]
        self._default_interval = default_interval
        self._max_retries = max_retries
        self._retry_delay = retry_delay

        # WebSocket 相关
        self._ws = None
        self._ws_thread: Optional[threading.Thread] = None
        self._ws_running = False
        self._ws_lock = threading.Lock()

        # 缓存
        self._latest_klines: Dict[str, KLine] = {}
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "NEMT-Simulator/1.0", "Content-Type": "application/json"})

    def connect(self) -> bool:
        """
        连接到 Binance API

        Returns:
            bool: 连接是否成功
        """
        if self._is_connected:
            return True

        print(f"[{self.name}] Connecting to Binance API...")

        # 测试 REST API 连接
        try:
            response = self._session.get(f"{self.REST_BASE_URL}/exchangeInfo", timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[{self.name}] REST API connection failed: {e}")
            return False

        self._is_connected = True
        print(f"[{self.name}] Connected to Binance REST API")

        return True

    def disconnect(self) -> None:
        """断开与 Binance 的连接"""
        # 停止 WebSocket
        self._stop_websocket()

        self._is_connected = False
        self._session.close()
        print(f"[{self.name}] Disconnected")

    def _stop_websocket(self) -> None:
        """停止 WebSocket 连接"""
        self._ws_running = False

        with self._ws_lock:
            if self._ws:
                try:
                    self._ws.close()
                except Exception:
                    pass
                self._ws = None

        if self._ws_thread and self._ws_thread.is_alive():
            self._ws_thread.join(timeout=2)

    def _request_with_retry(
        self, method: str, endpoint: str, params: Optional[Dict] = None, retries: Optional[int] = None
    ) -> Optional[Dict]:
        """
        带重试的请求

        Args:
            method: HTTP 方法
            endpoint: API 端点
            params: 请求参数
            retries: 重试次数

        Returns:
            响应数据或 None
        """
        retries = retries or self._max_retries

        for attempt in range(retries):
            try:
                url = f"{self.REST_BASE_URL}/{endpoint}"
                response = self._session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt < retries - 1:
                    time.sleep(self._retry_delay * (attempt + 1))
                else:
                    print(f"[{self.name}] Request failed after {retries} attempts: {e}")
                    return None

        return None

    def get_latest(self, symbol: str, interval: str = "1h") -> Optional[KLine]:
        """
        获取最新K线数据

        Args:
            symbol: 交易对符号，如 'BTCUSDT'
            interval: K线周期

        Returns:
            KLine: 最新K线数据
        """
        if not self._is_connected:
            return None

        # 使用 get_history 获取最后一条
        klines = self.get_history(symbol, interval, limit=1)
        return klines[-1] if klines else None

    def get_history(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[KLine]:
        """
        获取历史K线数据

        Args:
            symbol: 交易对符号
            interval: K线周期
            limit: 获取数量上限 (1-1000)
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            List[KLine]: K线数据列表
        """
        if not self._is_connected:
            return []

        params = {"symbol": symbol.upper(), "interval": interval, "limit": min(limit, 1000)}

        if start_time:
            params["startTime"] = int(start_time.timestamp() * 1000)
        if end_time:
            params["endTime"] = int(end_time.timestamp() * 1000)

        data = self._request_with_retry("GET", "klines", params)
        if not data:
            return []

        klines = []
        for item in data:
            kline = self._parse_kline(item, symbol, interval)
            klines.append(kline)

        return klines

    def get_history_by_days(self, symbol: str, interval: str = "1h", days: int = 7) -> List[KLine]:
        """
        获取最近N天的K线数据（自动分页）

        Args:
            symbol: 交易对符号
            interval: K线周期
            days: 天数

        Returns:
            List[KLine]: K线数据列表
        """
        all_klines = []
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

        limit = 1000
        interval_ms = self._interval_to_ms(interval)

        while start_time < end_time:
            fetch_until = min(start_time + limit * interval_ms, end_time)

            klines = self.get_history(
                symbol=symbol,
                interval=interval,
                limit=limit,
                start_time=datetime.fromtimestamp(start_time / 1000),
                end_time=datetime.fromtimestamp(fetch_until / 1000),
            )

            if not klines:
                break

            all_klines.extend(klines)
            start_time = int(klines[-1].timestamp.timestamp() * 1000) + interval_ms

            if len(klines) < limit:
                break

            time.sleep(0.2)  # 避免API限流

        return all_klines

    def _parse_kline(self, item: List, symbol: str, interval: str) -> KLine:
        """解析K线数据"""
        return KLine(
            timestamp=datetime.fromtimestamp(item[0] / 1000),
            open=float(item[1]),
            high=float(item[2]),
            low=float(item[3]),
            close=float(item[4]),
            volume=float(item[5]),
            symbol=symbol,
            interval=interval,
        )

    def get_ticker(self, symbol: str) -> Optional[MarketData]:
        """
        获取实时行情

        Args:
            symbol: 交易对符号

        Returns:
            MarketData: 市场数据
        """
        if not self._is_connected:
            return None

        params = {"symbol": symbol.upper()}
        data = self._request_with_retry("GET", "ticker/24hr", params)
        if not data:
            return None

        return MarketData(
            symbol=symbol,
            price=float(data.get("lastPrice", 0)),
            bid=float(data.get("bidPrice", 0)),
            ask=float(data.get("askPrice", 0)),
            volume=float(data.get("volume", 0)),
            timestamp=datetime.now(),
            change_24h=float(data.get("priceChange", 0)),
            change_pct_24h=float(data.get("priceChangePercent", 0)),
            high_24h=float(data.get("highPrice", 0)),
            low_24h=float(data.get("lowPrice", 0)),
        )

    def get_all_tickers(self) -> List[MarketData]:
        """获取所有交易对的24小时行情"""
        if not self._is_connected:
            return []

        data = self._request_with_retry("GET", "ticker/24hr")
        if not data:
            return []

        tickers = []
        for item in data:
            if item.get("symbol", "").endswith(("USDT", "BTC", "ETH", "BNB")):
                tickers.append(
                    MarketData(
                        symbol=item["symbol"],
                        price=float(item.get("lastPrice", 0)),
                        bid=float(item.get("bidPrice", 0)),
                        ask=float(item.get("askPrice", 0)),
                        volume=float(item.get("volume", 0)),
                        timestamp=datetime.now(),
                        change_24h=float(item.get("priceChange", 0)),
                        change_pct_24h=float(item.get("priceChangePercent", 0)),
                        high_24h=float(item.get("highPrice", 0)),
                        low_24h=float(item.get("lowPrice", 0)),
                    )
                )

        return tickers

    def subscribe_websocket(self, symbols: Optional[List[str]] = None, intervals: Optional[List[str]] = None) -> bool:
        """
        订阅 WebSocket 实时K线

        Args:
            symbols: 交易对列表
            intervals: K线周期列表

        Returns:
            bool: 订阅是否成功
        """
        if not self._is_connected:
            print(f"[{self.name}] Not connected")
            return False

        symbols = symbols or self._symbols
        intervals = intervals or [self._default_interval]

        # 构建订阅消息
        streams = []
        for symbol in symbols:
            for interval in intervals:
                streams.append(f"{symbol.lower()}@kline_{interval}")

        if not streams:
            return False

        self._ws_running = True

        def ws_thread_target():
            while self._ws_running:
                try:
                    ws_url = f"{self.WS_BASE_URL}/{'/'.join(streams)}"
                    ws = create_connection(ws_url, timeout=10)

                    with self._ws_lock:
                        self._ws = ws

                    print(f"[{self.name}] WebSocket connected: {len(streams)} streams")

                    while self._ws_running:
                        try:
                            data = ws.recv()
                            self._handle_websocket_message(data)
                        except WebSocketTimeoutException:
                            continue
                        except WebSocketConnectionClosedException:
                            break
                        except Exception as e:
                            print(f"[{self.name}] WebSocket error: {e}")
                            break

                except Exception as e:
                    print(f"[{self.name}] WebSocket connection failed: {e}")
                    if self._ws_running:
                        time.sleep(5)  # 重连等待

        self._ws_thread = threading.Thread(target=ws_thread_target, daemon=True)
        self._ws_thread.start()

        return True

    def _handle_websocket_message(self, message: str) -> None:
        """处理 WebSocket 消息"""
        try:
            data = json.loads(message)

            if "e" in data and data["e"] == "kline":
                kline_data = data["k"]
                symbol = data["s"]

                kline = KLine(
                    timestamp=datetime.fromtimestamp(kline_data["t"] / 1000),
                    open=float(kline_data["o"]),
                    high=float(kline_data["h"]),
                    low=float(kline_data["l"]),
                    close=float(kline_data["c"]),
                    volume=float(kline_data["v"]),
                    symbol=symbol,
                    interval=kline_data["i"],
                )

                # 更新缓存
                self._latest_klines[symbol] = kline

                # 通知订阅者
                self._notify_subscribers(symbol, kline)

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            pass  # 忽略解析错误

    def unsubscribe_websocket(self) -> None:
        """取消订阅 WebSocket"""
        self._stop_websocket()
        self._latest_klines.clear()

    def get_cached_kline(self, symbol: str) -> Optional[KLine]:
        """获取缓存的最新K线"""
        return self._latest_klines.get(symbol)

    @staticmethod
    def _interval_to_ms(interval: str) -> int:
        """将interval转换为毫秒"""
        mapping = {
            "1m": 60 * 1000,
            "5m": 5 * 60 * 1000,
            "15m": 15 * 60 * 1000,
            "30m": 30 * 60 * 1000,
            "1h": 60 * 60 * 1000,
            "2h": 2 * 60 * 60 * 1000,
            "4h": 4 * 60 * 60 * 1000,
            "6h": 6 * 60 * 60 * 1000,
            "8h": 8 * 60 * 60 * 1000,
            "12h": 12 * 60 * 60 * 1000,
            "1d": 24 * 60 * 60 * 1000,
            "3d": 3 * 24 * 60 * 60 * 1000,
            "1w": 7 * 24 * 60 * 60 * 1000,
        }
        return mapping.get(interval, 60 * 1000)

    def get_status(self) -> Dict[str, Any]:
        """获取提供者状态"""
        status = super().get_status()
        status.update(
            {
                "symbols": self._symbols,
                "default_interval": self._default_interval,
                "websocket_running": self._ws_running,
                "cached_klines": len(self._latest_klines),
            }
        )
        return status


class BinanceKlinesIterator:
    """
    Binance K线数据迭代器
    用于遍历大量历史数据
    """

    def __init__(self, symbol: str, interval: str = "1h", days: int = 365):
        self.provider = BinanceMarketProvider()
        self.symbol = symbol
        self.interval = interval
        self.end_time = int(datetime.now().timestamp() * 1000)
        self.start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        self.limit = 1000
        self.interval_ms = BinanceMarketProvider._interval_to_ms(interval)
        self._current_time = self.start_time

    def __iter__(self):
        return self

    def __next__(self) -> List[KLine]:
        if self._current_time >= self.end_time:
            raise StopIteration

        fetch_until = min(self._current_time + self.limit * self.interval_ms, self.end_time)

        klines = self.provider.get_history(
            symbol=self.symbol,
            interval=self.interval,
            limit=self.limit,
            start_time=datetime.fromtimestamp(self._current_time / 1000),
            end_time=datetime.fromtimestamp(fetch_until / 1000),
        )

        if not klines:
            raise StopIteration

        self._current_time = int(klines[-1].timestamp.timestamp() * 1000) + self.interval_ms
        time.sleep(0.2)

        return klines

    def connect(self) -> bool:
        return self.provider.connect()

    def disconnect(self):
        self.provider.disconnect()


# 便捷函数
def fetch_binance_data(
    symbol: str = "BTCUSDT", interval: str = "1h", days: int = 30, save_csv: Optional[str] = None
) -> List[KLine]:
    """
    便捷函数：获取 Binance K线数据

    Args:
        symbol: 交易对
        interval: K线周期
        days: 天数
        save_csv: 保存为CSV的路径

    Returns:
        K线数据列表
    """
    provider = BinanceMarketProvider()

    if not provider.connect():
        print("Failed to connect to Binance")
        return []

    print(f"Fetching {symbol} {interval} data for last {days} days...")

    klines = provider.get_history_by_days(symbol, interval, days)

    if klines:
        print(f"Fetched {len(klines)} klines")
        print(f"Time range: {klines[0].timestamp} ~ {klines[-1].timestamp}")

        if save_csv:
            import pandas as pd

            df = pd.DataFrame([k.to_dict() for k in klines])
            df.to_csv(save_csv, index=False)
            print(f"Saved to {save_csv}")
    else:
        print("No data fetched")

    provider.disconnect()
    return klines


def stream_binance_realtime(
    symbols: List[str], interval: str = "1h", on_kline: Optional[Callable[[KLine], None]] = None
) -> BinanceMarketProvider:
    """
    便捷函数：启动实时数据流

    Args:
        symbols: 交易对列表
        interval: K线周期
        on_kline: K线回调函数

    Returns:
        BinanceMarketProvider 实例，需要手动 disconnect
    """
    provider = BinanceMarketProvider(symbols=symbols, default_interval=interval)

    if not provider.connect():
        raise ConnectionError("Failed to connect to Binance")

    if on_kline:
        for symbol in symbols:
            provider.subscribe(symbol, on_kline)

    provider.subscribe_websocket(symbols=symbols, intervals=[interval])

    return provider
