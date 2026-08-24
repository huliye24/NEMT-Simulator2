"""
Error Handler Tests - 错误处理器测试

测试步骤 29：错误处理器注册路由、冷却机制、告警回调
"""

import sys
from pathlib import Path

# Add nemt_os root to path so 'nemt' package can be imported
# Path: e:\NEMT Simulator\nemt_os\nemt\core\dark_matter\tests\test_error_handler.py
# Target: e:\NEMT Simulator\nemt_os
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "nemt_os"))  # 确保 nemt 包可导入
sys.stdout.reconfigure(encoding="utf-8")


def test_error_handler_singleton():
    """测试错误处理器模块级单例"""
    print("\n" + "=" * 60)
    print("测试: 错误处理器模块级单例")
    print("=" * 60)

    from nemt.core.dark_matter.error_handler import (
        get_error_handler,
        reset_error_handler,
    )

    # 重置单例
    reset_error_handler()

    handler1 = get_error_handler()
    handler2 = get_error_handler()

    assert handler1 is handler2, "两次 get_error_handler 应返回同一实例"
    print("[PASS] 模块级单例正确")

    # 清理
    reset_error_handler()


def test_error_handler_register():
    """测试错误处理器注册"""
    print("\n" + "=" * 60)
    print("测试: 错误处理器注册")
    print("=" * 60)

    from nemt.core.dark_matter.error_handler import (
        get_error_handler,
        reset_error_handler,
    )
    from nemt.core.dark_matter.error_types import InsufficientBalanceError

    reset_error_handler()
    handler = get_error_handler()

    # 测试注册
    call_log = []

    def balance_handler(error, context):
        call_log.append(("balance", error, context.source))

    def generic_handler(error, context):
        call_log.append(("generic", error, context.source))

    handler.register(InsufficientBalanceError, balance_handler)
    handler.register_default(generic_handler)

    # 触发精确匹配
    err = InsufficientBalanceError(required=1000.0, available=500.0)
    handler.handle(err)

    assert len(call_log) == 1, "应只调用一次"
    assert call_log[0][0] == "balance", "应调用精确匹配的处理器"
    print("[PASS] 精确匹配正确")

    # 清理
    reset_error_handler()


def test_error_handler_inheritance_match():
    """测试基类匹配"""
    print("\n" + "=" * 60)
    print("测试: 基类匹配")
    print("=" * 60)

    from nemt.core.dark_matter.error_handler import get_error_handler, reset_error_handler
    from nemt.core.dark_matter.error_types import TradingError

    reset_error_handler()
    handler = get_error_handler()

    call_log = []

    def trading_handler(error, context):
        call_log.append(("trading", error.code))

    handler.register(TradingError, trading_handler)

    # 子类错误应匹配基类处理器
    from nemt.core.dark_matter.error_types import InsufficientBalanceError

    err = InsufficientBalanceError(required=1000.0, available=500.0)
    handler.handle(err)

    assert len(call_log) == 1, "应匹配基类处理器"
    assert call_log[0][0] == "trading", "应调用 TradingError 处理器"
    print("[PASS] 基类匹配正确")

    # 清理
    reset_error_handler()


def test_error_handler_default():
    """测试默认处理器"""
    print("\n" + "=" * 60)
    print("测试: 默认处理器")
    print("=" * 60)

    from nemt.core.dark_matter.error_handler import get_error_handler, reset_error_handler

    reset_error_handler()
    handler = get_error_handler()

    call_log = []

    def default_handler(error, context):
        call_log.append(("default", type(error).__name__))

    handler.register_default(default_handler)

    # 未知错误应走默认处理器
    err = ValueError("Unknown error")
    handler.handle(err)

    assert len(call_log) == 1, "应调用默认处理器"
    assert call_log[0][0] == "default", "应调用默认处理器"
    print("[PASS] 默认处理器正确")

    # 清理
    reset_error_handler()


