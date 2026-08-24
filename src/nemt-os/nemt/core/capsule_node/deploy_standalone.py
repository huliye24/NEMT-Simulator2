"""
CapsuleNode 独立部署脚本

不依赖外部包的独立版本
"""

import argparse
import json
import logging
import threading
from abc import ABC, abstractmethod

# ═══════════════════════════════════════════════════════════════════════════════
# 简化版 CapsuleNode (内联)
# ═══════════════════════════════════════════════════════════════════════════════


class CapsuleNodeState:
    CREATED = "created"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    RUNNING = "running"
    IDLE = "idle"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class NodePhase:
    SCHEMA_LOADING = "schema_loading"
    INITIALIZATION_COMPLETE = "initialization_complete"
    PROCESSING = "processing"
    EXECUTION_COMPLETE = "execution_complete"
    SHUTTING_DOWN = "shutting_down"
    TERMINATED = "terminated"


class CapsuleNode(ABC):
    NODE_ID = "base"
    NODE_NAME = "Base Node"
    NODE_VERSION = "1.0.0"
    INPUT_PORTS = []
    OUTPUT_PORTS = []
    CONSTRAINTS = []

    def __init__(self, node_id: str | None = None):
        self.node_id = node_id or self.NODE_ID
        self._state = CapsuleNodeState.CREATED
        self._phase = NodePhase.SCHEMA_LOADING
        self._exec_count = 0
        self._error_count = 0
        self._total_exec_time = 0.0
        self._lock = threading.RLock()

    @property
    def state(self):
        return type("State", (), {"phase": self._phase})()

    @property
    def capsule_state(self):
        return self._state

    @property
    def metrics(self):
        avg = self._total_exec_time / self._exec_count if self._exec_count > 0 else 0
        return {"exec_count": self._exec_count, "error_count": self._error_count, "avg_time_ms": avg * 1000}

    def init(self):
        with self._lock:
            self._state = CapsuleNodeState.INITIALIZING
            self._phase = NodePhase.INITIALIZATION_COMPLETE
            self._state = CapsuleNodeState.INITIALIZED
        return self

    def _validate_inputs(self, inputs: dict) -> bool:
        for port in self.INPUT_PORTS:
            if port.get("required") and port["name"] not in inputs:
                raise ValueError(f"Missing required input: {port['name']}")
        return True

    def run(self, inputs: dict) -> dict:
        with self._lock:
            self._validate_inputs(inputs)
            self._state = CapsuleNodeState.RUNNING
            self._phase = NodePhase.PROCESSING

            import time

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
            "state": {"capsule_state": self._state, "phase": self._phase},
            "schemas": {
                "inputs": [p["name"] for p in self.INPUT_PORTS],
                "outputs": [p["name"] for p in self.OUTPUT_PORTS],
                "constraints": [c["name"] for c in self.CONSTRAINTS],
            },
            "metrics": self.metrics,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 节点实现
# ═══════════════════════════════════════════════════════════════════════════════


class MarketNode(CapsuleNode):
    NODE_ID = "market_node"
    NODE_NAME = "Market Data Node"

    INPUT_PORTS = [
        {"name": "raw_feed", "type": "object", "required": True, "fields": ["symbol", "price", "timestamp"]},
    ]
    OUTPUT_PORTS = [
        {"name": "ohlcv", "type": "object", "required": True},
        {"name": "phase", "type": "string", "required": True},
    ]
    CONSTRAINTS = [
        {"name": "max_latency_ms", "type": "runtime", "value": 1000},
    ]

    def __init__(self):
        super().__init__("market_node")
        self._bars = {}

    def _process_impl(self, inputs: dict) -> dict:
        raw = inputs.get("raw_feed", {})
        symbol = raw.get("symbol", "").upper()
        price = raw.get("price", 0)
        volume = raw.get("volume", 0)
        timestamp = raw.get("timestamp", 0)

        self._bars[symbol] = self._bars.get(symbol, [])
        self._bars[symbol].append({"close": price, "volume": volume})

        phase = "RANGE" if len(self._bars.get(symbol, [])) > 5 else "UNKNOWN"

        return {
            "ohlcv": {"symbol": symbol, "close": price, "volume": volume},
            "phase": phase,
        }


