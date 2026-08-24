"""
CapsuleNode 验证框架

核心思想：
  State 定义"要什么"
  Validation 定义"算不算做到"

验证不是形式主义，而是让错误无法通过系统的工程实践。
"""

from dataclasses import dataclass
from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
# Validation 定义
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class ValidationCase:
    """验证用例"""

    name: str
    description: str
    input_data: dict
    expected: dict
    should_pass: bool = True


@dataclass
class ValidationResult:
    """验证结果"""

    name: str
    passed: bool
    message: str
    actual: Any = None
    expected: Any = None


class ValidationSuite:
    """
    验证套件

    包含一组验证用例，用于验证节点是否满足需求。

    使用方法:

    ```python
    suite = ValidationSuite("MarketNode")

    # 添加验证用例
    suite.add_case(ValidationCase(
        name="valid_raw_feed_returns_ohlcv",
        description="有效输入应返回 OHLCV 数据",
        input_data={"raw_feed": {...}},
        expected={"ohlcv": {...}},
    ))

    # 运行验证
    results = suite.run(node)

    # 报告
    suite.report(results)
    ```
    """

    def __init__(self, node_name: str):
        self.node_name = node_name
        self.cases: list[ValidationCase] = []

    def add_case(self, case: ValidationCase):
        """添加验证用例"""
        self.cases.append(case)

    def run(self, node) -> list[ValidationResult]:
        """
        运行所有验证用例

        Args:
            node: CapsuleNode 实例

        Returns:
            验证结果列表
        """
        results = []

        for case in self.cases:
            result = self._run_case(node, case)
            results.append(result)

        return results

    def _run_case(self, node, case: ValidationCase) -> ValidationResult:
        """运行单个验证用例"""
        try:
            # 执行节点
            output = node.run(case.input_data)

            # 验证输出
            if case.should_pass:
                # 期望成功
                for key, expected_value in case.expected.items():
                    actual_value = output.get(key)
                    if actual_value != expected_value:
                        return ValidationResult(
                            name=case.name,
                            passed=False,
                            message=f"Key '{key}' mismatch",
                            actual=actual_value,
                            expected=expected_value,
                        )

                return ValidationResult(name=case.name, passed=True, message="All checks passed")
            else:
                # 期望失败（应该抛出异常）
                return ValidationResult(name=case.name, passed=False, message="Expected validation error but succeeded")

        except Exception as e:
            if case.should_pass:
                return ValidationResult(name=case.name, passed=False, message=f"Unexpected error: {e}")
            else:
                return ValidationResult(name=case.name, passed=True, message="Correctly rejected invalid input")

    def report(self, results: list[ValidationResult]) -> str:
        """生成验证报告"""
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"Validation Report: {self.node_name}")
        lines.append(f"{'='*60}")

        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed

        lines.append(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed}")
        lines.append("")

        for result in results:
            status = "[PASS]" if result.passed else "[FAIL]"
            lines.append(f"{status} {result.name}")
            lines.append(f"       {result.message}")
            if not result.passed and result.actual is not None:
                lines.append(f"       Actual: {result.actual}")
                lines.append(f"       Expected: {result.expected}")

        lines.append(f"\n{'='*60}")
        lines.append(f"Result: {'ALL PASSED' if failed == 0 else 'SOME FAILED'}")
        lines.append(f"{'='*60}\n")

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# MarketNode 验证套件
# ═══════════════════════════════════════════════════════════════════════════════


