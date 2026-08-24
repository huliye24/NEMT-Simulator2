"""
CapsuleNode 管理器

管理多个 CapsuleNode 实例的生命周期
"""

import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class NodeConfig:
    """节点配置"""

    node_class: type
    node_id: str
    node_name: str = ""
    auto_init: bool = True
    config: dict[str, Any] = field(default_factory=dict)


class NodeManager:
    """
    CapsuleNode 管理器

    管理多个 CapsuleNode 实例的生命周期、依赖注入和通信。

    使用方法:

    ```python
    from capsules import MarketNode, SignalNode, RiskNode
    from tools.node_manager import NodeManager

    # 创建管理器
    manager = NodeManager()

    # 注册节点
    manager.register(MarketNode, "market")
    manager.register(SignalNode, "signal")
    manager.register(RiskNode, "risk")

    # 初始化所有节点
    manager.init_all()

    # 获取节点
    market = manager.get("market")

    # 启动所有节点
    manager.start_all()

    # 停止所有节点
    manager.shutdown_all()
    ```
    """

    def __init__(self):
        self._nodes: dict[str, Any] = {}
        self._configs: dict[str, NodeConfig] = {}
        self._lock = threading.RLock()
        self._initialized = False
        self._running = False

    def register(self, node_class: type, node_id: str, **kwargs) -> None:
        """
        注册节点类

        Args:
            node_class: CapsuleNode 子类
            node_id: 节点 ID
            **kwargs: 额外配置
        """
        with self._lock:
            config = NodeConfig(node_class=node_class, node_id=node_id, **kwargs)
            self._configs[node_id] = config

    def get(self, node_id: str) -> Any | None:
        """
        获取节点实例

        Args:
            node_id: 节点 ID

        Returns:
            节点实例，如果不存在返回 None
        """
        with self._lock:
            return self._nodes.get(node_id)

    def get_all(self) -> dict[str, Any]:
        """获取所有节点"""
        with self._lock:
            return self._nodes.copy()

    def list_nodes(self) -> list[str]:
        """列出所有注册的节点 ID"""
        with self._lock:
            return list(self._configs.keys())

    def init_all(self) -> None:
        """初始化所有节点"""
        with self._lock:
            if self._initialized:
                raise RuntimeError("Nodes already initialized")

            for node_id, config in self._configs.items():
                node = config.node_class(node_id=node_id)

                # 应用配置
                for key, value in config.config.items():
                    if hasattr(node, "set_config"):
                        node.set_config(key, value)

                # 初始化
                if config.auto_init:
                    node.init()

                self._nodes[node_id] = node

            self._initialized = True

    def start_all(self) -> None:
        """启动所有节点"""
        with self._lock:
            if not self._initialized:
                raise RuntimeError("Nodes not initialized")

            for node in self._nodes.values():
                if hasattr(node, "start"):
                    node.start()

            self._running = True

    def shutdown_all(self) -> None:
        """关闭所有节点"""
        with self._lock:
            for node in self._nodes.values():
                if hasattr(node, "shutdown"):
                    node.shutdown()

            self._running = False
            self._initialized = False

    def get_status(self) -> dict[str, Any]:
        """获取所有节点状态"""
        with self._lock:
            status = {
                "initialized": self._initialized,
                "running": self._running,
                "node_count": len(self._nodes),
                "nodes": {},
            }

            for node_id, node in self._nodes.items():
                status["nodes"][node_id] = {
                    "state": str(node.capsule_state) if hasattr(node, "capsule_state") else "unknown",
                    "metrics": node.metrics if hasattr(node, "metrics") else {},
                }

            return status

    def reset_all(self) -> None:
        """重置所有节点"""
        with self._lock:
            for node in self._nodes.values():
                if hasattr(node, "reset"):
                    node.reset()


