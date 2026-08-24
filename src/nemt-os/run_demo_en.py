"""
NEMT Backtest Demo - English Version

Run an actual backtest with the NEMT framework.
"""

import sys
from pathlib import Path

# Add path
sys.path.insert(0, str(Path(__file__).parent.parent / "nemt_os"))

from nemt.core import create_engine, ConfigCenter


def generate_sample_data(symbol: str, count: int = 500, trend: float = 0.0002):
    """Generate sample OHLCV data"""
    import random
    import time

    data = []
    price = 50000.0
    timestamp = int(time.time()) - count * 3600

    for i in range(count):
        change = trend + random.gauss(0, 0.015)
        close = price * (1 + change)

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


def main():
    print("=" * 60)
    print("NEMT Quant Backtest System - Demo")
    print("=" * 60)

    # 1. Create config
    print("\n[1] Creating configuration...")
    config = ConfigCenter()
    config.set("risk.max_drawdown", 0.2)
    config.set("risk.stop_loss", 0.05)
    config.set("execution.base_size", 0.15)
    config.set("signal.confidence_threshold", 0.55)

    print(f"    Max Drawdown: {config.get('risk.max_drawdown')}")
    print(f"    Stop Loss: {config.get('risk.stop_loss')}")
    print(f"    Base Position: {config.get('execution.base_size')}")

    # 2. Create engine
    print("\n[2] Creating engine...")
    engine = create_engine()

    # 3. Generate sample data
    print("\n[3] Generating sample data...")
    print("    Mode: Uptrend + Volatility")
    data = generate_sample_data("BTC", count=500, trend=0.0005)
    print(f"    Generated {len(data)} OHLCV bars")
    print(f"    Start price: ${data[0]['close']:,.2f}")
    print(f"    End price: ${data[-1]['close']:,.2f}")
    print(f"    Change: {((data[-1]['close'] - data[0]['close']) / data[0]['close']):.2%}")

    # 4. Load data and run
    print("\n[4] Running backtest...")
    print("-" * 40)

    engine.load_data("BTC", data)
    results = engine.run()

    # 5. Display results
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)

    # Dashboard
    dashboard = results.get("capsules", {}).get("dashboard", {})
    if dashboard:
        print("\n[Trading Statistics]")
        print(f"  Current Equity: ${dashboard.get('current_equity', 0):,.2f}")
        print(f"  Total Return: {dashboard.get('total_return', 0):.2%}")
        print(f"  Total Trades: {dashboard.get('trade_count', 0)}")
        print(f"  Win Rate: {dashboard.get('win_rate', 0):.2%}")
        print(f"  Max Drawdown: {dashboard.get('max_drawdown', 0):.2%}")
        print(f"  Current Drawdown: {dashboard.get('current_drawdown', 0):.2%}")

    # Signal
    signal = results.get("capsules", {}).get("signal", {})
    if signal:
        print("\n[Signal Statistics]")
        signals = signal.get("signals", {})
        for sig_type, count in signals.items():
            if count > 0:
                print(f"  {sig_type}: {count}")

    # Risk
    risk = results.get("capsules", {}).get("risk", {})
    if risk:
        print("\n[Risk Status]")
        print(f"  Risk Level: {risk.get('risk_level', 'unknown')}")
        print(f"  Defensive Mode: {'Yes' if risk.get('is_defensive') else 'No'}")
        print(f"  Risk Events: {risk.get('risk_events_count', 0)}")

    # Execution
    execution = results.get("capsules", {}).get("execution", {})
    if execution:
        stats = execution.get("statistics", {})
        print("\n[Execution Statistics]")
        print(f"  Total Orders: {stats.get('total_orders', 0)}")
        print(f"  Filled Orders: {stats.get('filled_orders', 0)}")
        print(f"  Rejected Orders: {stats.get('rejected_orders', 0)}")
        print(f"  Total Commission: ${stats.get('total_commission', 0):.4f}")

    # Market
    market = results.get("capsules", {}).get("market", {})
    if market:
        print("\n[Market Data]")
        print(f"  Processed Bars: {results.get('bars', 0)}")
        print(f"  Execution Time: {results.get('elapsed', 0):.2f}s")

    print("\n" + "=" * 60)
    print("Backtest Complete!")
    print("=" * 60)

    return results


if __name__ == "__main__":
    main()
