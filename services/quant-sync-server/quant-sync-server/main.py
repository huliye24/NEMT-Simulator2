#!/usr/bin/env python3
"""
Quant-Sync-Server - CLI 入口
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path

# 由于目录名包含连字符，需要将目录添加到路径后重命名
PROJECT_ROOT = Path(__file__).parent.resolve()
SERVER_DIR = PROJECT_ROOT

# 将 quant-sync-server 目录添加到路径
sys.path.insert(0, str(SERVER_DIR))

# 创建别名以支持 quant_sync_server 模块名
sys.modules['quant_sync_server'] = sys.modules['__main__']

import importlib.util

def load_submodule(package_name, module_name, file_path):
    spec = importlib.util.spec_from_file_location(f"{package_name}.{module_name}", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"{package_name}.{module_name}"] = module
    spec.loader.exec_module(module)
    return module

# 加载核心模块
config_module = load_submodule("quant_sync_server", "config", SERVER_DIR / "config.py")
config = config_module.config

# 加载适配器
notion_module = load_submodule("quant_sync_server", "adapters.notion_adapter", SERVER_DIR / "adapters" / "notion_adapter.py")
MatlabBridge = load_submodule("quant_sync_server", "adapters.matlab_bridge", SERVER_DIR / "adapters" / "matlab_bridge.py").MatlabBridge

# 加载转换器
DataTransformer = load_submodule("quant_sync_server", "transformers.data_transformer", SERVER_DIR / "transformers" / "data_transformer.py").DataTransformer

# 加载路由器
SignalRouter = load_submodule("quant_sync_server", "routers.signal_router", SERVER_DIR / "routers" / "signal_router.py").SignalRouter
SignalGenerator = load_submodule("quant_sync_server", "routers.signal_router", SERVER_DIR / "routers" / "signal_router.py").SignalGenerator

logger = logging.getLogger(__name__)


def cmd_status():
    """显示服务器状态"""
    print("=" * 60)
    print("Quant-Sync-Server 状态")
    print("=" * 60)

    # MATLAB
    bridge = MatlabBridge()
    matlab_info = bridge.get_engine_info()
    print(f"\nMATLAB 引擎:")
    print(f"  可用: {'yes' if matlab_info['available'] else 'NO'}")
    print(f"  运行: {'yes' if matlab_info['running'] else 'NO'}")
    print(f"  脚本路径: {matlab_info['scripts_path']}")

    # Notion
    from quant_sync_server.adapters.notion_adapter import NotionAdapter
    notion = NotionAdapter()
    notion_health = notion.health_check()
    print(f"\nNotion:")
    print(f"  已配置: {'yes' if notion_health['configured'] else 'NO'}")

    # Redis
    print(f"\nRedis:")
    print(f"  主机: {config.redis.host}:{config.redis.port}")

    print("\n" + "=" * 60)


def cmd_demo():
    """运行演示"""
    import numpy as np

    print("=" * 60)
    print("Quant-Sync-Server Demo")
    print("=" * 60)

    # 生成模拟数据
    t = np.linspace(0, 20 * np.pi, 500)
    prices = 50000 + 1000 * np.sin(t) + 200 * np.random.randn(500)

    print(f"\n[1] 生成模拟数据: {len(prices)} 个点")
    print(f"    价格范围: [{prices.min():.2f}, {prices.max():.2f}]")

    # 数据验证
    print("\n[2] 数据验证...")
    transformer = DataTransformer()
    transformer.load_prices(prices)
    valid, errors = transformer.validate()
    print(f"    验证: {'PASS' if valid else 'FAIL'}")

    # 语义压缩
    print("\n[3] 语义压缩...")
    summary = transformer.compress_to_summary()
    print(f"    数据点数: {summary.data_points}")
    print(f"    总收益率: {summary.total_return:.2%}")
    print(f"    波动率: {summary.volatility:.2%}")

    # MATLAB 分析
    print("\n[4] NEMT 分析...")
    bridge = MatlabBridge()
    if bridge.get_engine_info()['available']:
        result = bridge.run_analysis(prices.tolist())
        if result.success:
            print(f"    谱宽: {result.spectral_width:.6f}")
            print(f"    共振峰: {len(result.resonance_peaks)}")
        else:
            print(f"    FAIL: {result.error}")
    else:
        print("    SKIP: MATLAB 引擎不可用")

    print("\n" + "=" * 60)
    print("Demo 完成!")
    print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Quant-Sync-Server CLI")
    parser.add_argument('--action', '-a', choices=['status', 'demo'], default='status')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    if args.action == 'status':
        cmd_status()
    elif args.action == 'demo':
        cmd_demo()

    return 0


if __name__ == '__main__':
    sys.exit(main())
