"""
CapsuleNode 完整状态系统

核心思想：
  整个软件都是状态

软件 = 状态的集合 + 状态的转换

每个时刻：
  SystemState = 当前时刻的完整快照

每个操作：
  StateTransition = 状态变化的记录

这使得：
  1. 软件状态可序列化、可恢复
  2. 任意时刻的状态可回溯
  3. 状态变化可审计
  4. 整个系统可验证
"""

import json
import threading
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
# 状态枚举
# ═══════════════════════════════════════════════════════════════════════════════


class SystemPhase(Enum):
    """系统阶段"""

    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class NodeStatus(Enum):
    """节点状态"""

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    IDLE = "idle"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


# ═══════════════════════════════════════════════════════════════════════════════
# 核心状态类
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class NodeState:
    """
    节点状态

    包含节点的完整状态，不仅仅是元信息。
    """

    # 身份
    node_id: str
    node_type: str
    node_name: str
    version: str

    # 状态
    status: str = NodeStatus.CREATED.value
    phase: str = ""

    # Schema
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)

    # 运行时数据
    data: dict[str, Any] = field(default_factory=dict)  # 节点的内部数据
    history: list[dict] = field(default_factory=list)  # 历史记录

    # 指标
    metrics: dict[str, Any] = field(default_factory=dict)

    # 时间戳
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

    def update(self, **kwargs) -> None:
        """更新状态"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now().isoformat()

        # 记录历史
        self.history.append({"timestamp": self.updated_at, "action": "update", "changes": kwargs})

        # 限制历史大小
        if len(self.history) > 1000:
            self.history = self.history[-500:]


@dataclass
class ConnectionState:
    """
    连接状态

    表示节点间的连接关系。
    """

    from_node: str
    to_node: str
    port_mapping: dict[str, str] = field(default_factory=dict)  # from_port -> to_port
    enabled: bool = True
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PipelineState:
    """
    Pipeline 状态

    包含 Pipeline 的完整配置和运行时状态。
    """

    pipeline_id: str
    name: str
    description: str = ""

    # 节点
    nodes: dict[str, NodeState] = field(default_factory=dict)

    # 连接
    connections: list[ConnectionState] = field(default_factory=list)

    # 执行状态
    current_tick: int = 0
    execution_count: int = 0
    error_count: int = 0

    # 缓存
    tick_cache: list[dict] = field(default_factory=list)  # 最近 N 次执行的结果

    def to_dict(self) -> dict:
        return {
            "pipeline_id": self.pipeline_id,
            "name": self.name,
            "description": self.description,
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "connections": [c.to_dict() for c in self.connections],
            "current_tick": self.current_tick,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "tick_cache": self.tick_cache,
        }


@dataclass
class SystemState:
    """
    系统状态

    包含整个软件系统的完整状态。

    这就是"把整个软件都做成状态"的核心理念：
    软件运行时 = SystemState 的当前快照
    软件操作 = SystemState 的转换
    """

    # 系统信息
    system_id: str
    system_name: str
    version: str

    # 系统阶段
    phase: str = SystemPhase.INITIALIZING.value

    # 全局配置
    config: dict[str, Any] = field(default_factory=dict)

    # 所有 Pipeline
    pipelines: dict[str, PipelineState] = field(default_factory=dict)

    # 当前活动的 Pipeline
    active_pipeline_id: str | None = None

    # 全局历史
    history: list[dict] = field(default_factory=list)

    # 时间戳
    started_at: str = ""
    last_tick_at: str = ""

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()
        self.last_tick_at = self.started_at

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "system_id": self.system_id,
            "system_name": self.system_name,
            "version": self.version,
            "phase": self.phase,
            "config": self.config,
            "pipelines": {k: v.to_dict() for k, v in self.pipelines.items()},
            "active_pipeline_id": self.active_pipeline_id,
            "started_at": self.started_at,
            "last_tick_at": self.last_tick_at,
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, default=str)

    def update_phase(self, phase: SystemPhase) -> None:
        """更新系统阶段"""
        old_phase = self.phase
        self.phase = phase.value
        self._record_history("phase_change", {"from": old_phase, "to": phase.value})

    def _record_history(self, action: str, data: dict) -> None:
        """记录历史"""
        self.history.append({"timestamp": datetime.now().isoformat(), "action": action, "data": data})

        # 限制历史大小
        if len(self.history) > 10000:
            self.history = self.history[-5000:]


# ═══════════════════════════════════════════════════════════════════════════════
# 状态转换
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class StateTransition:
    """
    状态转换记录

    记录每次状态变化。
    """

    transition_id: str
    timestamp: str
    from_state: dict
    to_state: dict
    action: str
    description: str = ""


class StateTransitionLog:
    """
    状态转换日志

    记录所有状态转换，用于审计和回溯。
    """

    def __init__(self, max_size: int = 10000):
        self._log: list[StateTransition] = []
        self._max_size = max_size
        self._lock = threading.Lock()
        self._counter = 0

    def record(self, from_state: dict, to_state: dict, action: str, description: str = "") -> str:
        """记录状态转换"""
        with self._lock:
            self._counter += 1
            transition_id = f"t_{self._counter}_{int(time.time())}"

            transition = StateTransition(
                transition_id=transition_id,
                timestamp=datetime.now().isoformat(),
                from_state=from_state,
                to_state=to_state,
                action=action,
                description=description,
            )

            self._log.append(transition)

            # 限制大小
            if len(self._log) > self._max_size:
                self._log = self._log[-self._max_size // 2 :]

            return transition_id

    def get_log(self) -> list[dict]:
        """获取转换日志"""
        with self._lock:
            return [asdict(t) for t in self._log]

    def get_transition(self, transition_id: str) -> dict | None:
        """获取指定转换"""
        with self._lock:
            for t in self._log:
                if t.transition_id == transition_id:
                    return asdict(t)
            return None

    def get_history(self, entity_id: str = None, limit: int = 100) -> list[dict]:
        """获取历史记录"""
        with self._lock:
            if entity_id:
                # 筛选特定实体的历史
                history = []
                for t in self._log:
                    if entity_id in str(t.from_state) or entity_id in str(t.to_state):
                        history.append(asdict(t))
                return history[-limit:]
            return [asdict(t) for t in self._log[-limit:]]


# ═══════════════════════════════════════════════════════════════════════════════
# 状态管理器
# ═══════════════════════════════════════════════════════════════════════════════


class StateManager:
    """
    状态管理器

    管理整个软件系统的状态。

    核心职责：
    1. 维护 SystemState
    2. 记录状态转换
    3. 提供状态快照
    4. 支持状态恢复
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._system_state: SystemState | None = None
        self._transition_log = StateTransitionLog()
        self._snapshots: list[dict] = []
        self._lock = threading.RLock()
        self._initialized = True

    @property
    def state(self) -> SystemState:
        """获取当前状态"""
        return self._system_state

    def initialize(self, system_id: str, system_name: str, version: str, config: dict = None) -> SystemState:
        """初始化系统状态"""
        with self._lock:
            # 记录当前状态
            if self._system_state:
                self._transition_log.record(
                    self._system_state.to_dict(), {"phase": "initializing"}, "system_initialize"
                )

            self._system_state = SystemState(
                system_id=system_id,
                system_name=system_name,
                version=version,
                config=config or {},
                phase=SystemPhase.READY.value,
            )

            return self._system_state

    def create_pipeline(self, pipeline_id: str, name: str, description: str = "") -> PipelineState:
        """创建 Pipeline"""
        with self._lock:
            pipeline = PipelineState(pipeline_id=pipeline_id, name=name, description=description)

            self._system_state.pipelines[pipeline_id] = pipeline

            self._transition_log.record({}, pipeline.to_dict(), "create_pipeline", f"Created pipeline {pipeline_id}")

            return pipeline

    def add_node(self, pipeline_id: str, node_state: NodeState) -> None:
        """添加节点"""
        with self._lock:
            if pipeline_id not in self._system_state.pipelines:
                raise ValueError(f"Pipeline {pipeline_id} not found")

            pipeline = self._system_state.pipelines[pipeline_id]
            old_state = pipeline.to_dict()

            pipeline.nodes[node_state.node_id] = node_state

            self._transition_log.record(old_state, pipeline.to_dict(), "add_node", f"Added node {node_state.node_id}")

    def add_connection(self, pipeline_id: str, connection: ConnectionState) -> None:
        """添加连接"""
        with self._lock:
            pipeline = self._system_state.pipelines[pipeline_id]
            old_state = pipeline.to_dict()

            pipeline.connections.append(connection)

            self._transition_log.record(
                old_state,
                pipeline.to_dict(),
                "add_connection",
                f"Connected {connection.from_node} -> {connection.to_node}",
            )

    def update_node_state(self, pipeline_id: str, node_id: str, **kwargs) -> None:
        """更新节点状态"""
        with self._lock:
            pipeline = self._system_state.pipelines[pipeline_id]
            if node_id not in pipeline.nodes:
                raise ValueError(f"Node {node_id} not found")

            node = pipeline.nodes[node_id]
            old_state = node.to_dict()

            node.update(**kwargs)

            self._transition_log.record(
                old_state, node.to_dict(), "update_node", f"Updated node {node_id}: {list(kwargs.keys())}"
            )

    def tick(self, pipeline_id: str, tick_data: dict) -> None:
        """执行 tick"""
        with self._lock:
            pipeline = self._system_state.pipelines[pipeline_id]
            old_state = pipeline.to_dict()

            pipeline.current_tick += 1
            pipeline.execution_count += 1

            # 保存 tick 结果到缓存
            pipeline.tick_cache.append(
                {"tick": pipeline.current_tick, "data": tick_data, "timestamp": datetime.now().isoformat()}
            )

            # 限制缓存大小
            if len(pipeline.tick_cache) > 100:
                pipeline.tick_cache = pipeline.tick_cache[-50:]

            self._system_state.last_tick_at = datetime.now().isoformat()

            self._transition_log.record(old_state, pipeline.to_dict(), "tick", f"Tick {pipeline.current_tick}")

    def record_error(self, pipeline_id: str, error: Exception) -> None:
        """记录错误"""
        with self._lock:
            pipeline = self._system_state.pipelines[pipeline_id]
            pipeline.error_count += 1

            # 记录到系统历史
            self._system_state.history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "type": "error",
                    "pipeline_id": pipeline_id,
                    "error": str(error),
                    "error_type": type(error).__name__,
                }
            )

    def take_snapshot(self, name: str = "") -> str:
        """创建状态快照"""
        with self._lock:
            snapshot = {
                "snapshot_id": f"snap_{int(time.time())}",
                "name": name,
                "timestamp": datetime.now().isoformat(),
                "state": self._system_state.to_dict(),
            }

            self._snapshots.append(snapshot)

            # 限制快照数量
            if len(self._snapshots) > 10:
                self._snapshots = self._snapshots[-5:]

            return snapshot["snapshot_id"]

    def get_snapshot(self, snapshot_id: str) -> dict | None:
        """获取快照"""
        for s in self._snapshots:
            if s["snapshot_id"] == snapshot_id:
                return s
        return None

    def get_full_state(self) -> dict:
        """获取完整状态"""
        with self._lock:
            return {
                "system": self._system_state.to_dict(),
                "transition_log": self._transition_log.get_log()[-100:],
                "snapshots": [
                    {"id": s["snapshot_id"], "name": s["name"], "timestamp": s["timestamp"]} for s in self._snapshots
                ],
            }

    def get_node_state(self, pipeline_id: str, node_id: str) -> dict | None:
        """获取节点状态"""
        with self._lock:
            pipeline = self._system_state.pipelines.get(pipeline_id)
            if not pipeline:
                return None
            node = pipeline.nodes.get(node_id)
            if not node:
                return None
            return node.to_dict()

    def export_state(self) -> str:
        """导出状态为 JSON"""
        return self.get_full_state().__str__()

    def reset(self) -> None:
        """重置状态"""
        with self._lock:
            if self._system_state:
                self._transition_log.record(self._system_state.to_dict(), {}, "reset", "System reset")

            self._system_state = None
            self._snapshots.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# 状态装饰器
