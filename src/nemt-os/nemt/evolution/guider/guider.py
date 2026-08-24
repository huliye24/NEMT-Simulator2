"""
L-Guide: 开发者引导者层 - 演化引导器

当系统具备自演化能力后，开发者的角色从"建造者"转变为"引导者"。
引导者通过定义演化方向、设置约束、观察演化结果来引导系统。

核心概念:
- EvolutionGuider: 演化引导器
- EvolutionDirection: 演化方向定义
- EvolutionGoal: 演化目标定义
- EvolutionBoundary: 演化边界定义
- EvolutionTrajectory: 演化轨迹追踪
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import (
    Any,
)

logger = logging.getLogger(__name__)

# =============================================================================
# 基础类型定义
# =============================================================================

GuiderId = str
DirectionId = str
GoalId = str
BoundaryId = str
TrajectoryId = str


class EvolutionState(Enum):
    """演化状态"""

    IDLE = "idle"  # 空闲
    RUNNING = "running"  # 运行中
    PAUSED = "paused"  # 已暂停
    STOPPED = "stopped"  # 已停止
    CONVERGED = "converged"  # 已收敛
    DIVERGED = "diverged"  # 已发散
    FAILED = "failed"  # 失败


class InterventionType(Enum):
    """干预类型"""

    ACCELERATE = auto()  # 加速
    DECELERATE = auto()  # 减速
    PAUSE = auto()  # 暂停
    RESUME = auto()  # 恢复
    STEER = auto()  # 转向
    TERMINATE = auto()  # 终止
    INJECT = auto()  # 注入
    MODIFY_GOAL = auto()  # 修改目标


class GuiderRole(Enum):
    """引导者角色"""

    ARCHITECT = "architect"  # 架构师
    WATCHDOG = "watchdog"  # 看门狗
    CATALYST = "catalyst"  # 催化剂
    MEDIATOR = "mediator"  # 调解者


# =============================================================================
# 演化方向定义
# =============================================================================


@dataclass
class EvolutionDirection:
    """
    演化方向定义

    定义系统应该向哪个方向演化。
    开发者作为引导者，首先定义方向。
    """

    id: DirectionId
    name: str
    description: str = ""
    priority: int = 50  # 1-100
    weight: float = 1.0  # 影响权重

    # 方向向量 (多维空间)
    vector: dict[str, float] = field(default_factory=dict)

    # 约束条件
    constraints: list[str] = field(default_factory=list)  # 约束表达式

    # 目标指标
    target_metrics: dict[str, Any] = field(default_factory=dict)

    # 状态
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "human"

    def matches_state(self, state: dict[str, Any]) -> bool:
        """检查状态是否符合此方向"""
        if not self.is_active:
            return False

        # 检查约束
        for constraint in self.constraints:
            if not self._evaluate_constraint(constraint, state):
                return False

        return True

    def _evaluate_constraint(self, constraint: str, state: dict[str, Any]) -> bool:
        """评估约束"""
        try:
            # 简单的约束评估
            # 格式: "metric > threshold" 或 "metric < threshold"
            import re

            match = re.match(r"(\w+)\s*(>|<|>=|<=|==|!=)\s*([\d.]+)", constraint)
            if match:
                metric, op, threshold = match.groups()
                value = state.get(metric, 0)
                threshold = float(threshold)

                if op == ">":
                    return value > threshold
                elif op == "<":
                    return value < threshold
                elif op == ">=":
                    return value >= threshold
                elif op == "<=":
                    return value <= threshold
                elif op == "==":
                    return value == threshold
                elif op == "!=":
                    return value != threshold

            return True
        except Exception:
            return True

    def calculate_alignment(self, state: dict[str, Any]) -> float:
        """计算状态与方向的匹配度"""
        if not self.vector:
            return 0.0

        # 简化的余弦相似度
        alignment = 0.0
        for key, target_value in self.vector.items():
            current_value = state.get(key, 0)
            if target_value != 0:
                alignment += (current_value * target_value) / (abs(current_value) * abs(target_value) + 1e-6)

        return alignment / (len(self.vector) + 1e-6)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "weight": self.weight,
            "vector": self.vector,
            "constraints": self.constraints,
            "target_metrics": self.target_metrics,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }


# =============================================================================
# 演化目标定义
# =============================================================================


@dataclass
class EvolutionGoal:
    """
    演化目标定义

    定义具体的、可衡量的演化目标。
    """

    id: GoalId
    name: str
    description: str = ""

    # 目标类型
    goal_type: str = "optimize"  # optimize, achieve, maintain, avoid

    # 目标指标
    metric: str = ""
    direction: str = "increase"  # increase, decrease, maintain, reach
    target_value: float | None = None
    threshold: float = 0.01  # 达成阈值

    # 时间约束
    deadline: datetime | None = None
    max_iterations: int = 100

    # 状态
    current_value: float | None = None
    progress: float = 0.0  # 0-100
    is_achieved: bool = False
    is_abandoned: bool = False

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_progress(self, current_value: float) -> bool:
        """更新进度，返回是否达成"""
        self.current_value = current_value
        self.updated_at = datetime.now()

        if self.direction == "increase":
            if self.target_value:
                self.progress = min(100, (current_value / self.target_value) * 100)
                if current_value >= self.target_value * (1 - self.threshold):
                    self.is_achieved = True
        elif self.direction == "decrease":
            if self.target_value:
                initial = self.target_value * 2  # 假设初始值是目标的两倍
                self.progress = min(100, ((initial - current_value) / (initial - self.target_value)) * 100)
                if current_value <= self.target_value * (1 + self.threshold):
                    self.is_achieved = True
        elif self.direction == "reach":
            if self.target_value:
                distance = abs(current_value - self.target_value)
                if distance <= self.threshold * abs(self.target_value):
                    self.is_achieved = True

        return self.is_achieved

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "goal_type": self.goal_type,
            "metric": self.metric,
            "direction": self.direction,
            "target_value": self.target_value,
            "progress": self.progress,
            "is_achieved": self.is_achieved,
            "is_abandoned": self.is_abandoned,
            "created_at": self.created_at.isoformat(),
        }


# =============================================================================
# 演化边界定义
# =============================================================================


@dataclass
class EvolutionBoundary:
    """
    演化边界定义

    定义演化的安全边界，防止破坏性演化。
    """

    id: BoundaryId
    name: str
    description: str = ""

    # 边界类型
    boundary_type: str = "hard"  # hard (不可逾越), soft (警告), adaptive (可调整)

    # 边界条件
    condition: str = ""  # 条件表达式
    action: str = "block"  # block, warn, log

    # 元数据
    is_active: bool = True
    severity: str = "high"  # critical, high, medium, low
    exceptions: list[str] = field(default_factory=list)  # 例外列表

    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "human"

    def check(self, state: dict[str, Any], proposed_change: dict[str, Any]) -> tuple[bool, str | None]:
        """
        检查是否越界

        Returns:
            (是否安全, 警告消息)
        """
        if not self.is_active:
            return True, None

        # 检查是否有例外
        if str(proposed_change) in self.exceptions:
            return True, None

        try:
            # 评估边界条件
            import re

            match = re.match(r"(\w+)\s*(>|<|>=|<=|==|!=)\s*([\d.]+)", self.condition)
            if match:
                metric, op, threshold = match.groups()
                value = proposed_change.get(metric, state.get(metric, 0))
                threshold = float(threshold)

                is_violated = False
                if op == ">" and value > threshold:
                    is_violated = True
                elif op == "<" and value < threshold:
                    is_violated = True
                elif op == ">=" and value >= threshold:
                    is_violated = True
                elif op == "<=" and value <= threshold:
                    is_violated = True
                elif op == "==" and value == threshold:
                    is_violated = True
                elif op == "!=" and value != threshold:
                    is_violated = True

                if is_violated:
                    if self.action == "block":
                        return False, f"Boundary violated: {self.name}"
                    elif self.action == "warn":
                        return True, f"Warning: {self.name} boundary approached"
                    else:
                        return True, None

            return True, None
        except Exception as e:
            logger.error(f"Boundary check error: {e}")
            return True, None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "boundary_type": self.boundary_type,
            "condition": self.condition,
            "action": self.action,
            "is_active": self.is_active,
            "severity": self.severity,
            "created_at": self.created_at.isoformat(),
        }


# =============================================================================
# 演化轨迹追踪
# =============================================================================


@dataclass
class EvolutionTrajectory:
    """
    演化轨迹

    记录系统的演化历史，用于分析和回溯。
    """

    id: TrajectoryId
    name: str = ""
    description: str = ""

    # 轨迹点
    points: list[dict[str, Any]] = field(default_factory=list)

    # 统计
    total_steps: int = 0
    successful_steps: int = 0
    failed_steps: int = 0

    # 状态
    state: EvolutionState = EvolutionState.IDLE
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_point(
        self,
        step: int,
        state: dict[str, Any],
        metrics: dict[str, float],
        action: str | None = None,
        result: str | None = None,
        intervention: dict[str, Any] | None = None,
    ):
        """添加轨迹点"""
        self.points.append(
            {
                "step": step,
                "timestamp": datetime.now().isoformat(),
                "state": state,
                "metrics": metrics,
                "action": action,
                "result": result,
                "intervention": intervention,
            }
        )
        self.total_steps += 1

        if result == "success":
            self.successful_steps += 1
        elif result == "failed":
            self.failed_steps += 1

    def get_success_rate(self) -> float:
        """计算成功率"""
        if self.total_steps == 0:
            return 0.0
        return self.successful_steps / self.total_steps

    def get_recent_points(self, n: int = 10) -> list[dict[str, Any]]:
        """获取最近的n个点"""
        return self.points[-n:] if self.points else []

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "total_steps": self.total_steps,
            "successful_steps": self.successful_steps,
            "failed_steps": self.failed_steps,
            "success_rate": self.get_success_rate(),
            "state": self.state.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "points": self.points,
        }


# =============================================================================
# 干预记录
# =============================================================================


@dataclass
class Intervention:
    """干预记录"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: InterventionType = InterventionType.STEER
    target: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    result: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    actor: str = "human"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.name,
            "target": self.target,
            "parameters": self.parameters,
            "reason": self.reason,
            "result": self.result,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
        }


