"""
Debug Event Flow
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "nemt_os"))

from nemt.core import EventBus

# Create event bus
bus = EventBus()

# Track events
events = []


def tracker(event_type):
    def handler(event):
        events.append(event.type)
        print(f"Event: {event.type} -> data: {event.data}")

    return handler


# Subscribe
bus.subscribe("nemt.signal", tracker("signal"))
bus.subscribe("nemt.order_filled", tracker("order_filled"))
bus.subscribe("market.bar", tracker("bar"))

# Publish signal
print("Publishing signal...")
bus.publish("nemt.signal", {"signal": "long", "confidence": 0.8, "symbol": "BTC"})

print(f"\nTotal events: {len(events)}")
print(f"Events: {events}")
