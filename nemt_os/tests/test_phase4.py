"""
Phase 4 验收测试
集成 NEMT Core 与数据层
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np


def test_pipeline_import():
    """测试 Pipeline 导入"""
    print("\n" + "=" * 60)
    print("Test: Pipeline Import")
    print("=" * 60)
    
    from nemt.nemt_core import NEMTPipeline, MultiSymbolPipeline, NLSParams
    print("[OK] All imports successful")
    
    return True


def test_single_symbol_pipeline():
    """测试单符号管道"""
    print("\n" + "=" * 60)
    print("Test: Single Symbol Pipeline")
    print("=" * 60)
    
    from nemt.nemt_core import NEMTPipeline, NLSParams
    
    # Create pipeline
    pipeline = NEMTPipeline(NLSParams(steps=50), lookback_periods=128)
    
    # Generate test data
    np.random.seed(42)
    prices = np.cumsum(np.random.randn(150) * 2 + 0.1) + 100
    
    # Add prices
    signal_count = 0
    for price in prices:
        signals = pipeline.add_price(price)
        if signals:
            signal_count += len(signals)
    
    print("[OK] Added", len(prices), "prices")
    
    # Get state
    state = pipeline.get_current_state()
    assert state['phase'] != 'UNKNOWN'
    print("[OK] State phase:", state['phase'])
    print("[OK] Confidence:", state['phase_confidence'])
    print("[OK] Spectral width:", state['spectral_width'])
    print("[OK] Coherence:", state['coherence'])
    
    # Get signals
    signals = pipeline.get_latest_signals(10)
    print("[OK] Generated", signal_count, "signals")
    
    # Reset
    pipeline.reset()
    state = pipeline.get_current_state()
    assert state['phase'] == 'UNKNOWN'
    print("[OK] Pipeline reset successful")
    
    return True


def test_multi_symbol_pipeline():
    """测试多符号管道"""
    print("\n" + "=" * 60)
    print("Test: Multi-Symbol Pipeline")
    print("=" * 60)
    
    from nemt.nemt_core import MultiSymbolPipeline, NLSParams
    
    # Create multi-symbol pipeline
    msp = MultiSymbolPipeline(NLSParams(steps=50))
    
    # Add symbols
    btc_pipeline = msp.add_symbol('BTCUSDT')
    eth_pipeline = msp.add_symbol('ETHUSDT')
    
    print("[OK] Added BTCUSDT and ETHUSDT")
    
    # Generate data
    np.random.seed(42)
    btc_prices = np.cumsum(np.random.randn(150) * 50 + 0.1) + 67500
    eth_prices = np.cumsum(np.random.randn(150) * 5 + 0.1) + 3450
    
    # Add prices
    for i in range(len(btc_prices)):
        msp.add_price('BTCUSDT', btc_prices[i])
        msp.add_price('ETHUSDT', eth_prices[i])
    
    print("[OK] Added price data for both symbols")
    
    # Get states
    btc_state = msp.get_state('BTCUSDT')
    eth_state = msp.get_state('ETHUSDT')
    
    assert btc_state['phase'] != 'UNKNOWN'
    assert eth_state['phase'] != 'UNKNOWN'
    print("[OK] BTC state:", btc_state['phase'])
    print("[OK] ETH state:", eth_state['phase'])
    
    # Get all states
    all_states = msp.get_all_states()
    assert len(all_states) == 2
    print("[OK] All states:", list(all_states.keys()))
    
    return True


def test_pipeline_params():
    """测试参数更新"""
    print("\n" + "=" * 60)
    print("Test: Pipeline Parameters")
    print("=" * 60)
    
    from nemt.nemt_core import NEMTPipeline, NLSParams
    
    pipeline = NEMTPipeline()
    
    # Default params
    params = pipeline.nls_params
    print("[OK] Default alpha:", params.alpha)
    print("[OK] Default beta:", params.beta)
    print("[OK] Default steps:", params.steps)
    
    # Update params
    pipeline.set_nls_params(alpha=0.3, beta=2.0, steps=100)
    
    params = pipeline.nls_params
    assert params.alpha == 0.3
    assert params.beta == 2.0
    assert params.steps == 100
    print("[OK] Updated alpha:", params.alpha)
    print("[OK] Updated beta:", params.beta)
    print("[OK] Updated steps:", params.steps)
    
    return True


def test_integration():
    """集成测试"""
    print("\n" + "=" * 60)
    print("Test: Integration")
    print("=" * 60)
    
    from nemt.nemt_core import NEMTPipeline, MultiSymbolPipeline, NLSParams
    from nemt.market_providers import MockMarketProvider
    from nemt.event_bus import EventBus
    
    print("[OK] Import all components successful")
    
    # Create event bus
    eb = EventBus.get_instance()
    print("[OK] EventBus created")
    
    # Create market provider
    mp = MockMarketProvider()
    mp.connect()
    print("[OK] Market provider connected")
    
    # Create pipeline
    pipeline = NEMTPipeline(NLSParams(steps=30), lookback_periods=64)
    print("[OK] NEMT Pipeline created")
    
    # Simulate processing
    np.random.seed(123)
    prices = np.cumsum(np.random.randn(100) * 2 + 0.05) + 100
    
    for price in prices:
        pipeline.add_price(price)
    
    state = pipeline.get_current_state()
    print("[OK] Final state:", state['phase'])
    print("[OK] Strategy:", state['strategy']['strategy_text'])
    print("[OK] Position:", state['recommendations']['position'])
    print("[OK] Leverage:", state['recommendations']['leverage'])
    
    # Cleanup
    mp.disconnect()
    print("[OK] Cleanup successful")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("NEMT Phase 4 Acceptance Tests")
    print("Integration: NEMT Core + Data Layer + Event Bus")
    print("=" * 60)
    
    tests = [
        ("Pipeline Import", test_pipeline_import),
        ("Single Symbol Pipeline", test_single_symbol_pipeline),
        ("Multi-Symbol Pipeline", test_multi_symbol_pipeline),
        ("Pipeline Parameters", test_pipeline_params),
        ("Integration Test", test_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print("[FAIL]", name, ":", e)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for name, success, error in results:
        status = "[PASS]" if success else "[FAIL]"
        print(status, name)
        if error:
            print("     Error:", error)
        if not success:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("Phase 4 Acceptance Tests: ALL PASSED")
    else:
        print("Phase 4 Acceptance Tests: SOME FAILED")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
