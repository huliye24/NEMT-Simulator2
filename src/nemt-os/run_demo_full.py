"""
NEMT Backtest Demo - Full Pipeline Test

Test the complete backtest pipeline with simulated high-confidence signals.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "nemt_os"))

from nemt.core import create_engine, EventBus
import random
import time


def generate_trending_data(symbol: str, count: int = 200, trend: float = 0.002):
    """Generate trending OHLCV data"""
    data = []
    price = 50000.0
    timestamp = int(time.time()) - count * 3600

    for i in range(count):
        # Stronger trend + volatility
        change = trend + random.gauss(0, 0.01)
        close = price * (1 + change)

        open_price = price * (1 + random.uniform(-0.003, 0.003))
        high = max(open_price, close) * (1 + random.uniform(0, 0.005))
        low = min(open_price, close) * (1 - random.uniform(0, 0.005))

        data.append(
            {
                "symbol": symbol,
                "timestamp": timestamp + i * 3600,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": random.uniform(500, 2000),
            }
        )

        price = close

    return data


class SignalInjectorCapsule:
    """Inject strong signals for testing"""

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.inject_count = 0

    def inject_strong_signal(self, symbol: str = "BTC"):
        """Inject a strong long signal"""
        self.inject_count += 1
        self.event_bus.publish(
            "nemt.signal",
            {
                "signal": "long",
                "confidence": 0.75,
                "symbol": symbol,
                "indicators": {"dci": 50, "vortex": 0.7},
                "timestamp": time.time(),
            },
        )


def run_full_backtest():
    """Run full backtest with injected signals"""
    print("=" * 60)
    print("NEMT Quant Backtest - Full Pipeline Test")
    print("=" * 60)

    # 1. Create engine
    print("\n[1] Creating engine...")
    engine = create_engine()

    # 2. Generate trending data
    print("\n[2] Generating trending data...")
    data = generate_trending_data("BTC", count=200, trend=0.001)
    print(f"    Generated {len(data)} OHLCV bars")
    print(f"    Start price: ${data[0]['close']:,.2f}")
    print(f"    End price: ${data[-1]['close']:,.2f}")
    price_change = (data[-1]["close"] - data[0]["close"]) / data[0]["close"]
    print(f"    Price change: {price_change:+.2%}")

    # 3. Load data
    print("\n[3] Loading data into engine...")
    engine.load_data("BTC", data)

    # 4. Create signal injector
    injector = SignalInjectorCapsule(engine.event_bus)

    # 5. Modify signal handler to inject strong signals
    signal_capsule = engine.get_capsule("signal")

    # Store original handler
    original_bars = list(signal_capsule._bars)

    # 6. Inject signals every 10 bars
    print("\n[4] Injecting signals (every 10 bars)...")

    # We'll manually control the flow to inject signals
    market = engine.get_capsule("market")
    signal = engine.get_capsule("signal")
    execution = engine.get_capsule("execution")
    dashboard = engine.get_capsule("dashboard")

    # Initialize capsules
    market.init()
    signal.init()
    execution.init()
    dashboard.init()

    # Run backtest with signal injection
    print("\n[5] Running backtest...")
    print("-" * 40)

    equity_start = dashboard._current_equity

    for i, bar in enumerate(data):
        # Publish bar
        engine.event_bus.publish("market.bar", bar)

        # Inject signal every 10 bars
        if i > 10 and i % 10 == 0:
            injector.inject_strong_signal("BTC")

        # Execute capsules
        signal.exec()
        execution.exec()
        dashboard.exec()

        # Progress
        if (i + 1) % 50 == 0:
            equity = dashboard._current_equity
            trades = dashboard._trade_count
            print(f"    Bar {i+1}: Equity=${equity:,.2f}, Trades={trades}")

    # 7. Final results
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)

    equity_final = dashboard._current_equity
    equity_change = equity_final - equity_start
    equity_pct = equity_change / equity_start * 100 if equity_start > 0 else 0

    print(f"\n[Equity]")
    print(f"  Starting: ${equity_start:,.2f}")
    print(f"  Final:   ${equity_final:,.2f}")
    print(f"  Change:  ${equity_change:+,.2f} ({equity_pct:+.2f}%)")

    print(f"\n[Trading]")
    print(f"  Total Trades: {dashboard._trade_count}")
    print(f"  Winning: {dashboard._winning_trades}")
    print(f"  Losing: {dashboard._losing_trades}")
    win_rate = dashboard._winning_trades / (dashboard._trade_count) if dashboard._trade_count > 0 else 0
    print(f"  Win Rate: {win_rate:.2%}")

    print(f"\n[Execution]")
    print(f"  Orders Filled: {execution._filled_orders}")
    print(f"  Total Commission: ${execution._total_commission:.4f}")

    print(f"\n[Signals]")
    print(f"  Signals Injected: {injector.inject_count}")
    print(f"  Signal Capsule Count: {signal._signal_count}")

    print("\n" + "=" * 60)
    print("Backtest Complete!")
    print("=" * 60)

    return {
        "equity_start": equity_start,
        "equity_final": equity_final,
        "trades": dashboard._trade_count,
        "win_rate": win_rate,
        "commission": execution._total_commission,
    }


def run_simple_signal_test():
    """Simple test with direct signal injection"""
    print("\n\n" + "=" * 60)
    print("SIMPLE SIGNAL TEST")
    print("=" * 60)

    bus = EventBus()
    results = []

    def signal_handler(event):
        results.append(("signal", event.data))
        print(f"Signal received: {event.data}")

    def order_handler(event):
        results.append(("order", event.data))
        print(f"Order received: {event.data}")

    def dashboard_handler(event):
        results.append(("dashboard", event.data))
        print(f"Dashboard event: {event.data}")

    bus.subscribe("nemt.signal", signal_handler)
    bus.subscribe("nemt.order_filled", order_handler)
    bus.subscribe("nemt.equity", dashboard_handler)

    # Inject signal
    print("\nInjecting strong long signal...")
    bus.publish("nemt.signal", {"signal": "long", "confidence": 0.8, "symbol": "BTC"})

    print(f"\nTotal events: {len(results)}")
    for event_type, data in results:
        print(f"  {event_type}: {data}")


if __name__ == "__main__":
    # Run simple test first
    run_simple_signal_test()

    # Run full backtest
    results = run_full_backtest()
