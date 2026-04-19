# 接口契约
> 模块之间的接口定义、数据格式、异常规范

## 一、模块边界

```
┌─────────────────────────────────────────────────────────────┐
│                        NEMT Quant OS                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │  市场层   │───→│  模型层   │───→│  策略层   │          │
│  │  Market  │    │  Model   │    │ Strategy │          │
│  └──────────┘    └──────────┘    └────┬─────┘          │
│                                          │                  │
│                                          ▼                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │  执行层   │◀───│  风控层   │◀───│  资金层   │          │
│  │Execution │    │  Risk    │    │ Capital  │          │
│  └──────────┘    └──────────┘    └──────────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 二、数据结构定义

### 2.1 MarketData (市场数据)

```python
@dataclass
class MarketData:
    timestamp: datetime      # 时间戳
    symbol: str              # 交易对: "BTCUSDT"
    open: float              # 开盘价
    high: float              # 最高价
    low: float               # 最低价
    close: float             # 收盘价
    volume: float            # 成交量
```

### 2.2 ModelSignal (模型信号)

```python
@dataclass
class ModelSignal:
    direction: int           # 方向: 1(多), -1(空), 0(观望)
    confidence: float        # 置信度: 0.0 ~ 1.0
    strength: float          # 强度: 0.0 ~ 1.0
    model_name: str          # 模型名称
    indicators: Dict[str, float]  # 详细指标
```

### 2.3 Order (订单)

```python
@dataclass
class Order:
    strategy_id: str         # 策略 ID
    symbol: str              # 交易对
    direction: int          # 方向: 1(多), -1(空)
    quantity: float          # 数量
    stop_loss: float         # 止损价
    take_profit: float      # 止盈价
    entry_price: float       # 入场价
```

### 2.4 FinalOrder (最终订单)

```python
@dataclass
class FinalOrder:
    order: Order             # 原始订单
    allocated_capital: float # 分配资金
    weight: float           # 权重
    position_ratio: float   # 仓位比例
    risk_amount: float      # 风险金额
```

### 2.5 MarketPhase (市场相位)

```python
class MarketPhase(Enum):
    PHASE_A_NOISE = "phase_a"      # 高噪声混乱期
    PHASE_B_VORTEX = "phase_b"    # 涡旋蓄力期
    PHASE_C_RESONANCE = "phase_c" # 临界爆发前夜
    PHASE_D_TREND = "phase_d"      # 趋势运行期
```

## 三、接口定义

### 3.1 市场层接口

```python
class BaseMarketProvider(ABC):
    """市场数据提供者基类"""
    
    @abstractmethod
    def get_latest(self, symbol: str, interval: str) -> MarketData:
        """
        获取最新市场数据
        
        Args:
            symbol: 交易对，如 "BTCUSDT"
            interval: 周期，如 "1m", "5m", "1h"
            
        Returns:
            MarketData 对象
            
        Raises:
            MarketDataError: 获取数据失败
        """
        pass
    
    @abstractmethod
    def get_history(
        self, 
        symbol: str, 
        start: datetime, 
        end: datetime
    ) -> List[MarketData]:
        """
        获取历史数据
        
        Returns:
            MarketData 列表
            
        Raises:
            MarketDataError: 获取数据失败
        """
        pass
```

### 3.2 模型层接口

```python
class BaseModel(ABC):
    """模型基类"""
    
    @abstractmethod
    def predict(self, data: MarketData) -> ModelSignal:
        """
        预测信号
        
        Args:
            data: 市场数据
            
        Returns:
            ModelSignal 对象
        """
        pass
    
    def get_confidence(self) -> float:
        """获取模型置信度"""
        return 0.5
```

### 3.3 策略层接口

```python
class BaseStrategy(ABC):
    """策略基类"""
    
    @abstractmethod
    def generate_signal(
        self, 
        model_outputs: List[ModelSignal]
    ) -> Order:
        """
        生成订单
        
        Args:
            model_outputs: 模型输出列表
            
        Returns:
            Order 对象
        """
        pass
    
    @property
    def strategy_id(self) -> str:
        """策略 ID"""
        return self._strategy_id
