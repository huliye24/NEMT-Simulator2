"""
Debug Dashboard
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "nemt_os"))

from nemt.core import create_engine
import random
import time

# Generate test data
data = []
price = 50000
ts = int(time.time()) - 100 * 3600
for i in range(100):
    price *= 1 + random.uniform(-0.02, 0.03)
    data.append(
        {
            "symbol": "BTC",
            "timestamp": ts + i * 3600,
            "open": price * 0.99,
            "high": price * 1.01,
            "low": price * 0.98,
            "close": price,
            "volume": 1000,
        }
    )

print(f'Generated {len(data)} bars, price: {data[0]["close"]:.2f} -> {data[-1]["close"]:.2f}')

# Create engine
engine = create_engine()
engine.load_data("BTC", data)

# Get capsules
market = engine.get_capsule("market")
signal = engine.get_capsule("signal")
execution = engine.get_capsule("execution")
dashboard = engine.get_capsule("dashboard")

# Initialize
market.init()
signal.init()
execution.init()
dashboard.init()

# Manual test - run a few bars
for i in range(5):
    bar = data[i]
    print(f"\n--- Bar {i} ---")

    # Publish bar event
    engine.event_bus.publish("market.bar", bar)

    # Execute capsules
    s_result = signal.exec()
    print(f'Signal count: {s_result.get("signal_count", 0)}')

    e_result = execution.exec()
    print(f'Orders filled: {e_result.get("statistics", {}).get("filled_orders", 0)}')

    d_result = dashboard.exec()
    print(f'Equity: {d_result.get("current_equity", 0):.2f}')
    print(f'Trades: {d_result.get("trade_count", 0)}')

print(f"\nFinal equity: {dashboard._current_equity}")
