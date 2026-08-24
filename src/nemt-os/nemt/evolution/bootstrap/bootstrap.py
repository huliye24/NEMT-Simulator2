"""
L-Boot: 系统自举层 - 自举引擎

系统自举是自演化系统的最高境界——系统通过自身的规则和能力，
从初始状态演化出完整的自演化系统。

核心概念:
- BootstrapEngine: 自举引擎
- BootstrapSeed: 自举种子
- BootstrapPhase: 自举阶段
- BootstrapCheckpoint: 自举检查点
"""

from __future__ import annotations

import logging
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
)

# 动态导入，避免相对导入问题
try:
    # 尝试相对导入
    from ..base.meta_rule_engine import (
        ActionNode,
        ActionType,
        Comparator,
        ConditionNode,
        MetaRule,
        MetaRuleEngine,
        RuleStatus,
        RuleType,
        create_meta_rule,
    )
    from ..constraint.constraint import (
        Constraint,
        ConstraintType,
        ConstraintValidator,
        Severity,
    )
    from ..guider.guider import (
        EvolutionDirection,
        EvolutionGoal,
        EvolutionGuider,
        EvolutionState,
        GuiderRole,
    )
    from ..state_universe.state_universe import (
        EntityType,
        EventType,
        StateEntity,
        StateUniverse,
    )
except ImportError:
    # 回退到直接导入
    _base_path = os.path.join(os.path.dirname(__file__), "..")
    if _base_path not in sys.path:
        sys.path.insert(0, _base_path)

    from base.meta_rule_engine import (
        ActionType,
        Comparator,
        MetaRule,
        MetaRuleEngine,
        RuleType,
        create_meta_rule,
    )
    from constraint.constraint import (
        Constraint,
        ConstraintValidator,
        Severity,
    )
    from guider.guider import (
        EvolutionGuider,
        GuiderRole,
    )
    from state_universe.state_universe import (
        EntityType,
        StateEntity,
        StateUniverse,
    )

logger = logging.getLogger(__name__)

# =============================================================================
# 类型定义
# =============================================================================

BootstrapId = str
CheckpointId = str
PhaseId = str


class BootstrapPhase(Enum):
    """自举阶段"""

    INITIAL = "initial"  # 初始状态
    SEED = "seed"  # 种子生成
    LAYER_1 = "layer_1"  # 第一层演化
    LAYER_2 = "layer_2"  # 第二层演化
    LAYER_3 = "layer_3"  # 第三层演化
    STABLE = "stable"  # 稳定态
    COMPLETE = "complete"  # 完成


class BootstrapState(Enum):
    """自举状态"""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


# =============================================================================
# 自举种子
# =============================================================================


