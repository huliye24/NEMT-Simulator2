"""
业务约束测试

在 evolution 目录下运行: python test_business_constraints.py
"""

import os
import sys

# 添加 evolution 目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from constraint.constraint import Constraint, ConstraintValidator, Severity

print("=" * 60)
print("NEMT Business Constraints Test Suite")
print("=" * 60)

# =============================================================================
# 风控约束
# =============================================================================


def test_risk_constraints():
    """测试风控约束"""
    print("\n[Test] RiskConstraints")

    validator = ConstraintValidator()

    # 余额非负
    c1 = Constraint(
        id="inv_r001",
        name="账户余额非负",
        validator=lambda x: x.get("current_balance", 0) >= 0,
        severity=Severity.CRITICAL,
    )
    validator.add_constraint(c1)

    # 最大回撤
    c2 = Constraint(
        id="inv_r002",
        name="回撤上限",
        validator=lambda x: x.get("current_balance", 0) >= x.get("peak_balance", 0) * 0.8,
        severity=Severity.HIGH,
    )
    validator.add_constraint(c2)

    # 测试
    result = validator.validate({"current_balance": 1000})
    assert result.is_valid, f"Positive balance: {result.violations}"
    print("  [PASS] Balance positive")

    result = validator.validate({"current_balance": -100})
    assert not result.is_valid, "Negative balance should be invalid"
    print("  [PASS] Balance negative")

    result = validator.validate({"current_balance": 800, "peak_balance": 1000})
    assert result.is_valid, f"Valid drawdown: {result.violations}"
    print("  [PASS] Max drawdown")


# =============================================================================
# 信号约束
# =============================================================================


def test_signal_constraints():
    """测试信号约束"""
    print("\n[Test] SignalConstraints")

    validator = ConstraintValidator()

    # 置信度范围
    c1 = Constraint(
        id="inv_s001",
        name="置信度范围",
        validator=lambda x: 0 <= x.get("confidence", 0) <= 1,
        severity=Severity.HIGH,
    )
    validator.add_constraint(c1)

    # 止损止盈有效性
    def stop_loss_validator(x):
        signal_type = x.get("signal_type")
        entry = x.get("entry_price")
        sl = x.get("stop_loss")
        tp = x.get("take_profit")

        if signal_type == "LONG":
            if entry <= sl:
                return False, f"多头: 入场价 ({entry}) <= 止损 ({sl})"
            if tp <= entry:
                return False, f"多头: 止盈 ({tp}) <= 入场价 ({entry})"
        elif signal_type == "SHORT":
            if entry >= sl:
                return False, f"空头: 入场价 ({entry}) >= 止损 ({sl})"
            if tp >= entry:
                return False, f"空头: 止盈 ({tp}) >= 入场价 ({entry})"
        return True, None

    c2 = Constraint(
        id="inv_s002",
        name="止损止盈有效性",
        validator=stop_loss_validator,
        severity=Severity.HIGH,
    )
    validator.add_constraint(c2)

    # 测试置信度
    result = validator.validate({"confidence": 0.8})
    assert result.is_valid, f"Valid confidence: {result.violations}"
    print("  [PASS] Valid confidence")

    result = validator.validate({"confidence": 1.5})
    assert not result.is_valid, "Confidence > 1 should be invalid"
    print("  [PASS] Invalid confidence")

    # 测试止损止盈
    result = validator.validate({"signal_type": "LONG", "entry_price": 100, "stop_loss": 95, "take_profit": 110})
    assert result.is_valid, f"Valid stop loss/profit: {result.violations}"
    print("  [PASS] Valid stop loss/profit")


# =============================================================================
# 执行约束
# =============================================================================


def test_execution_constraints():
    """测试执行约束"""
    print("\n[Test] ExecutionConstraints")

    validator = ConstraintValidator()

    # 订单状态流转
    VALID_TRANSITIONS = {
        "PENDING": ["SUBMITTED", "CANCELLED", "REJECTED"],
        "SUBMITTED": ["PARTIAL_FILLED", "FILLED", "CANCELLED", "REJECTED"],
        "PARTIAL_FILLED": ["FILLED", "CANCELLED"],
        "FILLED": [],
        "CANCELLED": [],
        "REJECTED": [],
    }

    def state_validator(x):
        old = x.get("previous_state")
        new = x.get("current_state")
        if old in VALID_TRANSITIONS:
            if new not in VALID_TRANSITIONS[old]:
                return False, f"非法流转: {old} -> {new}"
        return True, None

    c1 = Constraint(
        id="inv_e001",
        name="订单状态流转",
        validator=state_validator,
        severity=Severity.CRITICAL,
    )
    validator.add_constraint(c1)

    # 成交数量限制
    c2 = Constraint(
        id="inv_e002",
        name="成交数量上限",
        validator=lambda x: x.get("filled_quantity", 0) <= x.get("quantity", float("inf")),
        severity=Severity.HIGH,
    )
    validator.add_constraint(c2)

    # 测试状态流转
    result = validator.validate({"previous_state": "PENDING", "current_state": "SUBMITTED"})
    assert result.is_valid, f"Valid transition: {result.violations}"
    print("  [PASS] Valid state transition")

    result = validator.validate({"previous_state": "FILLED", "current_state": "PENDING"})
    assert not result.is_valid, "Invalid transition should fail"
    print("  [PASS] Invalid state transition")

    # 测试成交数量
    result = validator.validate({"filled_quantity": 10, "quantity": 20})
    assert result.is_valid, f"Valid filled: {result.violations}"
    print("  [PASS] Valid filled quantity")


# =============================================================================
# 执行测试
# =============================================================================


def main():
    try:
        test_risk_constraints()
        test_signal_constraints()
        test_execution_constraints()

        print("\n" + "=" * 60)
        print("ALL BUSINESS CONSTRAINT TESTS PASSED!")
        print("=" * 60)
        print("\n覆盖的不变式:")
        print("  INV-R001: 账户余额非负")
        print("  INV-R002: 回撤上限")
        print("  INV-S001: 置信度范围")
        print("  INV-S002: 止损止盈有效性")
        print("  INV-E001: 订单状态流转")
        print("  INV-E002: 成交数量限制")
        return 0

    except Exception as e:
        print(f"\n\nTEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