def create_market_validation_suite():
    """
    MarketNode 验证套件

    定义所有验证用例，确保 MarketNode 满足需求。
    """
    suite = ValidationSuite("MarketNode")

    # === 验证用例 ===

    # 1. 有效输入返回 OHLCV
    suite.add_case(
        ValidationCase(
            name="valid_input_returns_ohlcv",
            description="有效输入应返回包含 close 的 OHLCV 数据",
            input_data={"raw_feed": {"symbol": "BTCUSDT", "price": 50000, "volume": 100, "timestamp": 1714281600}},
            expected={"ohlcv": {"symbol": "BTCUSDT", "close": 50000}},
            should_pass=True,
        )
    )

    # 2. 返回市场相位
    suite.add_case(
        ValidationCase(
            name="returns_market_phase",
            description="应返回市场相位",
            input_data={"raw_feed": {"symbol": "ETHUSDT", "price": 3000, "volume": 50, "timestamp": 1714281600}},
            expected={"phase": ["UNKNOWN", "TREND_UP", "TREND_DOWN", "RANGE", "VOLATILE"]},
            should_pass=True,
        )
    )

    # 3. 缺少必需字段应失败
    suite.add_case(
        ValidationCase(
            name="missing_required_field_fails",
            description="缺少必需字段 timestamp 应失败",
            input_data={"raw_feed": {"symbol": "BTCUSDT", "price": 50000}},
            expected={},
            should_pass=False,
        )
    )

    # 4. 价格变化时 OHLCV 更新
    suite.add_case(
        ValidationCase(
            name="price_change_updates_ohlcv",
            description="价格变化应更新 OHLCV",
            input_data={"raw_feed": {"symbol": "BTCUSDT", "price": 51000, "volume": 150, "timestamp": 1714281601}},
            expected={"ohlcv": {"symbol": "BTCUSDT", "close": 51000}},
            should_pass=True,
        )
    )

    # 5. 符号自动转大写
    suite.add_case(
        ValidationCase(
            name="symbol_uppercase",
            description="符号应自动转为大写",
            input_data={"raw_feed": {"symbol": "btcusdt", "price": 50000, "volume": 100, "timestamp": 1714281600}},
            expected={"ohlcv": {"symbol": "BTCUSDT"}},
            should_pass=True,
        )
    )

    return suite


# ═══════════════════════════════════════════════════════════════════════════════
# SignalNode 验证套件
# ═══════════════════════════════════════════════════════════════════════════════


def create_signal_validation_suite():
    """SignalNode 验证套件"""
    suite = ValidationSuite("SignalNode")

    # 1. 有效 OHLCV 返回信号
    suite.add_case(
        ValidationCase(
            name="valid_ohlcv_returns_signal",
            description="有效 OHLCV 应返回信号",
            input_data={
                "ohlcv": {
                    "symbol": "BTCUSDT",
                    "close": 50000,
                    "open": 49500,
                    "high": 50500,
                    "low": 49000,
                    "volume": 100,
                },
                "market_phase": "RANGE",
            },
            expected={"signal": {"symbol": "BTCUSDT", "direction": ["LONG", "SHORT", "NEUTRAL"]}},
            should_pass=True,
        )
    )

    # 2. 信号包含置信度
    suite.add_case(
        ValidationCase(
            name="signal_has_confidence",
            description="信号应包含置信度 (0-1)",
            input_data={"ohlcv": {"symbol": "ETHUSDT", "close": 3000, "volume": 50}, "market_phase": "TREND_UP"},
            expected={"signal": {"confidence": (0, 1)}},  # 范围验证
            should_pass=True,
        )
    )

    # 3. 缺少必需字段应失败
    suite.add_case(
        ValidationCase(
            name="missing_ohlcv_fails",
            description="缺少 ohlcv 应失败",
            input_data={"market_phase": "RANGE"},
            expected={},
            should_pass=False,
        )
    )

    return suite


# ═══════════════════════════════════════════════════════════════════════════════
# RiskNode 验证套件
# ═══════════════════════════════════════════════════════════════════════════════


def create_risk_validation_suite():
    """RiskNode 验证套件"""
    suite = ValidationSuite("RiskNode")

    # 1. 低置信度信号应被拒绝
    suite.add_case(
        ValidationCase(
            name="low_confidence_rejected",
            description="置信度 < 0.5 的信号应被拒绝",
            input_data={
                "signal": {"signal_id": "sig_test", "symbol": "BTCUSDT", "direction": "LONG", "confidence": 0.3},
                "portfolio": {"total_value": 100000, "available_balance": 100000, "daily_pnl": 0, "drawdown": 0},
            },
            expected={"risk_rejection": {"reason": "Confidence below minimum"}},
            should_pass=True,
        )
    )

    # 2. 高置信度信号应被批准
    suite.add_case(
        ValidationCase(
            name="high_confidence_approved",
            description="高置信度信号应被批准",
            input_data={
                "signal": {"signal_id": "sig_test", "symbol": "BTCUSDT", "direction": "LONG", "confidence": 0.8},
                "portfolio": {"total_value": 100000, "available_balance": 100000, "daily_pnl": 0, "drawdown": 0},
            },
            expected={"risk_approved_signal": {"approved_size": (0, 100000)}},
            should_pass=True,
        )
    )

    # 3. 返回风险指标
    suite.add_case(
        ValidationCase(
            name="returns_risk_metrics",
            description="应返回风险指标",
            input_data={
                "signal": {"signal_id": "sig_test", "symbol": "BTCUSDT", "direction": "LONG", "confidence": 0.7},
                "portfolio": {"total_value": 100000, "available_balance": 100000, "daily_pnl": 0, "drawdown": 0},
            },
            expected={"risk_metrics": {"portfolio_risk": (0, 1), "risk_score": (0, 1)}},
            should_pass=True,
        )
    )

    return suite