# ═══════════════════════════════════════════════════════════════════════════════


def stateful(method: Callable) -> Callable:
    """
    状态装饰器

    自动将方法调用记录到状态中。
    """

    def wrapper(self, *args, **kwargs):
        # 获取方法执行前的状态
        before_state = {}
        if hasattr(self, "_get_state_dict"):
            before_state = self._get_state_dict()

        # 执行方法
        result = method(self, *args, **kwargs)

        # 获取方法执行后的状态
        after_state = {}
        if hasattr(self, "_get_state_dict"):
            after_state = self._get_state_dict()

        # 记录转换
        if hasattr(self, "_state_manager"):
            self._state_manager._transition_log.record(
                before_state, after_state, method.__name__, f"Called {method.__name__}"
            )

        return result

    return wrapper


# ═══════════════════════════════════════════════════════════════════════════════
# 全局状态管理器实例
# ═══════════════════════════════════════════════════════════════════════════════

_state_manager = StateManager()


def get_state_manager() -> StateManager:
    """获取状态管理器"""
    return _state_manager


def get_current_state() -> SystemState:
    """获取当前状态"""
    return _state_manager.state


def initialize_system(system_id: str, system_name: str, version: str, config: dict = None) -> SystemState:
    """初始化系统"""
    return _state_manager.initialize(system_id, system_name, version, config)


