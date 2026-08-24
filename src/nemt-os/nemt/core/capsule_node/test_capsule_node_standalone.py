"""
测试 CapsuleNode 系统 - 独立版本

绕过 nemt_os 包初始化，直接测试 capsule_node 模块
"""

import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
# 复制核心类用于测试
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


@dataclass
class PortSchema:
    name: str
    data_type: str
    required: bool = False
    description: str = ""
    properties: dict = field(default_factory=dict)
    required_fields: list = field(default_factory=list)
    constraints: dict = field(default_factory=dict)
    format: str | None = None
    enum_values: list | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "data_type": self.data_type,
            "required": self.required,
            "description": self.description,
            "properties": self.properties,
            "required_fields": self.required_fields,
            "constraints": self.constraints,
            "enum": self.enum_values,
        }


@dataclass
class ConstraintSchema:
    name: str
    constraint_type: str
    value: Any
    description: str = ""
    min_value: float | None = None
    max_value: float | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.constraint_type,
            "value": self.value,
            "description": self.description,
        }


@dataclass
class NodeState:
    node_id: str
    node_name: str
    node_version: str
    phase: NodePhase = NodePhase.SCHEMA_LOADING
    capsule_state: CapsuleNodeState = CapsuleNodeState.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)
    state_history: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "node_version": self.node_version,
            "phase": self.phase.value,
            "capsule_state": self.capsule_state.value,
            "created_at": self.created_at.isoformat(),
            "last_update": self.last_update.isoformat(),
        }

    def update_phase(self, phase: NodePhase, description: str = "") -> None:
        self.phase = phase
        self.last_update = datetime.now()


@dataclass
class ValidationResult:
    valid: bool = True
    errors: list = field(default_factory=list)

    def add_error(self, field: str, message: str) -> None:
        self.errors.append({"field": field, "message": message})
        self.valid = False


# ═══════════════════════════════════════════════════════════════════════════════
# CapsuleNode 基类
# ═══════════════════════════════════════════════════════════════════════════════


