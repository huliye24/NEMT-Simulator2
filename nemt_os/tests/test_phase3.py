"""
Phase 3 验收测试
NEMT Core: NLS方程、四相位检测、谱分析、信号生成
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np


def test_nls_solver():
    """测试 NLS 方程求解器"""
    print("\n" + "=" * 60)
    print("Test: NLS Equation Solver")
    print("=" * 60)
    
    from nemt.emt_core import NLSSolver, NLSParams
    
    # Test with default params
    solver = NLSSolver()
    assert solver.params.alpha == 0.5
    assert solver.params.beta == 1.0
    print("[OK] Default params")
    
    # Test with custom params
    params = NLSParams(alpha=0.3, beta=2.0, noise_level=0.2, steps=50)
    solver = NLSSolver(params)
    assert solver.params.alpha == 0.3
    assert solver.params.beta == 2.0
    print("[OK] Custom params")
    
    # Test state initialization
    price_data = np.random.randn(128) * 10 + 100
    normalized = solver.initialize_state(price_data)
    assert len(normalized) == 128
    assert abs(np.mean(normalized)) < 0.1  # Should be close to 0
    print("[OK] State initialization")
    
    # Test evolution
    psi = solver.evolve()
    assert len(psi) == 128
    print("[OK] Evolution")
    
    # Test spectral analysis
    freqs, amps = solver.get_spectral_analysis()
    assert len(freqs) > 0
    assert len(amps) > 0
    print(f"[OK] Spectral analysis: {len(freqs)} frequencies")
    
    # Test spectral width
    sw = solver.compute_spectral_width()
    assert sw >= 0
    print(f"[OK] Spectral width: {sw:.6f}")
    
    # Test resonance peaks
    peaks = solver.detect_resonance_peaks()
    assert 'num_peaks' in peaks
    print(f"[OK] Resonance peaks: {peaks['num_peaks']}")
    
    # Test complete experiment
    result = solver.run_experiment(price_data)
    assert 'spectral_width' in result
    assert 'frequencies' in result
    assert 'resonance' in result
    print(f"[OK] Complete experiment: spectral_width={result['spectral_width']:.6f}")
    
    return True


def test_phase_detector():
    """测试相位检测器"""
    print("\n" + "=" * 60)
    print("Test: Phase Detector")
    print("=" * 60)
    
    from nemt.emt_core import PhaseDetector, MarketPhase, PHASE_STRATEGIES
    
    detector = PhaseDetector()
    
    # Test Phase A (Noise) - high spectral width
    result = detector.detect(spectral_width=0.03, resonance_peaks=0)
    assert result.phase == MarketPhase.PHASE_A_NOISE
    assert result.confidence > 0
    phase_val = result.phase.value
    print("[OK] Phase A (Noise):", phase_val, ", confidence =", round(result.confidence, 2))
    
    # Test Phase B (Vortex) - medium spectral width
    result = detector.detect(spectral_width=0.022, resonance_peaks=1)
    assert result.phase == MarketPhase.PHASE_B_VORTEX
    phase_val = result.phase.value
    print("[OK] Phase B (Vortex):", phase_val, ", confidence =", round(result.confidence, 2))
    
    # Test Phase C (Resonance) - low spectral width
    result = detector.detect(spectral_width=0.016, resonance_peaks=3)
    assert result.phase == MarketPhase.PHASE_C_RESONANCE
    phase_val = result.phase.value
    print("[OK] Phase C (Resonance):", phase_val, ", confidence =", round(result.confidence, 2))
    
    # Test Phase D (Trend) - very low spectral width
    result = detector.detect(spectral_width=0.010, resonance_peaks=2, trend_strength=0.8)
    assert result.phase == MarketPhase.PHASE_D_TREND
    phase_val = result.phase.value
    print("[OK] Phase D (Trend):", phase_val, ", confidence =", round(result.confidence, 2))
    
    # Test phase strategies
    strategy = detector.get_phase_strategy(MarketPhase.PHASE_C_RESONANCE)
    assert strategy.max_position == 0.6
    assert strategy.leverage_allowed == 3
    print("[OK] Phase strategy: max_position =", strategy.max_position, ", leverage =", strategy.leverage_allowed)
    
    # Test recommended position
    pos = detector.get_recommended_position(MarketPhase.PHASE_D_TREND)
    assert pos == 0.5  # strategy.max_position(1.0) * base_position(0.5)
    print("[OK] Recommended position:", pos)
    
    try:
        return True
    except Exception as e:
        print("[ERROR] Phase Detector:", str(e))
        raise


def test_spectral_analyzer():
    """测试谱分析器"""
    print("\n" + "=" * 60)
    print("Test: Spectral Analyzer")
    print("=" * 60)
    
    from nemt.emt_core import SpectralAnalyzer
    
    analyzer = SpectralAnalyzer()
    
    # Generate test signal
    t = np.linspace(0, 1, 256)
    signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 20 * t)
    
    # Test FFT
    freqs, amps = analyzer.compute_fft(signal)
    assert len(freqs) > 0
    assert len(freqs) == len(amps)
    print(f"[OK] FFT: {len(freqs)} frequencies")
    
    # Test spectral width
    sw = analyzer.compute_spectral_width(freqs, amps)
    assert sw >= 0
    print(f"[OK] Spectral width: {sw:.6f}")
    
    # Test peak finding
    peak_freqs, peak_amps = analyzer.find_peaks(freqs, amps)
    print(f"[OK] Found {len(peak_freqs)} peaks")
    
    # Test coherence
    coherence = analyzer.compute_coherence(freqs, amps)
    assert 0 <= coherence <= 1
    print(f"[OK] Coherence: {coherence:.4f}")
    
    # Test entropy
    entropy = analyzer.compute_entropy(freqs, amps)
    assert 0 <= entropy <= 1
    print(f"[OK] Entropy: {entropy:.4f}")
    
    # Test complete analysis
    metrics = analyzer.analyze(signal)
    assert metrics.spectral_width >= 0
    assert metrics.peak_count >= 0
    print(f"[OK] Complete analysis: {metrics.peak_count} peaks, coherence={metrics.coherence:.4f}")
    
    return True


def test_signal_generator():
    """测试信号生成器"""
    print("\n" + "=" * 60)
    print("Test: Signal Generator")
    print("=" * 60)
    
    from nemt.emt_core import SignalGenerator, SignalType, SignalDirection
    
    gen = SignalGenerator()
    
    # Test vortex breakout signal
    signal = gen.generate_vortex_breakout(
        phase='PHASE_B_VORTEX',
        spectral_width=0.022,
        coherence=0.6,
        price=100.0,
        prev_price=98.0
    )
    assert signal is not None
    assert signal.direction == SignalDirection.BULLISH
    dir_val = signal.direction.value
    print("[OK] Vortex breakout:", dir_val)
    
    # Test resonance trigger signal
    signal = gen.generate_resonance_trigger(
        phase='PHASE_C_RESONANCE',
        resonance_peaks=3,
        spectral_width=0.012,  # Lower than 0.015 to get strength_factor > 0.3
        price=100.0
    )
    assert signal is not None
    assert signal.signal_type == SignalType.RESONANCE_TRIGGER
    stype_val = signal.signal_type.value
    print("[OK] Resonance trigger:", stype_val)
    
    # Test phase transition signal
    signal = gen.generate_phase_transition(
        prev_phase='PHASE_C_RESONANCE',
        current_phase='PHASE_D_TREND',
        confidence=0.8,
        price=100.0
    )
    assert signal is not None
    assert signal.signal_type == SignalType.PHASE_TRANSITION
    phase_val = signal.phase
    print("[OK] Phase transition:", phase_val)
    
    # Test noise signal
    signal = gen.generate_noise_signal(
        phase='PHASE_A_NOISE',
        spectral_width=0.035,
        price=100.0
    )
    assert signal is not None
    assert signal.signal_type == SignalType.NOISE_SIGNAL
    reason_short = signal.reason[:30] if len(signal.reason) > 30 else signal.reason
    print("[OK] Noise signal:", reason_short, "...")
    
    # Test generate all signals
    signals = gen.generate_all_signals(
        phase='PHASE_C_RESONANCE',
        prev_phase='PHASE_B_VORTEX',
        spectral_width=0.016,
        coherence=0.7,
        resonance_peaks=2,
        price=100.0,
        prev_price=99.0,
        trend_price=98.0,
        confidence=0.75
    )
    assert len(signals) > 0
    sig_count = len(signals)
    print("[OK] Generated", sig_count, "signals")
    
    # Test signal history
    history = gen.get_latest_signals(5)
    assert len(history) > 0
    hist_len = len(history)
    print("[OK] Signal history:", hist_len, "signals")
    
    try:
        return True
    except Exception as e:
        print("[ERROR] Signal Generator:", str(e))
        raise


def test_integration():
    """集成测试"""
    print("\n" + "=" * 60)
    print("Test: Integration - Full Pipeline")
    print("=" * 60)
    
    from nemt.emt_core import NLSSolver, NLSParams, PhaseDetector, SpectralAnalyzer, SignalGenerator
    
    # 1. Generate market data
    np.random.seed(42)
    price_data = np.cumsum(np.random.randn(128) * 2 + 0.1) + 100
    print(f"[OK] Generated {len(price_data)} price points")
    
    # 2. Run NLS experiment
    solver = NLSSolver(NLSParams(steps=50))
    result = solver.run_experiment(price_data)
    sw = result['spectral_width']
    print(f"[OK] NLS Experiment: spectral_width={sw:.6f}")
    
    # 3. Detect phase
    detector = PhaseDetector()
    phase = detector.detect(spectral_width=sw, resonance_peaks=result['resonance']['num_peaks'])
    print(f"[OK] Phase: {phase.phase.value} (confidence={phase.confidence:.2f})")
    
    # 4. Spectral analysis
    analyzer = SpectralAnalyzer()
    metrics = analyzer.analyze(result['frequencies'], result['amplitudes'])
    print(f"[OK] Spectral metrics: coherence={metrics.coherence:.4f}, entropy={metrics.entropy:.4f}")
    
    # 5. Generate signals
    gen = SignalGenerator()
    signals = gen.generate_all_signals(
        phase=phase.phase.value,
        prev_phase='PHASE_B_VORTEX',
        spectral_width=sw,
        coherence=metrics.coherence,
        resonance_peaks=result['resonance']['num_peaks'],
        price=price_data[-1],
        prev_price=price_data[-2],
        trend_price=np.mean(price_data[-10:]),
        confidence=phase.confidence
    )
    print(f"[OK] Generated {len(signals)} trading signals")
    
    # 6. Get recommendation
    strategy = detector.get_phase_strategy(phase.phase)
    position = detector.get_recommended_position(phase.phase)
    leverage = detector.get_recommended_leverage(phase.phase)
    print(f"[OK] Recommendation: {strategy.strategy_text}")
    print(f"    Position: {position:.0%}, Leverage: up to {leverage}x")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("NEMT Phase 3 Acceptance Tests")
    print("NEMT Core: NLS, Phase Detection, Spectral Analysis, Signal Generation")
    print("=" * 60)
    
    tests = [
        ("NLS Equation Solver", test_nls_solver),
        ("Phase Detector", test_phase_detector),
        ("Spectral Analyzer", test_spectral_analyzer),
        ("Signal Generator", test_signal_generator),
        ("Integration Test", test_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"[FAIL] {name}: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for name, success, error in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {name}")
        if error:
            print(f"       Error: {error}")
        if not success:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("Phase 3 Acceptance Tests: ALL PASSED")
    else:
        print("Phase 3 Acceptance Tests: SOME FAILED")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