class PipelineNodeManager(NodeManager):
    """
    Pipeline 节点管理器

    扩展 NodeManager，支持节点间的数据流水线。

    使用方法:

    ```python
    manager = PipelineNodeManager()

    # 注册节点
    manager.register(MarketNode, "market")
    manager.register(SignalNode, "signal")
    manager.register(RiskNode, "risk")
    manager.register(BrainNode, "brain")
    manager.register(ExecutionNode, "execution")

    # 定义流程
    manager.define_pipeline([
        ("market", "signal"),
        ("signal", "risk"),
        ("risk", "brain"),
        ("brain", "execution"),
    ])

    # 初始化
    manager.init_all()

    # 执行单次流程
    result = manager.execute_pipeline({
        "raw_feed": {...}
    })

    # 获取结果
    print(result["execution"]["portfolio"])
    ```
    """

    def __init__(self):
        super().__init__()
        self._pipeline: list[tuple] = []  # [(from_node, to_node), ...]
        self._cache: dict[str, Any] = {}

    def define_pipeline(self, connections: list[tuple]) -> None:
        """
        定义数据流水线

        Args:
            connections: 连接列表，每个元素是 (源节点, 目标节点) 的元组
        """
        self._pipeline = connections

    def execute_pipeline(self, initial_input: dict[str, Any]) -> dict[str, Any]:
        """
        执行流水线

        Args:
            initial_input: 初始输入数据

        Returns:
            所有节点的输出结果
        """
        self._cache.clear()
        results = {}

        # 解析初始输入，确定起始节点
        start_node = None
        input_data = initial_input

        # 找到起始节点（没有前置节点的节点）
        targets = {c[1] for c in self._pipeline}
        sources = {c[0] for c in self._pipeline}

        for node_id in self._configs.keys():
            if node_id not in targets:
                start_node = node_id
                break

        if start_node is None:
            # 没有明确的起点，使用第一个注册的节点
            start_node = list(self._configs.keys())[0]

        # 执行节点
        current_node = start_node
        current_output = None

        # 如果有初始输入，先执行市场节点
        if initial_input:
            market = self.get(current_node)
            if market:
                current_output = market.run(initial_input)
                results[current_node] = current_output
                self._cache[current_node] = current_output

        # 按顺序执行后续节点
        # 构建节点顺序
        node_order = self._build_node_order()

        for node_id in node_order:
            if node_id == start_node:
                continue

            node = self.get(node_id)
            if not node:
                continue

            # 准备输入
            node_input = self._prepare_node_input(node_id)

            # 执行
            output = node.run(node_input)
            results[node_id] = output
            self._cache[node_id] = output

        return results

    def _build_node_order(self) -> list[str]:
        """构建节点执行顺序"""
        ordered = []
        visited = set()

        def visit(node_id):
            if node_id in visited:
                return
            visited.add(node_id)

            # 先访问依赖的节点
            for source, target in self._pipeline:
                if target == node_id:
                    visit(source)

            ordered.append(node_id)

        for node_id in self._configs.keys():
            visit(node_id)

        return ordered

    def _prepare_node_input(self, node_id: str) -> dict[str, Any]:
        """准备节点输入"""
        input_data = {}

        # 查找所有指向此节点的连接
        for source, target in self._pipeline:
            if target != node_id:
                continue

            # 获取源节点的输出
            source_output = self._cache.get(source)
            if source_output is None:
                continue

            # 合并输出
            input_data.update(source_output)

        return input_data


if __name__ == "__main__":
    # 示例用法
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    from capsules import BrainNode, ExecutionNode, MarketNode, RiskNode, SignalNode

    # 创建管理器
    manager = PipelineNodeManager()

    # 注册节点
    manager.register(MarketNode, "market")
    manager.register(SignalNode, "signal")
    manager.register(RiskNode, "risk")
    manager.register(BrainNode, "brain")
    manager.register(ExecutionNode, "execution")

    # 定义流程
    manager.define_pipeline(
        [
            ("market", "signal"),
            ("signal", "risk"),
            ("risk", "brain"),
            ("brain", "execution"),
        ]
    )

    # 初始化
    manager.init_all()

    print("Pipeline Status:")
    print(manager.get_status())

    # 执行单次流程
    result = manager.execute_pipeline(
        {"raw_feed": {"symbol": "BTCUSDT", "price": 50000, "volume": 100, "timestamp": 1714281600}}
    )

    print("\nPipeline Results:")
    for node_id, output in result.items():
        print(f"  {node_id}: {list(output.keys())}")

    # 最终投资组合
    if "execution" in result:
        portfolio = result["execution"].get("portfolio", {})
        print(f"\nFinal Portfolio: {portfolio}")

    # 关闭
    manager.shutdown_all()