class SignalNode(CapsuleNode):
    NODE_ID = "signal_node"
    NODE_NAME = "Signal Node"

    INPUT_PORTS = [{"name": "ohlcv", "type": "object", "required": True}]
    OUTPUT_PORTS = [{"name": "signal", "type": "object", "required": True}]
    CONSTRAINTS = [{"name": "min_confidence", "type": "validation", "value": 0.6}]

    def __init__(self):
        super().__init__("signal_node")

        self._counter = 0

    def _process_impl(self, inputs: dict) -> dict:
        import uuid

        ohlcv = inputs.get("ohlcv", {})
        close = ohlcv.get("close", 100)

        self._counter += 1
        direction = "LONG" if close > 100 else "SHORT"

        return {
            "signal": {
                "signal_id": f"sig_{uuid.uuid4().hex[:8]}",
                "symbol": ohlcv.get("symbol", "UNKNOWN"),
                "direction": direction,
                "confidence": 0.7,
                "entry_price": close,
            }
        }


class RiskNode(CapsuleNode):
    NODE_ID = "risk_node"
    NODE_NAME = "Risk Node"

    INPUT_PORTS = [{"name": "signal", "type": "object", "required": True}]
    OUTPUT_PORTS = [{"name": "approved", "type": "object", "required": True}]
    CONSTRAINTS = [{"name": "max_position_size", "type": "runtime", "value": 0.1}]

    def _process_impl(self, inputs: dict) -> dict:
        signal = inputs.get("signal", {})
        confidence = signal.get("confidence", 0)

        approved = confidence > 0.5

        return {
            "approved": {
                "signal_id": signal.get("signal_id"),
                "approved": approved,
                "size": 1000 if approved else 0,
                "risk_score": 0.3 if approved else 1.0,
            }
        }


class BrainNode(CapsuleNode):
    NODE_ID = "brain_node"
    NODE_NAME = "Brain Node"

    INPUT_PORTS = [{"name": "signal", "type": "object", "required": True}]
    OUTPUT_PORTS = [{"name": "decision", "type": "object", "required": True}]
    CONSTRAINTS = [{"name": "min_threshold", "type": "validation", "value": 0.65}]

    def __init__(self):
        super().__init__("brain_node")
        self._decisions = 0

    def _process_impl(self, inputs: dict) -> dict:
        import uuid

        signal = inputs.get("signal", {})
        self._decisions += 1

        return {
            "decision": {
                "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
                "action": "EXECUTE",
                "symbol": signal.get("symbol"),
                "size": 1000,
            }
        }


