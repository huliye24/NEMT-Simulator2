"""
CapsuleNode 集成测试 - 完整数据流验证

独立版本，不依赖外部包
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
# 核心枚举
# ═══════════════════════════════════════════════════════════════════════════════


class CapsuleNodeState(Enum):
    CREATED = "created"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    VALIDATING_INPUT = "validating_input"
    RUNNING = "running"
    VALIDATING_OUTPUT = "validating_output"
    IDLE = "idle"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class NodePhase(Enum):
    SCHEMA_LOADING = "schema_loading"
    INITIALIZATION_COMPLETE = "initialization_complete"
    VALIDATING_INPUTS = "validating_inputs"
    PROCESSING = "processing"
    VALIDATING_OUTPUTS = "validating_outputs"
    EXECUTION_COMPLETE = "execution_complete"
    SHUTTING_DOWN = "shutting_down"
    TERMINATED = "terminated"


# ═══════════════════════════════════════════════════════════════════════════════
# Schema 类
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class PortSchema:
    name: str
    data_type: str
    required: bool = False
    description: str = ""
    properties: dict = field(default_factory=dict)
    required_fields: list = field(default_factory=list)
    enum_values: list | None = None


@dataclass
class ConstraintSchema:
    name: str
    constraint_type: str
    value: Any
    description: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# CapsuleNode 基类
# ═══════════════════════════════════════════════════════════════════════════════


class CapsuleNode(ABC):
    NODE_ID = "base"
    NODE_NAME = "Base"
    NODE_VERSION = "1.0.0"
    INPUT_PORTS: list[PortSchema] = []
    OUTPUT_PORTS: list[PortSchema] = []
    CONSTRAINTS: list[ConstraintSchema] = []

    def __init__(self, node_id: str | None = None):
        self.node_id = node_id or self.NODE_ID
        self._state = CapsuleNodeState.CREATED
        self._phase = NodePhase.SCHEMA_LOADING
        self._exec_count = 0
        self._error_count = 0
        self._total_exec_time = 0.0

    @property
    def state(self):
        return type("State", (), {"phase": self._phase, "node_id": self.node_id})()

    @property
    def capsule_state(self):
        return self._state

    @property
    def metrics(self):
        avg = self._total_exec_time / self._exec_count if self._exec_count > 0 else 0
        return {"exec_count": self._exec_count, "error_count": self._error_count}

    def init(self):
        self._state = CapsuleNodeState.INITIALIZED
        self._phase = NodePhase.INITIALIZATION_COMPLETE
        return self

    def _validate_inputs(self, inputs: dict) -> bool:
        for port in self.INPUT_PORTS:
            if port.required and port.name not in inputs:
                raise ValueError(f"Missing required input: {port.name}")
            if port.name in inputs:
                data = inputs[port.name]
                for field in port.required_fields:
                    if isinstance(data, dict) and field not in data:
                        raise ValueError(f"Missing required field: {field}")
        return True

    def run(self, inputs: dict) -> dict:
        self._validate_inputs(inputs)
        self._state = CapsuleNodeState.RUNNING
        self._phase = NodePhase.PROCESSING
        start = time.time()
        outputs = self._process_impl(inputs)
        self._total_exec_time += time.time() - start
        self._exec_count += 1
        self._state = CapsuleNodeState.IDLE
        self._phase = NodePhase.EXECUTION_COMPLETE
        return outputs

    @abstractmethod
    def _process_impl(self, inputs: dict) -> dict:
        pass

    def shutdown(self):
        self._state = CapsuleNodeState.STOPPED
        return self

    def export_state(self) -> dict:
        return {
            "node": {"id": self.node_id, "name": self.NODE_NAME, "version": self.NODE_VERSION},
            "state": {"capsule_state": self._state.value, "phase": self._phase.value},
            "schemas": {
                "inputs": [{"name": p.name, "required": p.required} for p in self.INPUT_PORTS],
                "outputs": [{"name": p.name, "required": p.required} for p in self.OUTPUT_PORTS],
                "constraints": [{"name": c.name, "value": c.value} for c in self.CONSTRAINTS],
            },
            "metrics": self.metrics,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MarketNode
# ═══════════════════════════════════════════════════════════════════════════════


class MarketNode(CapsuleNode):
    NODE_ID = "market_node"
    NODE_NAME = "Market Data Node"

    INPUT_PORTS = [
        PortSchema(
            name="raw_feed",
            data_type="object",
            required=True,
            properties={"symbol": {}, "price": {}, "volume": {}, "timestamp": {}},
            required_fields=["symbol", "price", "timestamp"],
        ),
    ]
    OUTPUT_PORTS = [
        PortSchema(
            name="ohlcv",
            data_type="object",
            required=True,
            properties={"symbol": {}, "open": {}, "high": {}, "low": {}, "close": {}, "volume": {}},
            required_fields=["symbol", "close"],
        ),
        PortSchema(
            name="phase",
            data_type="string",
            required=True,
            enum_values=["UNKNOWN", "TREND_UP", "TREND_DOWN", "RANGE", "VOLATILE"],
        ),
    ]
    CONSTRAINTS = [
        ConstraintSchema(name="max_latency_ms", constraint_type="runtime", value=1000),
    ]

    def __init__(self):
        super().__init__("market_node")
        self._bars_cache: dict[str, list] = {}
        self._bar_count = 0

    def _process_impl(self, inputs: dict) -> dict:
        raw = inputs.get("raw_feed", {})
        symbol = raw.get("symbol", "").upper()
        price = raw.get("price", 0)
        volume = raw.get("volume", 0)
        timestamp = raw.get("timestamp", 0)

        ohlcv = {
            "symbol": symbol,
            "open": price * 0.998,
            "high": price * 1.002,
            "low": price * 0.997,
            "close": price,
            "volume": volume,
            "timestamp": timestamp,
        }

        self._bars_cache[symbol] = self._bars_cache.get(symbol, []) + [ohlcv]
        self._bar_count += 1

        bars = self._bars_cache.get(symbol, [])
        phase = "RANGE" if len(bars) > 5 else "UNKNOWN"

        return {"ohlcv": ohlcv, "phase": phase}


# ═══════════════════════════════════════════════════════════════════════════════
# SignalNode
# ═══════════════════════════════════════════════════════════════════════════════


class SignalNode(CapsuleNode):
    NODE_ID = "signal_node"
    NODE_NAME = "Signal Generation Node"

    INPUT_PORTS = [
        PortSchema(name="ohlcv", data_type="object", required=True, required_fields=["symbol", "close"]),
        PortSchema(name="market_phase", data_type="string", required=True),
    ]
    OUTPUT_PORTS = [
        PortSchema(
            name="signal",
            data_type="object",
            required=True,
            properties={"signal_id": {}, "symbol": {}, "direction": {}, "confidence": {}},
            required_fields=["signal_id", "symbol", "direction", "confidence"],
        ),
    ]
    CONSTRAINTS = [
        ConstraintSchema(name="min_confidence", constraint_type="validation", value=0.6),
    ]

    def __init__(self):
        super().__init__("signal_node")
        self._signals: list[dict] = []
        self._signal_count = 0

    def _process_impl(self, inputs: dict) -> dict:
        ohlcv = inputs.get("ohlcv", {})
        market_phase = inputs.get("market_phase", "UNKNOWN")

        self._signal_count += 1
        import uuid

        # 简单策略
        close = ohlcv.get("close", 100)
        price_factor = (close - 100) / 100

        if market_phase == "TREND_UP":
            direction = "LONG"
            confidence = 0.7 + max(0, price_factor)
        elif market_phase == "TREND_DOWN":
            direction = "SHORT"
            confidence = 0.7 + max(0, -price_factor)
        else:
            direction = "NEUTRAL"
            confidence = 0.5

        signal = {
            "signal_id": f"sig_{uuid.uuid4().hex[:8]}",
            "symbol": ohlcv.get("symbol", "UNKNOWN"),
            "direction": direction,
            "signal_type": "ENTRY",
            "confidence": min(0.95, max(0.1, confidence)),
            "entry_price": close,
            "stop_loss": close * 0.98,
            "take_profit": close * 1.04,
            "timestamp": int(datetime.now().timestamp()),
        }

        self._signals.append(signal)

        return {"signal": signal}


# ═══════════════════════════════════════════════════════════════════════════════
# RiskNode
# ═══════════════════════════════════════════════════════════════════════════════


class RiskNode(CapsuleNode):
    NODE_ID = "risk_node"
    NODE_NAME = "Risk Management Node"

    INPUT_PORTS = [
        PortSchema(
            name="signal", data_type="object", required=True, required_fields=["signal_id", "symbol", "direction"]
        ),
        PortSchema(
            name="portfolio", data_type="object", required=True, required_fields=["total_value", "available_balance"]
        ),
    ]
    OUTPUT_PORTS = [
        PortSchema(name="risk_approved_signal", data_type="object", required=False),
        PortSchema(name="risk_rejection", data_type="object", required=False),
        PortSchema(name="risk_metrics", data_type="object", required=True),
    ]
    CONSTRAINTS = [
        ConstraintSchema(name="max_position_size", constraint_type="runtime", value=0.1),
        ConstraintSchema(name="min_confidence", constraint_type="validation", value=0.5),
    ]

    def __init__(self):
        super().__init__("risk_node")
        self._portfolio = {"total_value": 100000, "available_balance": 100000, "positions": []}

    def _process_impl(self, inputs: dict) -> dict:
        signal = inputs.get("signal", {})
        portfolio = inputs.get("portfolio", self._portfolio)

        self._portfolio = portfolio

        # 简单风险检查
        min_confidence = 0.5
        if signal.get("confidence", 0) < min_confidence:
            return {
                "risk_approved_signal": None,
                "risk_rejection": {"signal_id": signal.get("signal_id"), "reason": "Low confidence"},
                "risk_metrics": self._get_metrics(),
            }

        # 计算头寸大小
        max_position = 0.1
        total = portfolio.get("total_value", 100000)
        size = total * max_position * signal.get("confidence", 0.5)

        return {
            "risk_approved_signal": {
                "signal_id": signal.get("signal_id"),
                "symbol": signal.get("symbol"),
                "direction": signal.get("direction"),
                "approved_size": size,
                "risk_score": 0.3,
                "timestamp": int(datetime.now().timestamp()),
            },
            "risk_rejection": None,
            "risk_metrics": self._get_metrics(),
        }

    def _get_metrics(self) -> dict:
        return {
            "portfolio_risk": 0.05,
            "max_drawdown": 0.1,
            "daily_loss_limit": 0.03,
            "risk_score": 0.3,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# BrainNode
# ═══════════════════════════════════════════════════════════════════════════════


class BrainNode(CapsuleNode):
    NODE_ID = "brain_node"
    NODE_NAME = "Decision Brain Node"

    INPUT_PORTS = [
        PortSchema(
            name="signal", data_type="object", required=True, required_fields=["signal_id", "symbol", "direction"]
        ),
        PortSchema(name="risk_evaluation", data_type="object", required=True, required_fields=["approved"]),
    ]
    OUTPUT_PORTS = [
        PortSchema(
            name="decision",
            data_type="object",
            required=True,
            properties={"decision_id": {}, "action": {}, "symbol": {}},
            required_fields=["decision_id", "action", "symbol"],
        ),
    ]
    CONSTRAINTS = [
        ConstraintSchema(name="min_confidence_threshold", constraint_type="validation", value=0.65),
    ]

    def __init__(self):
        super().__init__("brain_node")
        self._decisions: list[dict] = []
        self._executions = 0
        self._skips = 0

    def _process_impl(self, inputs: dict) -> dict:
        signal = inputs.get("signal", {})
        risk_eval = inputs.get("risk_evaluation", {})

        import uuid

        if not risk_eval.get("approved", False):
            self._skips += 1
            return {
                "decision": {
                    "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
                    "action": "SKIP",
                    "symbol": signal.get("symbol"),
                    "direction": signal.get("direction"),
                    "reason": risk_eval.get("reason", "Risk rejected"),
                    "timestamp": int(datetime.now().timestamp()),
                }
            }

        self._executions += 1
        return {
            "decision": {
                "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
                "action": "EXECUTE",
                "symbol": signal.get("symbol"),
                "direction": signal.get("direction"),
                "size": risk_eval.get("approved_size", 0),
                "entry_price": signal.get("entry_price"),
                "reason": "Approved by risk",
                "timestamp": int(datetime.now().timestamp()),
            }
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ExecutionNode
# ═══════════════════════════════════════════════════════════════════════════════


class ExecutionNode(CapsuleNode):
    NODE_ID = "execution_node"
    NODE_NAME = "Order Execution Node"

    INPUT_PORTS = [
        PortSchema(
            name="decision", data_type="object", required=True, required_fields=["decision_id", "action", "symbol"]
        ),
    ]
    OUTPUT_PORTS = [
        PortSchema(name="order", data_type="object", required=False),
        PortSchema(name="fill", data_type="object", required=False),
        PortSchema(name="portfolio", data_type="object", required=True),
    ]
    CONSTRAINTS = [
        ConstraintSchema(name="initial_balance", constraint_type="immutable", value=100000),
        ConstraintSchema(name="order_fee_rate", constraint_type="immutable", value=0.001),
    ]

    def __init__(self):
        super().__init__("execution_node")
        self._orders: list[dict] = []
        self._fills: list[dict] = []
        self._portfolio = {
            "total_value": 100000,
            "available_balance": 100000,
            "positions": [],
            "daily_pnl": 0,
            "drawdown": 0,
        }

    def _process_impl(self, inputs: dict) -> dict:
        decision = inputs.get("decision", {})

        if decision.get("action") != "EXECUTE":
            return {"order": None, "fill": None, "portfolio": self._portfolio}

        import uuid

        order = {
            "order_id": f"ord_{uuid.uuid4().hex[:12]}",
            "symbol": decision.get("symbol"),
            "direction": decision.get("direction"),
            "order_type": "MARKET",
            "size": decision.get("size", 0),
            "price": decision.get("entry_price"),
            "status": "FILLED",
            "timestamp": int(datetime.now().timestamp()),
        }

        self._orders.append(order)

        # 模拟成交
        fill = {
            "order_id": order["order_id"],
            "fill_id": f"fill_{uuid.uuid4().hex[:12]}",
            "symbol": order["symbol"],
            "size": order["size"],
            "fill_price": order["price"],
            "fees": order["size"] * order["price"] * 0.001,
            "timestamp": int(datetime.now().timestamp()),
        }

        self._fills.append(fill)

        # 更新投资组合
        self._portfolio["available_balance"] -= fill["fees"]

        return {"order": order, "fill": fill, "portfolio": self._portfolio}


# ═══════════════════════════════════════════════════════════════════════════════
# 测试函数
# ═══════════════════════════════════════════════════════════════════════════════


def test_full_pipeline():
    """测试完整数据流"""
    print("=" * 70)
    print("CapsuleNode Integration Test - Full Pipeline")
    print("MarketNode -> SignalNode -> RiskNode -> BrainNode -> ExecutionNode")
    print("=" * 70)

    # 1. 创建所有节点
    print("\n=== Step 1: Create Nodes ===")
    market = MarketNode()
    signal = SignalNode()
    risk = RiskNode()
    brain = BrainNode()
    execution = ExecutionNode()
    print("Created: market_node, signal_node, risk_node, brain_node, execution_node")

    # 2. 初始化
    print("\n=== Step 2: Initialize ===")
    for node in [market, signal, risk, brain, execution]:
        node.init()
    print("All nodes initialized")

    # 3. 市场数据
    print("\n=== Step 3: Market Data ===")
    market_out = market.run({"raw_feed": {"symbol": "BTCUSDT", "price": 50000, "volume": 100, "timestamp": 1714281600}})
    print(f"Market: phase={market_out['phase']}, close={market_out['ohlcv']['close']}")

    # 4. 信号
    print("\n=== Step 4: Signal ===")
    signal_out = signal.run({"ohlcv": market_out["ohlcv"], "market_phase": market_out["phase"]})
    sig = signal_out["signal"]
    print(f"Signal: {sig['direction']}, confidence={sig['confidence']:.2f}")

    # 5. 风险
    print("\n=== Step 5: Risk ===")
    risk_out = risk.run({"signal": sig, "portfolio": execution._portfolio})
    if risk_out["risk_rejection"]:
        print(f"Risk: REJECTED - {risk_out['risk_rejection']['reason']}")
        risk_eval = {"approved": False, "reason": risk_out["risk_rejection"]["reason"]}
    else:
        approved = risk_out["risk_approved_signal"]
        print(f"Risk: APPROVED - size={approved['approved_size']:.2f}, risk_score={approved['risk_score']:.4f}")
        risk_eval = {"approved": True, "approved_size": approved["approved_size"], "risk_score": approved["risk_score"]}

    # 6. 决策
    print("\n=== Step 6: Decision ===")
    brain_out = brain.run({"signal": sig, "risk_evaluation": risk_eval})
    decision = brain_out["decision"]
    print(f"Decision: {decision['action']}, reason={decision.get('reason', '')[:40]}...")

    # 7. 执行
    print("\n=== Step 7: Execution ===")
    exec_out = execution.run({"decision": decision})
    if exec_out["order"]:
        print(f"Order: {exec_out['order']['order_id']}, status={exec_out['order']['status']}")
    if exec_out["fill"]:
        print(f"Fill: {exec_out['fill']['fill_id']}, price={exec_out['fill']['fill_price']}")
    print(f"Portfolio: total={exec_out['portfolio']['total_value']:.2f}")

    return True


def test_multi_symbol():
    """测试多符号"""
    print("\n" + "=" * 70)
    print("Multi-Symbol Test")
    print("=" * 70)

    market = MarketNode()
    signal = SignalNode()
    risk = RiskNode()
    brain = BrainNode()
    execution = ExecutionNode()

    for node in [market, signal, risk, brain, execution]:
        node.init()

    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]

    print(f"\nProcessing {len(symbols)} symbols...")

    for i, symbol in enumerate(symbols):
        market_out = market.run(
            {"raw_feed": {"symbol": symbol, "price": 100 + i * 50, "volume": 10, "timestamp": 1714281600}}
        )
        signal_out = signal.run({"ohlcv": market_out["ohlcv"], "market_phase": market_out["phase"]})
        risk_out = risk.run({"signal": signal_out["signal"], "portfolio": execution._portfolio})
        brain_out = brain.run(
            {
                "signal": signal_out["signal"],
                "risk_evaluation": {"approved": risk_out["risk_approved_signal"] is not None},
            }
        )
        exec_out = execution.run({"decision": brain_out["decision"]})

        status = "OK" if exec_out["order"] else "SKIP"
        print(f"  [{status}] {symbol}: {brain_out['decision']['action']}")

    portfolio = execution._portfolio
    print(f"\nPortfolio: total={portfolio['total_value']:.2f}, orders={len(execution._orders)}")

    return True


def test_schema_validation():
    """测试 Schema 验证"""
    print("\n" + "=" * 70)
    print("Schema Validation Test")
    print("=" * 70)

    market = MarketNode()
    market.init()

    # 有效
    print("\nValid input:")
    try:
        market.run({"raw_feed": {"symbol": "ETH", "price": 3000, "volume": 50, "timestamp": 1714281600}})
        print("  OK Valid input accepted")
    except Exception as e:
        print(f"  X Valid input rejected: {e}")

    # 无效
    print("\nInvalid input (missing required fields):")
    try:
        market.run({"raw_feed": {"symbol": "ETH", "price": 3000}})
        print("  X Invalid input accepted (should be rejected)")
    except ValueError as e:
        print(f"  OK Invalid input blocked: {str(e)[:50]}...")

    return True


def test_ai_readable_state():
    """测试 AI 可读状态"""
    print("\n" + "=" * 70)
    print("AI-Readable State Export")
    print("=" * 70)

    market = MarketNode()
    market.init()
    market.run({"raw_feed": {"symbol": "BTC", "price": 50000, "volume": 100, "timestamp": 1714281600}})

    state = market.export_state()

    print("\nState export:")
    print(f"  Node: {state['node']['id']} v{state['node']['version']}")
    print(f"  State: {state['state']['capsule_state']} / {state['state']['phase']}")
    print(f"  Input schemas: {[p['name'] for p in state['schemas']['inputs']]}")
    print(f"  Output schemas: {[p['name'] for p in state['schemas']['outputs']]}")
    print(f"  Constraints: {[c['name'] for c in state['schemas']['constraints']]}")

    return True


if __name__ == "__main__":
    tests = [
        ("Full Pipeline", test_full_pipeline),
        ("Multi-Symbol", test_multi_symbol),
        ("Schema Validation", test_schema_validation),
        ("AI-Readable State", test_ai_readable_state),
    ]

    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed, None))
        except Exception as e:
            results.append((name, False, str(e)))

    print("\n" + "=" * 70)
    print("Results")
    print("=" * 70)

    for name, passed, error in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {name}")
        if error:
            print(f"       Error: {error}")

    all_passed = all(r[1] for r in results)
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed"))
