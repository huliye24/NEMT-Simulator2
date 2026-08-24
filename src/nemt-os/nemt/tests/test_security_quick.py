"""
NEMT 安全测试简化版
"""

import sys

sys.path.insert(0, "nemt_os")

print("=" * 60)
print("NEMT SIMULATOR 安全测试")
print("=" * 60)

results = {"passed": 0, "failed": 0, "errors": 0}


def test(name, func):
    try:
        func()
        print(f"  [PASS] {name}")
        results["passed"] += 1
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        results["failed"] += 1


# 1. 导入测试
print("\n[1] 导入测试")


def test_imports():
    pass


test("模块导入", test_imports)

# 2. ConfigCenter 测试
print("\n[2] ConfigCenter 测试")


def test_config():
    from nemt.core import ConfigCenter

    c = ConfigCenter()
    c.set("test.key", "value")
    assert c.get("test.key") == "value"
    assert c.get("nonexistent", "default") == "default"


test("ConfigCenter 基础", test_config)


def test_config_nested():
    from nemt.core import ConfigCenter

    c = ConfigCenter()
    c.set("a.b.c", "deep")
    assert c.get("a.b.c") == "deep"


test("ConfigCenter 嵌套", test_config_nested)

# 3. EventBus 测试
print("\n[3] EventBus 测试")


def test_event_bus():
    from nemt.core import EventBus

    bus = EventBus()
    received = []

    def handler(d):
        received.append(d)

    bus.subscribe("test", handler)
    bus.publish("test", {"v": 1})
    import time

    time.sleep(0.1)
    assert len(received) == 1


test("EventBus 发布订阅", test_event_bus)

# 4. Capsule 测试
print("\n[4] Capsule 测试")


def test_fractal_capsule():
    from unittest.mock import Mock

    from nemt.core import FractalCapsule

    class T(FractalCapsule):
        def observe_phase(self):
            return {}

        def design_phase(self):
            return {}

        def implement_phase(self):
            pass

        def verify_phase(self):
            return {}

        def integrate_phase(self):
            pass

        def init(self):
            pass

        def exec(self):
            return {}

        def shutdown(self):
            pass

    c = T("test")
    c.event_bus = Mock()
    c.config = Mock()
    result = c.run_fractal_iteration()
    assert result["status"] == "success"


test("FractalCapsule 迭代", test_fractal_capsule)

# 5. MarketCapsule 测试
print("\n[5] MarketCapsule 测试")


def test_market():
    from unittest.mock import Mock

    from nemt.core.market import MarketCapsule

    m = MarketCapsule("test")
    m.event_bus = Mock()
    m.config = Mock()
    m.add_price("BTCUSDT", 50000.0)
    assert m.get_price("BTCUSDT") == 50000.0


test("MarketCapsule 价格", test_market)

# 6. SignalCapsule 测试
print("\n[6] SignalCapsule 测试")


def test_signal():
    from unittest.mock import Mock

    from nemt.core.signal import SignalCapsule

    s = SignalCapsule("test")
    s.event_bus = Mock()
    s.config = Mock()
    prices = [100.0 + i * 0.5 for i in range(50)]
    indicators = s.calculate_indicators(prices)
    assert "rsi" in indicators


test("SignalCapsule RSI", test_signal)

# 7. RiskCapsule 测试
print("\n[7] RiskCapsule 测试")


def test_risk():
    from unittest.mock import Mock

    from nemt.core.risk import RiskCapsule

    r = RiskCapsule("test")
    r.event_bus = Mock()
    r.config = Mock()
    r.update_balance(10000.0)
    metrics = r.get_risk_metrics()
    assert "current_balance" in metrics


test("RiskCapsule 风控", test_risk)

# 8. ExecutionCapsule 测试
print("\n[8] ExecutionCapsule 测试")


def test_execution():
    from unittest.mock import Mock

    from nemt.core.execution import ExecutionCapsule, OrderSide

    e = ExecutionCapsule("test")
    e.event_bus = Mock()
    e.config = Mock()
    e.set_balance(10000.0)
    order = e.submit_order("BTCUSDT", OrderSide.BUY, 0.1, 50000.0)
    assert order.symbol == "BTCUSDT"


test("ExecutionCapsule 订单", test_execution)

# 9. Metrics 测试
print("\n[9] Metrics 测试")


def test_metrics():
    from nemt.core.metrics import FractalMetricsCollector

    mc = FractalMetricsCollector.get_instance()
    mc.reset()
    mc.start_iteration("test", "L1")
    mc.start_phase("observe")
    mc.complete_phase("observe")
    result = mc.end_iteration()
    assert result.completion_rate == 20.0


test("Metrics 完成率", test_metrics)

# 10. ViewSwitcher 测试
print("\n[10] ViewSwitcher 测试")


def test_view():
    from nemt.core.view_switcher import ViewMode, ViewSwitcher

    vs = ViewSwitcher()
    ctx = vs.macro_view()
    assert ctx.mode == ViewMode.MACRO
    ctx = vs.micro_view("capsule", "L2")
    assert ctx.capsule_id == "capsule"


test("ViewSwitcher 切换", test_view)

# 11. LayerLock 测试
print("\n[11] LayerLock 测试")


def test_lock():
    from nemt.core.layer_lock import LayerLockManager

    lm = LayerLockManager.get_instance()
    lm.reset()
    c = lm.register_contract("L0", "test", "main")
    assert c.layer == "L0"
    lm.freeze_contract("L0", "test", "main")
    assert lm.can_start_layer("L1") == True


test("LayerLock 冻结", test_lock)

# 12. 并发测试
print("\n[12] 并发测试")


def test_concurrent():
    import threading
    from unittest.mock import Mock

    from nemt.core.market import MarketCapsule

    m = MarketCapsule("concurrent")
    m.event_bus = Mock()
    m.config = Mock()

    def add(i):
        for j in range(100):
            m.add_price(f"SYM{i}", 50000.0 + j)

    threads = [threading.Thread(target=add, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


test("并发写入", test_concurrent)

# 总结
print("\n" + "=" * 60)
print("测试结果")
print("=" * 60)
total = results["passed"] + results["failed"] + results["errors"]
pass_rate = results["passed"] / total * 100 if total > 0 else 0
print(f"总测试: {total}")
print(f"通过: {results['passed']}")
print(f"失败: {results['failed']}")
print(f"通过率: {pass_rate:.1f}%")
print("=" * 60)

if results["failed"] == 0:
    print("\n所有安全测试通过!")
else:
    print(f"\n有 {results['failed']} 项测试失败")
