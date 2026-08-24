"""
Debug Capsule Communication
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "nemt_os"))

from nemt.core import EventBus
from nemt.core.capsule import ModuleCapsule
from nemt.core.event_bus import Event


# Create capsules
class SignalCapsule(ModuleCapsule):
    def __init__(self, event_bus):
        super().__init__("signal")
        self.event_bus = event_bus
        self.count = 0

    def init(self):
        self.subscribe("market.bar", self._on_bar)

    def exec(self):
        return {"count": self.count}

    def _on_bar(self, event):
        self.count += 1
        print(f"Signal: Publishing signal #{self.count}")
        self.publish("nemt.signal", {"signal": "long", "confidence": 0.8})


class ExecutionCapsule(ModuleCapsule):
    def __init__(self, event_bus):
        super().__init__("execution")
        self.event_bus = event_bus
        self.orders = 0

    def init(self):
        self.subscribe("nemt.signal", self._on_signal)

    def exec(self):
        return {"orders": self.orders}

    def _on_signal(self, event):
        self.orders += 1
        print(f"Execution: Received order #{self.orders}, data: {event.data}")


# Test
bus = EventBus()

signal = SignalCapsule(bus)
execution = ExecutionCapsule(bus)

signal.init()
execution.init()

print("Subscribing complete. Publishing events...")
print()

# Publish bar events
for i in range(3):
    print(f"--- Publishing market.bar #{i} ---")
    bus.publish("market.bar", {"close": 50000 + i})

print()
print(f"Signal capsule count: {signal.count}")
print(f"Execution capsule orders: {execution.orders}")
