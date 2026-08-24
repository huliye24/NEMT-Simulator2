"""
Event Sourcing Module - 事件溯源模块

提供事件溯源、CQRS 和 Saga 模式实现。
"""

from nemt.event_sourcing.cqrs import (
    Command,
    CommandBus,
    CommandHandler,
    CommandResult,
    CQRSMediator,
    Query,
    QueryBus,
    QueryHandler,
    QueryResult,
)
from nemt.event_sourcing.event_sourcing import (
    AggregateRoot,
    DomainEvent,
    EventPublisher,
    EventStore,
    SnapshotStore,
)
from nemt.event_sourcing.saga import (
    CompensableAction,
    CompensationResult,
    Saga,
    SagaOrchestrator,
    SagaState,
    SagaStepResult,
    saga_step,
)

__all__ = [
    # 事件溯源
    "DomainEvent",
    "EventStore",
    "AggregateRoot",
    "EventPublisher",
    "SnapshotStore",
    # CQRS
    "Command",
    "Query",
    "CommandHandler",
    "QueryHandler",
    "CommandBus",
    "QueryBus",
    "CQRSMediator",
    "CommandResult",
    "QueryResult",
    # Saga
    "Saga",
    "SagaStepResult",
    "SagaState",
    "SagaOrchestrator",
    "CompensableAction",
    "CompensationResult",
    "saga_step",
]
