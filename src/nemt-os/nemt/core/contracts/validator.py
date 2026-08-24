"""
Capsule Contract Validator - 胶囊契约验证器

运行时检查 Capsule 是否符合接口契约。

版本: v1.0.0
更新: 2026-04-27
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class ContractViolation(Exception):
    """契约违反异常"""

    def __init__(self, message: str, violations: list[str] = None):
        self.message = message
        self.violations = violations or []
        super().__init__(message)


@dataclass
class ValidationReport:
    """验证报告"""

    capsule_id: str
    capsule_class: str
    timestamp: datetime = field(default_factory=datetime.now)

    is_valid: bool = True
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    # 详细检查结果
    lifecycle_checks: dict[str, bool] = field(default_factory=dict)
    fractal_checks: dict[str, bool] = field(default_factory=dict)
    event_checks: dict[str, bool] = field(default_factory=dict)

    def add_violation(self, message: str) -> None:
        self.violations.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_info(self, message: str) -> None:
        self.info.append(message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "capsule_id": self.capsule_id,
            "capsule_class": self.capsule_class,
            "timestamp": self.timestamp.isoformat(),
            "is_valid": self.is_valid,
            "violations": self.violations,
            "warnings": self.warnings,
            "info": self.info,
            "checks": {
                "lifecycle": self.lifecycle_checks,
                "fractal": self.fractal_checks,
                "event": self.event_checks,
            },
        }


class ContractValidator:
    """契约验证器"""

    # 必需的生命周期方法
    REQUIRED_LIFECYCLE_METHODS = ["init", "exec", "shutdown"]

    # 必需的五阶段方法
    REQUIRED_FRACTAL_METHODS = [
        "observe_phase",
        "design_phase",
        "implement_phase",
        "verify_phase",
        "integrate_phase",
    ]

    # 必需的属性
    REQUIRED_PROPERTIES = [
        "capsule_id",
        "is_initialized",
        "is_running",
    ]

    def __init__(self):
        self._validators: list[BaseValidator] = []
        self._register_default_validators()

    def _register_default_validators(self) -> None:
        """注册默认验证器"""
        self._validators = [
            LifecycleMethodValidator(),
            FractalMethodValidator(),
            PropertyValidator(),
            DependencyValidator(),
            EventBusValidator(),
        ]

    def validate(self, capsule: Any) -> ValidationReport:
        """
        验证 Capsule 契约

        Args:
            capsule: Capsule 实例

        Returns:
            验证报告
        """
        capsule_id = getattr(capsule, "_capsule_id", "unknown")
        capsule_class = capsule.__class__.__name__

        report = ValidationReport(
            capsule_id=capsule_id,
            capsule_class=capsule_class,
        )

        # 运行所有验证器
        for validator in self._validators:
            try:
                validator.validate(capsule, report)
            except Exception as e:
                report.add_violation(f"{validator.__class__.__name__}: {str(e)}")

        return report

    def validate_class(self, capsule_class: type) -> ValidationReport:
        """
        验证 Capsule 类定义

        Args:
            capsule_class: Capsule 类

        Returns:
            验证报告
        """
        capsule_id = capsule_class.__name__
        capsule_class_name = capsule_class.__name__

        report = ValidationReport(
            capsule_id=capsule_id,
            capsule_class=capsule_class_name,
        )

        # 检查必需方法
        for method_name in self.REQUIRED_LIFECYCLE_METHODS:
            if not hasattr(capsule_class, method_name):
                report.add_violation(f"Missing lifecycle method: {method_name}")
                report.lifecycle_checks[method_name] = False
            else:
                report.lifecycle_checks[method_name] = True

        # 检查五阶段方法
        for method_name in self.REQUIRED_FRACTAL_METHODS:
            if not hasattr(capsule_class, method_name):
                report.add_violation(f"Missing fractal method: {method_name}")
                report.fractal_checks[method_name] = False
            else:
                report.fractal_checks[method_name] = True

        return report


class BaseValidator(ABC):
    """验证器基类"""

    @abstractmethod
    def validate(self, capsule: Any, report: ValidationReport) -> None:
        """执行验证"""
        pass


class LifecycleMethodValidator(BaseValidator):
    """生命周期方法验证器"""

    def validate(self, capsule: Any, report: ValidationReport) -> None:
        for method_name in ContractValidator.REQUIRED_LIFECYCLE_METHODS:
            if hasattr(capsule, method_name):
                method = getattr(capsule, method_name)
                if not callable(method):
                    report.add_violation(f"{method_name} is not callable")
                    report.lifecycle_checks[method_name] = False
                else:
                    report.lifecycle_checks[method_name] = True
            else:
                report.add_violation(f"Missing lifecycle method: {method_name}")
                report.lifecycle_checks[method_name] = False


class FractalMethodValidator(BaseValidator):
    """五阶段方法验证器"""

    def validate(self, capsule: Any, report: ValidationReport) -> None:
        for method_name in ContractValidator.REQUIRED_FRACTAL_METHODS:
            if hasattr(capsule, method_name):
                method = getattr(capsule, method_name)
                if not callable(method):
                    report.add_violation(f"{method_name} is not callable")
                    report.fractal_checks[method_name] = False
                else:
                    # 检查方法签名
                    sig = inspect.signature(method)
                    report.fractal_checks[method_name] = True
            else:
                report.add_violation(f"Missing fractal method: {method_name}")
                report.fractal_checks[method_name] = False


class PropertyValidator(BaseValidator):
    """属性验证器"""

    def validate(self, capsule: Any, report: ValidationReport) -> None:
        for prop_name in ContractValidator.REQUIRED_PROPERTIES:
            if hasattr(capsule, prop_name):
                report.add_info(f"Property exists: {prop_name}")
            else:
                report.add_warning(f"Missing property: {prop_name}")


class DependencyValidator(BaseValidator):
    """依赖验证器"""

    def validate(self, capsule: Any, report: ValidationReport) -> None:
        # 检查 event_bus
        if hasattr(capsule, "_event_bus"):
            event_bus = getattr(capsule, "_event_bus", None)
            if event_bus is None:
                report.add_warning("EventBus not injected (expected after CapsuleManager.setup)")
            else:
                report.add_info("EventBus injected")
        else:
            report.add_warning("Missing _event_bus attribute")

        # 检查 config
        if hasattr(capsule, "_config"):
            config = getattr(capsule, "_config", None)
            if config is None:
                report.add_warning("ConfigCenter not injected (expected after CapsuleManager.setup)")
            else:
                report.add_info("ConfigCenter injected")
        else:
            report.add_warning("Missing _config attribute")


class EventBusValidator(BaseValidator):
    """事件总线验证器"""

    def validate(self, capsule: Any, report: ValidationReport) -> None:
        event_bus = getattr(capsule, "_event_bus", None)
        if event_bus is None:
            return  # 尚未注入，跳过

        # 检查事件方法
        required_methods = ["subscribe", "unsubscribe", "publish"]
        for method_name in required_methods:
            if not hasattr(event_bus, method_name):
                report.add_violation(f"EventBus missing method: {method_name}")
                report.event_checks[method_name] = False
            else:
                report.event_checks[method_name] = True


# =============================================================================
# Contract Decorators
# =============================================================================


def requires_initialized(func):
    """要求胶囊已初始化的装饰器"""

    def wrapper(self, *args, **kwargs):
        if not getattr(self, "_initialized", False):
            raise ContractViolation(f"{self._capsule_id} not initialized. Call init() first.")
        return func(self, *args, **kwargs)

    return wrapper


def requires_event_bus(func):
    """要求事件总线可用的装饰器"""

    def wrapper(self, *args, **kwargs):
        if getattr(self, "_event_bus", None) is None:
            raise ContractViolation(f"{self._capsule_id} has no EventBus. CapsuleManager.setup() required.")
        return func(self, *args, **kwargs)

    return wrapper


# =============================================================================
# Schema Validators
# =============================================================================


def validate_input_schema(data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """
    验证输入数据是否符合 schema

    Args:
        data: 输入数据
        schema: Schema 定义

    Returns:
        错误列表
    """
    errors = []

    if schema.get("required"):
        for field_name in schema["required"]:
            if field_name not in data:
                errors.append(f"Required field missing: {field_name}")

    properties = schema.get("properties", {})
    for field_name, field_schema in properties.items():
        if field_name in data:
            value = data[field_name]
            expected_type = field_schema.get("type")

            if expected_type == "string" and not isinstance(value, str):
                errors.append(f"{field_name} must be string")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"{field_name} must be number")
            elif expected_type == "boolean" and not isinstance(value, bool):
                errors.append(f"{field_name} must be boolean")
            elif expected_type == "array" and not isinstance(value, list):
                errors.append(f"{field_name} must be array")

    return errors


# =============================================================================
# Global Validator Instance
# =============================================================================

_global_validator: ContractValidator | None = None


def get_validator() -> ContractValidator:
    """获取全局验证器"""
    global _global_validator
    if _global_validator is None:
        _global_validator = ContractValidator()
    return _global_validator


def validate_capsule(capsule: Any) -> ValidationReport:
    """快捷验证函数"""
    return get_validator().validate(capsule)
