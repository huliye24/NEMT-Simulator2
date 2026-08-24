"""
Deep Debug Dashboard
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "nemt_os"))

from nemt.core import create_engine, EventBus
import random
import time

# Create test data
data = []
price = 50000
ts = int(time.time()) - 100 * 3600
for i in range(50):
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

print(f"Generated {len(data)} bars")

# Create engine
engine = create_engine()
engine.load_data("BTC", data)

# Get capsules
market = engine.get_capsule("market")
signal = engine.get_capsule("signal")
execution = engine.get_capsule("execution")
dashboard = engine.get_capsule("dashboard")

print(f'Config confidence threshold: {engine.config.get("signal.confidence_threshold")}')

# Initialize all capsules
market.init()
signal.init()
execution.init()
dashboard.init()

# Track events
print("\n--- Running 10 bars ---")
for i in range(10):
    bar = data[i]

    # Publish bar event
    engine.event_bus.publish("market.bar", bar)

    # Check execution
    e_result = execution.exec()
    filled = e_result.get("statistics", {}).get("filled_orders", 0)

    # Check dashboard
    d_result = dashboard.exec()
    equity = d_result.get("current_equity", 0)
    trades = d_result.get("trade_count", 0)

    print(f"Bar {i}: Filled={filled}, Dashboard Trades={trades}, Equity=${equity:.2f}")

print(f"\n--- Final State ---")
print(f"Execution filled_orders: {execution._filled_orders}")
print(f"Execution _total_commission: {execution._total_commission:.4f}")
print(f"Dashboard _current_equity: {dashboard._current_equity:.2f}")
print(f"Dashboard _trade_count: {dashboard._trade_count}")

# Check if Dashboard is receiving events
print(f"\n--- Event History ---")
history = engine.event_bus.get_history(limit=20)
for e in history:
    print(f"{e.type}: {e.data}")
