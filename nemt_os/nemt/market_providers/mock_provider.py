"""
Mock 市场数据提供者 (Mock Market Provider)
用于测试和开发阶段，返回模拟数据
"""

import random
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from threading import Thread, Lock

from .base import BaseMarketProvider, MarketData, KLine


class MockMarketProvider(BaseMarketProvider):
    """
    Mock 市场数据提供者
    
    生成模拟的K线和实时数据，用于:
    - 开发测试
    - UI 演示
    - 回测验证
    """

    # 默认模拟的交易对
    DEFAULT_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']
    
    # 默认价格
    DEFAULT_PRICES = {
        'BTCUSDT': 67500.0,
        'ETHUSDT': 3450.0,
        'BNBUSDT': 580.0,
        'SOLUSDT': 145.0
    }

    def __init__(
        self, 
        name: str = "MockProvider",
        base_prices: Optional[Dict[str, float]] = None,
        volatility: float = 0.002
    ):
        super().__init__(name)
        self._base_prices = base_prices or self.DEFAULT_PRICES.copy()
        self._volatility = volatility  # 价格波动幅度
        self._current_prices: Dict[str, float] = self._base_prices.copy()
        self._kline_cache: Dict[str, List[KLine]] = {}
        self._lock = Lock()
        self._running = False
        self._tick_thread: Optional[Thread] = None

    def connect(self) -> bool:
        """连接模拟数据源"""
        if self._is_connected:
            return True
        
        print(f"[{self.name}] Connecting to mock data source...")
        time.sleep(0.1)  # 模拟连接延迟
        
        self._is_connected = True
        self._running = True
        
        # 启动模拟tick
        self._tick_thread = Thread(target=self._tick_loop, daemon=True)
        self._tick_thread.start()
        
        print(f"[{self.name}] Connected successfully")
        return True

    def disconnect(self) -> None:
        """断开模拟连接"""
        if not self._is_connected:
            return
        
        self._running = False
        if self._tick_thread:
            self._tick_thread.join(timeout=1)
        
        self._is_connected = False
        print(f"[{self.name}] Disconnected")

    def _tick_loop(self) -> None:
        """模拟价格tick循环"""
        while self._running:
            try:
                # 更新所有交易对的价格
                with self._lock:
                    for symbol in self._current_prices:
                        change_pct = random.gauss(0, self._volatility)
                        self._current_prices[symbol] *= (1 + change_pct)
                        
                        # 生成新的K线数据
                        kline = self._generate_kline(symbol)
                        if symbol not in self._kline_cache:
                            self._kline_cache[symbol] = []
                        self._kline_cache[symbol].append(kline)
                        
                        # 只保留最近100条
                        if len(self._kline_cache[symbol]) > 100:
                            self._kline_cache[symbol] = self._kline_cache[symbol][-100:]
                        
                        # 通知订阅者
                        self._notify_subscribers(symbol, kline)
                
                time.sleep(1)  # 每秒更新一次
            except Exception as e:
                print(f"[WARN] Tick loop error: {e}")

    def _generate_kline(self, symbol: str, interval: str = "1h") -> KLine:
        """生成一条K线"""
        base_price = self._current_prices.get(symbol, 67000.0)
        
        # 生成随机OHLC
        open_price = base_price * random.uniform(0.998, 1.002)
        close_price = base_price * random.uniform(0.998, 1.002)
        high_price = max(open_price, close_price) * random.uniform(1.0, 1.003)
        low_price = min(open_price, close_price) * random.uniform(0.997, 1.0)
        volume = random.uniform(100, 10000) * (base_price / 1000)
        
        return KLine(
            timestamp=datetime.now(),
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=volume,
            symbol=symbol,
            interval=interval
        )

    def get_latest(self, symbol: str, interval: str = "1h") -> Optional[KLine]:
        """获取最新K线"""
        if not self._is_connected:
            return None
        
        if symbol not in self._current_prices:
            print(f"[WARN] Unknown symbol: {symbol}")
            return None
        
        with self._lock:
            return self._generate_kline(symbol, interval)

    def get_history(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[KLine]:
        """获取历史K线"""
        if not self._is_connected:
            return []
        
        if symbol not in self._current_prices:
            return []
        
        # 生成模拟历史数据
        klines = []
        base_price = self._base_prices.get(symbol, 67000.0)
        current_time = end_time or datetime.now()
        
        for i in range(limit):
            # 逆向生成历史数据
            timestamp = current_time - timedelta(hours=limit - i)
            price_factor = 1 + random.uniform(-0.05, 0.05) * (i / limit)
            price = base_price * price_factor
            
            open_price = price * random.uniform(0.998, 1.002)
            close_price = price * random.uniform(0.998, 1.002)
            high_price = max(open_price, close_price) * random.uniform(1.0, 1.002)
            low_price = min(open_price, close_price) * random.uniform(0.998, 1.0)
            volume = random.uniform(100, 10000) * (price / 1000)
            
            klines.append(KLine(
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
                symbol=symbol,
                interval=interval
            ))
        
        return klines

    def get_ticker(self, symbol: str) -> Optional[MarketData]:
        """获取实时行情"""
        if not self._is_connected:
            return None
        
        if symbol not in self._current_prices:
            return None
        
        with self._lock:
            price = self._current_prices[symbol]
            base_price = self._base_prices.get(symbol, price)
            
            change_24h = price - base_price
            change_pct = (change_24h / base_price) * 100 if base_price > 0 else 0
            
            return MarketData(
                symbol=symbol,
                price=price,
                bid=price * 0.9999,
                ask=price * 1.0001,
                volume=random.uniform(1000000, 10000000),
                timestamp=datetime.now(),
                change_24h=change_24h,
                change_pct_24h=change_pct,
                high_24h=price * 1.02,
                low_24h=price * 0.98
            )

    def get_all_tickers(self) -> List[MarketData]:
        """获取所有交易对的行情"""
        return [self.get_ticker(symbol) for symbol in self._current_prices.keys()]

    def get_status(self) -> Dict[str, Any]:
        """获取Mock提供者状态"""
        status = super().get_status()
        status.update({
            'prices': self._current_prices.copy(),
            'kline_cache_size': {symbol: len(klines) for symbol, klines in self._kline_cache.items()}
        })
        return status


class DeterministicMockProvider(MockMarketProvider):
    """
    确定性Mock提供者
    
    使用固定的种子生成可重复的数据，用于:
    - 单元测试
    - 回测复现
    """

    def __init__(self, seed: int = 42, **kwargs):
        super().__init__(**kwargs)
        self._seed = seed
        random.seed(seed)
        
    def _generate_with_seed(self) -> float:
        """使用种子生成随机数"""
        return random.uniform(0, 1)
