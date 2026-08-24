"""
L-Base: 基础框架层 - 元规则引擎

元规则引擎是自演化系统的核心，它不是执行具体业务规则，
而是定义规则本身如何存在、变化和演化。

核心概念:
- MetaRule: 元规则定义
- MetaRuleEngine: 元规则执行引擎
- RuleType: 规则类型枚举
- ConditionNode: 条件节点树
- ActionNode: 动作节点树
"""

from __future__ import annotations

import logging
import uuid
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

RuleId = str
Version = str
Priority = int


class RuleType(Enum):
    """规则类型"""

    BUSINESS = auto()  # 业务规则
    SYSTEM = auto()  # 系统规则
    META = auto()  # 元规则
    CONSTRAINT = auto()  # 约束规则
    REPAIR = auto()  # 修复规则
    OPTIMIZE = auto()  # 优化规则
    EVOLVE = auto()  # 演化规则


class ConditionOperator(Enum):
    """条件操作符"""

    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    XOR = "XOR"
    COMPARE = "COMPARE"


class Comparator(Enum):
    """比较器"""

    EQ = "=="  # 等于
    NE = "!="  # 不等于
    GT = ">"  # 大于
    GE = ">="  # 大于等于
    LT = "<"  # 小于
    LE = "<="  # 小于等于
    IN = "IN"  # 在集合中
    NOT_IN = "NOT_IN"
    CONTAINS = "CONTAINS"  # 包含
    MATCHES = "MATCHES"  # 正则匹配


class ActionType(Enum):
    """动作类型"""

    CALL = auto()  # 调用方法
    EMIT = auto()  # 发送事件
    SET = auto()  # 设置属性
    CREATE = auto()  # 创建实体
    DELETE = auto()  # 删除实体
    GENERATE = auto()  # 生成规则
    MUTATE = auto()  # 变异规则
    EVOLVE = auto()  # 演化规则