@dataclass
class BootstrapSeed:
    """
    自举种子

    定义启动自演化系统所需的最小规则集。
    """

    id: str
    name: str
    description: str = ""

    # 种子元规则
    meta_rules: list[MetaRule] = field(default_factory=list)

    # 种子约束
    constraints: list[Constraint] = field(default_factory=list)

    # 种子实体类型
    entity_types: list[EntityType] = field(default_factory=list)

    # 演化方向
    directions: list[dict[str, Any]] = field(default_factory=list)

    # 演化目标
    goals: list[dict[str, Any]] = field(default_factory=list)

    # 演化边界
    boundaries: list[dict[str, Any]] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "human"

    def get_default_seed() -> BootstrapSeed:
        """获取默认种子"""
        seed = BootstrapSeed(
            id="default_seed",
            name="Default Bootstrap Seed",
            description="The minimal seed to bootstrap the self-evolution system",
        )

        # 添加基础元规则
        seed.meta_rules = [
            create_meta_rule(
                name="anomaly_detection_rule",
                condition_field="state.anomaly_score",
                condition_comparator=Comparator.GT,
                condition_value=0.8,
                action_type=ActionType.EMIT,
                action_target="alert_manager",
                action_method="send_alert",
                action_args={"level": "warning"},
                priority=90,
                rule_type=RuleType.SYSTEM,
            ),
            create_meta_rule(
                name="performance_optimization_rule",
                condition_field="state.performance_score",
                condition_comparator=Comparator.LT,
                condition_value=0.7,
                action_type=ActionType.GENERATE,
                action_target="rule_engine",
                action_method="create_rule",
                action_args={"type": "optimization"},
                priority=70,
                rule_type=RuleType.OPTIMIZE,
            ),
            create_meta_rule(
                name="rule_failure_repair_rule",
                condition_field="state.last_rule_status",
                condition_comparator=Comparator.EQ,
                condition_value="failed",
                action_type=ActionType.CALL,
                action_target="repair_engine",
                action_method="repair",
                action_args={},
                priority=85,
                rule_type=RuleType.REPAIR,
            ),
            create_meta_rule(
                name="evolution_trigger_rule",
                condition_field="state.evolution_trigger",
                condition_comparator=Comparator.EQ,
                condition_value=True,
                action_type=ActionType.EVOLVE,
                action_target="evolution_engine",
                action_method="evolve",
                action_args={},
                priority=60,
                rule_type=RuleType.EVOLVE,
            ),
        ]

        # 添加基础约束
        seed.constraints = [
            Constraint(
                id="seed_constraint_001",
                name="state_consistency",
                validator=lambda x: x.get("is_consistent", True),
                severity=Severity.CRITICAL,
            ),
            Constraint(
                id="seed_constraint_002",
                name="no_negative_balance",
                validator=lambda x: x.get("balance", 0) >= 0,
                severity=Severity.CRITICAL,
            ),
            Constraint(
                id="seed_constraint_003",
                name="max_iteration_limit",
                validator=lambda x: x.get("iteration", 0) < 1000,
                severity=Severity.HIGH,
            ),
        ]

        # 添加实体类型
        seed.entity_types = [
            EntityType.META_RULE,
            EntityType.RULE,
            EntityType.CONSTRAINT,
            EntityType.METRIC,
            EntityType.EVOLUTION,
        ]

        # 添加演化方向
        seed.directions = [
            {
                "name": "performance_improvement",
                "priority": 80,
                "vector": {"performance": 1.0, "efficiency": 0.8},
                "constraints": ["cpu_usage < 90", "memory_usage < 95"],
            },
            {
                "name": "reliability_improvement",
                "priority": 75,
                "vector": {"reliability": 1.0, "stability": 0.9},
                "constraints": ["error_rate < 0.01"],
            },
        ]

        # 添加演化目标
        seed.goals = [
            {
                "name": "achieve_self_repair",
                "metric": "repair_success_rate",
                "direction": "increase",
                "target_value": 0.95,
                "goal_type": "achieve",
            },
            {
                "name": "optimize_performance",
                "metric": "avg_response_time",
                "direction": "decrease",
                "target_value": 50,  # ms
                "goal_type": "optimize",
            },
        ]

        # 添加演化边界
        seed.boundaries = [
            {
                "name": "no_data_loss",
                "condition": "data_integrity >= 1.0",
                "boundary_type": "hard",
                "action": "block",
                "severity": "critical",
            },
            {
                "name": "max_resource_usage",
                "condition": "resource_usage < 99",
                "boundary_type": "soft",
                "action": "warn",
                "severity": "high",
            },
        ]

        return seed


@dataclass
class BootstrapCheckpoint:
    """自举检查点"""

    id: CheckpointId
    phase: BootstrapPhase
    state: dict[str, Any]
    rules: list[dict[str, Any]]
    entities: list[dict[str, Any]]
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# 自举引擎
# =============================================================================


