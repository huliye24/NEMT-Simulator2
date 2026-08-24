"""
L-Evolve: 自演化层 - 自优化系统

自优化系统是自演化系统的进化引擎。
它持续寻找优化机会并实施优化。

核心概念:
- SelfOptimizeEngine: 自优化引擎
- OptimizeAction: 优化动作
- OptimizePlan: 优化计划
- BottleneckDetector: 瓶颈检测器
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

OptimizeId = str
BottleneckId = str


class OptimizeType(Enum):
    """优化类型"""

    PERFORMANCE = auto()  # 性能优化
    MEMORY = auto()  # 内存优化
    NETWORK = auto()  # 网络优化
    STORAGE = auto()  # 存储优化
    ALGORITHM = auto()  # 算法优化
    CACHE = auto()  # 缓存优化


class OptimizeStatus(Enum):
    """优化状态"""

    PENDING = "pending"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    SUCCESS = "success"
    FAILED = "failed"
    REVERTED = "reverted"


class OptimizeStrategy(Enum):
    """优化策略"""

    CACHE = auto()  # 添加缓存
    BATCH = auto()  # 批处理
    PARALLEL = auto()  # 并行化
    INDEX = auto()  # 添加索引
    COMPRESS = auto()  # 压缩
    PRECOMPUTE = auto()  # 预计算
    DEBOUNCE = auto()  # 防抖
    THROTTLE = auto()  # 节流


# =============================================================================
# 优化定义
# =============================================================================


@dataclass
class Bottleneck:
    """瓶颈"""

    id: BottleneckId
    bottleneck_type: OptimizeType
    severity: str  # critical, high, medium, low
    description: str

    # 上下文
    component: str
    metric_name: str
    current_value: float
    target_value: float

    # 建议
    suggested_strategies: list[OptimizeStrategy] = field(default_factory=list)

    # 状态
    detected_at: datetime = field(default_factory=datetime.now)
    is_resolved: bool = False
    resolved_at: datetime | None = None

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizeAction:
    """优化动作"""

    id: str
    action_type: str
    target: str
    parameters: dict[str, Any] = field(default_factory=dict)
    rollback_action: dict[str, Any] | None = None

    order: int = 0
    estimated_improvement: float = 0.0  # 预期提升百分比
    risk_level: str = "low"

    status: OptimizeStatus = OptimizeStatus.PENDING
    executed_at: datetime | None = None
    actual_improvement: float | None = None
    error: str | None = None


@dataclass
class OptimizePlan:
    """优化计划"""

    id: OptimizeId
    bottleneck_id: BottleneckId
    optimize_type: OptimizeType
    strategy: OptimizeStrategy
    actions: list[OptimizeAction] = field(default_factory=list)

    # 评估
    estimated_total_improvement: float = 0.0
    risk_level: str = "low"
    execution_window: str = "immediate"  # immediate, low_traffic, maintenance

    # 状态
    status: OptimizeStatus = OptimizeStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # 回滚
    can_revert: bool = True
    pre_optimize_snapshot: str | None = None

    def expected_metrics(self) -> dict[str, float]:
        """预期指标改善"""
        return {
            "total_improvement": self.estimated_total_improvement,
            "action_count": len(self.actions),
        }


# =============================================================================
# 瓶颈检测器
# =============================================================================


class BottleneckDetector:
    """瓶颈检测器"""

    def __init__(self):
        self._thresholds: dict[str, dict[str, float]] = {}
        self._baselines: dict[str, float] = {}

    def set_threshold(
        self,
        metric_name: str,
        warning_threshold: float,
        critical_threshold: float,
    ):
        """设置阈值"""
        self._thresholds[metric_name] = {
            "warning": warning_threshold,
            "critical": critical_threshold,
        }

    def set_baseline(self, metric_name: str, baseline: float):
        """设置基线"""
        self._baselines[metric_name] = baseline

    def detect(
        self,
        metric_name: str,
        current_value: float,
        component: str,
    ) -> Bottleneck | None:
        """检测瓶颈"""
        thresholds = self._thresholds.get(metric_name)
        if not thresholds:
            return None

        bottleneck_type = self._infer_type(metric_name)

        # 检查是否超过阈值
        if current_value >= thresholds["critical"]:
            severity = "critical"
            target_value = thresholds["warning"]
        elif current_value >= thresholds["warning"]:
            severity = "high"
            target_value = thresholds["warning"] * 0.8
        else:
            return None

        # 生成建议策略
        strategies = self._infer_strategies(metric_name, current_value)

        bottleneck = Bottleneck(
            id=str(uuid.uuid4()),
            bottleneck_type=bottleneck_type,
            severity=severity,
            description=f"{metric_name} in {component} exceeds threshold",
            component=component,
            metric_name=metric_name,
            current_value=current_value,
            target_value=target_value,
            suggested_strategies=strategies,
        )

        logger.info(f"Bottleneck detected: {metric_name} = {current_value} (target: {target_value})")
        return bottleneck

    def _infer_type(self, metric_name: str) -> OptimizeType:
        """推断优化类型"""
        name_lower = metric_name.lower()

        if "cpu" in name_lower or "time" in name_lower or "latency" in name_lower:
            return OptimizeType.PERFORMANCE
        elif "memory" in name_lower or "heap" in name_lower:
            return OptimizeType.MEMORY
        elif "network" in name_lower or "bandwidth" in name_lower:
            return OptimizeType.NETWORK
        elif "disk" in name_lower or "io" in name_lower:
            return OptimizeType.STORAGE
        elif "cache" in name_lower:
            return OptimizeType.CACHE
        else:
            return OptimizeType.ALGORITHM

    def _infer_strategies(self, metric_name: str, current_value: float) -> list[OptimizeStrategy]:
        """推断优化策略"""
        strategies = []
        name_lower = metric_name.lower()

        if "latency" in name_lower or "time" in name_lower:
            if current_value > 1000:  # > 1s
                strategies.extend([OptimizeStrategy.CACHE, OptimizeStrategy.PARALLEL])
            else:
                strategies.extend([OptimizeStrategy.BATCH, OptimizeStrategy.INDEX])

        if "memory" in name_lower:
            strategies.extend([OptimizeStrategy.COMPRESS, OptimizeStrategy.CACHE])

        if "count" in name_lower or "batch" in name_lower:
            strategies.append(OptimizeStrategy.BATCH)

        if "call" in name_lower or "request" in name_lower:
            strategies.extend([OptimizeStrategy.CACHE, OptimizeStrategy.DEBOUNCE])

        if not strategies:
            strategies.append(OptimizeStrategy.CACHE)

        return strategies


# =============================================================================
# 自优化引擎
# =============================================================================


class SelfOptimizeEngine:
    """
    自优化引擎

    负责:
    - 瓶颈检测
    - 优化计划生成
    - 优化执行
    - 优化验证
    - 回滚
    """

    def __init__(self):
        self._bottlenecks: dict[BottleneckId, Bottleneck] = {}
        self._optimize_plans: dict[OptimizeId, OptimizePlan] = {}
        self._detector = BottleneckDetector()

        # 处理器
        self._optimize_executors: dict[str, Callable] = {}
        self._optimize_handlers: list[Callable] = []

        # 配置
        self._auto_optimize = False
        self._optimization_interval = 60  # 秒

        self._logger = logging.getLogger(f"{__name__}.SelfOptimize")

    def set_auto_optimize(self, enabled: bool):
        """设置自动优化"""
        self._auto_optimize = enabled

    def register_executor(
        self,
        strategy: OptimizeStrategy,
        executor: Callable[[OptimizeAction], dict[str, Any]],
    ):
        """注册优化执行器"""
        self._optimize_executors[strategy.name.lower()] = executor

    def on_optimize_complete(self, handler: Callable):
        """优化完成回调"""
        self._optimize_handlers.append(handler)

    def add_metric_threshold(
        self,
        metric_name: str,
        warning_threshold: float,
        critical_threshold: float,
    ):
        """添加指标阈值"""
        self._detector.set_threshold(metric_name, warning_threshold, critical_threshold)

    def check_metric(
        self,
        metric_name: str,
        current_value: float,
        component: str,
    ) -> Bottleneck | None:
        """检查指标并检测瓶颈"""
        bottleneck = self._detector.detect(metric_name, current_value, component)

        if bottleneck:
            self._bottlenecks[bottleneck.id] = bottleneck

            # 自动创建优化计划
            if self._auto_optimize and bottleneck.severity == "critical":
                self.create_optimize_plan(bottleneck.id)

        return bottleneck

    def get_active_bottlenecks(
        self,
        optimize_type: OptimizeType | None = None,
    ) -> list[Bottleneck]:
        """获取活跃瓶颈"""
        bottlenecks = [b for b in self._bottlenecks.values() if not b.is_resolved]

        if optimize_type:
            bottlenecks = [b for b in bottlenecks if b.bottleneck_type == optimize_type]

        return sorted(bottlenecks, key=lambda b: ({"critical": 0, "high": 1, "medium": 2, "low": 3}.get(b.severity, 4)))

    def create_optimize_plan(self, bottleneck_id: BottleneckId) -> OptimizePlan | None:
        """创建优化计划"""
        bottleneck = self._bottlenecks.get(bottleneck_id)
        if not bottleneck:
            return None

        # 选择策略
        strategies = bottleneck.suggested_strategies
        strategy = strategies[0] if strategies else OptimizeStrategy.CACHE

        # 创建计划
        plan = OptimizePlan(
            id=str(uuid.uuid4()),
            bottleneck_id=bottleneck_id,
            optimize_type=bottleneck.bottleneck_type,
            strategy=strategy,
        )

        # 添加优化动作
        action = OptimizeAction(
            id=str(uuid.uuid4()),
            action_type=strategy.name.lower(),
            target=bottleneck.component,
            parameters={
                "metric": bottleneck.metric_name,
                "current": bottleneck.current_value,
                "target": bottleneck.target_value,
            },
            order=1,
            estimated_improvement=(
                (bottleneck.current_value - bottleneck.target_value) / bottleneck.current_value * 100
                if bottleneck.current_value > 0
                else 0
            ),
        )
        plan.actions.append(action)
        plan.estimated_total_improvement = action.estimated_improvement

        self._optimize_plans[plan.id] = plan
        self._logger.info(f"Created optimize plan {plan.id} for bottleneck {bottleneck_id}")

        return plan

    def execute_optimize(self, plan_id: OptimizeId) -> bool:
        """执行优化计划"""
        plan = self._optimize_plans.get(plan_id)
        if not plan:
            return False

        bottleneck = self._bottlenecks.get(plan.bottleneck_id)

        plan.status = OptimizeStatus.EXECUTING
        plan.started_at = datetime.now()

        self._logger.info(f"Executing optimize plan {plan_id}...")

        # 按顺序执行动作
        for action in plan.actions:
            action.status = OptimizeStatus.EXECUTING

            executor = self._optimize_executors.get(action.action_type)
            if not executor:
                self._logger.warning(f"No executor for action type: {action.action_type}")
                action.status = OptimizeStatus.FAILED
                action.error = "No executor registered"
                plan.status = OptimizeStatus.FAILED
                return False

            try:
                result = executor(action)
                action.status = OptimizeStatus.SUCCESS
                action.executed_at = datetime.now()
                action.actual_improvement = result.get("improvement", 0.0)
                self._logger.info(f"Action {action.action_type} completed")
            except Exception as e:
                self._logger.error(f"Action {action.action_type} failed: {e}")
                action.status = OptimizeStatus.FAILED
                action.error = str(e)
                plan.status = OptimizeStatus.FAILED
                return False

        # 验证优化
        plan.status = OptimizeStatus.VERIFYING
        if self._verify_optimize(plan, bottleneck):
            plan.status = OptimizeStatus.SUCCESS
            plan.completed_at = datetime.now()
            if bottleneck:
                bottleneck.is_resolved = True
                bottleneck.resolved_at = datetime.now()

            self._logger.info(f"Optimize plan {plan_id} completed successfully")

            # 调用完成回调
            for handler in self._optimize_handlers:
                try:
                    handler(bottleneck, plan)
                except Exception as e:
                    self._logger.error(f"Optimize handler error: {e}")

            return True

        plan.status = OptimizeStatus.FAILED
        return False

    def _verify_optimize(self, plan: OptimizePlan, bottleneck: Bottleneck | None) -> bool:
        """验证优化"""
        if not bottleneck:
            return True

        # 检查实际改善
        for action in plan.actions:
            if action.actual_improvement is not None:
                if action.actual_improvement < action.estimated_improvement * 0.5:
                    return False

        return True

    def revert_optimize(self, plan_id: OptimizeId) -> bool:
        """回滚优化"""
        plan = self._optimize_plans.get(plan_id)
        if not plan or not plan.can_revert:
            return False

        self._logger.info(f"Reverting optimize plan {plan_id}...")

        # 执行回滚
        for action in reversed(plan.actions):
            if action.rollback_action:
                # 执行回滚
                pass

        plan.status = OptimizeStatus.REVERTED

        bottleneck = self._bottlenecks.get(plan.bottleneck_id)
        if bottleneck:
            bottleneck.is_resolved = False

        return True

    def get_optimize_history(
        self,
        limit: int = 100,
    ) -> list[OptimizePlan]:
        """获取优化历史"""
        plans = list(self._optimize_plans.values())
        return sorted(plans, key=lambda p: p.created_at, reverse=True)[:limit]

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        plans = list(self._optimize_plans.values())
        bottlenecks = list(self._bottlenecks.values())

        return {
            "total_bottlenecks": len(bottlenecks),
            "active_bottlenecks": len([b for b in bottlenecks if not b.is_resolved]),
            "resolved_bottlenecks": len([b for b in bottlenecks if b.is_resolved]),
            "total_optimizations": len(plans),
            "successful_optimizations": len([p for p in plans if p.status == OptimizeStatus.SUCCESS]),
            "failed_optimizations": len([p for p in plans if p.status == OptimizeStatus.FAILED]),
            "reverted_optimizations": len([p for p in plans if p.status == OptimizeStatus.REVERTED]),
            "success_rate": (len([p for p in plans if p.status == OptimizeStatus.SUCCESS]) / max(1, len(plans))),
            "avg_improvement": (
                sum(p.estimated_total_improvement for p in plans if p.status == OptimizeStatus.SUCCESS)
                / max(1, len([p for p in plans if p.status == OptimizeStatus.SUCCESS]))
            ),
        }


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    # 类型别名
    "OptimizeId",
    "BottleneckId",
    # 枚举
    "OptimizeType",
    "OptimizeStatus",
    "OptimizeStrategy",
    # 数据类
    "Bottleneck",
    "OptimizeAction",
    "OptimizePlan",
    # 核心类
    "BottleneckDetector",
    "SelfOptimizeEngine",
]