class RuleStatus(Enum):
    """规则状态"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    DEPRECATED = "deprecated"
    FAILED = "failed"


@dataclass
class RuleMetadata:
    """规则元数据"""

    author: str = "system"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: list[str] = field(default_factory=list)
    description: str = ""
    examples: list[dict[str, Any]] = field(default_factory=list)
    test_cases: list[dict[str, Any]] = field(default_factory=list)


# =============================================================================
# 条件节点和动作节点
# =============================================================================


@dataclass
class ConditionNode:
    """
    条件节点 - 构成条件树的节点

    支持树形结构表示复杂条件:
    - AND/OR/NOT 组合条件
    - 比较条件 (field comparator value)
    - 嵌套条件
    """

    operator: ConditionOperator
    left: ConditionNode | str | None = None
    right: ConditionNode | str | Any | None = None
    field: str = ""  # 字段路径，如 "state.cpu_usage"
    comparator: Comparator = Comparator.EQ
    value: Any = None
    description: str = ""

    def __post_init__(self):
        if self.operator == ConditionOperator.COMPARE:
            assert self.field, "比较条件必须有 field"

    def evaluate(self, context: dict[str, Any]) -> bool:
        """
        评估条件是否满足

        Args:
            context: 评估上下文，包含所有变量的字典

        Returns:
            条件是否满足
        """
        if self.operator == ConditionOperator.AND:
            left_result = self.left.evaluate(context) if isinstance(self.left, ConditionNode) else bool(self.left)
            right_result = self.right.evaluate(context) if isinstance(self.right, ConditionNode) else bool(self.right)
            return left_result and right_result

        elif self.operator == ConditionOperator.OR:
            left_result = self.left.evaluate(context) if isinstance(self.left, ConditionNode) else bool(self.left)
            right_result = self.right.evaluate(context) if isinstance(self.right, ConditionNode) else bool(self.right)
            return left_result or right_result

        elif self.operator == ConditionOperator.NOT:
            child_result = self.left.evaluate(context) if isinstance(self.left, ConditionNode) else bool(self.left)
            return not child_result

        elif self.operator == ConditionOperator.XOR:
            left_result = self.left.evaluate(context) if isinstance(self.left, ConditionNode) else bool(self.left)
            right_result = self.right.evaluate(context) if isinstance(self.right, ConditionNode) else bool(self.right)
            return bool(left_result) != bool(right_result)

        elif self.operator == ConditionOperator.COMPARE:
            field_value = self._get_nested_value(context, self.field)
            return self._compare(field_value, self.value)

        return False

    def _get_nested_value(self, context: dict, field_path: str) -> Any:
        """获取嵌套字段值"""
        keys = field_path.split(".")
        value = context
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif hasattr(value, key):
                value = getattr(value, key)
            else:
                return None
        return value

    def _compare(self, left: Any, right: Any) -> bool:
        """执行比较"""
        # None 值处理
        if left is None:
            return False

        try:
            if self.comparator == Comparator.EQ:
                return left == right
            elif self.comparator == Comparator.NE:
                return left != right
            elif self.comparator == Comparator.GT:
                return left > right
            elif self.comparator == Comparator.GE:
                return left >= right
            elif self.comparator == Comparator.LT:
                return left < right
            elif self.comparator == Comparator.LE:
                return left <= right
            elif self.comparator == Comparator.IN:
                return left in (right if isinstance(right, (list, tuple, set)) else [right])
            elif self.comparator == Comparator.NOT_IN:
                return left not in (right if isinstance(right, (list, tuple, set)) else [right])
            elif self.comparator == Comparator.CONTAINS:
                return right in left if left else False
            elif self.comparator == Comparator.MATCHES:
                import re

                return bool(re.match(right, str(left)))
        except TypeError:
            return False
        return False

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "operator": self.operator.value,
            "left": self.left.to_dict() if isinstance(self.left, ConditionNode) else self.left,
            "right": self.right.to_dict() if isinstance(self.right, ConditionNode) else self.right,
            "field": self.field,
            "comparator": self.comparator.value if self.comparator else None,
            "value": self.value,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConditionNode:
        """从字典创建"""
        left = data.get("left")
        right = data.get("right")

        if isinstance(left, dict):
            left = cls.from_dict(left)
        if isinstance(right, dict):
            right = cls.from_dict(right)

        comparator = data.get("comparator")
        if comparator:
            comparator = Comparator(comparator)

        return cls(
            operator=ConditionOperator(data["operator"]),
            left=left,
            right=right,
            field=data.get("field", ""),
            comparator=comparator,
            value=data.get("value"),
            description=data.get("description", ""),
        )

    @classmethod
    def simple(cls, field: str, comparator: Comparator, value: Any) -> ConditionNode:
        """创建简单比较条件"""
        return cls(
            operator=ConditionOperator.COMPARE,
            field=field,
            comparator=comparator,
            value=value,
        )

    @classmethod
    def and_(cls, left: ConditionNode, right: ConditionNode) -> ConditionNode:
        """创建 AND 条件"""
        return cls(operator=ConditionOperator.AND, left=left, right=right)

    @classmethod
    def or_(cls, left: ConditionNode, right: ConditionNode) -> ConditionNode:
        """创建 OR 条件"""
        return cls(operator=ConditionOperator.OR, left=left, right=right)

    @classmethod
    def not_(cls, child: ConditionNode) -> ConditionNode:
        """创建 NOT 条件"""
        return cls(operator=ConditionOperator.NOT, left=child)


@dataclass
class ActionNode:
    """
    动作节点 - 构成动作树的节点

    支持树形结构表示复杂动作序列
    """

    type: ActionType
    target: str = ""  # 目标对象，如 "rule_engine", "state_universe"
    method: str = ""  # 方法名，如 "register", "execute"
    args: dict[str, Any] = field(default_factory=dict)  # 参数
    next_action: ActionNode | None = None  # 下一个动作
    rollback: ActionNode | None = None  # 回滚动作
    condition: ConditionNode | None = None  # 执行条件
    description: str = ""

    def execute(self, context: dict[str, Any], executor: MetaRuleExecutor) -> dict[str, Any]:
        """
        执行动作

        Args:
            context: 执行上下文
            executor: 执行器实例

        Returns:
            执行结果
        """
        # 检查条件
        if self.condition and not self.condition.evaluate(context):
            return {"skipped": True, "reason": "condition_not_met"}

        try:
            # 获取目标对象
            target = executor.get_target(self.target)

            # 获取方法
            method = getattr(target, self.method, None)
            if not method:
                raise AttributeError(f"Target {self.target} has no method {self.method}")

            # 解析参数
            resolved_args = self._resolve_args(self.args, context)

            # 执行方法
            result = method(**resolved_args)

            # 执行后续动作
            if self.next_action:
                next_result = self.next_action.execute(context, executor)
                result["next"] = next_result

            return {"success": True, "result": result}

        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            # 执行回滚
            if self.rollback:
                self.rollback.execute(context, executor)
            return {"success": False, "error": str(e)}

    def _resolve_args(self, args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """解析参数，支持变量引用 ${var_name}"""
        resolved = {}
        for key, value in args.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                var_name = value[2:-1]
                resolved[key] = context.get(var_name)
            else:
                resolved[key] = value
        return resolved

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type.name,
            "target": self.target,
            "method": self.method,
            "args": self.args,
            "next": self.next_action.to_dict() if self.next_action else None,
            "rollback": self.rollback.to_dict() if self.rollback else None,
            "condition": self.condition.to_dict() if self.condition else None,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ActionNode:
        """从字典创建"""
        next_action = data.get("next")
        if next_action:
            next_action = cls.from_dict(next_action)

        rollback = data.get("rollback")
        if rollback:
            rollback = cls.from_dict(rollback)

        condition = data.get("condition")
        if condition:
            condition = ConditionNode.from_dict(condition)

        return cls(
            type=ActionType[data["type"]],
            target=data.get("target", ""),
            method=data.get("method", ""),
            args=data.get("args", {}),
            next_action=next_action,
            rollback=rollback,
            condition=condition,
            description=data.get("description", ""),
        )


@dataclass
class Constraint:
    """约束定义"""

    id: str
    name: str
    description: str = ""
    validator: Callable[[Any], bool] | None = None
    error_message: str = "Constraint violated"
    severity: str = "high"  # high, medium, low

    def validate(self, value: Any) -> tuple[bool, str | None]:
        """验证约束"""
        if self.validator:
            try:
                if self.validator(value):
                    return True, None
                return False, self.error_message
            except Exception as e:
                return False, f"Validation error: {e}"
        return True, None


@dataclass
class EvolveRule:
    """演化规则 - 定义元规则如何被演化"""

    id: str
    name: str
    mutation_types: list[str] = field(default_factory=list)  # 可用的变异类型
    max_iterations: int = 10
    fitness_function: str | None = None
    selection_strategy: str = "tournament"

    def can_mutate(self, mutation_type: str) -> bool:
        """是否可以进行某种变异"""
        return mutation_type in self.mutation_types


# =============================================================================
# MetaRule 核心定义
# =============================================================================


@dataclass
class MetaRule:
    """
    元规则定义

    元规则是定义规则本身如何创建、修改、演化的规则。
    这是自演化系统的核心——规则生成规则。

    结构:
    - id: 唯一标识
    - name: 规则名称
    - type: 规则类型
    - condition: 触发条件
    - action: 执行动作
    - priority: 优先级
    - dependencies: 依赖规则
    - constraints: 约束列表
    - metadata: 元数据
    - evolve_rules: 演化规则
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: RuleType = RuleType.META
    version: str = "1.0.0"

    # 核心定义
    condition: ConditionNode = field(default_factory=lambda: ConditionNode.simple("true", Comparator.EQ, True))
    action: ActionNode = field(default_factory=lambda: ActionNode(type=ActionType.CALL))

    # 管理属性
    priority: int = 50  # 1-100, 越高越优先
    dependencies: list[str] = field(default_factory=list)  # 依赖的规则ID
    constraints: list[Constraint] = field(default_factory=list)
    metadata: RuleMetadata = field(default_factory=RuleMetadata)
    evolve_rules: list[EvolveRule] = field(default_factory=list)

    # 状态
    status: RuleStatus = RuleStatus.DRAFT
    evolve_enabled: bool = False  # 是否允许自演化
    trigger_count: int = 0  # 触发次数
    success_count: int = 0  # 成功次数
    last_triggered: datetime | None = None
    last_error: str | None = None

    # 时序
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"  # system, human, ai

    def __post_init__(self):
        if not self.name:
            self.name = f"rule_{self.id[:8]}"

    def evaluate(self, context: dict[str, Any]) -> bool:
        """评估条件是否满足"""
        try:
            return self.condition.evaluate(context)
        except Exception as e:
            logger.error(f"Rule {self.id} evaluation error: {e}")
            self.last_error = str(e)
            return False

    def can_evolve(self) -> bool:
        """是否可以演化"""
        return self.evolve_enabled and len(self.evolve_rules) > 0

    def record_trigger(self, success: bool = True):
        """记录触发"""
        self.trigger_count += 1
        if success:
            self.success_count += 1
        self.last_triggered = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.name,
            "version": self.version,
            "condition": self.condition.to_dict(),
            "action": self.action.to_dict(),
            "priority": self.priority,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "evolve_enabled": self.evolve_enabled,
            "trigger_count": self.trigger_count,
            "success_count": self.success_count,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "metadata": {
                "author": self.metadata.author,
                "tags": self.metadata.tags,
                "description": self.metadata.description,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MetaRule:
        """从字典创建"""
        condition = data.get("condition")
        if isinstance(condition, dict):
            condition = ConditionNode.from_dict(condition)

        action = data.get("action")
        if isinstance(action, dict):
            action = ActionNode.from_dict(action)

        metadata = data.get("metadata", {})
        rule_metadata = RuleMetadata(
            author=metadata.get("author", "system"),
            tags=metadata.get("tags", []),
            description=metadata.get("description", ""),
        )

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            type=RuleType[data.get("type", "META")],
            version=data.get("version", "1.0.0"),
            condition=condition or ConditionNode.simple("true", Comparator.EQ, True),
            action=action or ActionNode(type=ActionType.CALL),
            priority=data.get("priority", 50),
            dependencies=data.get("dependencies", []),
            status=RuleStatus(data.get("status", "draft")),
            evolve_enabled=data.get("evolve_enabled", False),
            trigger_count=data.get("trigger_count", 0),
            success_count=data.get("success_count", 0),
            metadata=rule_metadata,
            created_by=data.get("created_by", "system"),
        )


