"""
Entity Validators - 实体验证器

提供领域模型的验证功能：
- 字段级验证
- 业务规则验证
- 不变式验证

版本: v1.0.0
更新: 2026-04-27
"""

from __future__ import annotations

import re
from dataclasses import fields, is_dataclass
from typing import Any


class ValidationError(Exception):
    """验证错误异常"""

    def __init__(self, field: str, message: str, code: str = ""):
        self.field = field
        self.message = message
        self.code = code or "VALIDATION_ERROR"
        super().__init__(f"[{field}] {message}")


class ValidationResult:
    """验证结果"""

    def __init__(self):
        self.errors: list[ValidationError] = []

    def add_error(self, field: str, message: str, code: str = "") -> None:
        self.errors.append(ValidationError(field, message, code))

    def add_exception(self, exc: ValidationError) -> None:
        self.errors.append(exc)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def error_messages(self) -> list[str]:
        return [str(e) for e in self.errors]

    def raise_if_invalid(self) -> None:
        if not self.is_valid:
            raise ValidationError("entity", f"Validation failed: {len(self.errors)} errors")

    def __repr__(self) -> str:
        if self.is_valid:
            return "ValidationResult(valid=True)"
        return f"ValidationResult(valid=False, errors={len(self.errors)})"


# =============================================================================
# Field Validators
# =============================================================================


class FieldValidator:
    """字段验证器"""

    @staticmethod
    def required(value: Any, field_name: str) -> ValidationResult:
        result = ValidationResult()
        if value is None or (isinstance(value, str) and not value.strip()):
            result.add_error(field_name, "Field is required", "REQUIRED")
        return result

    @staticmethod
    def positive(value: float, field_name: str) -> ValidationResult:
        result = ValidationResult()
        if value is not None and value <= 0:
            result.add_error(field_name, "Value must be positive", "NOT_POSITIVE")
        return result

    @staticmethod
    def non_negative(value: float, field_name: str) -> ValidationResult:
        result = ValidationResult()
        if value is not None and value < 0:
            result.add_error(field_name, "Value must be non-negative", "NOT_NON_NEGATIVE")
        return result

    @staticmethod
    def range(value: float, field_name: str, min_val: float, max_val: float) -> ValidationResult:
        result = ValidationResult()
        if value is not None and not (min_val <= value <= max_val):
            result.add_error(field_name, f"Value must be between {min_val} and {max_val}", "OUT_OF_RANGE")
        return result

    @staticmethod
    def in_values(value: Any, field_name: str, valid_values: list[Any]) -> ValidationResult:
        result = ValidationResult()
        if value is not None and value not in valid_values:
            result.add_error(field_name, f"Value must be one of {valid_values}", "INVALID_VALUE")
        return result

    @staticmethod
    def min_length(value: str, field_name: str, min_len: int) -> ValidationResult:
        result = ValidationResult()
        if value is not None and len(value) < min_len:
            result.add_error(field_name, f"Length must be at least {min_len}", "TOO_SHORT")
        return result

    @staticmethod
    def max_length(value: str, field_name: str, max_len: int) -> ValidationResult:
        result = ValidationResult()
        if value is not None and len(value) > max_len:
            result.add_error(field_name, f"Length must be at most {max_len}", "TOO_LONG")
        return result

    @staticmethod
    def pattern(value: str, field_name: str, regex: str) -> ValidationResult:
        result = ValidationResult()
        if value is not None and not re.match(regex, value):
            result.add_error(field_name, f"Value does not match pattern {regex}", "PATTERN_MISMATCH")
        return result


# =============================================================================
# Trading Signal Validators
# =============================================================================


def validate_trading_signal(data: dict[str, Any]) -> ValidationResult:
    """验证交易信号"""
    result = ValidationResult()
    fv = FieldValidator

    # 必填字段
    for field_name in ["signal_id", "symbol", "signal_type"]:
        result.add_exception(fv.required(data.get(field_name), field_name))

    # 信号类型
    valid_types = ["long", "short", "close_long", "close_short", "hold"]
    result.add_exception(fv.in_values(data.get("signal_type"), "signal_type", valid_types))

    # 价格验证
    entry = data.get("entry_price", 0)
    result.add_exception(fv.positive(entry, "entry_price"))

    sl = data.get("stop_loss", 0)
    tp = data.get("take_profit", 0)
    signal_type = data.get("signal_type")

    if entry > 0:
        if signal_type == "long":
            if sl >= entry:
                result.add_error("stop_loss", "LONG: stop_loss must be < entry_price", "INVALID_PRICE")
            if tp <= entry:
                result.add_error("take_profit", "LONG: take_profit must be > entry_price", "INVALID_PRICE")
        elif signal_type == "short":
            if sl <= entry:
                result.add_error("stop_loss", "SHORT: stop_loss must be > entry_price", "INVALID_PRICE")
            if tp >= entry:
                result.add_error("take_profit", "SHORT: take_profit must be < entry_price", "INVALID_PRICE")

    # 置信度
    confidence = data.get("confidence", 0)
    result.add_exception(fv.range(confidence, "confidence", 0, 1))

    return result


# =============================================================================
# Order Validators
# =============================================================================


