"""
NEMT Core Module

核心模块:
- ConfigCenter: 配置中心
- EventBus: 事件总线
- ModuleCapsule: 胶囊基类 (支持分形迭代)
- FractalCapsule: 分形迭代胶囊基类
- CapsuleManager: 胶囊管理器
- 业务胶囊: MarketCapsule, SignalCapsule, RiskCapsule, ExecutionCapsule, BrainCapsule, MonitorCapsule
- 分形框架: contracts, metrics, view_switcher, layer_lock
- 接口定义: ICapsule, IEventBus, IStorage
- 依赖注入: DIContainer
- 模块注册: ModuleRegistry
- 健康检查: HealthCheck
"""

# 核心接口 (接口抽象层)
from .brain import BrainCapsule, StrategyConfig, StrategyType
from .capsule import FractalCapsule, ModuleCapsule
from .capsule_manager import CapsuleManager
from .config_center import ConfigCenter

# 分形迭代框架
from .contracts import (
    CapsuleMetadata,
    ICapsuleContract,
    IPipelineContract,
    MarketPhase,
    PipelineInput,
    PipelineOutput,
)

# 新增组件
from .di import DIContainer, Lifetime
from .event_bus import Event, EventBus
from .execution import ExecutionCapsule, Order, OrderSide, OrderStatus
from .health import (
    CheckStatus,
    CompositeHealthCheck,
    HealthCheck,
    HealthCheckerRegistry,
    HealthCheckResult,
    create_system_health_check,
)
from .interfaces import (
    CapsuleState,
    EventPriority,
    HealthStatus,
    ICapsule,
    IEventBus,
    IEventPublisher,
    IEventSubscriber,
    IKVStorage,
    IStorage,
)
from .layer_lock import (
    LayerContract,
    LayerLockManager,
    LockStatus,
    freeze_layer,
    get_lock_manager,
)

# 仓位管理
from .position_capsule import PositionCapsule, PositionOrder, PositionHistory
from .position_calculator import (
    PositionCalculator,
    PositionResult,
    RiskTier,
    AlgoMode,
    DynamicRiskCalculator,
    HybridPositionAlgorithm,
    KellyCalculator,
    ATRCalculator,
)

# 业务胶囊
from .market import MarketCapsule, MarketDataCache
from .metrics import (
    FractalMetricsCollector,
    IterationMetrics,
    PhaseMetrics,
    PhaseStatus,
)
from .monitor import HealthMetric, MonitorCapsule
from .monitor import HealthStatus as MonitorHealthStatus
from .registry import ModuleInfo, ModuleRegistry
from .risk import RiskCapsule, RiskCheckResult
from .signal import SignalCapsule, SignalType, TradingSignal
from .view_switcher import (
    ViewContext,
    ViewMode,
    ViewSwitcher,
    get_view_switcher,
    require_view,
    with_view,
)

from .nemt_engine import NEMTEngine, create_engine

__all__ = [
    # 核心引擎
    "NEMTEngine",
    "create_engine",
    # 核心接口
    "ICapsule",
    "CapsuleState",
    "HealthStatus",
    "IEventBus",
    "IEventPublisher",
    "IEventSubscriber",
    "Event",
    "EventPriority",
    "IStorage",
    "IKVStorage",
    "IConfigCenter",
    # 核心组件
    "ConfigCenter",
    "EventBus",
    "ModuleCapsule",
    "FractalCapsule",
    "CapsuleManager",
    # 依赖注入
    "DIContainer",
    "Lifetime",
    # 模块注册
    "ModuleRegistry",
    "ModuleInfo",
    # 健康检查
    "HealthCheck",
    "HealthCheckResult",
    "CheckStatus",
    "HealthCheckerRegistry",
    "CompositeHealthCheck",
    "create_system_health_check",
    # 分形迭代框架
    "ICapsuleContract",
    "CapsuleMetadata",
    "IPipelineContract",
    "PipelineInput",
    "PipelineOutput",
    "MarketPhase",
    "PhaseStatus",
    "PhaseMetrics",
    "IterationMetrics",
    "FractalMetricsCollector",
    "ViewMode",
    "ViewContext",
    "ViewSwitcher",
    "get_view_switcher",
    "with_view",
    "require_view",
    "LockStatus",
    "LayerContract",
    "LayerLockManager",
    "get_lock_manager",
    "freeze_layer",
    # 仓位管理
    "PositionCapsule",
    "PositionOrder",
    "PositionHistory",
    "PositionCalculator",
    "PositionResult",
    "RiskTier",
    "AlgoMode",
    "DynamicRiskCalculator",
    "HybridPositionAlgorithm",
    "KellyCalculator",
    "ATRCalculator",
    # 业务胶囊
    "MarketCapsule",
    "MarketDataCache",
    "SignalCapsule",
    "TradingSignal",
    "SignalType",
    "RiskCapsule",
    "RiskCheckResult",
    "ExecutionCapsule",
    "Order",
    "OrderStatus",
    "OrderSide",
    "BrainCapsule",
    "StrategyConfig",
    "MonitorCapsule",
    "HealthMetric",
    # 枚举
    "StrategyType",
    "MonitorHealthStatus",
]

__version__ = "1.1.0-container-ready"
