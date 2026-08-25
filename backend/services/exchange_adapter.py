"""
Exchange Adapter Interface
统一交易所接口抽象层
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"


class OrderStatus(Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class MarketData:
    """市场数据"""
    symbol: str
    price: float
    bid: float
    ask: float
    volume24h: float
    change24h: float
    timestamp: str


@dataclass
class Order:
    """订单"""
    id: str
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float]
    stop_price: Optional[float]
    status: OrderStatus
    filled_quantity: float = 0.0
    avg_price: float = 0.0
    created_at: str = ""
    updated_at: str = ""


@dataclass
class Position:
    """持仓"""
    symbol: str
    quantity: float
    avg_price: float
    unrealized_pnl: float
    realized_pnl: float


@dataclass
class AccountBalance:
    """账户余额"""
    asset: str
    free: float
    locked: float


class ExchangeAdapter(ABC):
    """交易所适配器抽象基类"""

    def __init__(self, name: str, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.name = name
        self.api_key = api_key
        self.api_secret = api_secret
        self._connected = False
        self._paper_trading = True  # 默认模拟模式

    @abstractmethod
    async def connect(self) -> bool:
        """连接交易所"""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接"""
        pass

    @abstractmethod
    async def get_market_data(self, symbol: str) -> MarketData:
        """获取市场数据"""
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict:
        """获取Ticker"""
        pass

    @abstractmethod
    async def get_orderbook(self, symbol: str, limit: int = 100) -> Dict:
        """获取订单簿"""
        pass

    @abstractmethod
    async def get_balance(self) -> List[AccountBalance]:
        """获取账户余额"""
        pass

    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """获取持仓"""
        pass

    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Order:
        """下单"""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """取消订单"""
        pass

    @abstractmethod
    async def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """获取订单"""
        pass

    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """获取未成交订单"""
        pass

    @abstractmethod
    async def get_order_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Order]:
        """获取订单历史"""
        pass

    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected

    def is_paper_trading(self) -> bool:
        """是否模拟交易模式"""
        return self._paper_trading

    def set_paper_trading(self, enabled: bool):
        """设置模拟交易模式"""
        self._paper_trading = enabled

    def get_api_permissions(self) -> Dict:
        """获取API权限"""
        return {
            "read": True,
            "trade": not self._paper_trading,
            "withdraw": False,  # 永远禁止提现
        }
