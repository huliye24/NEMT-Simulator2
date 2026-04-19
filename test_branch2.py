#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NEMT模型层测试脚本 - 支线2"""

import sys
import os
import numpy as np

def run_tests():
    """运行测试"""
    print("=" * 60)
    print("NEMT Model Node (Branch 2) - Testing")
    print("=" * 60)
    
    # 测试1: 增强相位检测器
    print("\n[1] Testing Enhanced Phase Detector...")
    try:
        from enhanced_phase_detector import EnhancedPhaseDetector, Phase
        
        detector = EnhancedPhaseDetector()
        
        # 生成不同相位的测试数据
        # Phase A: chaotic
        np.random.seed(42)
        prices_a = 50000 + 1000 * np.random.randn(200)
        # Phase B: low volatility
        t_b = np.linspace(0, 10, 200)
        prices_b = 50000 + 500 * np.sin(0.3 * t_b) + 100 * np.random.randn(200)
        # Phase C: converging
        prices_c = 50000 + 200 * np.linspace(-1, 1, 200) + 50 * np.random.randn(200)
        # Phase D: trend
        np.random.seed(42)
        prices_d = 50000 + np.cumsum(100 + 50 * np.random.randn(200))
        
        test_cases = [
            ("Phase A", prices_a),
            ("Phase B", prices_b),
            ("Phase C", prices_c),
            ("Phase D", prices_d),
        ]
        
        print(f"{'Test':<12} {'Detected':>12} {'Confidence':>12}")
        print("-" * 40)
        
        for name, prices in test_cases:
            result = detector.analyze(prices)
            print(f"{name:<12} [{result.phase.value}]         {result.confidence.combined:>10.1%}")
        
        print("  [PASS] Phase detector working")
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
    
    # 测试2: NLS求解器（如果存在）
    print("\n[2] Testing NLS Solver...")
    try:
        # 尝试从不同位置导入
        try:
            from nls_solver import NLSSolver
        except ImportError:
            from quant_sync_server.nls_solver import NLSSolver
        
        solver = NLSSolver()
        
        np.random.seed(42)
        t = np.linspace(0, 10, 500)
        prices = (50000 + 2000 * np.sin(0.5 * t) + 500 * np.random.randn(500)).tolist()
        
        result = solver.solve(prices, steps=200)
        
        print(f"  Spectral Width: {result.spectral_width:.6f}")
        print(f"  Mean Frequency: {result.mean_frequency:.6f}")
        print(f"  Resonance Peaks: {len(result.resonance_peaks)}")
        print(f"  Execution Time: {result.execution_time*1000:.1f}ms")
        print("  [PASS] NLS solver working")
    except Exception as e:
        print(f"  [FAIL] {e}")
    
    # 测试3: 模型节点
    print("\n[3] Testing NEMT Model Node...")
    try:
        from nemt_model_node import NEMTModelNode, ModelInput, ModelNodeConfig
        
        # 生成测试数据
        np.random.seed(42)
        t = np.linspace(0, 10, 500)
        prices = (50000 + 2000 * np.sin(0.5 * t) + 500 * np.random.randn(500)).tolist()
        
        # 创建配置
        config = ModelNodeConfig(
            alpha=0.1,
            beta=1.0,
            noise_level=0.2,
            steps=200,
            use_cache=True
        )
        
        # 创建节点
        node = NEMTModelNode(config)
        
        # 创建输入
        input_data = ModelInput(
            prices=prices,
            symbol="BTCUSDT",
            interval="1m"
        )
        
        # 运行推理
        result = node.run(input_data)
        
        print(f"  Status: {'SUCCESS' if result.success else 'FAIL'}")
        print(f"  Time: {result.execution_time*1000:.1f}ms")
        print(f"  Phase: [{result.phase.value}] {result.phase_name}")
        print(f"  DCI: {result.dci_value:.3f}")
        print(f"  Spectral Width: {result.spectral_width:.6f}")
        
        if result.strategy_metrics:
            print(f"  Max Position: {result.strategy_metrics.get('max_position', 0):.0%}")
        
        # 测试缓存
        print("\n  Testing cache...")
        result2 = node.run(input_data)  # 应该命中缓存
        print(f"  Cache hit: {node.metrics.cache_hits > 0}")
        print(f"  Cache hit rate: {node.metrics.cache_hit_rate:.1%}")
        
        print("  [PASS] Model node working")
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
    
    # 测试4: 性能基准 - NEMT Core
    print("\n[4] Testing NEMT Core Performance...")
    try:
        from nemt_core import NEMTSimulator, NEMTParams
        
        np.random.seed(42)
        t = np.linspace(0, 10, 500)
        prices = (50000 + 2000 * np.sin(0.5 * t) + 500 * np.random.randn(500))
        
        params = NEMTParams(alpha=0.1, beta=1.0, noise_level=0.2, steps=200)
        sim = NEMTSimulator(params)
        
        # 初始化
        psi = sim.initialize_state(prices)
        
        # 演化
        import time
        start = time.time()
        psi_final = sim.evolve(psi, 200)
        elapsed = time.time() - start
        
        # 频谱分析
        freqs, spectrum = sim.spectral_analysis()
        sw = sim.compute_spectral_width()
        
        print(f"  Execution Time: {elapsed*1000:.1f}ms")
        print(f"  Spectral Width: {sw:.6f}")
        print(f"  Mean Frequency: {sim.mean_frequency:.6f}")
        print("  [PASS] NEMT Core working")
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
    
    # 测试5: 模型层综合测试
    print("\n[5] Comprehensive Model Node Test...")
    try:
        from nemt_model_node import NEMTModelNode, ModelInput, ModelNodeConfig
        
        # 生成模拟的混合数据
        np.random.seed(42)
        t = np.linspace(0, 30, 600)
        prices = (
            50000
            + 2000 * np.sin(0.5 * t)
            + 1500 * np.sin(1.3 * t + 0.3)
            + 500 * np.sin(2.7 * t + 0.7)
            + 300 * np.random.randn(600)
        ).tolist()
        
        volumes = [1000 + 500 * np.random.randn() for _ in range(600)]
        
        # 创建节点
        config = ModelNodeConfig(
            alpha=0.1,
            beta=1.0,
            noise_level=0.2,
            steps=200,
            use_cache=True,
            max_cache_size=50
        )
        
        node = NEMTModelNode(config)
        
        # 批量测试
        batch_results = []
        for i in range(5):
            start_idx = i * 100
            end_idx = start_idx + 400
            
            input_data = ModelInput(
                prices=prices[start_idx:end_idx],
                volumes=volumes[start_idx:end_idx],
                symbol="BTCUSDT",
                interval="1m"
            )
            
            result = node.run(input_data)
            batch_results.append(result)
        
        print(f"  Batch size: 5")
        print(f"  Successful: {sum(1 for r in batch_results if r.success)}")
        print(f"  Avg time: {np.mean([r.execution_time for r in batch_results])*1000:.1f}ms")
        
        # 打印所有结果
        print("\n  Results:")
        for i, r in enumerate(batch_results):
            print(f"    [{i+1}] Phase={r.phase.value}, DCI={r.dci_value:.3f}, Time={r.execution_time*1000:.1f}ms")
        
        print("  [PASS] Comprehensive test passed")
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
