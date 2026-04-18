# -*- coding: utf-8 -*-
"""
NEMT Test Suite
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(str(project_root))

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')


def test_imports():
    """Test module imports"""
    try:
        from nemt.market import MarketLayer, MarketState
        from nemt.data_layer import DataLayer
        from nemt.signal_layer import SignalLayer
        from nemt.strategy import Strategy, StrategyPool, TrendStrategy
        from nemt.execution import ExecutionLayer
        from nemt.risk import RiskLayer, RiskMode
        from nemt.brain import BrainLayer
        from nemt.evolution import EvolutionLayer
        from nemt.dashboard import Dashboard
        from nemt.backtest import NEMTEngine
        print("[PASS] All imports successful")
        return True
    except ImportError as e:
        print(f"[FAIL] Import failed: {e}")
        return False


def test_market_layer():
    """Test market layer"""
    from nemt.market import MarketLayer, MarketState

    market = MarketLayer()
    # Test without data - should handle gracefully
    state = market.detect_regime()
    print(f"  Market state (no data): {state.value}")

    print("[PASS] Market layer test")
    return True


def test_data_layer():
    """Test data layer"""
    from nemt.data_layer import DataLayer
    import pandas as pd
    import numpy as np

    dates = pd.date_range('2024-01-01', periods=100, freq='h')
    data = pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.rand(100) * 1000
    }, index=dates)

    dl = DataLayer(data)
    bar = dl.get_current_bar()
    assert bar is not None
    print(f"  Current price: {bar.close:.2f}")

    # Move to middle of data to test history
    for _ in range(50):
        dl.advance()

    history = dl.get_history(10)
    assert len(history) >= 10, f"Expected at least 10 bars, got {len(history)}"

    print("[PASS] Data layer test")
    return True


def test_signal_layer():
    """Test signal layer"""
    from nemt.signal_layer import SignalLayer
    import numpy as np

    sl = SignalLayer()
    closes = np.cumsum(np.random.randn(100)) + 100
    highs = closes + np.random.rand(100) * 2
    lows = closes - np.random.rand(100) * 2
    volumes = np.random.rand(100) * 1000

    indicators = sl.calculate_indicators(closes, highs, lows, volumes)
    print(f"  RSI: {indicators.get('rsi', 0):.2f}")
    print(f"  ATR: {indicators.get('atr', 0):.4f}")

    signals = sl.generate_all_signals(closes, highs, lows, volumes, closes[-1])
    print(f"  Signals generated: {len(signals)}")

    print("[PASS] Signal layer test")
    return True


def test_strategy():
    """Test strategy layer"""
    from nemt.strategy import TrendStrategy, StrategyPool, StrategyStatus
    import numpy as np

    closes = np.cumsum(np.random.randn(100)) + 100
    highs = closes + 2
    lows = closes - 2
    volumes = np.random.rand(100) * 1000

    strategy = TrendStrategy("Test Trend", fast_period=10, slow_period=30)
    signal = strategy.generate_signal(closes, highs, lows, volumes)
    print(f"  Strategy signal: {signal:.2f}")

    pool = StrategyPool()
    pool.add_strategy(strategy)
    active = pool.get_active_strategies()
    print(f"  Active strategies: {len(active)}")

    print("[PASS] Strategy layer test")
    return True


def test_execution():
    """Test execution layer"""
    from nemt.execution import ExecutionLayer, OrderSide, OrderType

    exec_layer = ExecutionLayer(initial_capital=10000)

    order = exec_layer.create_order(
        side=OrderSide.BUY,
        symbol="BTC/USDT",
        quantity=0.1,
        price=50000,
        order_type=OrderType.MARKET
    )
    print(f"  Order ID: {order.order_id}")

    success, msg = exec_layer.execute_order(order, 50000)
    print(f"  Execution result: {msg}")

    success, msg = exec_layer.close_position("BTC/USDT", exit_price=51000)
    print(f"  Close result: {msg}")

    print("[PASS] Execution layer test")
    return True


def test_risk():
    """Test risk layer"""
    from nemt.risk import RiskLayer, RiskMode

    risk = RiskLayer(max_drawdown_pct=20)

    approved, reason = risk.check_order(0.5, "test_strategy")
    print(f"  Risk check: {approved}, {reason}")

    risk.update_equity(9000)
    print(f"  Risk mode: {risk.get_risk_mode().value}")
    print(f"  Current drawdown: {risk.metrics.current_drawdown:.2f}%")

    print("[PASS] Risk layer test")
    return True


def test_full_pipeline():
    """Test full pipeline"""
    from nemt.backtest import NEMTEngine
    from nemt.config.settings import NEMTConfig

    config = NEMTConfig()
    engine = NEMTEngine(config)
    print("  Engine components initialized")

    print("[PASS] Full pipeline test")
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("NEMT System Tests")
    print("=" * 60)

    tests = [
        ("Module Imports", test_imports),
        ("Market Layer", test_market_layer),
        ("Data Layer", test_data_layer),
        ("Signal Layer", test_signal_layer),
        ("Strategy Layer", test_strategy),
        ("Execution Layer", test_execution),
        ("Risk Layer", test_risk),
        ("Full Pipeline", test_full_pipeline),
    ]

    results = []
    for name, test_func in tests:
        print(f"\nTest: {name}")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"[FAIL] Test failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = 0
    failed = 0
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
