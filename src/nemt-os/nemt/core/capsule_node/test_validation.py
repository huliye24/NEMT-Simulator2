"""
CapsuleNode 验证测试

运行所有验证用例，确保节点满足需求。

运行方式:
    python test_validation.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from validation_framework import (
    ValidationResult,
    ValidationSuite,
    create_brain_validation_suite,
    create_execution_validation_suite,
    create_market_validation_suite,
    create_risk_validation_suite,
    create_signal_validation_suite,
)

# ═══════════════════════════════════════════════════════════════════════════════
# 简单节点实现 (用于验证测试)
# ═══════════════════════════════════════════════════════════════════════════════


class SimpleMarketNode:
    """简化版 MarketNode"""

    NODE_ID = "market_node"

    def __init__(self):
        self._exec_count = 0

    @property
    def capsule_state(self):
        return "idle"

    @property
    def metrics(self):
        return {"exec_count": self._exec_count}

    def run(self, inputs):
        self._exec_count += 1

        raw = inputs.get("raw_feed", {})
        symbol = raw.get("symbol", "").upper()
        price = raw.get("price", 0)
        volume = raw.get("volume", 0)
        timestamp = raw.get("timestamp")

        # 验证必需字段
        if not symbol or price is None or timestamp is None:
            raise ValueError("Missing required field: symbol, price, or timestamp")

        return {
            "ohlcv": {
                "symbol": symbol,
                "close": price,
                "volume": volume,
            },
            "phase": "RANGE",
        }


class SimpleSignalNode:
    """简化版 SignalNode"""

    NODE_ID = "signal_node"

    def __init__(self):
        self._exec_count = 0

    @property
    def capsule_state(self):
        return "idle"

    @property
    def metrics(self):
        return {"exec_count": self._exec_count}

    def run(self, inputs):
        self._exec_count += 1

        ohlcv = inputs.get("ohlcv")
        market_phase = inputs.get("market_phase", "UNKNOWN")

        if not ohlcv:
            raise ValueError("Missing required input: ohlcv")

        close = ohlcv.get("close", 100)
        direction = "LONG" if close > 100 else "SHORT"

        import uuid

        return {
            "signal": {
                "signal_id": f"sig_{uuid.uuid4().hex[:8]}",
                "symbol": ohlcv.get("symbol", "UNKNOWN"),
                "direction": direction,
                "confidence": 0.7,
                "entry_price": close,
            }
        }


class SimpleRiskNode:
    """简化版 RiskNode"""

    NODE_ID = "risk_node"

    def __init__(self):
        self._exec_count = 0

    @property
    def capsule_state(self):
        return "idle"

    @property
    def metrics(self):
        return {"exec_count": self._exec_count}

    def run(self, inputs):
        self._exec_count += 1

        signal = inputs.get("signal", {})
        portfolio = inputs.get("portfolio", {"total_value": 100000, "available_balance": 100000})

        if not signal:
            raise ValueError("Missing required input: signal")

        confidence = signal.get("confidence", 0)

        if confidence < 0.5:
            return {
                "risk_approved_signal": None,
                "risk_rejection": {"signal_id": signal.get("signal_id"), "reason": "Confidence below minimum"},
                "risk_metrics": {"portfolio_risk": 0.05, "risk_score": 0.8},
            }

        return {
            "risk_approved_signal": {
                "signal_id": signal.get("signal_id"),
                "symbol": signal.get("symbol"),
                "direction": signal.get("direction"),
                "approved_size": 10000,
                "risk_score": 0.3,
            },
            "risk_rejection": None,
            "risk_metrics": {"portfolio_risk": 0.05, "risk_score": 0.3},
        }


class SimpleBrainNode:
    """简化版 BrainNode"""

    NODE_ID = "brain_node"

    def __init__(self):
        self._exec_count = 0

    @property
    def capsule_state(self):
        return "idle"

    @property
    def metrics(self):
        return {"exec_count": self._exec_count}

    def run(self, inputs):
        self._exec_count += 1

        signal = inputs.get("signal", {})
        risk_eval = inputs.get("risk_evaluation", {})

        if not signal:
            raise ValueError("Missing required input: signal")

        import uuid

        action = "EXECUTE" if risk_eval.get("approved", False) else "SKIP"

        return {
            "decision": {
                "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
                "action": action,
                "symbol": signal.get("symbol"),
                "size": risk_eval.get("approved_size", 0),
            }
        }


class SimpleExecutionNode:
    """简化版 ExecutionNode"""

    NODE_ID = "execution_node"

    def __init__(self):
        self._exec_count = 0
        self._orders = 0
        self._portfolio = 100000

    @property
    def capsule_state(self):
        return "idle"

    @property
    def metrics(self):
        return {"exec_count": self._exec_count}

    def run(self, inputs):
        self._exec_count += 1

        decision = inputs.get("decision", {})

        if decision.get("action") != "EXECUTE":
            return {"order": None, "portfolio": {"total_value": self._portfolio, "orders": self._orders}}

        import uuid

        self._orders += 1

        return {
            "order": {
                "order_id": f"ord_{uuid.uuid4().hex[:12]}",
                "symbol": decision.get("symbol"),
                "status": "FILLED",
            },
            "portfolio": {"total_value": self._portfolio, "orders": self._orders},
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 验证结果比较
# ═══════════════════════════════════════════════════════════════════════════════


def check_value(actual, expected):
    """检查值是否匹配"""
    if expected is None:
        return actual is None

    if isinstance(expected, tuple):
        # 范围检查
        min_val, max_val = expected
        return min_val <= actual <= max_val

    if isinstance(expected, type):
        # 类型检查
        return isinstance(actual, expected)

    if isinstance(expected, dict):
        # 字典检查
        for key, exp_val in expected.items():
            if key not in actual:
                return False
            if not check_value(actual[key], exp_val):
                return False
        return True

    if isinstance(expected, list):
        # 枚举检查
        return actual in expected

    # 相等检查
    return actual == expected


def run_suite(suite: ValidationSuite, node) -> list:
    """运行验证套件"""
    results = []

    for case in suite.cases:
        result = ValidationResult(name=case.name, passed=False, message="")

        try:
            output = node.run(case.input_data)

            if case.should_pass:
                # 期望成功
                all_match = True
                for key, expected in case.expected.items():
                    # 支持嵌套 key 如 "ohlcv.symbol"
                    keys = key.split(".")
                    actual = output
                    for k in keys:
                        if isinstance(actual, dict):
                            actual = actual.get(k)
                        else:
                            actual = None
                            break

                    if not check_value(actual, expected):
                        all_match = False
                        result.message = f"Key '{key}' mismatch: got {actual}, expected {expected}"
                        result.actual = actual
                        result.expected = expected
                        break

                if all_match:
                    result.passed = True
                    result.message = "All checks passed"
            else:
                # 期望失败但成功了
                result.message = "Expected validation error but succeeded"

        except Exception as e:
            if case.should_pass:
                result.message = f"Unexpected error: {e}"
            else:
                result.passed = True
                result.message = "Correctly rejected invalid input"

        results.append(result)

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 主测试
# ═══════════════════════════════════════════════════════════════════════════════


def run_all_tests():
    """运行所有验证测试"""
    print("\n" + "=" * 70)
    print("CapsuleNode Validation Tests")
    print("核心思想: State定义'要什么', Validation定义'算不算做到'")
    print("=" * 70)

    # 创建节点
    nodes = {
        "market": SimpleMarketNode(),
        "signal": SimpleSignalNode(),
        "risk": SimpleRiskNode(),
        "brain": SimpleBrainNode(),
        "execution": SimpleExecutionNode(),
    }

    all_results = {}
    total_passed = 0
    total_failed = 0

    # === MarketNode 测试 ===
    print("\n\n" + "=" * 60)
    print("Testing MarketNode")
    print("=" * 60)

    suite = create_market_validation_suite()
    results = run_suite(suite, nodes["market"])
    all_results["MarketNode"] = results

    for r in results:
        status = "[PASS]" if r.passed else "[FAIL]"
        print(f"{status} {r.name}")
        print(f"       {r.message}")

    total_passed += sum(1 for r in results if r.passed)
    total_failed += sum(1 for r in results if not r.passed)

    # === SignalNode 测试 ===
    print("\n" + "=" * 60)
    print("Testing SignalNode")
    print("=" * 60)

    suite = create_signal_validation_suite()
    results = run_suite(suite, nodes["signal"])
    all_results["SignalNode"] = results

    for r in results:
        status = "[PASS]" if r.passed else "[FAIL]"
        print(f"{status} {r.name}")
        print(f"       {r.message}")

    total_passed += sum(1 for r in results if r.passed)
    total_failed += sum(1 for r in results if not r.passed)

    # === RiskNode 测试 ===
    print("\n" + "=" * 60)
    print("Testing RiskNode")
    print("=" * 60)

    suite = create_risk_validation_suite()
    results = run_suite(suite, nodes["risk"])
    all_results["RiskNode"] = results

    for r in results:
        status = "[PASS]" if r.passed else "[FAIL]"
        print(f"{status} {r.name}")
        print(f"       {r.message}")

    total_passed += sum(1 for r in results if r.passed)
    total_failed += sum(1 for r in results if not r.passed)

    # === BrainNode 测试 ===
    print("\n" + "=" * 60)
    print("Testing BrainNode")
    print("=" * 60)

    suite = create_brain_validation_suite()
    results = run_suite(suite, nodes["brain"])
    all_results["BrainNode"] = results

    for r in results:
        status = "[PASS]" if r.passed else "[FAIL]"
        print(f"{status} {r.name}")
        print(f"       {r.message}")

    total_passed += sum(1 for r in results if r.passed)
    total_failed += sum(1 for r in results if not r.passed)

    # === ExecutionNode 测试 ===
    print("\n" + "=" * 60)
    print("Testing ExecutionNode")
    print("=" * 60)

    suite = create_execution_validation_suite()
    results = run_suite(suite, nodes["execution"])
    all_results["ExecutionNode"] = results

    for r in results:
        status = "[PASS]" if r.passed else "[FAIL]"
        print(f"{status} {r.name}")
        print(f"       {r.message}")

    total_passed += sum(1 for r in results if r.passed)
    total_failed += sum(1 for r in results if not r.passed)

    # === 最终报告 ===
    print("\n\n" + "=" * 70)
    print("FINAL VALIDATION REPORT")
    print("=" * 70)

    for suite_name, results in all_results.items():
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        print(f"{suite_name}: {passed}/{total} passed")

    print(f"\nTotal: {total_passed}/{total_passed + total_failed} passed")
    print(f"Status: {'ALL PASSED' if total_failed == 0 else 'SOME FAILED'}")

    print("\n" + "=" * 70)
    print("Validation Philosophy:")
    print("  State 定义'要什么'")
    print("  Validation 定义'算不算做到'")
    print("  NOT: 代码看着没问题")
    print("  BUT: 所有测试通过")
    print("=" * 70 + "\n")

    return total_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