# ═══════════════════════════════════════════════════════════════════════════════
# 示例和测试
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("CapsuleNode State System")
    print("核心思想: 整个软件都是状态")
    print("=" * 70)

    # 初始化系统
    sm = get_state_manager()
    system_state = initialize_system(
        system_id="nemt_trading_system",
        system_name="NEMT Trading System",
        version="1.0.0",
        config={"mode": "backtest", "symbols": ["BTCUSDT", "ETHUSDT"]},
    )

    print(f"\nSystem initialized: {system_state.system_name}")
    print(f"Phase: {system_state.phase}")

    # 创建 Pipeline
    pipeline = sm.create_pipeline(
        pipeline_id="main_trading", name="Main Trading Pipeline", description="Primary trading data flow"
    )

    print(f"\nPipeline created: {pipeline.name}")

    # 添加节点
    market_node = NodeState(
        node_id="market",
        node_type="MarketNode",
        node_name="Market Data Node",
        version="1.0.0",
        input_schema={"raw_feed": {"type": "object", "required": True}},
        output_schema={"ohlcv": {"type": "object"}, "phase": {"type": "string"}},
        constraints={"max_latency_ms": 1000},
        data={"bars_cache": {"BTCUSDT": []}, "symbols": []},
        metrics={"exec_count": 0},
    )

    signal_node = NodeState(
        node_id="signal",
        node_type="SignalNode",
        node_name="Signal Generation Node",
        version="1.0.0",
        input_schema={"ohlcv": {"type": "object"}},
        output_schema={"signal": {"type": "object"}},
        constraints={"min_confidence": 0.6},
        data={"signals": []},
        metrics={"exec_count": 0},
    )

    sm.add_node("main_trading", market_node)
    sm.add_node("main_trading", signal_node)

    print(f"\nNodes added: {list(pipeline.nodes.keys())}")

    # 添加连接
    sm.add_connection(
        "main_trading", ConnectionState(from_node="market", to_node="signal", port_mapping={"ohlcv": "ohlcv"})
    )

    print(f"Connections: {len(pipeline.connections)}")

    # 执行 tick
    sm.tick("main_trading", {"raw_feed": {"symbol": "BTCUSDT", "price": 50000, "volume": 100}})

    print(f"\nTick executed: {pipeline.current_tick}")

    # 更新节点状态
    sm.update_node_state("main_trading", "market", status="running", **{"metrics.exec_count": 1})

    # 再次 tick
    sm.tick("main_trading", {"raw_feed": {"symbol": "BTCUSDT", "price": 51000, "volume": 150}})

    print(f"Tick executed: {pipeline.current_tick}")

    # 创建快照
    snapshot_id = sm.take_snapshot("before_test")
    print(f"\nSnapshot created: {snapshot_id}")

    # 获取完整状态
    full_state = sm.get_full_state()

    print("\n" + "=" * 70)
    print("System State Snapshot")
    print("=" * 70)
    print(f"System: {full_state['system']['system_name']}")
    print(f"Phase: {full_state['system']['phase']}")
    print(f"Pipelines: {len(full_state['system']['pipelines'])}")
    print(f"Transitions: {len(full_state['transition_log'])}")
    print(f"Snapshots: {len(full_state['snapshots'])}")

    print("\n" + "=" * 70)
    print("Pipeline State")
    print("=" * 70)
    main_pipeline = full_state["system"]["pipelines"]["main_trading"]
    print(f"Nodes: {list(main_pipeline['nodes'].keys())}")
    print(f"Current Tick: {main_pipeline['current_tick']}")
    print(f"Execution Count: {main_pipeline['execution_count']}")

    for node_id, node in main_pipeline["nodes"].items():
        print(f"\n  [{node_id}]")
        print(f"    Status: {node['status']}")
        print(f"    Metrics: {node['metrics']}")
        print(f"    Data keys: {list(node['data'].keys())}")

    print("\n" + "=" * 70)
    print("State Philosophy")
    print("=" * 70)
    print("Software = State + Transitions")
    print("  - Every moment: SystemState snapshot")
    print("  - Every operation: StateTransition record")
    print("  - Result: Fully observable, reversible system")
    print("=" * 70)