class BootstrapEngine:
    """
    自举引擎

    负责系统的自举过程，将最小种子演化为完整的自演化系统。

    自举流程:
    1. 加载种子 (load_seed)
    2. 验证种子 (validate_seed)
    3. 初始化组件 (initialize_components)
    4. 执行分层演化 (execute_layered_evolution)
    5. 验证稳定态 (validate_stable_state)
    6. 完成自举 (complete)

    开发者作为引导者，通过设置方向、目标和边界来引导自举过程。
    """

    def __init__(
        self,
        engine_id: str | None = None,
        seed: BootstrapSeed | None = None,
    ):
        self.id = engine_id or str(uuid.uuid4())

        # 核心组件
        self._rule_engine = MetaRuleEngine()
        self._state_universe = StateUniverse(name=f"bootstrap_{self.id}")
        self._constraint_validator = ConstraintValidator()
        self._guider = EvolutionGuider(role=GuiderRole.ARCHITECT)

        # 自举状态
        self._seed = seed or BootstrapSeed.get_default_seed()
        self._phase = BootstrapPhase.INITIAL
        self._state = BootstrapState.IDLE
        self._checkpoints: list[BootstrapCheckpoint] = []
        self._layer_iterations = 0
        self._total_iterations = 0

        # 配置
        self._max_iterations_per_layer = 100
        self._convergence_threshold = 0.95
        self._auto_continue = True

        self._logger = logging.getLogger(f"{__name__}.Bootstrap.{self.id}")
        self._logger.info(f"BootstrapEngine initialized with seed: {self._seed.name}")

    # =========================================================================
    # 属性访问
    # =========================================================================

    @property
    def rule_engine(self) -> MetaRuleEngine:
        """获取规则引擎"""
        return self._rule_engine

    @property
    def state_universe(self) -> StateUniverse:
        """获取状态宇宙"""
        return self._state_universe

    @property
    def constraint_validator(self) -> ConstraintValidator:
        """获取约束验证器"""
        return self._constraint_validator

    @property
    def guider(self) -> EvolutionGuider:
        """获取引导器"""
        return self._guider

    @property
    def phase(self) -> BootstrapPhase:
        """获取当前阶段"""
        return self._phase

    @property
    def state(self) -> BootstrapState:
        """获取自举状态"""
        return self._state

    # =========================================================================
    # 自举流程
    # =========================================================================

    def bootstrap(self) -> bool:
        """
        执行完整自举流程

        Returns:
            是否成功完成自举
        """
        self._logger.info("Starting bootstrap process...")
        self._state = BootstrapState.RUNNING

        try:
            # 阶段 1: 加载种子
            if not self._load_seed():
                self._fail("Failed to load seed")
                return False

            # 阶段 2: 验证种子
            if not self._validate_seed():
                self._fail("Seed validation failed")
                return False

            # 阶段 3: 初始化组件
            if not self._initialize_components():
                self._fail("Component initialization failed")
                return False

            # 阶段 4: 第一层演化
            if not self._evolve_layer_1():
                self._fail("Layer 1 evolution failed")
                return False

            # 阶段 5: 第二层演化
            if not self._evolve_layer_2():
                self._fail("Layer 2 evolution failed")
                return False

            # 阶段 6: 第三层演化
            if not self._evolve_layer_3():
                self._fail("Layer 3 evolution failed")
                return False

            # 阶段 7: 验证稳定态
            if not self._validate_stable_state():
                self._fail("Stable state validation failed")
                return False

            # 完成
            self._complete()
            return True

        except Exception as e:
            self._logger.error(f"Bootstrap error: {e}", exc_info=True)
            self._fail(str(e))
            return False

    def _load_seed(self) -> bool:
        """加载种子"""
        self._logger.info(f"Loading seed: {self._seed.name}")
        self._phase = BootstrapPhase.SEED

        # 注册种子元规则
        for rule in self._seed.meta_rules:
            rule.evolve_enabled = True
            self._rule_engine.register(rule)

        # 注册种子约束
        for constraint in self._seed.constraints:
            self._constraint_validator.add_constraint(constraint)

        # 创建种子实体
        for entity_type in self._seed.entity_types:
            self._state_universe.create_entity(
                entity_type=entity_type,
                name=f"seed_{entity_type.name}",
            )

        self._save_checkpoint(
            phase=BootstrapPhase.SEED,
            description="Seed loaded",
        )

        self._logger.info(
            f"Seed loaded: {len(self._seed.meta_rules)} rules, " f"{len(self._seed.constraints)} constraints"
        )
        return True

    def _validate_seed(self) -> bool:
        """验证种子"""
        self._logger.info("Validating seed...")

        # 验证元规则
        for rule in self._seed.meta_rules:
            if not rule.condition or not rule.action:
                self._logger.error(f"Invalid rule: {rule.name}")
                return False

        # 验证约束
        for constraint in self._seed.constraints:
            if not constraint.validator:
                self._logger.error(f"Invalid constraint: {constraint.name}")
                return False

        self._logger.info("Seed validation passed")
        return True

    def _initialize_components(self) -> bool:
        """初始化组件"""
        self._logger.info("Initializing components...")

        # 注册目标到规则引擎
        self._rule_engine._executor.register_target("rule_engine", self._rule_engine)
        self._rule_engine._executor.register_target("state_universe", self._state_universe)
        self._rule_engine._executor.register_target("guider", self._guider)

        # 添加引导方向
        for dir_data in self._seed.directions:
            self._guider.add_direction(
                name=dir_data["name"],
                vector=dir_data.get("vector", {}),
                constraints=dir_data.get("constraints", []),
                priority=dir_data.get("priority", 50),
            )

        # 添加引导目标
        for goal_data in self._seed.goals:
            self._guider.add_goal(
                name=goal_data["name"],
                metric=goal_data["metric"],
                direction=goal_data["direction"],
                target_value=goal_data.get("target_value"),
                goal_type=goal_data.get("goal_type", "optimize"),
            )

        # 添加引导边界
        for boundary_data in self._seed.boundaries:
            self._guider.add_boundary(
                name=boundary_data["name"],
                condition=boundary_data["condition"],
                boundary_type=boundary_data.get("boundary_type", "hard"),
                action=boundary_data.get("action", "block"),
                severity=boundary_data.get("severity", "high"),
            )

        self._logger.info("Components initialized")
        return True

    def _evolve_layer_1(self) -> bool:
        """第一层演化: 生成基础状态管理和约束规则"""
        self._logger.info("Evolving Layer 1...")
        self._phase = BootstrapPhase.LAYER_1

        self._layer_iterations = 0
        context = self._create_context()

        while self._layer_iterations < self._max_iterations_per_layer:
            self._layer_iterations += 1
            self._total_iterations += 1

            # 执行规则
            results = self._rule_engine.execute(
                context=context,
                rule_type=RuleType.SYSTEM,
            )

            # 更新上下文
            context = self._update_context(context, results)

            # 检查收敛
            if self._check_convergence(context):
                self._logger.info(f"Layer 1 converged at iteration {self._layer_iterations}")
                break

        self._save_checkpoint(
            phase=BootstrapPhase.LAYER_1,
            description=f"Layer 1 complete, {self._layer_iterations} iterations",
        )

        return True

    def _evolve_layer_2(self) -> bool:
        """第二层演化: 生成复杂规则和元规则"""
        self._logger.info("Evolving Layer 2...")
        self._phase = BootstrapPhase.LAYER_2

        self._layer_iterations = 0
        context = self._create_context()

        while self._layer_iterations < self._max_iterations_per_layer:
            self._layer_iterations += 1
            self._total_iterations += 1

            # 执行规则
            results = self._rule_engine.execute(
                context=context,
                rule_type=RuleType.META,
            )

            # 演化元规则
            for rule in self._rule_engine.get_rules(evolve_enabled=True):
                if rule.can_evolve() and self._should_evolve(rule, context):
                    new_rule = self._rule_engine.evolve(rule.id)
                    if new_rule:
                        self._logger.debug(f"Evolved rule: {rule.id} -> {new_rule.id}")

            # 更新上下文
            context = self._update_context(context, results)

            # 检查收敛
            if self._check_convergence(context):
                self._logger.info(f"Layer 2 converged at iteration {self._layer_iterations}")
                break

        self._save_checkpoint(
            phase=BootstrapPhase.LAYER_2,
            description=f"Layer 2 complete, {self._layer_iterations} iterations",
        )

        return True

    def _evolve_layer_3(self) -> bool:
        """第三层演化: 生成自修复和自优化规则"""
        self._logger.info("Evolving Layer 3...")
        self._phase = BootstrapPhase.LAYER_3

        self._layer_iterations = 0
        context = self._create_context()

        while self._layer_iterations < self._max_iterations_per_layer:
            self._layer_iterations += 1
            self._total_iterations += 1

            # 执行所有规则
            results = self._rule_engine.execute(context=context)

            # 检查约束
            violations = self._constraint_validator.validate_all(context)
            if violations:
                self._handle_violations(violations)

            # 更新上下文
            context = self._update_context(context, results)

            # 检查收敛
            if self._check_convergence(context):
                self._logger.info(f"Layer 3 converged at iteration {self._layer_iterations}")
                break

        self._save_checkpoint(
            phase=BootstrapPhase.LAYER_3,
            description=f"Layer 3 complete, {self._layer_iterations} iterations",
        )

        return True

    def _validate_stable_state(self) -> bool:
        """验证稳定态"""
        self._logger.info("Validating stable state...")
        self._phase = BootstrapPhase.STABLE

        # 检查规则引擎状态
        metrics = self._rule_engine.get_metrics()
        if metrics["failed_triggers"] / max(1, metrics["total_triggers"]) > 0.1:
            self._logger.warning("High failure rate detected")
            return False

        # 检查状态宇宙一致性
        stats = self._state_universe.get_statistics()
        if stats["entities_count"] == 0:
            self._logger.warning("No entities in state universe")
            return False

        # 检查引导目标达成
        goals = self._guider.get_goals(active_only=True)
        if not goals:
            self._logger.info("All goals achieved")

        self._logger.info("Stable state validated")
        return True

    # =========================================================================
    # 辅助方法
    # =========================================================================

    def _create_context(self) -> dict[str, Any]:
        """创建执行上下文"""
        return {
            "iteration": self._total_iterations,
            "layer": self._phase.value,
            "anomaly_score": 0.0,
            "performance_score": 1.0,
            "last_rule_status": "success",
            "evolution_trigger": False,
            "rules_count": len(self._rule_engine.get_rules()),
            "entities_count": len(self._state_universe._entities),
        }

    def _update_context(self, context: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
        """更新执行上下文"""
        context["iteration"] = self._total_iterations

        success_count = sum(1 for r in results if r.get("success", False))
        fail_count = len(results) - success_count

        if results:
            context["last_rule_status"] = "success" if success_count > 0 else "failed"

        context["rules_count"] = len(self._rule_engine.get_rules())
        context["entities_count"] = len(self._state_universe._entities)

        # 计算健康指标
        total = metrics.get("total_triggers", 1)
        success = metrics.get("successful_triggers", 0)
        context["performance_score"] = success / total if total > 0 else 1.0

        return context

    def _should_evolve(self, rule: MetaRule, context: dict[str, Any]) -> bool:
        """判断规则是否应该演化"""
        # 基于触发次数和成功率判断
        if rule.trigger_count < 10:
            return False

        success_rate = rule.success_count / rule.trigger_count
        if success_rate > 0.9:
            return False  # 已经很好，不需要演化

        return True

    def _check_convergence(self, context: dict[str, Any]) -> bool:
        """检查是否收敛"""
        # 检查性能指标是否稳定
        if "performance_score" in context:
            if context["performance_score"] >= self._convergence_threshold:
                return True

        # 检查是否达到最大迭代
        if self._layer_iterations >= self._max_iterations_per_layer:
            return True

        return False

    def _handle_violations(self, violations: list[Any]):
        """处理约束违反"""
        for violation in violations:
            self._logger.warning(f"Constraint violation: {violation}")

    def _save_checkpoint(self, phase: BootstrapPhase, description: str = ""):
        """保存检查点"""
        checkpoint = BootstrapCheckpoint(
            id=str(uuid.uuid4()),
            phase=phase,
            state={
                "iteration": self._total_iterations,
                "layer_iteration": self._layer_iterations,
            },
            rules=[r.to_dict() for r in self._rule_engine.get_rules()],
            entities=[e.to_dict() for e in self._state_universe._entities.values()],
            description=description,
        )

        self._checkpoints.append(checkpoint)
        self._logger.debug(f"Checkpoint saved: {phase.value}")

    def _complete(self):
        """完成自举"""
        self._state = BootstrapState.COMPLETED
        self._phase = BootstrapPhase.COMPLETE

        self._save_checkpoint(
            phase=BootstrapPhase.COMPLETE,
            description=f"Bootstrap complete, total iterations: {self._total_iterations}",
        )

        self._logger.info(
            f"Bootstrap completed successfully! "
            f"Total iterations: {self._total_iterations}, "
            f"Rules: {len(self._rule_engine.get_rules())}, "
            f"Entities: {len(self._state_universe._entities)}"
        )

    def _fail(self, reason: str):
        """自举失败"""
        self._state = BootstrapState.FAILED
        self._logger.error(f"Bootstrap failed: {reason}")

    # =========================================================================
    # 控制方法
    # =========================================================================

    def pause(self):
        """暂停自举"""
        if self._state == BootstrapState.RUNNING:
            self._state = BootstrapState.PAUSED
            self._logger.info("Bootstrap paused")

    def resume(self):
        """恢复自举"""
        if self._state == BootstrapState.PAUSED:
            self._state = BootstrapState.RUNNING
            self._logger.info("Bootstrap resumed")

    def abort(self):
        """中止自举"""
        self._state = BootstrapState.ABORTED
        self._logger.info("Bootstrap aborted")

    def rollback(self, checkpoint_id: CheckpointId) -> bool:
        """回滚到检查点"""
        checkpoint = next((c for c in self._checkpoints if c.id == checkpoint_id), None)

        if not checkpoint:
            return False

        # 恢复状态
        self._phase = checkpoint.phase
        self._total_iterations = checkpoint.state.get("iteration", 0)
        self._layer_iterations = checkpoint.state.get("layer_iteration", 0)

        # 恢复规则
        self._rule_engine._rules = {}
        self._rule_engine._rules_by_type = {}
        for rule_dict in checkpoint.rules:
            rule = MetaRule.from_dict(rule_dict)
            self._rule_engine.register(rule)

        # 恢复实体
        self._state_universe._entities = {}
        for entity_dict in checkpoint.entities:
            entity = StateEntity.from_dict(entity_dict)
            self._state_universe._entities[entity.id] = entity

        self._logger.info(f"Rolled back to checkpoint: {checkpoint_id}")
        return True

    # =========================================================================
    # 状态和统计
    # =========================================================================

    def get_status(self) -> dict[str, Any]:
        """获取自举状态"""
        return {
            "id": self.id,
            "seed": self._seed.name,
            "phase": self._phase.value,
            "state": self._state.value,
            "total_iterations": self._total_iterations,
            "layer_iterations": self._layer_iterations,
            "checkpoints_count": len(self._checkpoints),
            "rules_count": len(self._rule_engine.get_rules()),
            "entities_count": len(self._state_universe._entities),
            "guider_status": self._guider.get_status(),
        }

    def get_metrics(self) -> dict[str, Any]:
        """获取指标"""
        return {
            "total_iterations": self._total_iterations,
            "rules_created": len(self._rule_engine.get_rules()),
            "entities_created": len(self._state_universe._entities),
            "events_recorded": len(self._state_universe._events),
            "snapshots_created": sum(len(s) for s in self._state_universe._snapshots.values()),
            "convergence_rate": (
                self._layer_iterations / self._max_iterations_per_layer if self._max_iterations_per_layer > 0 else 0
            ),
        }

    def get_checkpoints(self) -> list[BootstrapCheckpoint]:
        """获取检查点列表"""
        return self._checkpoints


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    # 类型别名
    "BootstrapId",
    "CheckpointId",
    "PhaseId",
    # 枚举
    "BootstrapPhase",
    "BootstrapState",
    # 数据类
    "BootstrapSeed",
    "BootstrapCheckpoint",
    # 核心类
    "BootstrapEngine",
]
