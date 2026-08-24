"""
NEMT 快速开始示例

演示如何使用 NEMT Engine 进行回测。
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from nemt.core.nemt_engine import NEMTEngine
from tests.data_generator import BarGenerator


def simple_backtest():
    """简单回测示例"""
    print("\n" + "=" * 60)
    print("NEMT 快速开始 - 简单回测")
    print("=" * 60 + "\n")

    # 创建引擎
    engine = NEMTEngine()
    engine.setup()

    # 生成测试数据
    gen = BarGenerator(symbol='BTC', base_price=50000, volatility=0.02, seed=42)
    bars = gen.generate_trending(100, trend=0.001)

    print(f"生成测试数据: {len(bars)} 条 K线")

    # 加载数据
    engine.load_data('BTC', bars)

    # 运行回测
    print("\n开始回测...")
    results = engine.run()

    # 输出结果
    print("\n" + "=" * 60)
    print("回测结果")
    print("=" * 60)

    print(f"\n处理 K线: {results['bars']}")
    print(f"运行时长: {results['elapsed']:.2f}s")

    # 输出各胶囊状态
    print("\n胶囊状态:")
    for capsule_id, state in results['capsules'].items():
        if isinstance(state, dict):
            print(f"  {capsule_id}: OK")

    # 生成报告
    report = engine.generate_report(results)
    print("\n" + report)


def advanced_backtest():
    """高级回测示例"""
    print("\n" + "=" * 60)
    print("NEMT 高级示例 - 多策略")
    print("=" * 60 + "\n")

    from nemt.core.brain_capsule import StrategyType

    # 创建引擎
    engine = NEMTEngine()
    engine.setup()

    # 生成不同类型的数据
    gen = BarGenerator(symbol='BTC', base_price=50000, volatility=0.02, seed=42)

    # 趋势数据
    trend_bars = gen.generate_trending(50, trend=0.002)

    # 震荡数据
    range_bars = gen.generate_ranging(50, range_pct=0.02)

    # 合并数据
    all_bars = trend_bars + range_bars

    print(f"生成测试数据: {len(all_bars)} 条 K线")

    # 加载数据
    engine.load_data('BTC', all_bars)

    # 运行回测
    print("\n开始回测...")
    results = engine.run()

    # 输出报告
    report = engine.generate_report(results)
    print("\n" + report)


def market_provider_demo():
    """市场数据提供者示例"""
    print("\n" + "=" * 60)
    print("NEMT 市场数据示例")
    print("=" * 60 + "\n")

    from nemt.core.market_capsule import MarketCapsule
    from nemt.market_providers import MockMarketProvider

    # 创建市场胶囊
    market = MarketCapsule()

    # 使用 Mock 提供者
    provider = MockMarketProvider()
    provider.connect()

    # 设置提供者
    market.set_provider(provider)

    print("连接市场数据提供者: MockProvider")
    print(f"提供者类型: {provider.name}")

    # 获取数据
    klines = provider.get_history('BTCUSDT', '1h', limit=10)
    print(f"\n获取 K线: {len(klines)} 条")

    for kline in klines[:3]:
        print(f"  {kline.symbol}: {kline.close}")

    # 断开连接
    provider.disconnect()
    print("\n提供者已断开")


def main():
    """主函数"""
    print("""
NEMT Quant OS - 快速开始

选择一个示例运行:

1. 简单回测     - 最基础的回测示例
2. 高级回测     - 多策略示例
3. 市场数据     - 市场数据提供者示例

或者运行测试:

    pytest tests/ -v
    """)

    choice = input("选择 (1/2/3): ").strip()

    if choice == '1':
        simple_backtest()
    elif choice == '2':
        advanced_backtest()
    elif choice == '3':
        market_provider_demo()
    else:
        print("无效选择")


if __name__ == '__main__':
    main()