class ExecutionNode(CapsuleNode):
    NODE_ID = "execution_node"
    NODE_NAME = "Execution Node"

    INPUT_PORTS = [{"name": "decision", "type": "object", "required": True}]
    OUTPUT_PORTS = [{"name": "order", "type": "object", "required": True}]
    CONSTRAINTS = [{"name": "initial_balance", "type": "immutable", "value": 100000}]

    def __init__(self):
        super().__init__("execution_node")
        self._orders = 0
        self._portfolio = 100000

    def _process_impl(self, inputs: dict) -> dict:
        import uuid

        decision = inputs.get("decision", {})
        self._orders += 1

        return {
            "order": {
                "order_id": f"ord_{uuid.uuid4().hex[:12]}",
                "symbol": decision.get("symbol"),
                "action": decision.get("action"),
                "status": "FILLED",
            },
            "portfolio": {"total": self._portfolio, "orders": self._orders},
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Pipeline 管理器
# ═══════════════════════════════════════════════════════════════════════════════


class PipelineManager:
    def __init__(self):
        self._nodes: dict[str, CapsuleNode] = {}
        self._pipeline: list[tuple] = []

    def register(self, node_class, node_id: str):
        self._nodes[node_id] = node_class()

    def define_pipeline(self, connections: list[tuple]):
        self._pipeline = connections

    def init_all(self):
        for node in self._nodes.values():
            node.init()

    def get(self, node_id: str) -> CapsuleNode | None:
        return self._nodes.get(node_id)

    def list_nodes(self) -> list[str]:
        return list(self._nodes.keys())

    def execute_pipeline(self, initial_input: dict) -> dict:
        results = {}

        # 执行 market
        market = self._nodes.get("market")
        if market and initial_input:
            out = market.run(initial_input)
            results["market"] = out
        else:
            out = {}

        # 执行 signal
        signal = self._nodes.get("signal")
        if signal and "ohlcv" in out:
            out = signal.run({"ohlcv": out["ohlcv"]})
            results["signal"] = out
        else:
            out = {}

        # 执行 risk
        risk = self._nodes.get("risk")
        if risk and "signal" in out:
            out = risk.run({"signal": out.get("signal", {})})
            results["risk"] = out
        else:
            out = {}

        # 执行 brain
        brain = self._nodes.get("brain")
        if brain and "signal" in out:
            out = brain.run({"signal": out.get("signal", {})})
            results["brain"] = out
        else:
            out = {}

        # 执行 execution
        execution = self._nodes.get("execution")
        if execution and "decision" in out:
            out = execution.run({"decision": out.get("decision", {})})
            results["execution"] = out

        return results

    def get_status(self) -> dict:
        return {
            "initialized": True,
            "node_count": len(self._nodes),
            "nodes": {nid: node.export_state() for nid, node in self._nodes.items()},
        }

    def shutdown_all(self):
        for node in self._nodes.values():
            node.shutdown()


# ═══════════════════════════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════════════════════════


def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper()), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def main():
    parser = argparse.ArgumentParser(description="CapsuleNode Deployment")
    parser.add_argument("--mode", choices=["status", "run", "simulate"], default="status")
    parser.add_argument("--ticks", type=int, default=10)
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")

    args = parser.parse_args()
    setup_logging(args.log_level)
    logger = logging.getLogger("CapsuleNode")

    # 创建 Pipeline
    manager = PipelineManager()
    manager.register(MarketNode, "market")
    manager.register(SignalNode, "signal")
    manager.register(RiskNode, "risk")
    manager.register(BrainNode, "brain")
    manager.register(ExecutionNode, "execution")

    manager.define_pipeline(
        [
            ("market", "signal"),
            ("signal", "risk"),
            ("risk", "brain"),
            ("brain", "execution"),
        ]
    )

    if args.mode == "status":
        logger.info("Getting status...")
        manager.init_all()
        status = manager.get_status()
        print(json.dumps(status, indent=2, default=str))
        manager.shutdown_all()

    elif args.mode == "run":
        logger.info("Running single tick...")
        manager.init_all()
        result = manager.execute_pipeline(
            {"raw_feed": {"symbol": "BTCUSDT", "price": 50000, "volume": 100, "timestamp": 1714281600}}
        )
        print(json.dumps(result, indent=2, default=str))
        manager.shutdown_all()

    elif args.mode == "simulate":
        logger.info(f"Running simulation: {args.ticks} ticks")
        manager.init_all()

        for i in range(args.ticks):
            result = manager.execute_pipeline(
                {"raw_feed": {"symbol": "BTCUSDT", "price": 50000 + i * 10, "volume": 100, "timestamp": 1714281600 + i}}
            )
            portfolio = result.get("execution", {}).get("portfolio", {})
            logger.info(f"Tick {i+1}: orders={portfolio.get('orders', 0)}")

        manager.shutdown_all()
        logger.info("Simulation complete")


if __name__ == "__main__":
    main()
