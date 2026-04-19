"""
市场数据抽象基类 (Base Market Provider)
定义所有市场数据提供者的标准接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class KLine:
    """K线数据结构"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str = ""
    interval: str = "1h"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'symbol': self.symbol,
            'interval': self.interval
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KLine':
        ts = data.get('timestamp')
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        elif isinstance(ts, (int, float)):
            ts = datetime.fromtimestamp(ts)
        elif ts is None:
            ts = datetime.now()
            
        return cls(
            timestamp=ts,
            open=float(data.get('open', 0)),
            high=float(data.get('high', 0)),
            low=float(data.get('low', 0)),
            close=float(data.get('close', 0)),
            volume=float(data.get('volume', 0)),
            symbol=data.get('symbol', ''),
            interval=data.get('interval', '1h')
        )


@dataclass
class MarketData:
    """实时市场数据"""
    symbol: str
    price: float
    bid: float = 0.0
    ask: float = 0.0
    volume: float = 0.0
    timestamp: Optional[datetime] = None
    change_24h: float = 0.0
    change_pct_24h: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.bid == 0.0 and self.price > 0:
            self.bid = self.price * 0.9999
        if self.ask == 0.0 and self.price > 0:
            self.ask = self.price * 1.0001

    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'price': self.price,
            'bid': self.bid,
            'ask': self.ask,
            'volume': self.volume,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            'change_24h': self.change_24h,
            'change_pct_24h': self.change_pct_24h,
            'high_24h': self.high_24h,
            'low_24h': self.low_24h
        }


class BaseMarketProvider(ABC):
    """
    市场数据抽象基类
    
    所有市场数据提供者必须实现此接口，确保数据源可替换性
    """

    def __init__(self, name: str = "BaseProvider"):
        self.name = name
        self._is_connected = False
        self._subscribers: Dict[str, List[callable]] = {}

    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._is_connected

    @abstractmethod
    def connect(self) -> bool:
        """连接到数据源
        
        Returns:
            bool: 连接是否成功
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """断开连接"""
        pass

    @abstractmethod
    def get_latest(self, symbol: str, interval: str = "1h") -> Optional[KLine]:
        """获取最新K线数据
        
        Args:
            symbol: 交易对符号，如 'BTCUSDT'
            interval: K线周期，如 '1m', '5m', '1h', '1d'
            
        Returns:
            KLine: 最新K线数据，失败返回 None
        """
        pass

    @abstractmethod
    def get_history(
        self, 
        symbol: str, 
        interval: str = "1h", 
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[KLine]:
        """获取历史K线数据
        
        Args:
            symbol: 交易对符号
            interval: K线周期
            limit: 获取数量上限
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[KLine]: K线数据列表
        """
        pass

    @abstractmethod
    def get_ticker(self, symbol: str) -> Optional[MarketData]:
        """获取实时行情
        
        Args:
            symbol: 交易对符号
            
        Returns:
            MarketData: 市场数据，失败返回 None
        """
        pass

    def subscribe(self, symbol: str, callback: callable) -> None:
        """订阅实时数据更新
        
        Args:
            symbol: 交易对符号
            callback: 回调函数，接收 KLine 或 MarketData
        """
        if symbol not in self._subscribers:
            self._subscribers[symbol] = []
        self._subscribers[symbol].append(callback)

    def unsubscribe(self, symbol: str, callback: callable) -> None:
        """取消订阅
        
        Args:
            symbol: 交易对符号
            callback: 之前注册的回调函数
        """
        if symbol in self._subscribers:
            self._subscribers[symbol] = [cb for cb in self._subscribers[symbol] if cb != callback]

    def _notify_subscribers(self, symbol: str, data: Any) -> None:
        """通知订阅者
        
        Args:
            symbol: 交易对符号
            data: 更新的数据
        """
        if symbol in self._subscribers:
            for callback in self._subscribers[symbol]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"[WARN] Subscriber callback error: {e}")

    def get_status(self) -> Dict[str, Any]:
        """获取提供者状态"""
        return {
            'name': self.name,
            'connected': self._is_connected,
            'subscribers': {symbol: len(callbacks) for symbol, callbacks in self._subscribers.items()}
        }
