"""
L-Rule: 规则生成层 - 约束系统

约束系统是自演化系统的法律框架。
它定义了什么是允许的、什么是不允许的、违反约束后如何处理。
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

ConstraintId = str
ViolationId = str


class ConstraintType(Enum):
    """约束类型"""

    BUSINESS = auto()  # 业务约束
    SYSTEM = auto()  # 系统约束
    SECURITY = auto()  # 安全约束
    PERFORMANCE = auto()  # 性能约束
    DATA = auto()  # 数据约束


class Severity(Enum):
    """严重程度"""

    CRITICAL = "critical"  # 极高
    HIGH = "high"  # 高
    MEDIUM = "medium"  # 中
    LOW = "low"  # 低


class ValidationLevel(Enum):
    """验证级别"""

    STRICT = auto()  # 严格 - 拒绝操作
    WARNING = auto()  # 警告 - 记录但不拒绝
    LOG = auto()  # 日志 - 仅记录


# =============================================================================
# 约束违规
# =============================================================================


@dataclass
class ConstraintViolation:
    """约束违规"""

    id: ViolationId
    constraint_id: ConstraintId
    constraint_name: str
    entity_id: str | None
    state: dict[str, Any]
    message: str
    severity: Severity
    timestamp: datetime = field(default_factory=datetime.now)
    auto_fixable: bool = False
    fix_action: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "constraint_id": self.constraint_id,
            "constraint_name": self.constraint_name,
            "entity_id": self.entity_id,
            "message": self.message,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "auto_fixable": self.auto_fixable,
            "fix_action": self.fix_action,
        }


@dataclass
class ConstraintResult:
    """约束验证结果"""

    is_valid: bool
    violations: list[ConstraintViolation] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls) -> ConstraintResult:
        return cls(is_valid=True)

    @classmethod
    def failure(cls, violations: list[ConstraintViolation], warnings: list[str] | None = None) -> ConstraintResult:
        return cls(
            is_valid=False,
            violations=violations,
            warnings=warnings or [],
        )

    def merge(self, other: ConstraintResult) -> ConstraintResult:
        """合并两个结果"""
        return ConstraintResult(
            is_valid=self.is_valid and other.is_valid,
            violations=self.violations + other.violations,
            warnings=self.warnings + other.warnings,
        )


# =============================================================================
# 约束
# =============================================================================


@dataclass
class Constraint:
    """
    约束定义

    定义系统必须满足的条件。
    """

    id: ConstraintId
    name: str
    description: str = ""

    # 约束类型
    type: ConstraintType = ConstraintType.BUSINESS
    severity: Severity = Severity.HIGH

    # 验证配置
    validation_level: ValidationLevel = ValidationLevel.STRICT
    enabled: bool = True

    # 验证器
    validator: Callable[[Any], tuple[bool, str | None]] | None = None

    # 自动修复
    auto_fixable: bool = False
    fix_action: Callable[[Any], Any] | None = None

    # 豁免
    exemptions: list[str] = field(default_factory=list)  # 豁免的实体ID

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    version: str = "1.0.0"

    def validate(self, value: Any, entity_id: str | None = None) -> tuple[bool, str | None]:
        """
        验证值是否满足约束

        Returns:
            (是否满足, 错误消息)
        """
        if not self.enabled:
            return True, None

        # 检查豁免
        if entity_id and entity_id in self.exemptions:
            return True, None

        if self.validator:
            try:
                result = self.validator(value)
                # 支持返回 bool 或 Tuple[bool, str]
                if isinstance(result, bool):
                    return result, (
                        None if result else (getattr(self, "error_message", f"Constraint violated: {self.name}"))
                    )
                return result
            except Exception as e:
                return False, f"Validation error: {e}"

        return True, None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type.name,
            "severity": self.severity.value,
            "validation_level": self.validation_level.name,
            "enabled": self.enabled,
            "auto_fixable": self.auto_fixable,
            "created_at": self.created_at.isoformat(),
            "version": self.version,
        }


# =============================================================================
# 约束验证器
# =============================================================================


class ConstraintValidator:
    """
    约束验证器

    负责验证实体和操作是否满足所有约束。
    """

    def __init__(self):
        self._constraints: dict[ConstraintId, Constraint] = {}
        self._constraints_by_type: dict[ConstraintType, list[Constraint]] = {}
        self._violations: list[ConstraintViolation] = []

        self._logger = logging.getLogger(f"{__name__}.Validator")

    def add_constraint(self, constraint: Constraint) -> None:
        """添加约束"""
        self._constraints[constraint.id] = constraint

        if constraint.type not in self._constraints_by_type:
            self._constraints_by_type[constraint.type] = []
        self._constraints_by_type[constraint.type].append(constraint)

        self._logger.debug(f"Added constraint: {constraint.name}")

    def remove_constraint(self, constraint_id: ConstraintId) -> bool:
        """移除约束"""
        if constraint_id not in self._constraints:
            return False

        constraint = self._constraints[constraint_id]
        del self._constraints[constraint_id]

        if constraint.type in self._constraints_by_type:
            self._constraints_by_type[constraint.type] = [
                c for c in self._constraints_by_type[constraint.type] if c.id != constraint_id
            ]

        return True

    def get_constraint(self, constraint_id: ConstraintId) -> Constraint | None:
        """获取约束"""
        return self._constraints.get(constraint_id)

    def get_constraints(
        self,
        constraint_type: ConstraintType | None = None,
        enabled_only: bool = True,
    ) -> list[Constraint]:
        """获取约束列表"""
        constraints = list(self._constraints.values())

        if constraint_type:
            constraints = [c for c in constraints if c.type == constraint_type]
        if enabled_only:
            constraints = [c for c in constraints if c.enabled]

        return constraints

    def validate(
        self,
        value: Any,
        entity_id: str | None = None,
        constraint_ids: list[ConstraintId] | None = None,
    ) -> ConstraintResult:
        """
        验证值是否满足指定约束

        Args:
            value: 要验证的值
            entity_id: 实体ID（用于豁免检查）
            constraint_ids: 约束ID列表，如果为None则验证所有

        Returns:
            验证结果
        """
        violations = []
        warnings = []

        # 确定要验证的约束
        if constraint_ids:
            constraints = [self._constraints[cid] for cid in constraint_ids if cid in self._constraints]
        else:
            constraints = self.get_constraints()

        for constraint in constraints:
            is_valid, message = constraint.validate(value, entity_id)

            if not is_valid:
                violation = ConstraintViolation(
                    id=str(uuid.uuid4()),
                    constraint_id=constraint.id,
                    constraint_name=constraint.name,
                    entity_id=entity_id,
                    state={"value": str(value)[:100]},  # 截断避免过大
                    message=message or f"Constraint violated: {constraint.name}",
                    severity=constraint.severity,
                    auto_fixable=constraint.auto_fixable,
                )
                violations.append(violation)

                if constraint.validation_level == ValidationLevel.WARNING:
                    warnings.append(message)

                self._violations.append(violation)

        return ConstraintResult(
            is_valid=len(violations) == 0,
            violations=violations,
            warnings=warnings,
        )

    def validate_all(
        self,
        context: dict[str, Any],
    ) -> list[ConstraintViolation]:
        """
        验证整个上下文

        Returns:
            所有违规列表
        """
        all_violations = []

        for constraint in self.get_constraints():
            # 提取上下文中的相关值
            # 这里简化处理，实际应该根据约束定义提取
            value = context.get(constraint.name)
            if value is not None:
                result = self.validate(value)
                all_violations.extend(result.violations)

        return all_violations

    def get_violations(
        self,
        constraint_id: ConstraintId | None = None,
        entity_id: str | None = None,
        limit: int = 100,
    ) -> list[ConstraintViolation]:
        """获取违规记录"""
        violations = list(self._violations)

        if constraint_id:
            violations = [v for v in violations if v.constraint_id == constraint_id]
        if entity_id:
            violations = [v for v in violations if v.entity_id == entity_id]

        return violations[-limit:]

    def clear_violations(self) -> None:
        """清除违规记录"""
        self._violations = []

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_constraints": len(self._constraints),
            "enabled_constraints": len(self.get_constraints()),
            "total_violations": len(self._violations),
            "by_type": {t.name: len(c) for t, c in self._constraints_by_type.items()},
            "by_severity": {s.value: len([v for v in self._violations if v.severity == s]) for s in Severity},
        }


# =============================================================================
# 业务约束工厂
# =============================================================================


class BusinessConstraints:
    """业务约束工厂"""

    @staticmethod
    def create_balance_positive() -> Constraint:
        """余额非负约束"""
        return Constraint(
            id="inv_r001_balance_positive",
            name="账户余额非负",
            description="账户余额永远不能为负",
            type=ConstraintType.BUSINESS,
            severity=Severity.CRITICAL,
            validator=lambda x: x.get("balance", 0) >= 0,
        )

    @staticmethod
    def create_max_drawdown(max_pct: float = 0.2) -> Constraint:
        """最大回撤约束"""
        return Constraint(
            id="inv_r002_max_drawdown",
            name="回撤上限",
            description=f"当前余额不能低于峰值减去{max_pct*100}%",
            type=ConstraintType.BUSINESS,
            severity=Severity.HIGH,
            validator=lambda x: (x.get("current_balance", 0) >= x.get("peak_balance", 0) * (1 - max_pct)),
        )

    @staticmethod
    def create_position_limit(max_position_pct: float = 0.3) -> Constraint:
        """仓位上限约束"""
        return Constraint(
            id="inv_r004_position_limit",
            name="仓位上限",
            description=f"仓位不能超过账户的{max_position_pct*100}%",
            type=ConstraintType.BUSINESS,
            severity=Severity.HIGH,
            validator=lambda x: (x.get("position_size", 0) <= x.get("balance", 0) * max_position_pct),
        )

    @staticmethod
    def create_confidence_range() -> Constraint:
        """置信度范围约束"""
        return Constraint(
            id="inv_s001_confidence_range",
            name="置信度范围",
            description="置信度必须在[0, 1]范围内",
            type=ConstraintType.BUSINESS,
            severity=Severity.HIGH,
            validator=lambda x: 0 <= x.get("confidence", 0) <= 1,
        )


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    # 类型别名
    "ConstraintId",
    "ViolationId",
    # 枚举
    "ConstraintType",
    "Severity",
    "ValidationLevel",
    # 数据类
    "ConstraintViolation",
    "ConstraintResult",
    "Constraint",
    # 核心类
    "ConstraintValidator",
    "BusinessConstraints",
]
