"""测试 Node Schema 三层架构"""

import os
import sys

# 直接从文件路径导入，绕过包初始化
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nemt_os.nemt.core.market_node import MarketNode
from nemt_os.nemt.core.node_schema import (
    NODE_SCHEMA,
    PORT_SCHEMAS,
    NodeStatus,
    validate_node,
    validate_port_data,
    validate_transition,
)


def test_schema_validation():
    """测试 1: Schema 验证"""
    print("=== Test 1: Schema Validation ===")

    # 验证合法节点
    valid_node = {"id": "test_node", "name": "Test Node", "type": "processor", "version": "1.0.0", "status": "created"}

    is_valid, errors = validate_node(valid_node)
    print(f"Valid node: {is_valid}")

    # 验证非法节点 (缺少必需字段)
    invalid_node = {"id": "test", "name": "Test"}  # 缺少 type, version, status

    is_valid, errors = validate_node(invalid_node)
    print(f"Invalid node: {is_valid} (expected False)")
    if errors:
        print(f"  Errors: {errors[:2]}")

    return True


def test_port_validation():
    """测试 2: 端口数据验证"""
    print("\n=== Test 2: Port Data Validation ===")

    # 合法数据
    valid_ohlcv = {"symbol": "BTCUSDT", "open": 50000, "high": 50100, "low": 49900, "close": 50050, "volume": 100}

    is_valid, error = validate_port_data("ohlcv", valid_ohlcv)
    print(f"Valid OHLCV: {is_valid}")

    # 非法数据 (缺少必需字段)
    invalid_ohlcv = {
        "symbol": "BTCUSDT",
        "open": 50000,
        # 缺少 high, low, close, volume
    }

    is_valid, error = validate_port_data("ohlcv", invalid_ohlcv)
    print(f"Invalid OHLCV: {is_valid} (expected False)")
    if error:
        print(f"  Error: {error}")

    return True


def test_signal_validation():
    """测试 3: Signal 验证"""
    print("\n=== Test 3: Signal Validation ===")

    # 合法信号
    valid_signal = {"signal_id": "sig_001", "direction": "LONG", "confidence": 0.75}

    is_valid, error = validate_port_data("signal", valid_signal)
    print(f"Valid signal: {is_valid}")

    # 非法置信度
    invalid_signal = {"signal_id": "sig_002", "direction": "LONG", "confidence": 1.5}  # 超出 0-1 范围

    is_valid, error = validate_port_data("signal", invalid_signal)
    print(f"Invalid confidence: {is_valid} (expected False)")
    if error:
        print(f"  Error: {error}")

    return True


def test_market_node():
    """测试 4: MarketNode 执行"""
    print("\n=== Test 4: MarketNode Execution ===")

    # 创建节点
    node = MarketNode()
    print(f"Created: {node}")
    print(f"  ID: {node.id}")
    print(f"  Type: {node.NODE['type']}")
    print(f"  Status: {node.status.value}")

    # 初始化
    node.setup()
    print(f"  After setup: {node.status.value}")

    # 执行
    inputs = {"raw_feed": {"symbol": "BTCUSDT", "price": 50000, "volume": 100, "timestamp": 1714281600}}

    outputs = node.run(inputs)
    print(f"  Output keys: {list(outputs.keys())}")
    print(f"  OHLCV close: {outputs['ohlcv']['close']}")

    # 检查状态更新
    print(f"  Phase: {node.state.get('phase')}")
    print(f"  Bars generated: {node.state.get('bars_generated')}")

    return True


def test_state_transitions():
    """测试 5: 状态转换"""
    print("\n=== Test 5: State Transitions ===")

    node = MarketNode()

    # 有效转换
    transitions = [
        (NodeStatus.CREATED, NodeStatus.INITIALIZED),
        (NodeStatus.INITIALIZED, NodeStatus.RUNNING),
        (NodeStatus.RUNNING, NodeStatus.IDLE),
    ]

    for from_s, to_s in transitions:
        is_valid = validate_transition(from_s, to_s)
        print(f"  {from_s.value} -> {to_s.value}: {'VALID' if is_valid else 'INVALID'}")

    # 无效转换
    invalid = validate_transition(NodeStatus.STOPPED, NodeStatus.RUNNING)
    print(f"  STOPPED -> RUNNING: {'VALID' if invalid else 'INVALID'} (expected INVALID)")

    return True


def test_full_loop():
    """测试 6: 完整循环"""
    print("\n=== Test 6: Full Loop ===")
    print("Schema + State + Node -> AI Execution")

    # 1. AI 读取 Schema
    print("1. AI reads schema")
    print(f"   Required fields for node: {NODE_SCHEMA['required']}")
    print(f"   Available port types: {list(PORT_SCHEMAS.keys())}")

    # 2. AI 读取 State
    print("\n2. AI reads state")
    node = MarketNode()
    print(f"   Current phase: {node.state.get('phase')}")
    print(f"   Constraints: {list(node.NODE.get('constraints', {}).keys())}")

    # 3. AI 根据约束执行
    print("\n3. AI executes with constraints")
    node.setup()

    # 4. 输出被验证
    print("\n4. Output validated against schema")
    outputs = node.exec({"raw_feed": {"symbol": "ETHUSDT", "price": 3000, "volume": 50, "timestamp": 1714281600}})

    is_valid, error = validate_port_data("ohlcv", outputs["ohlcv"])
    print(f"   Output valid: {is_valid}")

    # 5. 状态更新
    print("\n5. State updated")
    print(f"   Phase: {node.state.get('phase')}")
    print(f"   Symbols: {node.state.get('symbols')}")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Node Schema Test - 三层架构验证")
    print("Schema (规则) -> State (数据) -> AI (执行)")
    print("=" * 60)

    results = []

    results.append(("Schema Validation", test_schema_validation()))
    results.append(("Port Validation", test_port_validation()))
    results.append(("Signal Validation", test_signal_validation()))
    results.append(("MarketNode Execution", test_market_node()))
    results.append(("State Transitions", test_state_transitions()))
    results.append(("Full Loop", test_full_loop()))

    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {name}")

    all_passed = all(r[1] for r in results)
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed"))
