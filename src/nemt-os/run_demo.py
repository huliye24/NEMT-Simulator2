"""
NEMT 实际回测演示

演示如何使用 NEMT 框架运行回测。
"""

import sys
from pathlib import Path

# 添加路径 - run_demo.py 在 nemt_os/ 下，直接 parent 即可
sys.path.insert(0, str(Path(__file__).parent))

from nemt.core import create_engine, ConfigCenter


def generate_sample_data(symbol: str, count: int = 500, trend: float = 0.0002):
    """生成样本数据"""
    import random
    import time

    data = []
    price = 50000.0  # 起始价格
    timestamp = int(time.time()) - count * 3600

    for i in range(count):
        # 趋势 + 随机波动
        change = trend + random.gauss(0, 0.015)
        close = price * (1 + change)

        # OHL
        open_price = price * (1 + random.uniform(-0.005, 0.005))
        high = max(open_price, close) * (1 + random.uniform(0, 0.008))
        low = min(open_price, close) * (1 - random.uniform(0, 0.008))

        data.append(
            {
                "symbol": symbol,
                "timestamp": timestamp + i * 3600,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": random.uniform(100, 1000),
            }
        )

        price = close

    return data


def run_backtest_demo():
    """运行回测演示"""
    print("=" * 60)
    print("NEMT 量化回测系统演示")
    print("=" * 60)

    # 1. 创建配置
    print("\n[1] 创建配置...")
    config = ConfigCenter()
    config.set("risk.max_drawdown", 0.2)
    config.set("risk.stop_loss", 0.05)
    config.set("execution.base_size", 0.15)
    config.set("signal.confidence_threshold", 0.55)

    print(f"    风险回撤限制: {config.get('risk.max_drawdown')}")
    print(f"    止损比例: {config.get('risk.stop_loss')}")
    print(f"    基础仓位: {config.get('execution.base_size')}")

    # 2. 创建引擎
    print("\n[2] 创建引擎...")
    engine = create_engine()

    # 3. 生成样本数据
    print("\n[3] 生成样本数据...")
    print("    模式: 上涨趋势 + 波动")
    data = generate_sample_data("BTC", count=500, trend=0.0005)
    print(f"    生成 {len(data)} 条 K线数据")
    print(f"    起始价格: {data[0]['close']:.2f}")
    print(f"    结束价格: {data[-1]['close']:.2f}")

    # 4. 加载数据并运行
    print("\n[4] 运行回测...")
    print("-" * 40)

    engine.load_data("BTC", data)
    results = engine.run()

    # 5. 显示结果
    print("\n[5] 回测结果")
    print("=" * 60)

    # Dashboard 数据
    dashboard = results.get("capsules", {}).get("dashboard", {})
    if dashboard:
        print("\n【交易统计】")
        print(f"  当前权益: ${dashboard.get('current_equity', 0):,.2f}")
        print(f"  总收益率: {dashboard.get('total_return', 0):.2%}")
        print(f"  交易次数: {dashboard.get('trade_count', 0)}")
        print(f"  胜率: {dashboard.get('win_rate', 0):.2%}")
        print(f"  最大回撤: {dashboard.get('max_drawdown', 0):.2%}")
        print(f"  当前回撤: {dashboard.get('current_drawdown', 0):.2%}")

    # Signal 数据
    signal = results.get("capsules", {}).get("signal", {})
    if signal:
        print("\n【信号统计】")
        signals = signal.get("signals", {})
        for sig_type, count in signals.items():
            if count > 0:
                print(f"  {sig_type}: {count}")

    # Risk 数据
    risk = results.get("capsules", {}).get("risk", {})
    if risk:
        print("\n【风控状态】")
        print(f"  风险等级: {risk.get('risk_level', 'unknown')}")
        print(f"  防御模式: {'是' if risk.get('is_defensive') else '否'}")
        print(f"  风险事件: {risk.get('risk_events_count', 0)}")

    # Execution 数据
    execution = results.get("capsules", {}).get("execution", {})
    if execution:
        stats = execution.get("statistics", {})
        print("\n【执行统计】")
        print(f"  总订单数: {stats.get('total_orders', 0)}")
        print(f"  成交订单: {stats.get('filled_orders', 0)}")
        print(f"  拒绝订单: {stats.get('rejected_orders', 0)}")
        print(f"  总佣金: ${stats.get('total_commission', 0):.4f}")

    # Market 数据
    market = results.get("capsules", {}).get("market", {})
    if market:
        print("\n【市场数据】")
        print(f"  处理 K线: {results.get('bars', 0)}")
        print(f"  运行时长: {results.get('elapsed', 0):.2f}s")

    print("\n" + "=" * 60)
    print("回测完成!")
    print("=" * 60)

    return results


def run_trend_backtest():
    """运行趋势跟踪回测"""
    print("\n\n" + "=" * 60)
    print("趋势跟踪策略回测")
    print("=" * 60)

    # 生成上涨趋势数据
    print("\n生成上涨趋势数据...")
    up_data = generate_sample_data("BTC", count=300, trend=0.001)

    # 创建引擎
    engine = create_engine()
    engine.load_data("BTC", up_data)

    results = engine.run()

    dashboard = results.get("capsules", {}).get("dashboard", {})
    print(f"\n结果:")
    print(f"  权益: ${dashboard.get('current_equity', 0):,.2f}")
    print(f"  收益率: {dashboard.get('total_return', 0):.2%}")
    print(f"  交易次数: {dashboard.get('trade_count', 0)}")


def run_volatility_backtest():
    """运行高波动回测"""
    print("\n\n" + "=" * 60)
    print("高波动策略回测")
    print("=" * 60)

    # 生成高波动数据
    print("\n生成高波动数据...")
    vol_data = generate_sample_data("ETH", count=300, trend=0.0)

    # 创建引擎
    engine = create_engine()
    engine.load_data("ETH", vol_data)

    results = engine.run()

    dashboard = results.get("capsules", {}).get("dashboard", {})
    print(f"\n结果:")
    print(f"  权益: ${dashboard.get('current_equity', 0):,.2f}")
    print(f"  收益率: {dashboard.get('total_return', 0):.2%}")
    print(f"  交易次数: {dashboard.get('trade_count', 0)}")


if __name__ == "__main__":
    # 主回测
    run_backtest_demo()

    # 可选: 运行更多回测
    # run_trend_backtest()
    # run_volatility_backtest()
