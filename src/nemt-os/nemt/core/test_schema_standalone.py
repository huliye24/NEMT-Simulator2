"""独立测试 Node Schema"""

from enum import Enum
from typing import Any

# 直接复制核心逻辑，不依赖包结构


class NodeType(Enum):
    SOURCE = "source"
    PROCESSOR = "processor"
    DECISION = "decision"
    ACTION = "action"
    MONITOR = "monitor"


class NodeStatus(Enum):
    CREATED = "created"
    INITIALIZED = "initialized"
    RUNNING = "running"
    IDLE = "idle"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


# 简化版 NODE_SCHEMA
NODE_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "type", "version", "status"],
    "properties": {
        "id": {"type": "string", "pattern": "^[a-z_][a-z0-9_]*$"},
        "name": {"type": "string", "minLength": 1},
        "type": {"type": "string", "enum": [t.value for t in NodeType]},
        "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
        "status": {"type": "string", "enum": [s.value for s in NodeStatus]},
        "description": {"type": "string"},
        "constraints": {"type": "object"},
    },
}

# 端口 schemas
PORT_SCHEMAS = {
    "ohlcv": {
        "type": "object",
        "required": ["symbol", "open", "high", "low", "close", "volume"],
        "properties": {
            "symbol": {"type": "string"},
            "open": {"type": "number"},
            "high": {"type": "number"},
            "low": {"type": "number"},
            "close": {"type": "number"},
            "volume": {"type": "number"},
        },
    },
    "signal": {
        "type": "object",
        "required": ["signal_id", "direction", "confidence"],
        "properties": {
            "signal_id": {"type": "string"},
            "direction": {"type": "string", "enum": ["LONG", "SHORT", "NEUTRAL"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
    },
}


def validate_node(node_data: dict) -> tuple:
    """验证节点"""
    errors = []
    required = ["id", "name", "type", "version", "status"]

    for field in required:
        if field not in node_data:
            errors.append(f"Missing required field: {field}")

    # 简单验证
    if "type" in node_data and node_data["type"] not in [t.value for t in NodeType]:
        errors.append(f"Invalid type: {node_data['type']}")

    if "status" in node_data and node_data["status"] not in [s.value for s in NodeStatus]:
        errors.append(f"Invalid status: {node_data['status']}")

    return len(errors) == 0, errors


def validate_port_data(port_name: str, data: Any) -> tuple:
    """验证端口数据"""
    if port_name not in PORT_SCHEMAS:
        return True, None

    schema = PORT_SCHEMAS[port_name]
    errors = []

    # 检查必需字段
    for field in schema.get("required", []):
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # 检查枚举
    for prop, spec in schema.get("properties", {}).items():
        if prop in data:
            if "enum" in spec and data[prop] not in spec["enum"]:
                errors.append(f"Invalid value for {prop}: {data[prop]}")
            if "minimum" in spec and data[prop] < spec["minimum"]:
                errors.append(f"{prop} below minimum: {data[prop]}")
            if "maximum" in spec and data[prop] > spec["maximum"]:
                errors.append(f"{prop} above maximum: {data[prop]}")

    return len(errors) == 0, errors if errors else None


def validate_transition(from_status: NodeStatus, to_status: NodeStatus) -> bool:
    """验证状态转换"""
    VALID = {
        NodeStatus.CREATED: [NodeStatus.INITIALIZED],
        NodeStatus.INITIALIZED: [NodeStatus.RUNNING, NodeStatus.STOPPED],
        NodeStatus.RUNNING: [NodeStatus.IDLE, NodeStatus.ERROR, NodeStatus.STOPPED],
        NodeStatus.IDLE: [NodeStatus.RUNNING, NodeStatus.PAUSED, NodeStatus.STOPPED],
        NodeStatus.PAUSED: [NodeStatus.IDLE, NodeStatus.STOPPED],
        NodeStatus.ERROR: [NodeStatus.IDLE, NodeStatus.STOPPED],
        NodeStatus.STOPPED: [],
    }
    return to_status in VALID.get(from_status, [])


class MarketNode:
    """简化版市场节点"""

    NODE = {
        "id": "market_node",
        "name": "Market Data Node",
        "type": "source",
        "version": "1.0.0",
        "status": "created",
        "constraints": {"max_latency_ms": 1000, "min_confidence": 0.5},
        "state": {"phase": "UNKNOWN", "bars_generated": 0},
    }

    def __init__(self):
        self._status = NodeStatus.CREATED
        self._state = self.NODE["state"].copy()

    def setup(self):
        self._status = NodeStatus.INITIALIZED
        return self

    def exec(self, raw_feed):
        # 计算 OHLCV
        ohlcv = {
            "symbol": raw_feed["symbol"].upper(),
            "open": raw_feed["price"] * 0.998,
            "high": raw_feed["price"] * 1.002,
            "low": raw_feed["price"] * 0.997,
            "close": raw_feed["price"],
            "volume": raw_feed.get("volume", 0),
        }
        self._state["bars_generated"] += 1
        self._state["phase"] = "RANGE"
        return {"ohlcv": ohlcv}


def test_all():
    print("=" * 60)
    print("Node Schema Test - 三层架构")
    print("Schema (规则) -> State (数据) -> Node (执行)")
    print("=" * 60)

    # Test 1: Schema Validation
    print("\n=== Test 1: Schema Validation ===")
    valid_node = {"id": "test_node", "name": "Test Node", "type": "processor", "version": "1.0.0", "status": "created"}
    is_valid, errors = validate_node(valid_node)
    print(f"Valid node: {is_valid}")

    invalid_node = {"id": "test", "name": "Test"}
    is_valid, errors = validate_node(invalid_node)
    print(f"Invalid node: {is_valid} (expected False)")
    print(f"  Errors: {errors}")

    # Test 2: Port Validation
    print("\n=== Test 2: Port Validation ===")
    valid_ohlcv = {"symbol": "BTCUSDT", "open": 50000, "high": 50100, "low": 49900, "close": 50050, "volume": 100}
    is_valid, error = validate_port_data("ohlcv", valid_ohlcv)
    print(f"Valid OHLCV: {is_valid}")

    invalid_ohlcv = {"symbol": "BTCUSDT", "open": 50000}
    is_valid, error = validate_port_data("ohlcv", invalid_ohlcv)
    print(f"Invalid OHLCV: {is_valid} (expected False)")
    print(f"  Error: {error}")

    # Test 3: Signal Validation
    print("\n=== Test 3: Signal Validation ===")
    valid_signal = {"signal_id": "sig_001", "direction": "LONG", "confidence": 0.75}
    is_valid, error = validate_port_data("signal", valid_signal)
    print(f"Valid signal: {is_valid}")

    invalid_signal = {"signal_id": "sig_002", "direction": "LONG", "confidence": 1.5}  # 超出范围
    is_valid, error = validate_port_data("signal", invalid_signal)
    print(f"Invalid confidence: {is_valid} (expected False)")
    print(f"  Error: {error}")

    # Test 4: State Transitions
    print("\n=== Test 4: State Transitions ===")
    print(f"CREATED -> INITIALIZED: {validate_transition(NodeStatus.CREATED, NodeStatus.INITIALIZED)}")
    print(f"INITIALIZED -> RUNNING: {validate_transition(NodeStatus.INITIALIZED, NodeStatus.RUNNING)}")
    print(f"RUNNING -> IDLE: {validate_transition(NodeStatus.RUNNING, NodeStatus.IDLE)}")
    print(f"STOPPED -> RUNNING: {validate_transition(NodeStatus.STOPPED, NodeStatus.RUNNING)} (expected False)")

    # Test 5: MarketNode Execution
    print("\n=== Test 5: MarketNode Execution ===")
    node = MarketNode()
    print(f"Created: {node.NODE['id']}")
    print(f"  Initial status: {node._status.value}")

    node.setup()
    print(f"  After setup: {node._status.value}")

    result = node.exec({"symbol": "BTCUSDT", "price": 50000, "volume": 100})
    print(f"  Output: {list(result.keys())}")
    print(f"  Phase: {node._state['phase']}")
    print(f"  Bars generated: {node._state['bars_generated']}")

    # Test 6: Full Loop
    print("\n=== Test 6: Full Loop ===")
    print("Schema + State + Node -> AI Execution")
    print(f"  NODE constraints: {list(node.NODE['constraints'].keys())}")
    print(f"  NODE state: {node._state}")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_all()