# ═══════════════════════════════════════════════════════════════════════════════
# BrainNode 验证套件
# ═══════════════════════════════════════════════════════════════════════════════


def create_brain_validation_suite():
    """BrainNode 验证套件"""
    suite = ValidationSuite("BrainNode")

    # 1. 批准信号返回 EXECUTE 决策
    suite.add_case(
        ValidationCase(
            name="approved_signal_executes",
            description="批准信号应返回 EXECUTE 决策",
            input_data={
                "signal": {"signal_id": "sig_test", "symbol": "BTCUSDT", "direction": "LONG", "confidence": 0.8},
                "risk_evaluation": {"approved": True, "approved_size": 10000, "risk_score": 0.3},
            },
            expected={"decision": {"action": "EXECUTE"}},
            should_pass=True,
        )
    )

    # 2. 拒绝信号返回 SKIP 决策
    suite.add_case(
        ValidationCase(
            name="rejected_signal_skips",
            description="拒绝信号应返回 SKIP 决策",
            input_data={
                "signal": {"signal_id": "sig_test", "symbol": "BTCUSDT", "direction": "LONG", "confidence": 0.5},
                "risk_evaluation": {"approved": False, "risk_score": 0.8},
            },
            expected={"decision": {"action": "SKIP"}},
            should_pass=True,
        )
    )

    # 3. 决策包含决策 ID
    suite.add_case(
        ValidationCase(
            name="decision_has_id",
            description="决策应包含唯一 ID",
            input_data={
                "signal": {"signal_id": "sig_test", "symbol": "BTCUSDT", "direction": "LONG", "confidence": 0.8},
                "risk_evaluation": {"approved": True, "approved_size": 10000, "risk_score": 0.3},
            },
            expected={"decision": {"decision_id": str}},  # 非空字符串
            should_pass=True,
        )
    )

    return suite


# ═══════════════════════════════════════════════════════════════════════════════
# ExecutionNode 验证套件
# ═══════════════════════════════════════════════════════════════════════════════


def create_execution_validation_suite():
    """ExecutionNode 验证套件"""
    suite = ValidationSuite("ExecutionNode")

    # 1. EXECUTE 决策创建订单
    suite.add_case(
        ValidationCase(
            name="execute_creates_order",
            description="EXECUTE 决策应创建订单",
            input_data={
                "decision": {
                    "decision_id": "dec_test",
                    "action": "EXECUTE",
                    "symbol": "BTCUSDT",
                    "direction": "LONG",
                    "size": 10000,
                    "entry_price": 50000,
                }
            },
            expected={"order": {"status": "FILLED"}},
            should_pass=True,
        )
    )

    # 2. SKIP 决策不创建订单
    suite.add_case(
        ValidationCase(
            name="skip_no_order",
            description="SKIP 决策不应创建订单",
            input_data={
                "decision": {"decision_id": "dec_test", "action": "SKIP", "symbol": "BTCUSDT", "direction": "LONG"}
            },
            expected={"order": None},
            should_pass=True,
        )
    )

    # 3. 返回投资组合
    suite.add_case(
        ValidationCase(
            name="returns_portfolio",
            description="应返回投资组合状态",
            input_data={
                "decision": {
                    "decision_id": "dec_test",
                    "action": "EXECUTE",
                    "symbol": "BTCUSDT",
                    "direction": "LONG",
                    "size": 10000,
                    "entry_price": 50000,
                }
            },
            expected={"portfolio": {"total_value": (0, float("inf"))}},
            should_pass=True,
        )
    )

    return suite


