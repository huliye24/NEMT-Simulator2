"""
Context Map - 限界上下文映射图

定义系统各上下文的边界和关系。

版本: v1.0.0
更新: 2026-04-27
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ContextType(Enum):
    """上下文类型"""

    CORE = "core"  # 核心上下文
    SUPPORTING = "supporting"  # 支持上下文
    GENERIC = "generic"  # 通用上下文


class RelationshipType(Enum):
    """上下文关系类型"""

    PUBLISHER_SUBSCRIBER = "publisher_subscriber"  # 发布-订阅
    Customer_Supplier = "customer_supplier"  # 客户-供应商
    CONFORMIST = "conformist"  # 顺从
    ANTICORRUPTION = "anticorruption"  # 防腐层
    OPEN_HOST_SERVICE = "open_host_service"  # 开放主机服务


@dataclass
class ContextBoundary:
    """上下文边界定义"""

    context_name: str
    capsule_names: list[str]
    context_type: ContextType
    public_api: list[str]  # 公开接口
    events_published: list[str]  # 发布的事件
    events_consumed: list[str]  # 消费的事件

    # 关系
    upstream_contexts: list[str] = field(default_factory=list)
    downstream_contexts: list[str] = field(default_factory=list)
    relationships: dict[str, RelationshipType] = field(default_factory=dict)

    # 描述
    description: str = ""
    invariants: list[str] = field(default_factory=list)


# =============================================================================
# Context Map Definition
# =============================================================================

CONTEXT_MAP = {
    "market": ContextBoundary(
        context_name="market",
        capsule_names=["MarketCapsule"],
        context_type=ContextType.CORE,
        public_api=[
            "get_price(symbol)",
            "get_klines(symbol, timeframe, limit)",
            "subscribe(symbol, callback)",
            "get_cached_symbols()",
        ],
        events_published=[
            "market.price_update",
            "market.candle_closed",
            "market.kline",
        ],
        events_consumed=[
            "market.subscribe_request",
        ],
        downstream_contexts=["signal", "brain"],
        relationships={
            "signal": RelationshipType.PUBLISHER_SUBSCRIBER,
            "brain": RelationshipType.PUBLISHER_SUBSCRIBER,
        },
        description="市场数据上下文，负责数据采集和分发",
        invariants=[
            "同一 symbol 只存在一个 MarketDataCache",
            "prices/timestamps 严格递增",
        ],
    ),
    "signal": ContextBoundary(
        context_name="signal",
        capsule_names=["SignalCapsule"],
        context_type=ContextType.CORE,
        public_api=[
            "generate_signal(symbol, market_data)",
            "calculate_indicators(prices)",
            "filter_signals(signals)",
            "get_latest_signals(n)",
        ],
        events_published=[
            "signal.generated",
            "signal.filtered",
        ],
        events_consumed=[
            "market.price_update",
            "market.candle_closed",
        ],
        upstream_contexts=["market"],
        downstream_contexts=["risk", "brain"],
        relationships={
            "market": RelationshipType.PUBLISHER_SUBSCRIBER,
            "risk": RelationshipType.PUBLISHER_SUBSCRIBER,
            "brain": RelationshipType.PUBLISHER_SUBSCRIBER,
        },
        description="信号生成上下文，负责技术指标计算和信号生成",
        invariants=[
            "单个 symbol 同时最多 1 个有效信号",
            "置信度必须在 [0, 1] 范围",
        ],
    ),
    "brain": ContextBoundary(
        context_name="brain",
        capsule_names=["BrainCapsule"],
        context_type=ContextType.CORE,
        public_api=[
            "add_strategy(type, config)",
            "remove_strategy(type)",
            "fuse_signals(signals)",
            "get_active_strategies()",
        ],
        events_published=[
            "brain.decision",
            "brain.weight_update",
        ],
        events_consumed=[
            "signal.generated",
            "position.closed",
        ],
        upstream_contexts=["signal"],
        downstream_contexts=["risk"],
        relationships={
            "signal": RelationshipType.PUBLISHER_SUBSCRIBER,
            "risk": RelationshipType.PUBLISHER_SUBSCRIBER,
        },
        description="策略大脑上下文，负责多策略融合和决策",
        invariants=[
            "策略权重和必须等于 1",
            "最多同时运行 5 个策略",
        ],
    ),
    "risk": ContextBoundary(
        context_name="risk",
        capsule_names=["RiskCapsule"],
        context_type=ContextType.CORE,
        public_api=[
            "check_signal(signal)",
            "check_position(position)",
            "update_balance(balance)",
            "get_risk_metrics()",
        ],
        events_published=[
            "risk.approved",
            "risk.rejected",
            "risk.alert",
        ],
        events_consumed=[
            "signal.generated",
        ],
        upstream_contexts=["signal", "brain"],
        downstream_contexts=["execution"],
        relationships={
            "signal": RelationshipType.PUBLISHER_SUBSCRIBER,
            "brain": RelationshipType.PUBLISHER_SUBSCRIBER,
            "execution": RelationshipType.PUBLISHER_SUBSCRIBER,
        },
        description="风控上下文，负责风险检查和仓位管理",
        invariants=[
            "账户余额永远不能为负",
            "回撤不能超过最大回撤限制",
        ],
    ),
    "execution": ContextBoundary(
        context_name="execution",
        capsule_names=["ExecutionCapsule"],
        context_type=ContextType.CORE,
        public_api=[
            "submit_order(symbol, side, quantity, price)",
            "cancel_order(order_id)",
            "get_position(symbol)",
            "get_orders(status)",
            "get_balance()",
        ],
        events_published=[
            "order.submitted",
            "order.filled",
            "position.updated",
        ],
        events_consumed=[
            "risk.approved",
        ],
        upstream_contexts=["risk"],
        downstream_contexts=["monitor"],
        relationships={
            "risk": RelationshipType.PUBLISHER_SUBSCRIBER,
            "monitor": RelationshipType.PUBLISHER_SUBSCRIBER,
        },
        description="执行上下文，负责订单管理和持仓更新",
        invariants=[
            "订单状态机严格流转",
            "filled_quantity <= quantity",
        ],
    ),
    "monitor": ContextBoundary(
        context_name="monitor",
        capsule_names=["MonitorCapsule"],
        context_type=ContextType.SUPPORTING,
        public_api=[
            "check_health()",
            "get_metrics()",
            "get_alerts(hours)",
            "set_threshold(metric, value)",
        ],
        events_published=[
            "monitor.health",
            "monitor.alert",
            "monitor.report",
        ],
        events_consumed=[
            "system.metric",
            "order.filled",
            "error.*",
        ],
        upstream_contexts=["market", "signal", "risk", "execution"],
        relationships={
            "market": RelationshipType.PUBLISHER_SUBSCRIBER,
            "signal": RelationshipType.PUBLISHER_SUBSCRIBER,
            "risk": RelationshipType.PUBLISHER_SUBSCRIBER,
            "execution": RelationshipType.PUBLISHER_SUBSCRIBER,
        },
        description="监控上下文，负责系统健康检查和告警",
        invariants=[
            "健康指标采集时间不超过 2 分钟",
            "告警历史最多保留 100 条",
        ],
    ),
}


# =============================================================================
# Context Map Queries
# =============================================================================


def get_context(context_name: str) -> ContextBoundary | None:
    """获取上下文定义"""
    return CONTEXT_MAP.get(context_name)


def get_all_contexts() -> dict[str, ContextBoundary]:
    """获取所有上下文"""
    return CONTEXT_MAP


def get_upstream_contexts(context_name: str) -> list[str]:
    """获取上游上下文"""
    context = CONTEXT_MAP.get(context_name)
    return context.upstream_contexts if context else []


def get_downstream_contexts(context_name: str) -> list[str]:
    """获取下游上下文"""
    context = CONTEXT_MAP.get(context_name)
    return context.downstream_contexts if context else []


def get_event_consumers(event_type: str) -> list[str]:
    """获取事件的消费者"""
    consumers = []
    for name, context in CONTEXT_MAP.items():
        if event_type in context.events_consumed:
            consumers.append(name)
    return consumers


def get_event_producers(event_type: str) -> list[str]:
    """获取事件的生产者"""
    producers = []
    for name, context in CONTEXT_MAP.items():
        if event_type in context.events_published:
            producers.append(name)
    return producers


def validate_context_relationship(
    from_context: str,
    to_context: str,
) -> bool:
    """
    验证上下文关系是否合法

    Args:
        from_context: 来源上下文
        to_context: 目标上下文

    Returns:
        是否合法
    """
    from_def = CONTEXT_MAP.get(from_context)
    if not from_def:
        return False

    return to_context in from_def.downstream_contexts


def get_full_event_flow() -> list[dict[str, str]]:
    """
    获取完整事件流

    Returns:
        事件流列表
    """
    flows = []

    for from_ctx_name, from_ctx in CONTEXT_MAP.items():
        for event in from_ctx.events_published:
            consumers = get_event_consumers(event)
            for to_ctx_name in consumers:
                flows.append(
                    {
                        "from": from_ctx_name,
                        "to": to_ctx_name,
                        "event": event,
                    }
                )

    return flows


# =============================================================================
# Anticorruption Layer
# =============================================================================


@dataclass
class AnticorruptionRule:
    """防腐层规则"""

    source_context: str
    target_context: str
    field_mappings: dict[str, str]  # source_field -> target_field
    value_transformations: dict[str, Any]  # field -> transformation
    validation_rules: list[str] = field(default_factory=list)


ANTICORRUPTION_LAYER = {
    ("market", "signal"): AnticorruptionRule(
        source_context="market",
        target_context="signal",
        field_mappings={
            "symbol": "symbol",
            "price": "current_price",
            "volume": "volume",
        },
        value_transformations={},
    ),
    ("signal", "risk"): AnticorruptionRule(
        source_context="signal",
        target_context="risk",
        field_mappings={
            "signal_id": "signal_id",
            "symbol": "symbol",
            "entry_price": "entry_price",
            "stop_loss": "stop_loss",
            "take_profit": "take_profit",
            "confidence": "confidence",
        },
        value_transformations={},
    ),
    ("risk", "execution"): AnticorruptionRule(
        source_context="risk",
        target_context="execution",
        field_mappings={
            "symbol": "symbol",
            "position_size": "quantity",
            "adjusted_entry": "price",
        },
        value_transformations={},
    ),
}


def get_anticorruption_rule(
    source_context: str,
    target_context: str,
) -> AnticorruptionRule | None:
    """获取防腐层规则"""
    return ANTICORRUPTION_LAYER.get((source_context, target_context))


def transform_data(
    source_context: str,
    target_context: str,
    source_data: dict[str, Any],
) -> dict[str, Any]:
    """
    跨上下文数据转换

    Args:
        source_context: 源上下文
        target_context: 目标上下文
        source_data: 源数据

    Returns:
        转换后的数据
    """
    rule = get_anticorruption_rule(source_context, target_context)
    if not rule:
        return source_data

    result = {}
    for source_field, target_field in rule.field_mappings.items():
        if source_field in source_data:
            result[target_field] = source_data[source_field]

    return result
