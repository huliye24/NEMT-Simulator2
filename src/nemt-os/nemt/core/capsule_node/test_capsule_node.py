"""测试 CapsuleNode 系统"""

import importlib.util
import json
import sys


# 直接导入模块文件，绕过包初始化
def load_module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# 加载 capsule_node 模块
capsule_node = load_module_from_path(
    "nemt.core.capsule_node", "e:/NEMT Simulator/nemt_os/nemt/core/capsule_node/__init__.py"
)


def test_basic_node():
    """测试 1: 基本节点创建"""
    print("=== Test 1: Basic Node ===")

    node = MarketNode()
    print(f"Created: {node}")
    print(f"  Node ID: {node.node_id}")
    print(f"  Node Name: {node.node_name}")
    print(f"  Node Version: {node.node_version}")
    print(f"  State: {node.capsule_state.value}")
    print(f"  Phase: {node.state.phase.value}")

    return True


def test_schema_definitions():
    """测试 2: Schema 定义"""
    print("\n=== Test 2: Schema Definitions ===")

    # 检查输入端口
    print(f"Input Ports: {len(MarketNode.INPUT_PORTS)}")
    for port in MarketNode.INPUT_PORTS:
        print(f"  - {port.name} ({port.data_type}, required={port.required})")
        print(f"    Fields: {port.required_fields}")

    # 检查输出端口
    print(f"Output Ports: {len(MarketNode.OUTPUT_PORTS)}")
    for port in MarketNode.OUTPUT_PORTS:
        print(f"  - {port.name} ({port.data_type}, required={port.required})")
        if port.enum_values:
            print(f"    Enum: {port.enum_values}")

    # 检查约束
    print(f"Constraints: {len(MarketNode.CONSTRAINTS)}")
    for constraint in MarketNode.CONSTRAINTS:
        print(f"  - {constraint.name} = {constraint.value} ({constraint.constraint_type})")

    return True


def test_ai_readable_state():
    """测试 3: AI 可读状态"""
    print("\n=== Test 3: AI-Readable State ===")

    node = MarketNode()
    node.init()

    # 导出状态 (JSON 格式)
    state_json = node.export_json()

    # 解析并展示关键部分
    state = json.loads(state_json)

    print("State Export:")
    print(f"  Node: {state['node']['id']} v{state['node']['version']}")
    print(f"  State: {state['state']['capsule_state']}")
    print(f"  Phase: {state['state']['phase']}")
    print(f"  Health: {state['health']}")

    print("\nInput Schemas:")
    for name, schema in state["schemas"]["inputs"].items():
        print(f"  {name}:")
        print(f"    Type: {schema['data_type']}")
        print(f"    Required: {schema['required']}")
        print(f"    Required Fields: {schema['required_fields']}")

    print("\nConstraints:")
    for name, constraint in state["schemas"]["constraints"].items():
        print(f"  {name}: {constraint['value']} ({constraint['type']})")

    return True


def test_node_lifecycle():
    """测试 4: 节点生命周期"""
    print("\n=== Test 4: Node Lifecycle ===")

    node = MarketNode()

    # 初始状态
    print(f"Initial: {node.capsule_state.value}")

    # 初始化
    node.init()
    print(f"After init: {node.capsule_state.value}")
    print(f"Phase: {node.state.phase.value}")

    # 运行
    inputs = {"raw_feed": {"symbol": "BTCUSDT", "price": 50000, "volume": 100, "timestamp": 1714281600}}

    outputs = node.run(inputs)
    print(f"After run: {node.capsule_state.value}")
    print(f"Phase: {node.state.phase.value}")
    print(f"Output keys: {list(outputs.keys())}")
    print(f"Phase detected: {outputs.get('phase')}")

    # 关闭
    node.shutdown()
    print(f"After shutdown: {node.capsule_state.value}")

    return True