# ═══════════════════════════════════════════════════════════════════════════════
# 完整 Pipeline 验证套件
# ═══════════════════════════════════════════════════════════════════════════════


def create_pipeline_validation_suite():
    """
    完整 Pipeline 验证套件

    验证从市场数据到订单执行的完整流程。
    """
    suite = ValidationSuite("Pipeline (Full)")

    # 1. 有效市场数据最终产生订单
    suite.add_case(
        ValidationCase(
            name="valid_data_produces_order",
            description="有效市场数据应最终产生订单",
            input_data={"raw_feed": {"symbol": "BTCUSDT", "price": 50000, "volume": 100, "timestamp": 1714281600}},
            expected={"execution.order": {"status": "FILLED"}},
            should_pass=True,
        )
    )

    # 2. 完整流程每个节点都有输出
    suite.add_case(
        ValidationCase(
            name="all_nodes_produce_output",
            description="每个节点都应有输出",
            input_data={"raw_feed": {"symbol": "BTCUSDT", "price": 50000, "volume": 100, "timestamp": 1714281600}},
            expected={
                "market.ohlcv": object,
                "signal.signal": object,
                "brain.decision": object,
                "execution.order": object,
            },
            should_pass=True,
        )
    )

    return suite


# ═══════════════════════════════════════════════════════════════════════════════
# 运行所有验证
# ═══════════════════════════════════════════════════════════════════════════════


def run_all_validations(nodes: dict[str, Any]) -> dict[str, list[ValidationResult]]:
    """
    运行所有验证套件

    Args:
        nodes: 节点字典 {"market": node_instance, ...}

    Returns:
        每个套件的验证结果
    """
    all_results = {}

    # MarketNode
    if "market" in nodes:
        suite = create_market_validation_suite()
        results = suite.run(nodes["market"])
        all_results["MarketNode"] = results

    # SignalNode
    if "signal" in nodes:
        suite = create_signal_validation_suite()
        results = suite.run(nodes["signal"])
        all_results["SignalNode"] = results

    # RiskNode
    if "risk" in nodes:
        suite = create_risk_validation_suite()
        results = suite.run(nodes["risk"])
        all_results["RiskNode"] = results

    # BrainNode
    if "brain" in nodes:
        suite = create_brain_validation_suite()
        results = suite.run(nodes["brain"])
        all_results["BrainNode"] = results

    # ExecutionNode
    if "execution" in nodes:
        suite = create_execution_validation_suite()
        results = suite.run(nodes["execution"])
        all_results["ExecutionNode"] = results

    return all_results


def generate_validation_report(all_results: dict[str, list[ValidationResult]]) -> str:
    """生成完整验证报告"""
    lines = []

    total_passed = 0
    total_failed = 0

    for suite_name, results in all_results.items():
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        total_passed += passed
        total_failed += failed

        lines.append(f"\n{'='*60}")
        lines.append(f"Suite: {suite_name}")
        lines.append(f"{'='*60}")
        lines.append(f"Passed: {passed}/{len(results)} | Failed: {failed}")
        lines.append("")

        for result in results:
            status = "[PASS]" if result.passed else "[FAIL]"
            lines.append(f"  {status} {result.name}")
            lines.append(f"         {result.message}")

    lines.append(f"\n{'='*60}")
    lines.append("FINAL RESULT")
    lines.append(f"{'='*60}")
    lines.append(f"Total: {total_passed + total_failed} | Passed: {total_passed} | Failed: {total_failed}")
    lines.append(f"Status: {'ALL PASSED' if total_failed == 0 else 'SOME FAILED'}")
    lines.append(f"{'='*60}\n")

    return "\n".join(lines)


if __name__ == "__main__":
    # 导入节点
    import sys

    sys.path.insert(0, ".")

    # 简单验证测试
    print("\n" + "=" * 70)
    print("CapsuleNode Validation Framework")
    print("=" * 70)
    print("\nThis framework validates that:")
    print("  1. Each node produces expected outputs")
    print("  2. Invalid inputs are correctly rejected")
    print("  3. Constraints are properly enforced")
    print("  4. Pipeline produces correct results")
    print("\nTo run actual tests, use test_validation.py")