def validate_order(data: dict[str, Any]) -> ValidationResult:
    """验证订单"""
    result = ValidationResult()
    fv = FieldValidator

    # 必填字段
    for field_name in ["order_id", "symbol", "side", "quantity"]:
        result.add_exception(fv.required(data.get(field_name), field_name))

    # 订单方向
    valid_sides = ["buy", "sell"]
    result.add_exception(fv.in_values(data.get("side"), "side", valid_sides))

    # 数量验证
    quantity = data.get("quantity", 0)
    result.add_exception(fv.positive(quantity, "quantity"))

    # 价格验证
    price = data.get("price", 0)
    result.add_exception(fv.positive(price, "price"))

    # 成交数量验证
    filled = data.get("filled_quantity", 0)
    result.add_exception(fv.non_negative(filled, "filled_quantity"))
    if filled > quantity:
        result.add_error("filled_quantity", "filled_quantity cannot exceed quantity", "INVALID_QUANTITY")

    return result


# =============================================================================
# Position Validators
# =============================================================================


def validate_position(data: dict[str, Any]) -> ValidationResult:
    """验证持仓"""
    result = ValidationResult()
    fv = FieldValidator

    # 必填字段
    for field_name in ["symbol", "side", "size", "entry"]:
        result.add_exception(fv.required(data.get(field_name), field_name))

    # 方向验证
    valid_sides = ["long", "short"]
    result.add_exception(fv.in_values(data.get("side"), "side", valid_sides))

    # 数量验证
    size = data.get("size", 0)
    result.add_exception(fv.non_negative(size, "size"))

    # 价格验证
    entry = data.get("entry", 0)
    result.add_exception(fv.positive(entry, "entry"))

    return result


# =============================================================================
# Risk Check Result Validators
# =============================================================================


def validate_risk_result(data: dict[str, Any]) -> ValidationResult:
    """验证风控结果"""
    result = ValidationResult()
    fv = FieldValidator

    # 必填字段
    for field_name in ["signal_id", "symbol", "approved"]:
        result.add_exception(fv.required(data.get(field_name), field_name))

    # 批准状态
    approved = data.get("approved", False)
    position_size = data.get("position_size", 0)

    # 如果不批准，仓位必须为0
    if not approved and position_size > 0:
        result.add_error("position_size", "position_size must be 0 when not approved", "INVALID_STATE")

    # 风险评分
    risk_score = data.get("risk_score", 0)
    result.add_exception(fv.range(risk_score, "risk_score", 0, 1))

    return result


# =============================================================================
# Dataclass Validators
# =============================================================================


def validate_dataclass(obj: Any) -> ValidationResult:
    """验证 dataclass 对象"""
    result = ValidationResult()

    if not is_dataclass(obj):
        result.add_error("object", "Object is not a dataclass", "NOT_DATACLASS")
        return result

    for field in fields(obj):
        value = getattr(obj, field.name)

        # 基本类型检查
        if field.type in (int, float) and value is not None:
            result.add_exception(FieldValidator.non_negative(value, field.name))

    return result


# =============================================================================
# Business Rule Validators
# =============================================================================


class BusinessRuleValidator:
    """业务规则验证器"""

    @staticmethod
    def validate_price_consistency(
        entry: float, stop_loss: float, take_profit: float, signal_type: str
    ) -> ValidationResult:
        """验证价格一致性"""
        result = ValidationResult()

        if signal_type == "long":
            if stop_loss >= entry:
                result.add_error("stop_loss", "Long stop_loss must be below entry", "INVALID_SL")
            if take_profit <= entry:
                result.add_error("take_profit", "Long take_profit must be above entry", "INVALID_TP")
        elif signal_type == "short":
            if stop_loss <= entry:
                result.add_error("stop_loss", "Short stop_loss must be above entry", "INVALID_SL")
            if take_profit >= entry:
                result.add_error("take_profit", "Short take_profit must be below entry", "INVALID_TP")

        return result

    @staticmethod
    def validate_risk_reward_ratio(
        entry: float, stop_loss: float, take_profit: float, min_ratio: float = 1.5
    ) -> ValidationResult:
        """验证风险回报比"""
        result = ValidationResult()

        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)

        if risk > 0:
            ratio = reward / risk
            if ratio < min_ratio:
                result.add_error(
                    "risk_reward_ratio", f"Risk-reward ratio {ratio:.2f} is below minimum {min_ratio}", "LOW_RR_RATIO"
                )

        return result

    @staticmethod
    def validate_order_state_transition(current_state: str, new_state: str) -> ValidationResult:
        """验证订单状态转换"""
        result = ValidationResult()

        valid_transitions = {
            "pending": ["submitted", "cancelled", "rejected"],
            "submitted": ["partial_filled", "filled", "cancelled", "rejected"],
            "partial_filled": ["filled", "cancelled"],
            "filled": [],
            "cancelled": [],
            "rejected": [],
        }

        allowed = valid_transitions.get(current_state, [])
        if new_state not in allowed:
            result.add_error("status", f"Cannot transition from {current_state} to {new_state}", "INVALID_TRANSITION")

        return result

    @staticmethod
    def validate_strategy_weights(weights: list[float]) -> ValidationResult:
        """验证策略权重"""
        result = ValidationResult()

        # 检查范围
        for i, w in enumerate(weights):
            if not (0 <= w <= 1):
                result.add_error(f"weight_{i}", f"Weight {i} must be in [0, 1]", "INVALID_WEIGHT")

        # 检查和是否为1
        total = sum(weights)
        if abs(total - 1.0) > 0.01:
            result.add_error("weights_sum", f"Weights sum {total:.4f} should be 1.0", "INVALID_WEIGHT_SUM")

        return result