# =============================================================================
# 演化引导器
# =============================================================================


class EvolutionGuider:
    """
    演化引导器

    开发者通过引导器来引导系统的自演化过程。
    主要功能:
    - 定义演化方向
    - 设置演化目标
    - 划定演化边界
    - 观察演化轨迹
    - 干预演化过程
    """

    def __init__(self, guider_id: str | None = None, role: GuiderRole = GuiderRole.ARCHITECT):
        self.id = guider_id or str(uuid.uuid4())
        self.role = role

        # 核心组件
        self._directions: dict[DirectionId, EvolutionDirection] = {}
        self._goals: dict[GoalId, EvolutionGoal] = {}
        self._boundaries: dict[BoundaryId, EvolutionBoundary] = {}
        self._trajectories: dict[TrajectoryId, EvolutionTrajectory] = {}

        # 当前轨迹
        self._current_trajectory: EvolutionTrajectory | None = None

        # 干预历史
        self._interventions: list[Intervention] = []

        # 回调
        self._callbacks: dict[str, list[Callable]] = defaultdict(list)

        self._logger = logging.getLogger(f"{__name__}.Guider.{self.id}")
        self._logger.info(f"EvolutionGuider initialized, role: {role.value}")

    # =========================================================================
    # 方向管理
    # =========================================================================

    def add_direction(
        self,
        name: str,
        description: str = "",
        vector: dict[str, float] | None = None,
        constraints: list[str] | None = None,
        priority: int = 50,
        created_by: str = "human",
    ) -> EvolutionDirection:
        """
        添加演化方向

        Args:
            name: 方向名称
            description: 描述
            vector: 方向向量
            constraints: 约束条件
            priority: 优先级
            created_by: 创建者
        """
        direction = EvolutionDirection(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            vector=vector or {},
            constraints=constraints or [],
            priority=priority,
            created_by=created_by,
        )

        self._directions[direction.id] = direction
        self._logger.info(f"Added direction: {direction.name} ({direction.id})")

        self._emit("direction_added", direction)
        return direction

    def remove_direction(self, direction_id: DirectionId) -> bool:
        """移除演化方向"""
        if direction_id in self._directions:
            direction = self._directions[direction_id]
            del self._directions[direction_id]
            self._logger.info(f"Removed direction: {direction.name}")
            self._emit("direction_removed", direction)
            return True
        return False

    def get_directions(self, active_only: bool = False) -> list[EvolutionDirection]:
        """获取演化方向列表"""
        directions = list(self._directions.values())
        if active_only:
            directions = [d for d in directions if d.is_active]
        return sorted(directions, key=lambda d: d.priority, reverse=True)

    def get_best_direction(self, state: dict[str, Any]) -> EvolutionDirection | None:
        """获取最匹配的方向"""
        directions = self.get_directions(active_only=True)
        if not directions:
            return None

        best = None
        best_alignment = -1

        for direction in directions:
            if direction.matches_state(state):
                alignment = direction.calculate_alignment(state)
                if alignment > best_alignment:
                    best_alignment = alignment
                    best = direction

        return best

    # =========================================================================
    # 目标管理
    # =========================================================================

    def add_goal(
        self,
        name: str,
        metric: str,
        direction: str,
        target_value: float | None = None,
        deadline: datetime | None = None,
        description: str = "",
        goal_type: str = "optimize",
    ) -> EvolutionGoal:
        """添加演化目标"""
        goal = EvolutionGoal(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            goal_type=goal_type,
            metric=metric,
            direction=direction,
            target_value=target_value,
            deadline=deadline,
        )

        self._goals[goal.id] = goal
        self._logger.info(f"Added goal: {goal.name} ({goal.id})")

        self._emit("goal_added", goal)
        return goal

    def update_goal_progress(self, goal_id: GoalId, current_value: float) -> bool:
        """更新目标进度"""
        goal = self._goals.get(goal_id)
        if not goal:
            return False

        is_achieved = goal.update_progress(current_value)
        self._emit("goal_progress", {"goal": goal, "achieved": is_achieved})

        if is_achieved:
            self._logger.info(f"Goal achieved: {goal.name}")
            self._emit("goal_achieved", goal)

        return is_achieved

    def abandon_goal(self, goal_id: GoalId, reason: str = "") -> bool:
        """放弃目标"""
        goal = self._goals.get(goal_id)
        if not goal:
            return False

        goal.is_abandoned = True
        self._logger.info(f"Goal abandoned: {goal.name}, reason: {reason}")
        self._emit("goal_abandoned", {"goal": goal, "reason": reason})
        return True

    def get_goals(
        self,
        achieved_only: bool = False,
        active_only: bool = False,
    ) -> list[EvolutionGoal]:
        """获取目标列表"""
        goals = list(self._goals.values())

        if achieved_only:
            goals = [g for g in goals if g.is_achieved]
        if active_only:
            goals = [g for g in goals if not g.is_achieved and not g.is_abandoned]

        return sorted(goals, key=lambda g: g.priority, reverse=True)

    # =========================================================================
    # 边界管理
    # =========================================================================

    def add_boundary(
        self,
        name: str,
        condition: str,
        action: str = "block",
        boundary_type: str = "hard",
        severity: str = "high",
        description: str = "",
    ) -> EvolutionBoundary:
        """添加演化边界"""
        boundary = EvolutionBoundary(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            condition=condition,
            action=action,
            boundary_type=boundary_type,
            severity=severity,
        )

        self._boundaries[boundary.id] = boundary
        self._logger.info(f"Added boundary: {boundary.name}")

        self._emit("boundary_added", boundary)
        return boundary

    def check_boundaries(
        self,
        state: dict[str, Any],
        proposed_change: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """检查是否越界"""
        warnings = []
        is_safe = True

        for boundary in self._boundaries.values():
            safe, msg = boundary.check(state, proposed_change)
            if not safe:
                is_safe = False
                warnings.append(msg)
            elif msg:
                warnings.append(msg)

        return is_safe, warnings

    def remove_boundary(self, boundary_id: BoundaryId) -> bool:
        """移除边界"""
        if boundary_id in self._boundaries:
            del self._boundaries[boundary_id]
            return True
        return False

    # =========================================================================
    # 轨迹追踪
    # =========================================================================

    def start_trajectory(
        self,
        name: str = "",
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> EvolutionTrajectory:
        """开始新轨迹"""
        trajectory = EvolutionTrajectory(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            metadata=metadata or {},
        )

        self._trajectories[trajectory.id] = trajectory
        self._current_trajectory = trajectory

        self._logger.info(f"Started trajectory: {trajectory.id}")
        self._emit("trajectory_started", trajectory)

        return trajectory

    def record_step(
        self,
        step: int,
        state: dict[str, Any],
        metrics: dict[str, float],
        action: str | None = None,
        result: str | None = None,
    ):
        """记录演化步骤"""
        if not self._current_trajectory:
            self.start_trajectory()

        self._current_trajectory.add_point(
            step=step,
            state=state,
            metrics=metrics,
            action=action,
            result=result,
        )

        self._emit(
            "step_recorded",
            {
                "trajectory": self._current_trajectory,
                "step": step,
            },
        )

    def end_trajectory(self, state: EvolutionState = EvolutionState.STOPPED):
        """结束当前轨迹"""
        if self._current_trajectory:
            self._current_trajectory.state = state
            self._current_trajectory.end_time = datetime.now()

            self._logger.info(
                f"Ended trajectory: {self._current_trajectory.id}, "
                f"state: {state.value}, "
                f"steps: {self._current_trajectory.total_steps}"
            )

            self._emit("trajectory_ended", self._current_trajectory)
            self._current_trajectory = None

    def get_trajectories(
        self,
        limit: int = 10,
    ) -> list[EvolutionTrajectory]:
        """获取轨迹列表"""
        trajectories = list(self._trajectories.values())
        return sorted(trajectories, key=lambda t: t.start_time, reverse=True)[:limit]

    # =========================================================================
    # 干预
    # =========================================================================

    def intervene(
        self,
        intervention_type: InterventionType,
        reason: str,
        parameters: dict[str, Any] | None = None,
        target: str | None = None,
    ) -> Intervention:
        """执行干预"""
        intervention = Intervention(
            type=intervention_type,
            target=target,
            parameters=parameters or {},
            reason=reason,
            actor=self.role.value,
        )

        self._interventions.append(intervention)
        self._logger.info(f"Intervention: {intervention_type.name}, reason: {reason}")

        self._emit("intervention", intervention)

        return intervention

    def accelerate(self, factor: float = 2.0, reason: str = ""):
        """加速演化"""
        return self.intervene(
            InterventionType.ACCELERATE,
            reason=reason or "Accelerating evolution",
            parameters={"factor": factor},
        )

    def decelerate(self, factor: float = 0.5, reason: str = ""):
        """减速演化"""
        return self.intervene(
            InterventionType.DECELERATE,
            reason=reason or "Decelerating evolution",
            parameters={"factor": factor},
        )

    def steer(
        self,
        direction_id: DirectionId,
        reason: str = "",
    ):
        """转向"""
        direction = self._directions.get(direction_id)
        if not direction:
            self._logger.warning(f"Direction not found: {direction_id}")
            return None

        return self.intervene(
            InterventionType.STEER,
            reason=reason or f"Steering to {direction.name}",
            parameters={"direction_id": direction_id},
            target=direction_id,
        )

    def terminate(self, reason: str = ""):
        """终止演化"""
        self.end_trajectory(EvolutionState.STOPPED)
        return self.intervene(
            InterventionType.TERMINATE,
            reason=reason or "Evolution terminated by guider",
        )

    def get_interventions(self, limit: int = 100) -> list[Intervention]:
        """获取干预历史"""
        return self._interventions[-limit:]

    # =========================================================================
    # 订阅
    # =========================================================================

    def subscribe(self, event_type: str, callback: Callable):
        """订阅事件"""
        self._callbacks[event_type].append(callback)

    def _emit(self, event_type: str, data: Any):
        """触发事件"""
        for callback in self._callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                self._logger.error(f"Callback error: {e}")

    # =========================================================================
    # 状态和统计
    # =========================================================================

    def get_status(self) -> dict[str, Any]:
        """获取引导器状态"""
        return {
            "id": self.id,
            "role": self.role.value,
            "directions_count": len(self._directions),
            "active_directions": len(self.get_directions(active_only=True)),
            "goals_count": len(self._goals),
            "achieved_goals": len(self.get_goals(achieved_only=True)),
            "active_goals": len(self.get_goals(active_only=True)),
            "boundaries_count": len(self._boundaries),
            "trajectories_count": len(self._trajectories),
            "interventions_count": len(self._interventions),
            "current_trajectory": (self._current_trajectory.id if self._current_trajectory else None),
        }

    def get_summary(self) -> dict[str, Any]:
        """获取摘要"""
        trajectories = self.get_trajectories()
        recent_trajectory = trajectories[0] if trajectories else None

        return {
            "status": self.get_status(),
            "recent_trajectory": (recent_trajectory.to_dict() if recent_trajectory else None),
            "active_directions": [d.to_dict() for d in self.get_directions(active_only=True)],
            "active_goals": [g.to_dict() for g in self.get_goals(active_only=True)],
            "recent_interventions": [i.to_dict() for i in self.get_interventions(limit=10)],
        }


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    # 类型别名
    "GuiderId",
    "DirectionId",
    "GoalId",
    "BoundaryId",
    "TrajectoryId",
    # 枚举
    "EvolutionState",
    "InterventionType",
    "GuiderRole",
    # 数据类
    "EvolutionDirection",
    "EvolutionGoal",
    "EvolutionBoundary",
    "EvolutionTrajectory",
    "Intervention",
    # 核心类
    "EvolutionGuider",
]
