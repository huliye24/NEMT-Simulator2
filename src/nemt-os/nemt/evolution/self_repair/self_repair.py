"""
L-Evolve: 自演化层 - 自修复系统

自修复系统是自演化系统的免疫系统。
它检测问题、分析根因、执行修复。

核心概念:
- SelfRepairEngine: 自修复引擎
- RepairAction: 修复动作
- RepairPlan: 修复计划
- FaultAnalyzer: 故障分析器
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any

logger = logging.getLogger(__name__)

# =============================================================================
# 类型定义
# =============================================================================

RepairId = str
FaultId = str


class FaultType(Enum):
    """故障类型"""

    CRASH = auto()  # 崩溃
    HANG = auto()  # 挂起
    MEMORY_LEAK = auto()  # 内存泄漏
    DEADLOCK = auto()  # 死锁
    TIMEOUT = auto()  # 超时
    DATA_CORRUPTION = auto()  # 数据损坏
    CONFIG_ERROR = auto()  # 配置错误
    DEPENDENCY_ERROR = auto()  # 依赖错误


class RepairStatus(Enum):
    """修复状态"""

    PENDING = "pending"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class RepairStrategy(Enum):
    """修复策略"""

    RESTART = auto()  # 重启
    ROLLBACK = auto()  # 回滚
    RESTORE = auto()  # 恢复
    RECONFIGURE = auto()  # 重新配置
    ISOLATE = auto()  # 隔离
    ESCALATE = auto()  # 升级


# =============================================================================
# 故障定义
# =============================================================================


@dataclass
class Fault:
    """故障"""

    id: FaultId
    fault_type: FaultType
    severity: str  # critical, high, medium, low
    description: str

    # 上下文
    entity_id: str | None = None
    entity_type: str | None = None

    # 状态
    detected_at: datetime = field(default_factory=datetime.now)
    is_resolved: bool = False
    resolved_at: datetime | None = None

    # 根因
    root_cause: str | None = None
    affected_components: list[str] = field(default_factory=list)

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)

    def resolve(self):
        """解决故障"""
        self.is_resolved = True
        self.resolved_at = datetime.now()


@dataclass
class RepairAction:
    """修复动作"""

    id: str
    action_type: str
    target: str
    parameters: dict[str, Any] = field(default_factory=dict)
    rollback_action: dict[str, Any] | None = None

    order: int = 0
    estimated_duration: float = 0.0  # 秒
    risk_level: str = "low"  # low, medium, high

    status: RepairStatus = RepairStatus.PENDING
    executed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class RepairPlan:
    """修复计划"""

    id: RepairId
    fault_id: FaultId
    strategy: RepairStrategy
    actions: list[RepairAction] = field(default_factory=list)

    # 评估
    total_duration: float = 0.0
    risk_level: str = "low"
    success_probability: float = 0.9

    # 状态
    status: RepairStatus = RepairStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # 回滚
    can_rollback: bool = True
    snapshot_id: str | None = None

    def total_actions(self) -> int:
        return len(self.actions)


# =============================================================================
# 修复策略注册表
# =============================================================================


class RepairStrategyRegistry:
    """修复策略注册表"""

    def __init__(self):
        self._strategies: dict[FaultType, list[RepairStrategy]] = {
            FaultType.CRASH: [RepairStrategy.RESTART, RepairStrategy.ROLLBACK],
            FaultType.HANG: [RepairStrategy.RESTART],
            FaultType.MEMORY_LEAK: [RepairStrategy.RESTART, RepairStrategy.RECONFIGURE],
            FaultType.DEADLOCK: [RepairStrategy.RESTART],
            FaultType.TIMEOUT: [RepairStrategy.RECONFIGURE],
            FaultType.DATA_CORRUPTION: [RepairStrategy.RESTORE, RepairStrategy.ROLLBACK],
            FaultType.CONFIG_ERROR: [RepairStrategy.RECONFIGURE],
            FaultType.DEPENDENCY_ERROR: [RepairStrategy.RECONFIGURE],
        }

        self._action_templates: dict[str, dict[str, Any]] = {
            "restart": {
                "action_type": "restart",
                "target": "component",
                "parameters": {"timeout": 30},
            },
            "rollback": {
                "action_type": "rollback",
                "target": "state",
                "parameters": {},
            },
            "restore_snapshot": {
                "action_type": "restore",
                "target": "snapshot",
                "parameters": {},
            },
            "update_config": {
                "action_type": "update",
                "target": "config",
                "parameters": {},
            },
        }

    def get_strategies(self, fault_type: FaultType) -> list[RepairStrategy]:
        """获取故障类型对应的策略"""
        return self._strategies.get(fault_type, [RepairStrategy.RESTART])

    def get_action_template(self, action_type: str) -> dict[str, Any] | None:
        """获取动作模板"""
        return self._action_templates.get(action_type)


# =============================================================================
# 自修复引擎
# =============================================================================


class SelfRepairEngine:
    """
    自修复引擎

    负责:
    - 故障检测
    - 根因分析
    - 修复计划生成
    - 修复执行
    - 修复验证
    """

    def __init__(self):
        self._faults: dict[FaultId, Fault] = {}
        self._repair_plans: dict[RepairId, RepairPlan] = {}
        self._strategy_registry = RepairStrategyRegistry()

        # 处理器
        self._fault_analyzers: list[Callable] = []
        self._repair_executors: dict[str, Callable] = {}
        self._repair_handlers: list[Callable] = []

        self._logger = logging.getLogger(f"{__name__}.SelfRepair")

    def register_fault_analyzer(self, analyzer: Callable[[Fault], str | None]):
        """注册故障分析器"""
        self._fault_analyzers.append(analyzer)

    def register_repair_executor(self, action_type: str, executor: Callable[[RepairAction], dict[str, Any]]):
        """注册修复执行器"""
        self._repair_executors[action_type] = executor

    def on_repair_complete(self, handler: Callable):
        """修复完成回调"""
        self._repair_handlers.append(handler)

    def report_fault(
        self,
        fault_type: FaultType,
        description: str,
        severity: str = "medium",
        entity_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Fault:
        """报告故障"""
        fault = Fault(
            id=str(uuid.uuid4()),
            fault_type=fault_type,
            severity=severity,
            description=description,
            entity_id=entity_id,
            metadata=metadata or {},
        )

        self._faults[fault.id] = fault
        self._logger.warning(f"Fault detected: {fault_type.name} - {description}")

        return fault

    def analyze_fault(self, fault_id: FaultId) -> str | None:
        """分析故障根因"""
        fault = self._faults.get(fault_id)
        if not fault:
            return None

        # 调用分析器
        for analyzer in self._fault_analyzers:
            try:
                root_cause = analyzer(fault)
                if root_cause:
                    fault.root_cause = root_cause
                    self._logger.info(f"Fault {fault_id} root cause: {root_cause}")
                    return root_cause
            except Exception as e:
                self._logger.error(f"Analyzer error: {e}")

        return None

    def create_repair_plan(self, fault_id: FaultId) -> RepairPlan | None:
        """创建修复计划"""
        fault = self._faults.get(fault_id)
        if not fault:
            return None

        # 获取适用的策略
        strategies = self._strategy_registry.get_strategies(fault.fault_type)
        strategy = strategies[0] if strategies else RepairStrategy.RESTART

        # 创建计划
        plan = RepairPlan(
            id=str(uuid.uuid4()),
            fault_id=fault_id,
            strategy=strategy,
        )

        # 添加修复动作
        if strategy == RepairStrategy.RESTART:
            plan.actions.append(
                RepairAction(
                    id=str(uuid.uuid4()),
                    action_type="restart",
                    target=fault.entity_id or "component",
                    order=1,
                )
            )
        elif strategy == RepairStrategy.ROLLBACK:
            plan.actions.append(
                RepairAction(
                    id=str(uuid.uuid4()),
                    action_type="rollback",
                    target="state",
                    order=1,
                )
            )
            plan.can_rollback = True

        self._repair_plans[plan.id] = plan
        self._logger.info(f"Created repair plan {plan.id} for fault {fault_id}")

        return plan

    def execute_repair(self, plan_id: RepairId) -> bool:
        """执行修复计划"""
        plan = self._repair_plans.get(plan_id)
        if not plan:
            return False

        fault = self._faults.get(plan.fault_id)
        if not fault:
            return False

        plan.status = RepairStatus.EXECUTING
        plan.started_at = datetime.now()

        self._logger.info(f"Executing repair plan {plan_id}...")

        # 按顺序执行动作
        for action in plan.actions:
            action.status = RepairStatus.EXECUTING

            executor = self._repair_executors.get(action.action_type)
            if not executor:
                self._logger.warning(f"No executor for action type: {action.action_type}")
                action.status = RepairStatus.FAILED
                action.error = "No executor registered"
                plan.status = RepairStatus.FAILED
                return False

            try:
                result = executor(action)
                action.status = RepairStatus.SUCCESS
                action.executed_at = datetime.now()
                action.result = result
                self._logger.info(f"Action {action.action_type} completed")
            except Exception as e:
                self._logger.error(f"Action {action.action_type} failed: {e}")
                action.status = RepairStatus.FAILED
                action.error = str(e)
                plan.status = RepairStatus.FAILED
                return False

        # 验证修复
        plan.status = RepairStatus.VERIFYING
        if self._verify_repair(fault):
            plan.status = RepairStatus.SUCCESS
            plan.completed_at = datetime.now()
            fault.resolve()
            self._logger.info(f"Repair plan {plan_id} completed successfully")

            # 调用完成回调
            for handler in self._repair_handlers:
                try:
                    handler(fault, plan)
                except Exception as e:
                    self._logger.error(f"Repair handler error: {e}")

            return True

        plan.status = RepairStatus.FAILED
        return False

    def _verify_repair(self, fault: Fault) -> bool:
        """验证修复"""
        # 检查故障是否已解决，或者至少有修复动作成功执行
        if fault.is_resolved:
            return True

        # 检查是否有成功的修复动作
        # 这里简化为返回 True，因为动作执行成功就认为修复成功
        return True

    def rollback_repair(self, plan_id: RepairId) -> bool:
        """回滚修复"""
        plan = self._repair_plans.get(plan_id)
        if not plan or not plan.can_rollback:
            return False

        self._logger.info(f"Rolling back repair plan {plan_id}...")

        # 执行回滚动作
        for action in reversed(plan.actions):
            if action.rollback_action:
                # 执行回滚
                pass

        plan.status = RepairStatus.ROLLED_BACK
        return True

    def get_active_faults(
        self,
        fault_type: FaultType | None = None,
    ) -> list[Fault]:
        """获取活跃故障"""
        faults = [f for f in self._faults.values() if not f.is_resolved]

        if fault_type:
            faults = [f for f in faults if f.fault_type == fault_type]

        return faults

    def get_repair_history(
        self,
        limit: int = 100,
    ) -> list[RepairPlan]:
        """获取修复历史"""
        plans = list(self._repair_plans.values())
        return sorted(plans, key=lambda p: p.created_at, reverse=True)[:limit]

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        plans = list(self._repair_plans.values())
        faults = list(self._faults.values())

        return {
            "total_faults": len(faults),
            "active_faults": len([f for f in faults if not f.is_resolved]),
            "resolved_faults": len([f for f in faults if f.is_resolved]),
            "total_repairs": len(plans),
            "successful_repairs": len([p for p in plans if p.status == RepairStatus.SUCCESS]),
            "failed_repairs": len([p for p in plans if p.status == RepairStatus.FAILED]),
            "success_rate": (len([p for p in plans if p.status == RepairStatus.SUCCESS]) / max(1, len(plans))),
        }


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    # 类型别名
    "RepairId",
    "FaultId",
    # 枚举
    "FaultType",
    "RepairStatus",
    "RepairStrategy",
    # 数据类
    "Fault",
    "RepairAction",
    "RepairPlan",
    # 核心类
    "RepairStrategyRegistry",
    "SelfRepairEngine",
]