# =============================================================================
# 元规则执行器
# =============================================================================


class MetaRuleExecutor:
    """
    元规则执行器

    负责执行元规则及其动作
    """

    def __init__(self, targets: dict[str, Any] | None = None):
        self._targets: dict[str, Any] = targets or {}
        self._action_history: list[dict[str, Any]] = []
        self._logger = logging.getLogger(f"{__name__}.Executor")

    def register_target(self, name: str, target: Any):
        """注册目标对象"""
        self._targets[name] = target
        self._logger.debug(f"Registered target: {name}")

    def get_target(self, name: str) -> Any:
        """获取目标对象"""
        if name not in self._targets:
            raise KeyError(f"Target not found: {name}")
        return self._targets[name]

    def execute_action(self, action: ActionNode, context: dict[str, Any]) -> dict[str, Any]:
        """执行动作"""
        try:
            result = action.execute(context, self)
            self._action_history.append(
                {
                    "action": action.type.name,
                    "target": action.target,
                    "method": action.method,
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return result
        except Exception as e:
            self._logger.error(f"Action execution failed: {e}")
            return {"success": False, "error": str(e)}

    def get_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """获取动作历史"""
        return self._action_history[-limit:]


# =============================================================================
# MetaRuleEngine 核心引擎
# =============================================================================


class MetaRuleEngine:
    """
    元规则引擎

    负责:
    - 规则注册和管理
    - 规则评估和执行
    - 规则版本控制
    - 规则冲突检测
    - 规则演化

    核心工作流程:
    1. 规则注册 (register)
    2. 规则评估 (evaluate)
    3. 规则执行 (execute)
    4. 规则演化 (evolve)
    """

    def __init__(self):
        # 规则存储
        self._rules: dict[RuleId, MetaRule] = {}
        self._rules_by_type: dict[RuleType, list[MetaRule]] = {}
        self._rules_by_priority: list[MetaRule] = []

        # 依赖图
        self._dependency_graph: dict[RuleId, set[RuleId]] = {}
        self._reverse_graph: dict[RuleId, set[RuleId]] = {}

        # 执行器
        self._executor = MetaRuleExecutor()

        # 事件
        self._event_handlers: dict[str, list[Callable]] = {}

        # 指标
        self._metrics: dict[str, Any] = {
            "total_triggers": 0,
            "successful_triggers": 0,
            "failed_triggers": 0,
            "rules_created": 0,
            "rules_evolved": 0,
        }

        self._logger = logging.getLogger(f"{__name__}.Engine")

    # =========================================================================
    # 规则注册管理
    # =========================================================================

    def register(self, rule: MetaRule) -> None:
        """
        注册元规则

        Args:
            rule: 要注册的规则
        """
        # 检查ID冲突
        if rule.id in self._rules:
            self._logger.warning(f"Rule {rule.id} already exists, replacing")

        # 添加到规则存储
        self._rules[rule.id] = rule

        # 添加到类型索引
        if rule.type not in self._rules_by_type:
            self._rules_by_type[rule.type] = []
        self._rules_by_type[rule.type].append(rule)

        # 更新优先级排序
        self._update_priority_queue()

        # 更新依赖图
        self._update_dependency_graph(rule)

        # 激活规则
        rule.status = RuleStatus.ACTIVE

        self._metrics["rules_created"] += 1
        self._logger.info(f"Registered rule: {rule.id} ({rule.name})")

        # 触发事件
        self._emit("rule_registered", rule)

    def unregister(self, rule_id: RuleId) -> bool:
        """
        注销规则

        Args:
            rule_id: 规则ID

        Returns:
            是否成功注销
        """
        if rule_id not in self._rules:
            return False

        rule = self._rules[rule_id]

        # 检查是否有依赖规则
        if rule_id in self._reverse_graph and self._reverse_graph[rule_id]:
            dependents = self._reverse_graph[rule_id]
            self._logger.warning(f"Cannot unregister {rule_id}: " f"depended by {dependents}")
            return False

        # 从存储中移除
        del self._rules[rule_id]

        # 从类型索引中移除
        if rule.type in self._rules_by_type:
            self._rules_by_type[rule.type] = [r for r in self._rules_by_type[rule.type] if r.id != rule_id]

        # 更新优先级排序
        self._update_priority_queue()

        # 从依赖图中移除
        if rule_id in self._dependency_graph:
            del self._dependency_graph[rule_id]
        for deps in self._dependency_graph.values():
            deps.discard(rule_id)
        if rule_id in self._reverse_graph:
            del self._reverse_graph[rule_id]

        self._logger.info(f"Unregistered rule: {rule_id}")
        self._emit("rule_unregistered", {"rule_id": rule_id})

        return True

    def get_rule(self, rule_id: RuleId) -> MetaRule | None:
        """获取规则"""
        return self._rules.get(rule_id)

    def get_rules(
        self,
        rule_type: RuleType | None = None,
        status: RuleStatus | None = None,
        evolve_enabled: bool | None = None,
    ) -> list[MetaRule]:
        """获取规则列表"""
        rules = list(self._rules.values())

        if rule_type:
            rules = [r for r in rules if r.type == rule_type]
        if status:
            rules = [r for r in rules if r.status == status]
        if evolve_enabled is not None:
            rules = [r for r in rules if r.evolve_enabled == evolve_enabled]

        return rules

    def _update_priority_queue(self):
        """更新优先级队列"""
        self._rules_by_priority = sorted(self._rules.values(), key=lambda r: r.priority, reverse=True)

    def _update_dependency_graph(self, rule: MetaRule):
        """更新依赖图"""
        if rule.id not in self._dependency_graph:
            self._dependency_graph[rule.id] = set()

        # 解析依赖
        for dep_id in rule.dependencies:
            if dep_id not in self._reverse_graph:
                self._reverse_graph[dep_id] = set()
            self._reverse_graph[dep_id].add(rule.id)

    # =========================================================================
    # 规则评估执行
    # =========================================================================

    def evaluate(
        self,
        context: dict[str, Any],
        rule_type: RuleType | None = None,
        max_rules: int = 100,
    ) -> list[tuple[MetaRule, bool]]:
        """
        评估所有规则

        Args:
            context: 评估上下文
            rule_type: 只评估指定类型
            max_rules: 最大评估规则数

        Returns:
            (规则, 是否触发) 列表
        """
        results = []
        rules = self.get_rules(rule_type=rule_type, status=RuleStatus.ACTIVE)
        rules = rules[:max_rules]

        for rule in rules:
            try:
                triggered = rule.evaluate(context)
                results.append((rule, triggered))
            except Exception as e:
                self._logger.error(f"Rule {rule.id} evaluation failed: {e}")
                results.append((rule, False))

        return results

    def execute(
        self,
        context: dict[str, Any],
        rule_type: RuleType | None = None,
        dry_run: bool = False,
    ) -> list[dict[str, Any]]:
        """
        评估并执行触发的规则

        Args:
            context: 执行上下文
            rule_type: 只执行指定类型
            dry_run: 模拟执行，不实际执行

        Returns:
            执行结果列表
        """
        results = []
        evaluations = self.evaluate(context, rule_type)

        for rule, triggered in evaluations:
            if not triggered:
                continue

            self._logger.info(f"Rule triggered: {rule.id} ({rule.name})")

            if dry_run:
                results.append(
                    {
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "action": rule.action.to_dict(),
                        "dry_run": True,
                    }
                )
                continue

            try:
                # 记录触发
                rule.record_trigger(success=True)
                self._metrics["total_triggers"] += 1

                # 执行动作
                action_result = self._executor.execute_action(rule.action, context)

                results.append(
                    {
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "success": action_result.get("success", False),
                        "result": action_result,
                    }
                )

                self._metrics["successful_triggers"] += 1

            except Exception as e:
                self._logger.error(f"Rule {rule.id} execution failed: {e}")
                rule.record_trigger(success=False)
                rule.last_error = str(e)
                self._metrics["failed_triggers"] += 1

                results.append(
                    {
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "success": False,
                        "error": str(e),
                    }
                )

        return results

    # =========================================================================
    # 规则冲突检测
    # =========================================================================

    def detect_conflicts(self, new_rule: MetaRule) -> list[tuple[MetaRule, str]]:
        """
        检测规则冲突

        Args:
            new_rule: 新规则

        Returns:
            冲突列表 [(冲突规则, 冲突原因)]
        """
        conflicts = []

        for rule in self._rules.values():
            if rule.id == new_rule.id:
                continue

            # 优先级冲突
            if rule.priority == new_rule.priority:
                conflicts.append((rule, f"Priority conflict: both have priority {rule.priority}"))

            # 依赖冲突 (循环依赖)
            if new_rule.id in rule.dependencies:
                conflicts.append((rule, "Circular dependency detected"))

            # 条件冲突 (相同条件，不同动作)
            if self._conditions_equal(rule.condition, new_rule.condition):
                if not self._actions_equal(rule.action, new_rule.action):
                    conflicts.append((rule, "Same condition, different actions"))

        return conflicts

    def _conditions_equal(self, c1: ConditionNode, c2: ConditionNode) -> bool:
        """比较两个条件是否等价"""
        if c1.operator != c2.operator:
            return False
        if c1.field and c2.field:
            if c1.field != c2.field:
                return False
            if c1.comparator != c2.comparator:
                return False
            if c1.value != c2.value:
                return False
        return True

    def _actions_equal(self, a1: ActionNode, a2: ActionNode) -> bool:
        """比较两个动作是否等价"""
        return a1.type == a2.type and a1.target == a2.target and a1.method == a2.method

    # =========================================================================
    # 规则演化
    # =========================================================================

    def evolve(
        self,
        rule_id: RuleId,
        mutation_type: str = "parameter_tweak",
    ) -> MetaRule | None:
        """
        演化指定规则

        Args:
            rule_id: 要演化的规则ID
            mutation_type: 变异类型

        Returns:
            演化后的新规则，如果演化失败返回None
        """
        rule = self.get_rule(rule_id)
        if not rule:
            self._logger.error(f"Rule not found: {rule_id}")
            return None

        if not rule.can_evolve():
            self._logger.warning(f"Rule {rule_id} cannot evolve")
            return None

        # 创建副本
        new_rule = MetaRule(
            id=str(uuid.uuid4()),
            name=f"{rule.name}_evolved",
            type=rule.type,
            version=self._increment_version(rule.version),
            condition=ConditionNode.from_dict(rule.condition.to_dict()),
            action=ActionNode.from_dict(rule.action.to_dict()),
            priority=rule.priority,
            dependencies=rule.dependencies.copy(),
            metadata=RuleMetadata(
                author="evolution",
                description=f"Evolved from {rule.id}",
            ),
            evolve_enabled=rule.evolve_enabled,
            created_by="evolution",
        )

        # 应用变异
        self._apply_mutation(new_rule, mutation_type)

        # 注册新规则
        self.register(new_rule)

        self._metrics["rules_evolved"] += 1
        self._logger.info(f"Evolved rule {rule_id} -> {new_rule.id}")

        return new_rule

    def _increment_version(self, version: str) -> str:
        """递增版本号"""
        parts = version.split(".")
        if len(parts) == 3:
            parts[2] = str(int(parts[2]) + 1)
        else:
            parts.append("1")
        return ".".join(parts)

    def _apply_mutation(self, rule: MetaRule, mutation_type: str):
        """应用变异"""
        import random

        if mutation_type == "parameter_tweak":
            # 微调参数
            rule.priority = max(1, min(100, rule.priority + random.randint(-5, 5)))

        elif mutation_type == "condition_expand":
            # 扩展条件
            rule.condition = ConditionNode.and_(rule.condition, ConditionNode.simple("true", Comparator.EQ, True))

        elif mutation_type == "action_add":
            # 添加后续动作
            pass

    # =========================================================================
    # 事件系统
    # =========================================================================

    def subscribe(self, event_type: str, handler: Callable):
        """订阅事件"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def _emit(self, event_type: str, data: Any):
        """触发事件"""
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                self._logger.error(f"Event handler error: {e}")

    # =========================================================================
    # 指标和状态
    # =========================================================================

    def get_metrics(self) -> dict[str, Any]:
        """获取指标"""
        metrics = self._metrics.copy()
        metrics["active_rules"] = len(self.get_rules(status=RuleStatus.ACTIVE))
        metrics["total_rules"] = len(self._rules)
        metrics["rules_by_type"] = {t.name: len(rules) for t, rules in self._rules_by_type.items()}
        return metrics

    def get_status(self) -> dict[str, Any]:
        """获取引擎状态"""
        return {
            "rules_count": len(self._rules),
            "active_rules": len(self.get_rules(status=RuleStatus.ACTIVE)),
            "metrics": self.get_metrics(),
            "targets": list(self._executor._targets.keys()),
        }


# =============================================================================
# 辅助函数
# =============================================================================


def create_meta_rule(
    name: str,
    condition_field: str,
    condition_comparator: Comparator,
    condition_value: Any,
    action_type: ActionType,
    action_target: str,
    action_method: str,
    action_args: dict[str, Any] | None = None,
    priority: int = 50,
    rule_type: RuleType = RuleType.META,
) -> MetaRule:
    """
    创建元规则的便捷函数

    Example:
        rule = create_meta_rule(
            name="high_cpu_alert",
            condition_field="state.cpu_usage",
            condition_comparator=Comparator.GT,
            condition_value=80,
            action_type=ActionType.EMIT,
            action_target="alert_manager",
            action_method="send_alert",
            action_args={"level": "warning"},
            priority=80,
        )
    """
    condition = ConditionNode.simple(
        field=condition_field,
        comparator=condition_comparator,
        value=condition_value,
    )

    action = ActionNode(
        type=action_type,
        target=action_target,
        method=action_method,
        args=action_args or {},
    )

    return MetaRule(
        name=name,
        condition=condition,
        action=action,
        priority=priority,
        type=rule_type,
    )


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    # 类型
    "RuleId",
    "Version",
    "Priority",
    "RuleType",
    "RuleStatus",
    "ConditionOperator",
    "Comparator",
    "ActionType",
    "RuleMetadata",
    "Constraint",
    "EvolveRule",
    # 节点
    "ConditionNode",
    "ActionNode",
    # 核心类
    "MetaRule",
    "MetaRuleExecutor",
    "MetaRuleEngine",
    # 辅助函数
    "create_meta_rule",
]
