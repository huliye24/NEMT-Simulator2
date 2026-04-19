#!/usr/bin/env python3
"""Test MATLAB bridge fix"""
import sys
from pathlib import Path

# 设置路径
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# 创建别名
sys.modules['quant_sync_server'] = sys.modules.get('__main__', sys.modules.get('test_bridge'))

import importlib.util

def load_submodule(package_name, module_name, file_path):
    spec = importlib.util.spec_from_file_location(f"{package_name}.{module_name}", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"{package_name}.{module_name}"] = module
    spec.loader.exec_module(module)
    return module

# 加载模块
load_submodule("quant_sync_server", "config", PROJECT_ROOT / "quant-sync-server" / "config.py")

MatlabBridge = load_submodule("quant_sync_server", "adapters.matlab_bridge", PROJECT_ROOT / "quant-sync-server" / "adapters" / "matlab_bridge.py").MatlabBridge
bridge = MatlabBridge()

# 测试引擎
info = bridge.get_engine_info()
print(f"MATLAB 可用: {info['available']}")
print(f"MATLAB 运行: {info['running']}")

if info["available"]:
    import numpy as np
    prices = [50000 + 100 * np.sin(i/10) for i in range(100)]

    print("运行 NEMT 分析...")
    result = bridge.run_analysis(prices)

    print(f"成功: {result.success}")
    if result.success:
        print(f"谱宽: {result.spectral_width}")
        print(f"平均频率: {result.mean_frequency}")
        print(f"共振峰数: {len(result.resonance_peaks)}")
        print(f"耗时: {result.execution_time:.2f}s")
    else:
        print(f"错误: {result.error}")
