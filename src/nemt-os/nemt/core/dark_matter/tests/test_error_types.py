"""
Error Types Tests - 错误类型测试

测试步骤 28-30：错误层次、错误处理器注册路由、ErrorFactory 映射
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.stdout.reconfigure(encoding="utf-8")


def test_error_hierarchy():
    """测试错误层次继承链"""
    print("\n" + "=" * 60)
    print("测试: 错误层次继承链")
    print("=" * 60)

    from nemt.core.dark_matter.error_types import (
        CapsuleInitError,
        DrawdownExceededError,
        ExchangeConnectionError,
        ExchangeError,
        InsufficientBalanceError,
        NEMTError,
        RiskError,
        SystemError,
        TradingError,
    )

    # 测试继承关系
    assert issubclass(InsufficientBalanceError, TradingError), "InsufficientBalanceError 应继承自 TradingError"
    assert issubclass(TradingError, NEMTError), "TradingError 应继承自 NEMTError"
    assert issubclass(ExchangeConnectionError, ExchangeError), "ExchangeConnectionError 应继承自 ExchangeError"
    assert issubclass(ExchangeError, NEMTError), "ExchangeError 应继承自 NEMTError"
    assert issubclass(DrawdownExceededError, RiskError), "DrawdownExceededError 应继承自 RiskError"
    assert issubclass(CapsuleInitError, SystemError), "CapsuleInitError 应继承自 SystemError"

    print("[PASS] 错误层次继承链正确")


def test_error_codes():
    """测试错误码定义"""
    print("\n" + "=" * 60)
    print("测试: 错误码定义")
    print("=" * 60)

    from nemt.core.dark_matter.error_types import ERROR_CODES

    # 测试关键错误码
    assert "INSUFFICIENT_BALANCE" in ERROR_CODES, "应有 INSUFFICIENT_BALANCE 错误码"
    assert "EXCHANGE_CONNECTION_ERROR" in ERROR_CODES, "应有 EXCHANGE_CONNECTION_ERROR 错误码"
    assert "DRAWDOWN_EXCEEDED" in ERROR_CODES, "应有 DRAWDOWN_EXCEEDED 错误码"

    # 测试错误码格式
    code, (desc, retryable, severity) = list(ERROR_CODES.items())[0]
    assert isinstance(desc, str), "错误描述应为字符串"
    assert isinstance(retryable, bool), "可重试标志应为布尔值"
    assert severity in ("INFO", "WARNING", "ERROR", "CRITICAL"), "严重等级应为有效值"

    print(f"[PASS] 错误码定义正确，共 {len(ERROR_CODES)} 个错误码")


def test_error_to_dict():
    """测试错误 to_dict 方法"""
    print("\n" + "=" * 60)
    print("测试: 错误 to_dict 方法")
    print("=" * 60)

    from nemt.core.dark_matter.error_types import ExchangeConnectionError, InsufficientBalanceError

    # 测试交易错误
    balance_err = InsufficientBalanceError(required=1000.0, available=500.0, symbol="BTC")
    balance_dict = balance_err.to_dict()

    assert balance_dict["error_code"] == "INSUFFICIENT_BALANCE", "错误码应正确"
    assert balance_dict["retryable"] == False, "交易错误不应可重试"
    assert balance_dict["severity"] == "WARNING", "严重等级应为 WARNING"
    assert "required" in balance_dict["details"], "应包含 required 详情"
    assert "available" in balance_dict["details"], "应包含 available 详情"

    print(f"[PASS] to_dict 输出: {balance_dict}")

    # 测试交易所错误
    exchange_err = ExchangeConnectionError(exchange="BINANCE", reason="Connection refused")
    exchange_dict = exchange_err.to_dict()

    assert exchange_dict["error_code"] == "EXCHANGE_CONNECTION_ERROR", "错误码应正确"
    assert exchange_dict["retryable"] == True, "交易所错误应可重试"
    assert exchange_dict["severity"] == "ERROR", "严重等级应为 ERROR"

    print(f"[PASS] to_dict 输出: {exchange_dict}")


def test_error_context():
    """测试 ErrorContext"""
    print("\n" + "=" * 60)
    print("测试: ErrorContext")
    print("=" * 60)

    from nemt.core.dark_matter.error_types import ErrorContext, InsufficientBalanceError

    err = InsufficientBalanceError(required=1000.0, available=500.0, symbol="BTC")
    context = ErrorContext(
        error=err,
        source="execution",
        attempt=1,
        max_attempts=3,
        details={"order_id": "ORD_001"},
    )

    # 测试 to_dict
    context_dict = context.to_dict()
    assert context_dict["error_type"] == "InsufficientBalanceError", "错误类型应正确"
    assert context_dict["source"] == "execution", "来源应正确"
    assert context_dict["attempt"] == 1, "重试次数应正确"
    assert context_dict["error_code"] == "INSUFFICIENT_BALANCE", "错误码应传递"
    assert "order_id" in context_dict["details"], "额外详情应传递"

    print(f"[PASS] ErrorContext to_dict: {context_dict}")

    # 测试 with_attempt
    context2 = context.with_attempt(2)
    assert context2.attempt == 2, "重试次数应更新"
    assert context2.source == "execution", "来源应保持"

    print("[PASS] ErrorContext.with_attempt 正确")


def test_recovery_strategy():
    """测试恢复策略"""
    print("\n" + "=" * 60)
    print("测试: 恢复策略")
    print("=" * 60)

    from nemt.core.dark_matter.error_types import (
        ExchangeConnectionError,
        InsufficientBalanceError,
        RecoveryStrategy,
    )

    # 测试 NEMTError 自动判断
    balance_err = InsufficientBalanceError(required=1000.0, available=500.0)
    assert balance_err.get_recovery_strategy() == RecoveryStrategy.PROPAGATE, "余额不足应传播"

    exchange_err = ExchangeConnectionError(exchange="BINANCE")
    assert exchange_err.get_recovery_strategy() == RecoveryStrategy.RETRY, "连接错误应重试"

    print("[PASS] 恢复策略判断正确")


def test_error_factory():
    """测试 ErrorFactory 异常映射"""
    print("\n" + "=" * 60)
    print("测试: ErrorFactory 异常映射")
    print("=" * 60)

    # 测试已知 NEMTError 直接返回
    from nemt.core.dark_matter.error_types import ErrorFactory, ExchangeConnectionError, NEMTError

    known_err = ExchangeConnectionError(exchange="BINANCE")
    result = ErrorFactory.from_exception(known_err, source="market")
    assert result is known_err, "已知 NEMTError 应直接返回"
    print("[PASS] 已知 NEMTError 直接返回")

    # 测试 ConnectionError 映射
    conn_err = ConnectionError("Connection refused")
    result = ErrorFactory.from_exception(conn_err, source="exchange")
    assert isinstance(result, NEMTError), "ConnectionError 应映射为 NEMTError"
    print(f"[PASS] ConnectionError 映射为: {type(result).__name__}")

    # 测试 TimeoutError 映射
    timeout_err = TimeoutError("Request timeout")
    result = ErrorFactory.from_exception(timeout_err, source="exchange")
    assert isinstance(result, NEMTError), "TimeoutError 应映射为 NEMTError"
    print(f"[PASS] TimeoutError 映射为: {type(result).__name__}")

    # 测试未知异常
    unknown_err = ValueError("Invalid value")
    result = ErrorFactory.from_exception(unknown_err, source="validation")
    assert isinstance(result, NEMTError), "未知异常应映射为 NEMTError"
    print(f"[PASS] 未知异常映射为: {type(result).__name__}")


def test_convenience_functions():
    """测试便捷函数"""
    print("\n" + "=" * 60)
    print("测试: 便捷函数")
    print("=" * 60)

    from nemt.core.dark_matter.error_types import (
        ExchangeConnectionError,
        InsufficientBalanceError,
        format_error_for_logging,
        get_error_code_info,
        is_retryable_error,
    )

    # 测试 is_retryable_error
    balance_err = InsufficientBalanceError(required=1000.0, available=500.0)
    assert is_retryable_error(balance_err) == False, "余额不足不应可重试"

    exchange_err = ExchangeConnectionError(exchange="BINANCE")
    assert is_retryable_error(exchange_err) == True, "连接错误应可重试"

    # error_types.is_retryable_error 只检查 NEMTError 实例
    # 标准异常（非 NEMTError）返回 False
    conn_err = ConnectionError("Failed")
    assert is_retryable_error(conn_err) == False, "标准异常应返回 False"

    print("[PASS] is_retryable_error 正确")

    # 测试 get_error_code_info
    desc, retryable, severity = get_error_code_info("INSUFFICIENT_BALANCE")
    assert desc == "余额不足", "描述应为余额不足"
    assert retryable == False, "不应可重试"
    assert severity == "WARNING", "严重等级应为 WARNING"

    print("[PASS] get_error_code_info 正确")

    # 测试 format_error_for_logging
    log_str = format_error_for_logging(exchange_err, context={"order_id": "ORD_001"})
    assert "ExchangeConnectionError" in log_str, "应包含错误类型"
    assert "BINANCE" in log_str, "应包含交易所名称"
    assert "order_id" in log_str, "应包含上下文"

    print(f"[PASS] format_error_for_logging: {log_str[:100]}...")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("暗物质框架 - 错误类型测试套件")
    print("=" * 60)

    tests = [
        test_error_hierarchy,
        test_error_codes,
        test_error_to_dict,
        test_error_context,
        test_recovery_strategy,
        test_error_factory,
        test_convenience_functions,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
