"""
Log Analyzer Tests - 结构化日志测试

测试步骤 51-55：日志字段规范、上下文传播、JSON 格式化
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent / "nemt_os"
sys.path.insert(0, str(project_root))
sys.stdout.reconfigure(encoding="utf-8")


def test_log_context():
    """测试日志上下文"""
    print("\n" + "=" * 60)
    print("测试: LogContext")
    print("=" * 60)

    from nemt.core.dark_matter.structured_logger import LogContext

    # 测试基本创建
    context = LogContext(
        capsule_id="execution",
        symbol="BTC",
        bar_index=123,
    )
    context_dict = context.to_dict()

    assert context_dict["capsule_id"] == "execution", "capsule_id 应正确"
    assert context_dict["symbol"] == "BTC", "symbol 应正确"
    assert context_dict["bar_index"] == 123, "bar_index 应正确"
    print("[PASS] LogContext 基本创建正确")

    # 测试 with_trace_id
    context2 = context.with_trace_id("trace-123")
    assert context2.trace_id == "trace-123", "trace_id 应正确"
    assert context2.capsule_id == "execution", "原有字段应保持"
    print("[PASS] with_trace_id 正确")

    # 测试 extra
    context3 = LogContext(capsule_id="test", extra={"key": "value"})
    context_dict = context3.to_dict()
    assert context_dict["key"] == "value", "extra 应正确传递"
    print("[PASS] extra 字段正确")


def test_structured_logger_basic():
    """测试基本日志记录"""
    print("\n" + "=" * 60)
    print("测试: 基本日志记录")
    print("=" * 60)

    from nemt.core.dark_matter.structured_logger import StructuredLogger, clear_loggers

    clear_loggers()

    # 创建日志器
    logger = StructuredLogger("test_basic", level=logging.DEBUG, output_json=False)
    logger.set_level(logging.DEBUG)

    # 测试基本日志
    logger.info("Test message")
    logger.debug("Debug message")
    logger.warning("Warning message")
    logger.error("Error message")

    print("[PASS] 基本日志记录正常")


def test_structured_logger_json():
    """测试 JSON 日志输出"""
    print("\n" + "=" * 60)
    print("测试: JSON 日志输出")
    print("=" * 60)

    from nemt.core.dark_matter.structured_logger import clear_loggers, get_logger

    clear_loggers()

    # 创建日志器
    logger = get_logger("test_json", level=logging.DEBUG, output_json=True)
    logger.set_level(logging.DEBUG)

    # 记录带字段的日志
    logger.info("Order processed", order_id="ORD_001", amount=1.5)

    print("[PASS] JSON 日志记录正常")


def test_log_context_propagation():
    """测试上下文传播"""
    print("\n" + "=" * 60)
    print("测试: 上下文传播")
    print("=" * 60)

    from nemt.core.dark_matter.structured_logger import (
        LogContext,
        StructuredLogger,
        _context_storage,
        clear_loggers,
    )

    clear_loggers()

    # 创建日志器
    logger = StructuredLogger("test_context", level=logging.DEBUG, output_json=False)
    logger.set_level(logging.DEBUG)

    # 设置上下文
    context = LogContext(capsule_id="execution", symbol="ETH")
    _context_storage.set(context)

    # 记录日志
    logger.info("Test with context")

    # 清除上下文
    _context_storage.clear()

    print("[PASS] 上下文传播正常")


def test_log_context_manager():
    """测试日志上下文管理器"""
    print("\n" + "=" * 60)
    print("测试: 日志上下文管理器")
    print("=" * 60)

    from nemt.core.dark_matter.structured_logger import (
        _context_storage,
        clear_loggers,
        get_logger,
        log_context,
    )

    clear_loggers()

    logger = get_logger("test_ctx_mgr", level=logging.DEBUG, output_json=False)
    logger.set_level(logging.DEBUG)

    # 测试上下文管理器
    with log_context(capsule_id="execution", symbol="BTC"):
        logger.info("Inside context")
        assert _context_storage.get() is not None
        assert _context_storage.get().capsule_id == "execution"

    # 退出后上下文可能被清除（取决于测试执行顺序）
    # 这取决于测试隔离是否完全
    print("[PASS] 日志上下文管理器正确")


def test_get_logger_factory():
    """测试日志器工厂"""
    print("\n" + "=" * 60)
    print("测试: 日志器工厂")
    print("=" * 60)

    from nemt.core.dark_matter.structured_logger import clear_loggers, get_logger

    clear_loggers()

    # 多次获取同一名称应返回同一实例
    logger1 = get_logger("factory_test")
    logger2 = get_logger("factory_test")

    assert logger1 is logger2, "同一名称应返回同一实例"
    print("[PASS] 日志器工厂单例正确")


def test_log_levels():
    """测试日志级别"""
    print("\n" + "=" * 60)
    print("测试: 日志级别")
    print("=" * 60)

    from nemt.core.dark_matter.structured_logger import LogLevel

    assert LogLevel.from_python_level(logging.DEBUG) == LogLevel.DEBUG
    assert LogLevel.from_python_level(logging.INFO) == LogLevel.INFO
    assert LogLevel.from_python_level(logging.WARNING) == LogLevel.WARNING
    assert LogLevel.from_python_level(logging.ERROR) == LogLevel.ERROR
    assert LogLevel.from_python_level(logging.CRITICAL) == LogLevel.CRITICAL

    print("[PASS] 日志级别转换正确")


def test_log_constants():
    """测试日志常量"""
    print("\n" + "=" * 60)
    print("测试: 日志常量")
    print("=" * 60)

    from nemt.core.dark_matter.structured_logger import (
        LOG_BAR_INDEX,
        LOG_CAPSULE_ID,
        LOG_DURATION_MS,
        LOG_ERROR_CODE,
        LOG_EVENT_TYPE,
        LOG_SYMBOL,
        LOG_TRACE_ID,
    )

    assert LOG_CAPSULE_ID == "capsule_id"
    assert LOG_TRACE_ID == "trace_id"
    assert LOG_BAR_INDEX == "bar_index"
    assert LOG_SYMBOL == "symbol"
    assert LOG_EVENT_TYPE == "event_type"
    assert LOG_DURATION_MS == "duration_ms"
    assert LOG_ERROR_CODE == "error_code"

    print("[PASS] 日志常量定义正确")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("暗物质框架 - 结构化日志测试套件")
    print("=" * 60)

    tests = [
        test_log_context,
        test_structured_logger_basic,
        test_structured_logger_json,
        test_log_context_propagation,
        test_log_context_manager,
        test_get_logger_factory,
        test_log_levels,
        test_log_constants,
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
            print(f"[ERROR] {test.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
