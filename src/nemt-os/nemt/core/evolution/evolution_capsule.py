"""
EvolutionCapsule - 自演化胶囊

将自演化系统封装为 NEMT 的标准胶囊，
使其可以与其他胶囊 (MarketCapsule, SignalCapsule 等) 无缝协作。

核心功能:
- 生命周期管理 (setup, execute, cleanup)
- 事件驱动通信
- 健康检查
- 指标采集
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from typing import (
    Any,
)

from nemt.core.capsule import BaseCapsule
from nemt.core.interfaces import CapsuleState, HealthStatus

# 自演化模块延迟导入
try:
    from nemt.evolution.base.meta_rule_engine import (
        ActionType,
        Comparator,
        MetaRuleEngine,
        RuleType,
        create_meta_rule,
    )
    from nemt.evolution.bootstrap.bootstrap import (
        BootstrapEngine,
        BootstrapPhase,
        BootstrapSeed,
    )
    from nemt.evolution.constraint.constraint import (
        BusinessConstraints,
        Constraint,
        ConstraintValidator,
        Severity,
    )
    from nemt.evolution.guider.guider import (
        EvolutionGuider,
        EvolutionState,
        GuiderRole,
        InterventionType,
    )
    from nemt.evolution.observer.observer import (
        AlertLevel,
        AnomalyDetector,
        MetricType,
        StateObserver,
    )
    from nemt.evolution.self_optimize.self_optimize import (
        OptimizeStatus,
        OptimizeType,
        SelfOptimizeEngine,
    )
    from nemt.evolution.self_repair.self_repair import (
        FaultType,
        RepairStatus,
        SelfRepairEngine,
    )
    from nemt.evolution.state_universe.state_universe import (
        EntityType,
        EventType,
        RelationType,
        StateUniverse,
    )

    EVOLUTION_AVAILABLE = True
except ImportError:
    EVOLUTION_AVAILABLE = False


__all__ = ["EvolutionCapsule"]


class EvolutionCapsule(BaseCapsule):
    """
    自演化胶囊

    封装自演化系统的核心功能，提供标准的胶囊接口。

    用法:
        capsule = EvolutionCapsule(capsule_id="evolution_main")
        capsule.init()
        capsule.execute()  # 执行演化步骤
        capsule.shutdown()
    """

    def __init__(
        self,
        capsule_id: str = "evolution_main",
        auto_bootstrap: bool = True,
        enable_self_repair: bool = True,
        enable_self_optimize: bool = True,
    ):
        super().__init__(capsule_id)

        if not EVOLUTION_AVAILABLE:
            raise ImportError("Evolution modules not available. " "Please ensure nemt.evolution is properly installed.")

        self._auto_bootstrap = auto_bootstrap
        self._enable_self_repair = enable_self_repair
        self._enable_self_optimize = enable_self_optimize

        # 核心组件
        self._state_universe: StateUniverse | None = None
        self._rule_engine: MetaRuleEngine | None = None
        self._constraint_validator: ConstraintValidator | None = None
        self._observer: StateObserver | None = None
        self._repair_engine: SelfRepairEngine | None = None
        self._optimize_engine: SelfOptimizeEngine | None = None
        self._guider: EvolutionGuider | None = None
        self._bootstrap_engine: BootstrapEngine | None = None

        # 状态
        self._is_bootstrapped = False
        self._evolution_iteration = 0

        # 业务胶囊引用
        self._market_capsule = None
        self._signal_capsule = None
        self._risk_capsule = None
        self._execution_capsule = None

        # 回调
        self._on_evolution_step: Callable | None = None
        self._on_anomaly_detected: Callable | None = None

        self._logger = logging.getLogger(f"EvolutionCapsule.{capsule_id}")

    # =========================================================================
    # BaseCapsule 接口实现
    # =========================================================================

    def init(self) -> None:
        """初始化胶囊"""
        self._logger.info("Initializing EvolutionCapsule...")
        self._state = CapsuleState.INITIALIZING

        try:
            # 初始化核心组件
            self._init_state_universe()
            self._init_rule_engine()
            self._init_constraint_validator()
            self._init_observer()
            self._init_repair_engine()
            self._init_optimize_engine()
            self._init_guider()

            # 注册业务约束
            self._register_business_constraints()

            # 注册演化规则
            self._register_evolution_rules()

            # 自动自举
            if self._auto_bootstrap:
                self._bootstrap()

            self._state = CapsuleState.INITIALIZED
            self._logger.info("EvolutionCapsule initialized successfully")

        except Exception as e:
            self._logger.error(f"Initialization failed: {e}")
            self._state = CapsuleState.ERROR
            raise

    def exec(self) -> dict[str, Any]:
        """执行演化步骤"""
        self._check_initialized()
        self._state = CapsuleState.RUNNING

        result = {
            "iteration": self._evolution_iteration,
            "timestamp": datetime.now().isoformat(),
            "actions": [],
            "status": "success",
        }

        try:
            # 1. 收集系统状态
            state = self._collect_system_state()

            # 2. 执行规则
            rule_results = self._rule_engine.execute(state)
            result["actions"].extend(rule_results)

            # 3. 验证约束
            constraint_result = self._constraint_validator.validate(state)
            if not constraint_result.is_valid:
                result["violations"] = [v.message for v in constraint_result.violations]

            # 4. 检查异常
            self._check_anomalies(state)

            # 5. 检查故障和修复
            if self._enable_self_repair:
                self._check_and_repair()

            # 6. 检查瓶颈和优化
            if self._enable_self_optimize:
                self._check_and_optimize()

            # 7. 记录指标
            self._record_metrics(state)

            self._evolution_iteration += 1

        except Exception as e:
            self._logger.error(f"Evolution step failed: {e}")
            result["status"] = "error"
            result["error"] = str(e)
            self._record_error(e)

        # 回调
        if self._on_evolution_step:
            try:
                self._on_evolution_step(result)
            except Exception as e:
                self._logger.error(f"Evolution step callback failed: {e}")

        return result

    def shutdown(self) -> None:
        """关闭胶囊"""
        self._logger.info("Shutting down EvolutionCapsule...")
        self._state = CapsuleState.STOPPING

        # 保存状态
        self._save_state()

        # 清理资源
        self._state = CapsuleState.STOPPED
        self._logger.info("EvolutionCapsule shut down")

    def get_health(self) -> HealthStatus:
        """获取健康状态"""
        if self._state == CapsuleState.ERROR:
            return HealthStatus.UNHEALTHY

        # 检查各组件状态
        issues = []

        if self._repair_engine:
            active_faults = self._repair_engine.get_active_faults()
            if active_faults:
                issues.append(f"{len(active_faults)} active faults")

        if self._optimize_engine:
            active_bottlenecks = self._optimize_engine.get_active_bottlenecks()
            if active_bottlenecks:
                issues.append(f"{len(active_bottlenecks)} bottlenecks")

        if issues:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    # =========================================================================
    # 初始化方法
    # =========================================================================

    def _init_state_universe(self):
        """初始化状态宇宙"""
        self._state_universe = StateUniverse(name=f"evolution_{self._capsule_id}")
        self._logger.debug("StateUniverse initialized")

    def _init_rule_engine(self):
        """初始化规则引擎"""
        self._rule_engine = MetaRuleEngine()
        self._rule_engine._executor.register_target("state_universe", self._state_universe)
        self._rule_engine._executor.register_target("constraint_validator", self._constraint_validator)
        self._rule_engine._executor.register_target("repair_engine", self._repair_engine)
        self._rule_engine._executor.register_target("optimize_engine", self._optimize_engine)
        self._logger.debug("MetaRuleEngine initialized")

    def _init_constraint_validator(self):
        """初始化约束验证器"""
        self._constraint_validator = ConstraintValidator()
        self._logger.debug("ConstraintValidator initialized")

    def _init_observer(self):
        """初始化观测器"""
        self._observer = StateObserver(name=f"evolution_{self._capsule_id}")

        # 注册默认指标
        self._observer.register_metric("evolution_iterations", "Evolution Iterations", MetricType.COUNTER)
        self._observer.register_metric("active_rules", "Active Rules", MetricType.GAUGE)
        self._observer.register_metric("constraint_violations", "Constraint Violations", MetricType.COUNTER)

        self._logger.debug("StateObserver initialized")

    def _init_repair_engine(self):
        """初始化自修复引擎"""
        self._repair_engine = SelfRepairEngine()

        # 注册默认执行器
        self._repair_engine.register_repair_executor("restart", lambda action: {"success": True, "action": "restart"})
        self._repair_engine.register_repair_executor("rollback", lambda action: {"success": True, "action": "rollback"})

        self._logger.debug("SelfRepairEngine initialized")

    def _init_optimize_engine(self):
        """初始化自优化引擎"""
        self._optimize_engine = SelfOptimizeEngine()

        # 设置默认阈值
        self._optimize_engine.add_metric_threshold("latency", 100, 500)
        self._optimize_engine.add_metric_threshold("cpu_usage", 70, 90)
        self._optimize_engine.add_metric_threshold("memory_usage", 80, 95)

        self._logger.debug("SelfOptimizeEngine initialized")

    def _init_guider(self):
        """初始化引导器"""
        self._guider = EvolutionGuider(guider_id=f"guider_{self._capsule_id}", role=GuiderRole.ARCHITECT)

        # 添加默认演化方向
        self._guider.add_direction(
            name="reliability",
            vector={"stability": 1.0, "availability": 0.9},
            priority=80,
            description="提升系统可靠性",
        )

        self._guider.add_direction(
            name="performance",
            vector={"speed": 1.0, "efficiency": 0.8},
            priority=70,
            description="提升系统性能",
        )

        # 添加默认目标
        self._guider.add_goal(
            name="zero_downtime",
            metric="downtime_minutes",
            direction="decrease",
            target_value=0,
            goal_type="achieve",
            description="实现零停机",
        )

        self._logger.debug("EvolutionGuider initialized")

    # =========================================================================
    # 业务集成
    # =========================================================================

    def register_business_capsules(
        self,
        market=None,
        signal=None,
        risk=None,
        execution=None,
    ):
        """注册业务胶囊"""
        self._market_capsule = market
        self._signal_capsule = signal
        self._risk_capsule = risk
        self._execution_capsule = execution

        if market:
            self._rule_engine._executor.register_target("market", market)
        if signal:
            self._rule_engine._executor.register_target("signal", signal)
        if risk:
            self._rule_engine._executor.register_target("risk", risk)
        if execution:
            self._rule_engine._executor.register_target("execution", execution)

    def _collect_system_state(self) -> dict[str, Any]:
        """收集系统状态"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "iteration": self._evolution_iteration,
            "capsule_id": self._capsule_id,
        }

        # 从业务胶囊收集状态
        if self._market_capsule and hasattr(self._market_capsule, "get_metrics"):
            state["market"] = self._market_capsule.get_metrics()

        if self._signal_capsule and hasattr(self._signal_capsule, "get_metrics"):
            state["signal"] = self._signal_capsule.get_metrics()

        if self._risk_capsule and hasattr(self._risk_capsule, "get_metrics"):
            state["risk"] = self._risk_capsule.get_metrics()

        if self._execution_capsule and hasattr(self._execution_capsule, "get_metrics"):
            state["execution"] = self._execution_capsule.get_metrics()

        # 从演化组件收集状态
        if self._rule_engine:
            state["rules_count"] = len(self._rule_engine.get_rules())
            state["metrics"] = self._rule_engine.get_metrics()

        if self._observer:
            state["observer"] = self._observer.get_statistics()

        return state

    # =========================================================================
    # 约束和规则
    # =========================================================================

    def _register_business_constraints(self):
        """注册业务约束"""
        # 账户余额非负
        self._constraint_validator.add_constraint(BusinessConstraints.create_balance_positive())

        # 最大回撤 20%
        self._constraint_validator.add_constraint(BusinessConstraints.create_max_drawdown(0.2))

        # 仓位上限 30%
        self._constraint_validator.add_constraint(BusinessConstraints.create_position_limit(0.3))

        # 置信度范围
        self._constraint_validator.add_constraint(BusinessConstraints.create_confidence_range())

        self._logger.info("Business constraints registered")

    def _register_evolution_rules(self):
        """注册演化规则"""
        # 异常检测规则
        self._rule_engine.register(
            create_meta_rule(
                name="anomaly_alert",
                condition_field="metrics.anomaly_score",
                condition_comparator=Comparator.GT,
                condition_value=0.8,
                action_type=ActionType.EMIT,
                action_target="observer",
                action_method="record",
                action_args={"metric_id": "anomaly_score", "value": 1.0},
                priority=90,
                rule_type=RuleType.SYSTEM,
            )
        )

        # 性能优化规则
        self._rule_engine.register(
            create_meta_rule(
                name="performance_optimize",
                condition_field="metrics.performance_score",
                condition_comparator=Comparator.LT,
                condition_value=0.7,
                action_type=ActionType.CALL,
                action_target="optimize_engine",
                action_method="check_metric",
                priority=70,
                rule_type=RuleType.OPTIMIZE,
            )
        )

        # 故障修复规则
        self._rule_engine.register(
            create_meta_rule(
                name="auto_repair",
                condition_field="metrics.error_count",
                condition_comparator=Comparator.GT,
                condition_value=5,
                action_type=ActionType.CALL,
                action_target="repair_engine",
                action_method="report_fault",
                priority=85,
                rule_type=RuleType.REPAIR,
            )
        )

        self._logger.info("Evolution rules registered")

    # =========================================================================
    # 自修复和自优化
    # =========================================================================

    def _check_anomalies(self, state: dict[str, Any]):
        """检查异常"""
        if not self._observer:
            return

        # 检查约束违规
        for metric_name, threshold in [("latency", 100), ("cpu_usage", 80)]:
            if metric_name in state:
                value = state[metric_name]
                self._observer.record(metric_name, value)

                if value > threshold:
                    bottleneck = self._optimize_engine.check_metric(metric_name, value, self._capsule_id)
                    if bottleneck and self._on_anomaly_detected:
                        self._on_anomaly_detected(bottleneck)

    def _check_and_repair(self):
        """检查并修复故障"""
        active_faults = self._repair_engine.get_active_faults()

        for fault in active_faults:
            # 检查是否有现成的修复计划
            plans = self._repair_engine.get_repair_history(limit=10)
            if not any(p.fault_id == fault.id and p.status == RepairStatus.SUCCESS for p in plans):
                # 创建并执行修复计划
                plan = self._repair_engine.create_repair_plan(fault.id)
                if plan:
                    self._repair_engine.execute_repair(plan.id)

    def _check_and_optimize(self):
        """检查并优化"""
        # 检查活跃瓶颈
        bottlenecks = self._optimize_engine.get_active_bottlenecks()

        for bottleneck in bottlenecks[:3]:  # 最多处理3个
            # 创建并执行优化计划
            plan = self._optimize_engine.create_optimize_plan(bottleneck.id)
            if plan:
                self._optimize_engine.execute_optimize(plan.id)

    def _record_metrics(self, state: dict[str, Any]):
        """记录指标"""
        if not self._observer:
            return

        self._observer.record("evolution_iterations", self._evolution_iteration)

        if "rules_count" in state:
            self._observer.record("active_rules", state["rules_count"])

    # =========================================================================
    # 自举
    # =========================================================================

    def _bootstrap(self):
        """执行自举"""
        self._logger.info("Starting bootstrap...")

        # 创建自举引擎
        seed = BootstrapSeed.get_default_seed()
        self._bootstrap_engine = BootstrapEngine(seed=seed)

        # 执行自举
        success = self._bootstrap_engine.bootstrap()

        if success:
            self._is_bootstrapped = True
            self._logger.info("Bootstrap completed successfully")
        else:
            self._logger.warning("Bootstrap completed with issues")

    # =========================================================================
    # 状态持久化
    # =========================================================================

    def _save_state(self):
        """保存状态"""
        if not self._state_universe:
            return

        # 保存到状态宇宙
        entity = self._state_universe.create_entity(
            entity_type=EntityType.EVOLUTION,
            name=f"evolution_state_{self._capsule_id}",
            properties={
                "is_bootstrapped": self._is_bootstrapped,
                "iteration": self._evolution_iteration,
                "state": self._state.value,
            },
        )

        self._state_universe.snapshot(
            entity.id,
            description="pre_shutdown_snapshot",
            tags=["shutdown", "backup"],
        )

    # =========================================================================
    # 回调设置
    # =========================================================================

    def on_evolution_step(self, callback: Callable[[dict], None]):
        """设置演化步骤回调"""
        self._on_evolution_step = callback

    def on_anomaly_detected(self, callback: Callable[[Any], None]):
        """设置异常检测回调"""
        self._on_anomaly_detected = callback

    # =========================================================================
    # 状态和指标
    # =========================================================================

    def get_status(self) -> dict[str, Any]:
        """获取状态"""
        return {
            "capsule_id": self._capsule_id,
            "state": self._state.value,
            "is_bootstrapped": self._is_bootstrapped,
            "evolution_iteration": self._evolution_iteration,
            "health": self.get_health().value,
            "components": {
                "state_universe": self._state_universe is not None,
                "rule_engine": self._rule_engine is not None,
                "constraint_validator": self._constraint_validator is not None,
                "observer": self._observer is not None,
                "repair_engine": self._repair_engine is not None,
                "optimize_engine": self._optimize_engine is not None,
                "guider": self._guider is not None,
            },
        }

    def get_metrics(self) -> dict[str, Any]:
        """获取指标"""
        metrics = {
            "evolution_iterations": self._evolution_iteration,
        }

        if self._rule_engine:
            metrics["rule_engine"] = self._rule_engine.get_metrics()

        if self._observer:
            metrics["observer"] = self._observer.get_statistics()

        if self._repair_engine:
            metrics["repair_engine"] = self._repair_engine.get_statistics()

        if self._optimize_engine:
            metrics["optimize_engine"] = self._optimize_engine.get_statistics()

        if self._guider:
            metrics["guider"] = self._guider.get_status()

        return metrics