```

### 3.4 资金层接口

```python
class BaseCapitalManager(ABC):
    """资金管理器基类"""
    
    @abstractmethod
    def allocate(
        self,
        orders: List[Order],
        total_capital: float,
        current_phase: MarketPhase,
        **kwargs
    ) -> AllocationResult:
        """
        分配资金
        
        Args:
            orders: 订单列表
            total_capital: 总资金
            current_phase: 当前相位
            
        Returns:
            AllocationResult 对象
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """获取管理器名称"""
        pass
```

### 3.5 风控层接口

```python
class BaseRiskManager(ABC):
    """风控管理器基类"""
    
    @abstractmethod
    def calculate_position_size(
        self,
        phase: MarketPhase,
        entry_price: float,
        stop_loss: float,
        **kwargs
    ) -> Tuple[float, float]:
        """
        计算仓位大小
        
        Args:
            phase: 当前相位
            entry_price: 入场价
            stop_loss: 止损价
            
        Returns:
            (仓位大小, 风险金额)
        """
        pass
    
    @abstractmethod
    def calculate_stop_loss(
        self,
        entry_price: float,
        atr: float,
        signal_type: str,
        phase: MarketPhase
    ) -> float:
        """
        计算止损价
        
        Returns:
            止损价格
        """
        pass
```

## 四、异常规范

### 4.1 异常层次

```
BaseNEMTException
├── DataException
│   ├── MarketDataError
│   └── DataParseError
├── ModelException
│   ├── ModelLoadError
│   └── ModelPredictError
├── StrategyException
│   ├── StrategyInitError
│   └── SignalGenerateError
├── RiskException
│   ├── RiskLimitExceeded
│   └── PositionLimitExceeded
└── ExecutionException
    ├── OrderRejectError
    └── ExecutionError
```

### 4.2 异常处理规范

```python
# Good: 具体异常 + 上下文
try:
    result = market_provider.get_latest("BTCUSDT", "1m")
except MarketDataError as e:
    logger.error(f"获取市场数据失败: {e}")
    raise DataFetchError(f"无法获取 {symbol} 数据") from e

# Bad: 裸 except
try:
    result = market_provider.get_latest("BTCUSDT", "1m")
except:
    pass
```

## 五、事件契约

### 5.1 事件类型

```python
class EventType(Enum):
    MARKET_UPDATE = "market_update"      # 市场数据更新
    SIGNAL_GENERATED = "signal_generated"  # 信号生成
    ORDER_CREATED = "order_created"       # 订单创建
    ORDER_EXECUTED = "order_executed"     # 订单执行
    RISK_ALERT = "risk_alert"             # 风险警报
    PHASE_CHANGED = "phase_changed"       # 相位变化
```

### 5.2 事件格式

```python
@dataclass
class Event:
    type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    source: str  # 事件来源模块
```

## 六、数据流规范

### 6.1 数据流方向

```
MarketData → ModelSignal → Order → FinalOrder → Execution
                              ↓
                         Risk Check
                              ↓
                    Risk Adjusted Order
```

### 6.2 数据验证

每个模块在接收数据时必须验证:

```python
def validate_market_data(data: MarketData) -> bool:
    """验证市场数据"""
    assert data.close > 0, "收盘价必须为正"
    assert data.high >= data.low, "最高价 >= 最低价"
    assert data.high >= data.close, "最高价 >= 收盘价"
    assert data.high >= data.open, "最高价 >= 开盘价"
    assert data.low <= data.close, "最低价 <= 收盘价"
    assert data.low <= data.open, "最低价 <= 开盘价"
    return True
```

---

*创建时间: 2026-04-19*
*最后更新: 2026-04-19*