def test_error_handler_stats():
    """测试错误统计"""
    print("\n" + "=" * 60)
    print("测试: 错误统计")
    print("=" * 60)

    from nemt.core.dark_matter.error_handler import get_error_handler, reset_error_handler

    reset_error_handler()
    handler = get_error_handler()

    from nemt.core.dark_matter.error_types import ExchangeConnectionError, InsufficientBalanceError

    # 触发多个错误
    handler.handle(InsufficientBalanceError(required=1000.0, available=500.0))
    handler.handle(InsufficientBalanceError(required=2000.0, available=500.0))
    handler.handle(ExchangeConnectionError(exchange="BINANCE"))

    stats = handler.get_error_stats()

    assert stats["total_errors"] == 3, f"应有 3 个错误，实际 {stats['total_errors']}"
    assert "InsufficientBalanceError" in stats["error_stats"], "应有 InsufficientBalanceError 统计"
    assert stats["error_stats"]["InsufficientBalanceError"] == 2, "应有 2 个余额不足错误"
    assert stats["error_stats"]["ExchangeConnectionError"] == 1, "应有 1 个连接错误"

    print(f"[PASS] 错误统计: {stats}")
    print("[PASS] reset_stats 前的统计正确")

    # 测试重置
    handler.reset_stats()
    stats = handler.get_error_stats()
    assert stats["total_errors"] == 0, "重置后应为 0 个错误"

    print("[PASS] reset_stats 正确")

    # 清理
    reset_error_handler()


def test_error_handler_history():
    """测试错误历史"""
    print("\n" + "=" * 60)
    print("测试: 错误历史")
    print("=" * 60)

    from nemt.core.dark_matter.error_handler import get_error_handler, reset_error_handler
    from nemt.core.dark_matter.error_types import InsufficientBalanceError

    reset_error_handler()
    handler = get_error_handler()

    # 触发多个错误
    for i in range(5):
        handler.handle(InsufficientBalanceError(required=float(i * 100), available=50.0))

    # 测试获取历史
    history = handler.get_error_history(limit=3)
    assert len(history) == 3, f"应返回 3 条历史，实际 {len(history)}"
    print(f"[PASS] 历史限制正确: {len(history)} 条")

    # 测试按类型过滤
    history = handler.get_error_history(error_type="InsufficientBalanceError")
    assert len(history) == 5, f"应返回 5 条历史，实际 {len(history)}"
    print("[PASS] 按类型过滤正确")

    # 测试清除历史
    handler.clear_history()
    history = handler.get_error_history()
    assert len(history) == 0, "清除后应为空"
    print("[PASS] 清除历史正确")

    # 清理
    reset_error_handler()


def test_error_context_manager():
    """测试错误上下文管理器"""
    print("\n" + "=" * 60)
    print("测试: 错误上下文管理器")
    print("=" * 60)

    from nemt.core.dark_matter.error_handler import get_error_handler, reset_error_handler

    reset_error_handler()
    handler = get_error_handler()

    call_log = []

    def tracking_handler(error, context):
        call_log.append(context.source)

    handler.register_default(tracking_handler)

    # 使用上下文管理器
    with handler.error_context("execution"):
        handler.handle(ValueError("test1"))

    handler.handle(ValueError("test2"))

    assert len(call_log) == 2, "应调用两次"
    assert call_log[0] == "execution", "第一个应有上下文"
    assert call_log[1] == "unknown", "第二个应为默认来源"
    print(f"[PASS] 上下文管理器正确: {call_log}")

    # 清理
    reset_error_handler()


def test_error_handler_alert_callback():
    """测试告警回调"""
    print("\n" + "=" * 60)
    print("测试: 告警回调")
    print("=" * 60)

    from nemt.core.dark_matter.error_handler import get_error_handler, reset_error_handler
    from nemt.core.dark_matter.error_types import ErrorContext, NEMTError

    reset_error_handler()
    handler = get_error_handler()

    alert_log = []

    def alert_callback(error: NEMTError, context: ErrorContext):
        alert_log.append((error.code, context.source))

    handler.register_alert_callback(alert_callback)

    # 触发告警
    from nemt.core.dark_matter.error_types import ExchangeConnectionError

    err = ExchangeConnectionError(exchange="BINANCE")
    handler.notify_alert(err, ErrorContext(error=err, source="market"))

    assert len(alert_log) == 1, "应触发一次告警"
    assert alert_log[0][0] == "EXCHANGE_CONNECTION_ERROR", "应记录错误码"
    print(f"[PASS] 告警回调正确: {alert_log}")

    # 清理
    handler.unregister_alert_callback(alert_callback)
    reset_error_handler()


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("暗物质框架 - 错误处理器测试套件")
    print("=" * 60)

    tests = [
        test_error_handler_singleton,
        test_error_handler_register,
        test_error_handler_inheritance_match,
        test_error_handler_default,
        test_error_handler_stats,
        test_error_handler_history,
        test_error_context_manager,
        test_error_handler_alert_callback,
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