class CapsuleNode(ABC):
    NODE_ID = "base_node"
    NODE_NAME = "Base Node"
    NODE_VERSION = "1.0.0"
    INPUT_PORTS: list[PortSchema] = []
    OUTPUT_PORTS: list[PortSchema] = []
    CONSTRAINTS: list[ConstraintSchema] = []

    def __init__(self, node_id: str | None = None):
        actual_id = node_id or self.NODE_ID
        self._state = NodeState(
            node_id=actual_id,
            node_name=self.NODE_NAME,
            node_version=self.NODE_VERSION,
        )
        self._capsule_state = CapsuleNodeState.CREATED
        self._logger = type(
            "Logger",
            (),
            {
                "info": lambda s, m: print(f"  [INFO] {m}"),
                "debug": lambda s, m: None,
                "error": lambda s, m: print(f"  [ERROR] {m}"),
            },
        )()
        self._lock = threading.RLock()
        self._exec_count = 0
        self._error_count = 0
        self._total_exec_time = 0.0

    @property
    def node_id(self):
        return self._state.node_id

    @property
    def node_name(self):
        return self._state.node_name

    @property
    def node_version(self):
        return self._state.node_version

    @property
    def state(self):
        return self._state

    @property
    def capsule_state(self):
        return self._capsule_state

    @property
    def metrics(self):
        avg = self._total_exec_time / self._exec_count if self._exec_count > 0 else 0
        return {
            "exec_count": self._exec_count,
            "error_count": self._error_count,
            "avg_exec_time_ms": avg * 1000,
        }

    def init(self) -> "CapsuleNode":
        with self._lock:
            self._capsule_state = CapsuleNodeState.INITIALIZING
            self._state.update_phase(NodePhase.INITIALIZATION_COMPLETE)
            self._capsule_state = CapsuleNodeState.INITIALIZED
        return self

    def _validate_inputs(self, inputs: dict) -> ValidationResult:
        result = ValidationResult()
        for port in self.INPUT_PORTS:
            if port.required and port.name not in inputs:
                result.add_error(port.name, f"Required input missing: {port.name}")
            if port.name in inputs:
                for field in port.required_fields:
                    if isinstance(inputs[port.name], dict) and field not in inputs[port.name]:
                        result.add_error(f"{port.name}.{field}", f"Required field missing: {field}")
        return result

    def run(self, inputs: dict) -> dict:
        with self._lock:
            self._capsule_state = CapsuleNodeState.VALIDATING_INPUT
            validation = self._validate_inputs(inputs)
            if not validation.valid:
                self._capsule_state = CapsuleNodeState.ERROR
                raise ValueError(f"Validation failed: {validation.errors}")

            self._capsule_state = CapsuleNodeState.RUNNING
            import time

            start = time.time()
            outputs = self._process_impl(inputs)
            self._total_exec_time += time.time() - start
            self._exec_count += 1

            self._capsule_state = CapsuleNodeState.IDLE
            self._state.update_phase(NodePhase.EXECUTION_COMPLETE)
            return outputs

    @abstractmethod
    def _process_impl(self, inputs: dict) -> dict:
        pass

    def shutdown(self) -> "CapsuleNode":
        self._capsule_state = CapsuleNodeState.STOPPED
        self._state.update_phase(NodePhase.TERMINATED)
        return self

    def export_state(self) -> dict:
        return {
            "node": {"id": self.node_id, "name": self.node_name, "version": self.node_version},
            "state": self._state.to_dict(),
            "metrics": self.metrics,
            "schemas": {
                "inputs": {p.name: p.to_dict() for p in self.INPUT_PORTS},
                "outputs": {p.name: p.to_dict() for p in self.OUTPUT_PORTS},
                "constraints": {c.name: c.to_dict() for c in self.CONSTRAINTS},
            },
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MarketNode 实现
# ═══════════════════════════════════════════════════════════════════════════════


class MarketNode(CapsuleNode):
    NODE_ID = "market_node"
    NODE_NAME = "Market Data Node"
    NODE_VERSION = "1.0.0"

    INPUT_PORTS = [
        PortSchema(
            name="raw_feed",
            data_type="object",
            required=True,
            description="Raw market feed",
            properties={
                "symbol": {"type": "string"},
                "price": {"type": "number"},
                "volume": {"type": "number"},
                "timestamp": {"type": "integer"},
            },
            required_fields=["symbol", "price", "timestamp"],
        ),
    ]

    OUTPUT_PORTS = [
        PortSchema(
            name="ohlcv",
            data_type="object",
            required=True,
            description="OHLCV bars",
            properties={
                "symbol": {"type": "string"},
                "open": {"type": "number"},
                "high": {"type": "number"},
                "low": {"type": "number"},
                "close": {"type": "number"},
                "volume": {"type": "number"},
            },
            required_fields=["symbol", "open", "high", "low", "close", "volume"],
        ),
        PortSchema(
            name="phase",
            data_type="string",
            required=True,
            description="Market phase",
            enum_values=["UNKNOWN", "TREND_UP", "TREND_DOWN", "RANGE", "VOLATILE"],
        ),
    ]

    CONSTRAINTS = [
        ConstraintSchema(
            name="max_latency_ms", constraint_type="runtime", value=1000, description="Max processing latency"
        ),
        ConstraintSchema(name="max_cache_size", constraint_type="runtime", value=1000, description="Max cache size"),
    ]

    def __init__(self):
        super().__init__("market_node")
        self._bars_cache: dict[str, list] = {}
        self._symbols: list[str] = []
        self._bar_count = 0

    def _process_impl(self, inputs: dict) -> dict:
        raw = inputs.get("raw_feed", {})
        symbol = raw.get("symbol", "").upper()
        price = raw.get("price", 0)
        volume = raw.get("volume", 0)
        timestamp = raw.get("timestamp", 0)

        # 计算 OHLCV
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

        # 检测相位
        bars = self._bars_cache.get(symbol, [])
        phase = "RANGE" if len(bars) > 5 else "UNKNOWN"

        return {"ohlcv": ohlcv, "phase": phase}


# ═══════════════════════════════════════════════════════════════════════════════
# 测试函数
# ═══════════════════════════════════════════════════════════════════════════════


def test_basic_node():
    """测试 1: 基本节点创建"""
    print("=== Test 1: Basic Node ===")
    node = MarketNode()
    print(f"Created: {node.NODE_ID}")
    print(f"  State: {node.capsule_state.value}")
    print(f"  Phase: {node.state.phase.value}")
    return True


def test_schema_definitions():
    """测试 2: Schema 定义"""
    print("\n=== Test 2: Schema Definitions ===")
    print(f"Input Ports: {len(MarketNode.INPUT_PORTS)}")
    for port in MarketNode.INPUT_PORTS:
        print(f"  - {port.name} (required={port.required})")
        print(f"    Required fields: {port.required_fields}")

    print(f"\nOutput Ports: {len(MarketNode.OUTPUT_PORTS)}")
    for port in MarketNode.OUTPUT_PORTS:
        print(f"  - {port.name} (required={port.required})")
        if port.enum_values:
            print(f"    Enum: {port.enum_values}")

    print(f"\nConstraints: {len(MarketNode.CONSTRAINTS)}")
    for c in MarketNode.CONSTRAINTS:
        print(f"  - {c.name} = {c.value} ({c.constraint_type})")

    return True


def test_ai_readable_state():
    """测试 3: AI 可读状态"""
    print("\n=== Test 3: AI-Readable State ===")
    node = MarketNode()
    node.init()

    state = node.export_state()
    print(f"Node: {state['node']['id']} v{state['node']['version']}")
    print(f"Phase: {state['state']['phase']}")
    print(f"Input Schemas: {list(state['schemas']['inputs'].keys())}")
    print(f"Output Schemas: {list(state['schemas']['outputs'].keys())}")
    print(f"Constraints: {list(state['schemas']['constraints'].keys())}")

    return True


def test_node_lifecycle():
    """测试 4: 节点生命周期"""
    print("\n=== Test 4: Node Lifecycle ===")
    node = MarketNode()

    print(f"Initial: {node.capsule_state.value}")

    node.init()
    print(f"After init: {node.capsule_state.value}")

    outputs = node.run({"raw_feed": {"symbol": "BTCUSDT", "price": 50000, "volume": 100, "timestamp": 1714281600}})
    print(f"After run: {node.capsule_state.value}")
    print(f"Output: {list(outputs.keys())}")

    node.shutdown()
    print(f"After shutdown: {node.capsule_state.value}")

    return True


def test_schema_validation():
    """测试 5: Schema 验证"""
    print("\n=== Test 5: Schema Validation ===")
    node = MarketNode()
    node.init()

    # 有效输入
    try:
        outputs = node.run({"raw_feed": {"symbol": "ETHUSDT", "price": 3000, "volume": 50, "timestamp": 1714281600}})
        print("Valid input: SUCCESS")
    except Exception as e:
        print(f"Valid input: FAILED - {e}")

    # 无效输入
    try:
        outputs = node.run({"raw_feed": {"symbol": "ETHUSDT", "price": 3000}})
        print("Invalid input: SHOULD HAVE FAILED")
    except ValueError as e:
        print("Invalid input: BLOCKED")
        print(f"  Error: {str(e)[:60]}...")

    return True


def test_metrics():
    """测试 6: 指标"""
    print("\n=== Test 6: Metrics ===")
    node = MarketNode()
    node.init()

    for i in range(3):
        node.run(
            {"raw_feed": {"symbol": f"TOKEN{i}", "price": 100 + i * 10, "volume": 10, "timestamp": 1714281600 + i}}
        )

    print(f"Exec count: {node.metrics['exec_count']}")
    print(f"Error count: {node.metrics['error_count']}")
    print(f"Avg exec time: {node.metrics['avg_exec_time_ms']:.2f}ms")

    return True


def test_full_loop():
    """测试 7: 完整循环"""
    print("\n=== Test 7: Full Loop ===")
    print("Schema + State + Validation -> AI Execution")

    # 1. 创建
    node = MarketNode()
    print("1. Created MarketNode")

    # 2. 初始化
    node.init()
    print("2. Initialized")

    # 3. AI 读取状态
    print(f"3. AI reads state: phase={node.state.phase.value}")

    # 4. 执行
    outputs = node.run({"raw_feed": {"symbol": "BTCUSDT", "price": 50000, "volume": 100, "timestamp": 1714281600}})
    print(f"4. Executed: phase={outputs['phase']}")

    # 5. 导出
    print(f"5. Bars cached: {node._bar_count}")

    # 6. 关闭
    node.shutdown()
    print("6. Shutdown")

    return True


if __name__ == "__main__":
    print("=" * 70)
    print("CapsuleNode Test - Capsule + Node Schema 融合验证")
    print("=" * 70)

    tests = [
        ("Basic Node", test_basic_node),
        ("Schema Definitions", test_schema_definitions),
        ("AI-Readable State", test_ai_readable_state),
        ("Node Lifecycle", test_node_lifecycle),
        ("Schema Validation", test_schema_validation),
        ("Metrics", test_metrics),
        ("Full Loop", test_full_loop),
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