def test_schema_validation():
    """测试 5: Schema 验证"""
    print("\n=== Test 5: Schema Validation ===")

    node = MarketNode()
    node.init()

    # 有效输入
    valid_inputs = {"raw_feed": {"symbol": "ETHUSDT", "price": 3000, "volume": 50, "timestamp": 1714281600}}

    try:
        outputs = node.run(valid_inputs)
        print("Valid input: SUCCESS")
        print(f"  Output: {list(outputs.keys())}")
    except Exception as e:
        print(f"Valid input: FAILED - {e}")

    # 无效输入 (缺少必需字段)
    invalid_inputs = {
        "raw_feed": {
            "symbol": "ETHUSDT",
            "price": 3000,
            # 缺少 timestamp
        }
    }

    try:
        outputs = node.run(invalid_inputs)
        print("Invalid input: SHOULD HAVE FAILED")
    except ValueError as e:
        print(f"Invalid input: BLOCKED - {str(e)[:80]}...")

    return True


def test_five_stage_iteration():
    """测试 6: 五阶段迭代"""
    print("\n=== Test 6: Five-Stage Iteration ===")

    node = MarketNode()
    node.init()

    # 执行五阶段迭代
    result = node.run_fractal_iteration()

    print(f"Iteration #{result['iteration']}")
    print(f"Status: {result['status']}")

    for phase_name, phase_data in result["phases"].items():
        duration_ms = phase_data.get("duration_ms", 0)
        print(f"  {phase_name}: {duration_ms:.2f}ms")

    # 观察报告
    if node.observe_report:
        print("\nObserve Report:")
        print(f"  Inputs: {list(node.observe_report.get('inputs', {}).keys())}")
        print(f"  Outputs: {list(node.observe_report.get('outputs', {}).keys())}")
        print(f"  Constraints: {len(node.observe_report.get('constraints', {}))}")

    return True


def test_full_loop():
    """测试 7: 完整循环"""
    print("\n=== Test 7: Full Loop ===")
    print("Schema + State + Validation -> AI Execution")

    # 1. 创建节点
    node = MarketNode()
    print("1. Created MarketNode")

    # 2. 初始化
    node.init()
    print("2. Initialized with schemas")

    # 3. 读取 AI 可读状态
    state = node.state
    print(f"3. AI reads state: phase={state.phase.value}, constraints={len(node.CONSTRAINTS)}")

    # 4. 运行多次
    for i in range(3):
        outputs = node.run(
            {
                "raw_feed": {
                    "symbol": f"TOKEN{i}",
                    "price": 100 + i * 10,
                    "volume": 10 + i,
                    "timestamp": 1714281600 + i * 60,
                }
            }
        )

    print(f"4. Executed {node.metrics['exec_count']} times")
    print(f"   Errors: {node.metrics['error_count']}")

    # 5. 导出最终状态
    final_state = node.export_state()
    print("5. Final state exported")
    print(f"   Bars cached: {node.get_metrics()['cache_size']}")

    # 6. 关闭
    node.shutdown()
    print("6. Shutdown")

    return True


def test_schema_registry():
    """测试 8: Schema 注册表"""
    print("\n=== Test 8: Schema Registry ===")

    registry = SchemaRegistry()

    # 查询注册的节点
    nodes = registry.list_nodes()
    print(f"Registered nodes: {len(nodes)}")
    for n in nodes[:5]:
        print(f"  - {n}")

    # 查询 MarketNode 的 schemas
    schemas = registry.get_node_schemas("market_node")
    print("\nMarketNode schemas:")
    print(f"  Inputs: {list(schemas['inputs'].keys())}")
    print(f"  Outputs: {list(schemas['outputs'].keys())}")
    print(f"  Constraints: {list(schemas['constraints'].keys())}")

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
        ("Five-Stage Iteration", test_five_stage_iteration),
        ("Full Loop", test_full_loop),
        ("Schema Registry", test_schema_registry),
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

    # 导出最终状态作为示例
    print("\n" + "=" * 70)
    print("Example: AI-Readable State Export")
    print("=" * 70)

    node = MarketNode()
    node.init()
    node.run({"raw_feed": {"symbol": "BTCUSDT", "price": 50000, "volume": 100, "timestamp": 1714281600}})

    print(node.export_json()[:1000] + "...")
