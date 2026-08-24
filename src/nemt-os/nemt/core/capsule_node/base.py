"""
CapsuleNode - 胶囊节点融合基类

融合现有 Capsule 系统 + Node Schema 验证层 + AI 可读状态

核心公式：
  Capsule (事件驱动 + 五阶段迭代 + 健康检查)
      +
  Node Schema (验证 + AI 可读状态)
      =
  CapsuleNode (完整 AI-native 系统)

架构：
  1. ICapsule 接口 - 标准化生命周期
  2. FractalCapsule - 五阶段迭代
  3. Schema 验证层 - 输入/输出/约束验证
  4. AI-Readable State - 结构化状态描述
"""

import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

__version__ = "1.0.0"
__all__ = [
    "CapsuleNodeState",
    "HealthStatus",
    "NodePhase",
    "PortSchema",
    "ConstraintSchema",
    "NodeState",
    "ValidationResult",
    "ValidationError",
    "SchemaRegistry",
    "CapsuleNode",
    "FractalCapsuleNode",
]


# ═══════════════════════════════════════════════════════════════════════════════
# 枚举定义
# ═══════════════════════════════════════════════════════════════════════════════


class CapsuleNodeState(Enum):
    """胶囊节点状态"""

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
    RECOVERING = "recovering"


class HealthStatus(Enum):
    """健康状态"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class NodePhase(Enum):
    """节点阶段 (AI 可读)"""

    # 初始化阶段
    SCHEMA_LOADING = "schema_loading"
    DEPENDENCY_INJECTION = "dependency_injection"
    INITIALIZATION_COMPLETE = "initialization_complete"

    # 观察阶段
    OBSERVING_INPUTS = "observing_inputs"
    ANALYZING_CONSTRAINTS = "analyzing_constraints"
    OBSERVATION_COMPLETE = "observation_complete"

    # 设计阶段
    DESIGNING_INTERFACE = "designing_interface"
    DEFINING_CONTRACTS = "defining_contracts"
    DESIGN_COMPLETE = "design_complete"

    # 执行阶段
    VALIDATING_INPUTS = "validating_inputs"
    PROCESSING = "processing"
    VALIDATING_OUTPUTS = "validating_outputs"
    EXECUTION_COMPLETE = "execution_complete"

    # 集成阶段
    INTEGRATING_UPSTREAM = "integrating_upstream"
    INTEGRATING_DOWNSTREAM = "integrating_downstream"
    INTEGRATION_COMPLETE = "integration_complete"

    # 异常
    ERROR_RECOVERY = "error_recovery"
    SHUTTING_DOWN = "shutting_down"
    TERMINATED = "terminated"


# ═══════════════════════════════════════════════════════════════════════════════
# Schema 定义
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class PortSchema:
    """
    端口 Schema 定义

    定义输入/输出端口的结构和约束。
    AI 可以直接读取此定义来理解数据格式。
    """

    name: str
    data_type: str  # "object", "array", "string", "number", "boolean"
    required: bool = False
    description: str = ""

    # Schema 定义
    properties: dict[str, Any] = field(default_factory=dict)
    required_fields: list[str] = field(default_factory=list)

    # 约束
    constraints: dict[str, Any] = field(default_factory=dict)

    # 元数据
    format: str | None = None
    default: Any = None
    enum_values: list[Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典 (AI 可读)"""
        return {
            "name": self.name,
            "data_type": self.data_type,
            "required": self.required,
            "description": self.description,
            "properties": self.properties,
            "required_fields": self.required_fields,
            "constraints": self.constraints,
            "format": self.format,
            "enum": self.enum_values,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PortSchema":
        """从字典创建"""
        return cls(
            name=data["name"],
            data_type=data["data_type"],
            required=data.get("required", False),
            description=data.get("description", ""),
            properties=data.get("properties", {}),
            required_fields=data.get("required_fields", []),
            constraints=data.get("constraints", {}),
            format=data.get("format"),
            default=data.get("default"),
            enum_values=data.get("enum"),
        )


@dataclass
class ConstraintSchema:
    """
    约束 Schema 定义

    定义运行时约束和限制条件。
    """

    name: str
    constraint_type: str  # "immutable", "runtime", "validation"
    value: Any
    description: str = ""

    # 验证规则
    min_value: float | None = None
    max_value: float | None = None
    pattern: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典 (AI 可读)"""
        return {
            "name": self.name,
            "type": self.constraint_type,
            "value": self.value,
            "description": self.description,
            "min": self.min_value,
            "max": self.max_value,
            "pattern": self.pattern,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# NodeState - AI 可读状态
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class NodeState:
    """
    节点状态 - AI 可直接读取

    与旧 CapsuleState 不同，这个状态是结构化的、可验证的。
    AI 可以通过读取这个对象来理解"现在是什么"。
    """

    # 身份
    node_id: str
    node_name: str
    node_version: str

    # 阶段 (AI 可读)
    phase: NodePhase = NodePhase.SCHEMA_LOADING
    phase_description: str = ""

    # 状态
    capsule_state: CapsuleNodeState = CapsuleNodeState.CREATED

    # 输入输出 Schema 描述
    input_schema: dict[str, PortSchema] = field(default_factory=dict)
    output_schema: dict[str, PortSchema] = field(default_factory=dict)
    constraints: dict[str, ConstraintSchema] = field(default_factory=dict)

    # 当前数据
    current_inputs: dict[str, Any] = field(default_factory=dict)
    current_outputs: dict[str, Any] = field(default_factory=dict)

    # 指标
    metrics: dict[str, Any] = field(default_factory=dict)

    # 历史
    state_history: list[dict] = field(default_factory=list)

    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典 (AI 可读)"""
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "node_version": self.node_version,
            "phase": self.phase.value,
            "phase_description": self.phase_description,
            "capsule_state": self.capsule_state.value,
            "input_schema": {k: v.to_dict() for k, v in self.input_schema.items()},
            "output_schema": {k: v.to_dict() for k, v in self.output_schema.items()},
            "constraints": {k: v.to_dict() for k, v in self.constraints.items()},
            "current_inputs": self.current_inputs,
            "current_outputs": self.current_outputs,
            "metrics": self.metrics,
            "created_at": self.created_at.isoformat(),
            "last_update": self.last_update.isoformat(),
        }

    def to_json(self) -> str:
        """转换为 JSON (AI 可直接解析)"""
        return json.dumps(self.to_dict(), indent=2, default=str)

    def update_phase(self, phase: NodePhase, description: str = "") -> None:
        """更新阶段"""
        self.phase = phase
        self.phase_description = description
        self.last_update = datetime.now()
        self._record_history("phase_change", {"from": self.phase.value, "to": phase.value, "description": description})

    def update_state(self, capsule_state: CapsuleNodeState) -> None:
        """更新状态"""
        old_state = self.capsule_state
        self.capsule_state = capsule_state
        self.last_update = datetime.now()
        self._record_history("state_change", {"from": old_state.value, "to": capsule_state.value})

    def _record_history(self, action: str, data: dict) -> None:
        """记录历史"""
        self.state_history.append({"timestamp": datetime.now().isoformat(), "action": action, "data": data})
        # 保持历史记录在合理范围内
        if len(self.state_history) > 100:
            self.state_history = self.state_history[-100:]


# ═══════════════════════════════════════════════════════════════════════════════
# 验证结果
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class ValidationError:
    """验证错误"""

    field: str
    message: str
    value: Any = None
    expected: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "message": self.message,
            "value": str(self.value) if self.value is not None else None,
            "expected": str(self.expected) if self.expected is not None else None,
        }


@dataclass
class ValidationResult:
    """验证结果"""

    valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    def add_error(self, field: str, message: str, value: Any = None, expected: Any = None) -> None:
        self.errors.append(ValidationError(field, message, value, expected))
        self.valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "error_count": self.error_count,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": self.warnings,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Schema 注册表
# ═══════════════════════════════════════════════════════════════════════════════


class SchemaRegistry:
    """
    Schema 注册表

    管理所有端口和约束的 Schema 定义。
    AI 可以查询此注册表来了解系统结构。
    """

    _instance: Optional["SchemaRegistry"] = None
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
        self._initialized = True
        self._port_schemas: dict[str, dict[str, PortSchema]] = {}  # node_id -> {port_name -> schema}
        self._constraint_schemas: dict[str, dict[str, ConstraintSchema]] = {}
        self._logger = logging.getLogger("CapsuleNode.SchemaRegistry")

    def register_port_schema(self, node_id: str, port_schema: PortSchema) -> None:
        """注册端口 Schema"""
        if node_id not in self._port_schemas:
            self._port_schemas[node_id] = {}
        self._port_schemas[node_id][port_schema.name] = port_schema
        self._logger.debug(f"Registered port schema: {node_id}.{port_schema.name}")

    def register_constraint_schema(self, node_id: str, constraint_schema: ConstraintSchema) -> None:
        """注册约束 Schema"""
        if node_id not in self._constraint_schemas:
            self._constraint_schemas[node_id] = {}
        self._constraint_schemas[node_id][constraint_schema.name] = constraint_schema
        self._logger.debug(f"Registered constraint schema: {node_id}.{constraint_schema.name}")

    def get_port_schema(self, node_id: str, port_name: str) -> PortSchema | None:
        """获取端口 Schema"""
        return self._port_schemas.get(node_id, {}).get(port_name)

    def get_constraint_schema(self, node_id: str, constraint_name: str) -> ConstraintSchema | None:
        """获取约束 Schema"""
        return self._constraint_schemas.get(node_id, {}).get(constraint_name)

    def get_node_schemas(self, node_id: str) -> dict[str, Any]:
        """获取节点所有 Schema (AI 可读)"""
        return {
            "node_id": node_id,
            "inputs": {
                k: v.to_dict() for k, v in self._port_schemas.get(node_id, {}).items() if v.data_type == "input"
            },
            "outputs": {
                k: v.to_dict() for k, v in self._port_schemas.get(node_id, {}).items() if v.data_type == "output"
            },
            "constraints": {k: v.to_dict() for k, v in self._constraint_schemas.get(node_id, {}).items()},
        }

    def list_nodes(self) -> list[str]:
        """列出所有注册的节点"""
        return list(set(list(self._port_schemas.keys()) + list(self._constraint_schemas.keys())))

    def clear(self) -> None:
        """清空注册表"""
        self._port_schemas.clear()
        self._constraint_schemas.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# CapsuleNode 基类
# ═══════════════════════════════════════════════════════════════════════════════


class CapsuleNode(ABC):
    """
    CapsuleNode 基类

    融合了：
    - ICapsule 接口 (标准化生命周期)
    - FractalCapsule (五阶段迭代)
    - Schema 验证层
    - AI-Readable State

    使用方式：

    class MarketNode(CapsuleNode):
        NODE_ID = "market_node"
        NODE_NAME = "Market Data Node"
        NODE_VERSION = "1.0.0"

        INPUT_PORTS = [
            PortSchema(name="raw_feed", data_type="object", required=True, ...)
        ]
        OUTPUT_PORTS = [
            PortSchema(name="ohlcv", data_type="object", required=True, ...)
        ]
        CONSTRAINTS = [
            ConstraintSchema(name="max_latency_ms", type="runtime", value=1000)
        ]

        def _observe_phase_impl(self) -> Dict[str, Any]:
            return {"inputs": {...}, "outputs": {...}}

        def _process_impl(self, inputs: Dict) -> Dict:
            return {"ohlcv": {...}}

    # AI 可以直接读取
    node = MarketNode()
    print(node.state.to_json())  # 当前状态 (AI 可读)
    """

    # ─────────────────────────────────────────────────────────────────────
    # 类属性 (子类必须定义)
    # ─────────────────────────────────────────────────────────────────────
    NODE_ID: str = "base_node"
    NODE_NAME: str = "Base Node"
    NODE_VERSION: str = "1.0.0"

    # 端口定义
    INPUT_PORTS: list[PortSchema] = []
    OUTPUT_PORTS: list[PortSchema] = []

    # 约束定义
    CONSTRAINTS: list[ConstraintSchema] = []

    # ─────────────────────────────────────────────────────────────────────
    # 实例属性
    # ─────────────────────────────────────────────────────────────────────
    _state: NodeState
    _capsule_state: CapsuleNodeState
    _logger: logging.Logger
    _lock: threading.RLock

    # 依赖注入
    _event_bus: Any | None = None
    _config: Any | None = None

    # 指标
    _exec_count: int = 0
    _error_count: int = 0
    _total_exec_time: float = 0.0

    # 历史
    _state_history: list[dict] = []

    # ─────────────────────────────────────────────────────────────────────
    # 初始化
    # ─────────────────────────────────────────────────────────────────────

    def __init__(self, node_id: str | None = None):
        self._init_state(node_id)
        self._init_dependencies()
        self._init_schemas()

    def _init_state(self, node_id: str | None) -> None:
        """初始化状态"""
        actual_id = node_id or self.NODE_ID
        self._state = NodeState(
            node_id=actual_id,
            node_name=self.NODE_NAME,
            node_version=self.NODE_VERSION,
        )
        self._capsule_state = CapsuleNodeState.CREATED
        self._logger = logging.getLogger(f"CapsuleNode.{actual_id}")
        self._lock = threading.RLock()
        self._state_history = []

    def _init_dependencies(self) -> None:
        """初始化依赖 (由 CapsuleManager 注入)"""
        self._event_bus = None
        self._config = None

    def _init_schemas(self) -> None:
        """初始化 Schema 注册"""
        registry = SchemaRegistry()

        # 注册输入端口
        for port in self.INPUT_PORTS:
            registry.register_port_schema(self.NODE_ID, port)

        # 注册输出端口
        for port in self.OUTPUT_PORTS:
            registry.register_port_schema(self.NODE_ID, port)

        # 注册约束
        for constraint in self.CONSTRAINTS:
            registry.register_constraint_schema(self.NODE_ID, constraint)

    # ─────────────────────────────────────────────────────────────────────
    # AI 可读属性
    # ─────────────────────────────────────────────────────────────────────

    @property
    def node_id(self) -> str:
        """节点 ID"""
        return self._state.node_id

    @property
    def node_name(self) -> str:
        """节点名称"""
        return self._state.node_name

    @property
    def node_version(self) -> str:
        """节点版本"""
        return self._state.node_version

    @property
    def state(self) -> NodeState:
        """AI 可读状态"""
        return self._state

    @property
    def capsule_state(self) -> CapsuleNodeState:
        """胶囊状态"""
        return self._capsule_state

    @property
    def is_initialized(self) -> bool:
        return self._capsule_state in (
            CapsuleNodeState.INITIALIZED,
            CapsuleNodeState.VALIDATING_INPUT,
            CapsuleNodeState.RUNNING,
            CapsuleNodeState.IDLE,
        )

    @property
    def is_running(self) -> bool:
        return self._capsule_state == CapsuleNodeState.RUNNING

    @property
    def is_error(self) -> bool:
        return self._capsule_state == CapsuleNodeState.ERROR

    @property
    def metrics(self) -> dict[str, Any]:
        """获取指标"""
        avg_time = self._total_exec_time / self._exec_count if self._exec_count > 0 else 0
        return {
            "exec_count": self._exec_count,
            "error_count": self._error_count,
            "avg_exec_time_ms": avg_time * 1000,
            "total_exec_time_ms": self._total_exec_time * 1000,
        }

    # ─────────────────────────────────────────────────────────────────────
    # 生命周期
    # ─────────────────────────────────────────────────────────────────────

    def init(self) -> "CapsuleNode":
        """
        初始化

        执行顺序：
        1. 状态转换到 INITIALIZING
        2. 执行 _init_impl() (子类可覆盖)
        3. 状态转换到 INITIALIZED

        Returns:
            self (支持链式调用)
        """
        with self._lock:
            self._transition(CapsuleNodeState.INITIALIZING)
            self._state.update_phase(NodePhase.SCHEMA_LOADING, "Loading schemas")

            try:
                self._state.update_phase(NodePhase.DEPENDENCY_INJECTION, "Injecting dependencies")
                self._init_impl()

                self._transition(CapsuleNodeState.INITIALIZED)
                self._state.update_phase(NodePhase.INITIALIZATION_COMPLETE, "Initialization complete")
                self._logger.info(f"{self.NODE_ID} initialized")

            except Exception as e:
                self._transition(CapsuleNodeState.ERROR)
                self._state.update_phase(NodePhase.ERROR_RECOVERY, f"Initialization failed: {e}")
                self._logger.error(f"{self.NODE_ID} initialization failed: {e}")
                raise

        return self

    def _init_impl(self) -> None:
        """初始化实现 (子类可覆盖)"""
        pass

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        运行节点 (完整流程)

        执行顺序：
        1. 验证输入 (Schema 验证)
        2. 处理数据
        3. 验证输出 (Schema 验证)

        Args:
            inputs: 输入数据

        Returns:
            输出数据

        Raises:
            ValueError: 输入验证失败
            RuntimeError: 处理失败
        """
        with self._lock:
            # 1. 验证输入
            self._transition(CapsuleNodeState.VALIDATING_INPUT)
            self._state.update_phase(NodePhase.VALIDATING_INPUTS, "Validating inputs")

            validation_result = self._validate_inputs(inputs)
            if not validation_result.valid:
                error_msg = f"Input validation failed: {validation_result.errors}"
                self._transition(CapsuleNodeState.ERROR)
                self._logger.error(error_msg)
                raise ValueError(error_msg)

            self._state.current_inputs = inputs

            # 2. 执行处理
            self._transition(CapsuleNodeState.RUNNING)
            self._state.update_phase(NodePhase.PROCESSING, "Processing")

            start_time = time.time()
            try:
                outputs = self._process_impl(inputs)
                self._total_exec_time += time.time() - start_time
                self._exec_count += 1

            except Exception as e:
                self._error_count += 1
                self._transition(CapsuleNodeState.ERROR)
                self._state.update_phase(NodePhase.ERROR_RECOVERY, f"Processing failed: {e}")
                self._logger.error(f"{self.NODE_ID} processing failed: {e}")
                raise

            # 3. 验证输出
            self._transition(CapsuleNodeState.VALIDATING_OUTPUT)
            self._state.update_phase(NodePhase.VALIDATING_OUTPUTS, "Validating outputs")

            validation_result = self._validate_outputs(outputs)
            if not validation_result.valid:
                error_msg = f"Output validation failed: {validation_result.errors}"
                self._transition(CapsuleNodeState.ERROR)
                self._logger.error(error_msg)
                raise ValueError(error_msg)

            self._state.current_outputs = outputs
            self._state.metrics = self.metrics

            # 4. 切换到空闲
            self._transition(CapsuleNodeState.IDLE)
            self._state.update_phase(NodePhase.EXECUTION_COMPLETE, "Execution complete")

            return outputs

    @abstractmethod
    def _process_impl(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        处理实现 (子类必须实现)

        Args:
            inputs: 验证后的输入数据

        Returns:
            输出数据
        """
        pass

    def shutdown(self) -> "CapsuleNode":
        """关闭"""
        with self._lock:
            self._transition(CapsuleNodeState.STOPPING)
            self._state.update_phase(NodePhase.SHUTTING_DOWN, "Shutting down")

            try:
                self._shutdown_impl()
            except Exception as e:
                self._logger.error(f"{self.NODE_ID} shutdown error: {e}")

            self._transition(CapsuleNodeState.STOPPED)
            self._state.update_phase(NodePhase.TERMINATED, "Terminated")
            self._logger.info(f"{self.NODE_ID} shutdown")

        return self

    def _shutdown_impl(self) -> None:
        """关闭实现 (子类可覆盖)"""
        pass

    def pause(self) -> "CapsuleNode":
        """暂停"""
        self._transition(CapsuleNodeState.PAUSED)
        return self

    def resume(self) -> "CapsuleNode":
        """恢复"""
        self._transition(CapsuleNodeState.IDLE)
        return self

    def reset(self) -> "CapsuleNode":
        """重置"""
        self._exec_count = 0
        self._error_count = 0
        self._total_exec_time = 0.0
        self._state.current_inputs.clear()
        self._state.current_outputs.clear()
        self._state.metrics.clear()
        return self

    # ─────────────────────────────────────────────────────────────────────
    # 验证
    # ─────────────────────────────────────────────────────────────────────

    def _validate_inputs(self, inputs: dict[str, Any]) -> ValidationResult:
        """验证输入"""
        result = ValidationResult(valid=True)

        for port in self.INPUT_PORTS:
            if port.required and port.name not in inputs:
                result.add_error(port.name, f"Required input missing: {port.name}")
                continue

            if port.name in inputs:
                self._validate_port_data(port, inputs[port.name], result)

        return result

    def _validate_outputs(self, outputs: dict[str, Any]) -> ValidationResult:
        """验证输出"""
        result = ValidationResult(valid=True)

        for port in self.OUTPUT_PORTS:
            if port.required and port.name not in outputs:
                result.add_error(port.name, f"Required output missing: {port.name}")
                continue

            if port.name in outputs:
                self._validate_port_data(port, outputs[port.name], result)

        return result

    def _validate_port_data(self, port: PortSchema, data: Any, result: ValidationResult) -> None:
        """验证端口数据"""
        # 检查必需字段
        for field in port.required_fields:
            if isinstance(data, dict) and field not in data:
                result.add_error(f"{port.name}.{field}", f"Required field missing: {field}", expected=field)

        # 检查枚举
        if port.enum_values and data not in port.enum_values:
            result.add_error(port.name, f"Value not in enum: {data}", value=data, expected=port.enum_values)

        # 检查约束
        for constraint_name, constraint_value in port.constraints.items():
            if constraint_name == "min" and isinstance(data, (int, float)):
                if data < constraint_value:
                    result.add_error(port.name, f"Value below minimum: {constraint_value}", value=data)
            elif constraint_name == "max" and isinstance(data, (int, float)):
                if data > constraint_value:
                    result.add_error(port.name, f"Value above maximum: {constraint_value}", value=data)

    def _validate_constraints(self, data: dict[str, Any]) -> ValidationResult:
        """验证约束"""
        result = ValidationResult(valid=True)

        for constraint in self.CONSTRAINTS:
            if constraint.name in data:
                value = data[constraint.name]

                if constraint.min_value is not None and isinstance(value, (int, float)):
                    if value < constraint.min_value:
                        result.add_error(constraint.name, f"Below minimum: {constraint.min_value}", value=value)

                if constraint.max_value is not None and isinstance(value, (int, float)):
                    if value > constraint.max_value:
                        result.add_error(constraint.name, f"Above maximum: {constraint.max_value}", value=value)

        return result

    # ─────────────────────────────────────────────────────────────────────
    # 内部方法
    # ─────────────────────────────────────────────────────────────────────

    def _transition(self, new_state: CapsuleNodeState) -> None:
        """状态转换"""
        old_state = self._capsule_state
        self._capsule_state = new_state
        self._state.update_state(new_state)
        self._state_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action": "state_change",
                "from": old_state.value,
                "to": new_state.value,
            }
        )
        self._logger.debug(f"{self.NODE_ID}: {old_state.value} -> {new_state.value}")

    def _record_error(self, error: Exception) -> None:
        """记录错误"""
        self._error_count += 1
        self._state_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action": "error",
                "error": str(error),
                "type": type(error).__name__,
            }
        )

    # ─────────────────────────────────────────────────────────────────────
    # 事件订阅
    # ─────────────────────────────────────────────────────────────────────

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """订阅事件"""
        if self._event_bus:
            self._event_bus.subscribe(event_type, handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """取消订阅"""
        if self._event_bus:
            self._event_bus.unsubscribe(event_type, handler)

    def publish(self, event_type: str, data: Any = None) -> None:
        """发布事件"""
        if self._event_bus:
            self._event_bus.publish(event_type, data)

    # ─────────────────────────────────────────────────────────────────────
    # 配置
    # ─────────────────────────────────────────────────────────────────────

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        if self._config:
            return self._config.get(key, default)
        return default

    def set_config(self, key: str, value: Any) -> None:
        """设置配置"""
        if self._config:
            self._config.set(key, value)

    # ─────────────────────────────────────────────────────────────────────
    # 健康检查
    # ─────────────────────────────────────────────────────────────────────

    def get_health(self) -> HealthStatus:
        """获取健康状态"""
        if self._capsule_state == CapsuleNodeState.ERROR:
            return HealthStatus.UNHEALTHY
        if self._capsule_state in (CapsuleNodeState.STOPPED, CapsuleNodeState.CREATED):
            return HealthStatus.UNKNOWN
        if self._error_count > 0:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY

    def get_health_details(self) -> dict[str, Any]:
        """获取健康详情"""
        return {
            "node_id": self.node_id,
            "state": self._capsule_state.value,
            "health": self.get_health().value,
            "metrics": self.metrics,
        }

    # ─────────────────────────────────────────────────────────────────────
    # 导出
    # ─────────────────────────────────────────────────────────────────────

    def export_state(self) -> dict[str, Any]:
        """导出完整状态 (AI 可读)"""
        return {
            "node": {
                "id": self.node_id,
                "name": self.node_name,
                "version": self.node_version,
            },
            "state": self._state.to_dict(),
            "metrics": self.metrics,
            "health": self.get_health().value,
            "schemas": {
                "inputs": {p.name: p.to_dict() for p in self.INPUT_PORTS},
                "outputs": {p.name: p.to_dict() for p in self.OUTPUT_PORTS},
                "constraints": {c.name: c.to_dict() for c in self.CONSTRAINTS},
            },
            "history": self._state_history[-50:],
        }

    def export_json(self) -> str:
        """导出 JSON (AI 可直接解析)"""
        return json.dumps(self.export_state(), indent=2, default=str)

    def __repr__(self) -> str:
        return f"<CapsuleNode {self.node_id} state={self._capsule_state.value}>"


# ═══════════════════════════════════════════════════════════════════════════════
# FractalCapsuleNode - 五阶段迭代增强
# ═══════════════════════════════════════════════════════════════════════════════


class FractalCapsuleNode(CapsuleNode):
    """
    FractalCapsuleNode - 五阶段迭代增强

    继承自 CapsuleNode，添加五阶段迭代支持。
    """

    def __init__(self, node_id: str | None = None):
        super().__init__(node_id)
        self._observe_report: dict | None = None
        self._design_contract: dict | None = None
        self._verify_result: dict | None = None
        self._iteration_count: int = 0

    # ─────────────────────────────────────────────────────────────────────
    # 五阶段实现
    # ─────────────────────────────────────────────────────────────────────

    def observe_phase(self) -> dict[str, Any]:
        """
        【看】观察阶段

        分析需求，返回结构化观察报告。
        """
        self._state.update_phase(NodePhase.OBSERVING_INPUTS, "Analyzing inputs")

        report = self._observe_phase_impl()
        self._observe_report = report
        self._state.update_phase(NodePhase.OBSERVATION_COMPLETE, "Observation complete")

        return report

    def _observe_phase_impl(self) -> dict[str, Any]:
        """
        观察阶段实现 (子类可覆盖)

        返回结构化观察报告，包含：
        - inputs: 输入分析
        - outputs: 输出分析
        - constraints: 约束分析
        - dependencies: 依赖分析
        - risks: 风险分析
        """
        return {
            "node_id": self.node_id,
            "phase": "observe",
            "timestamp": datetime.now().isoformat(),
            "inputs": {port.name: port.to_dict() for port in self.INPUT_PORTS},
            "outputs": {port.name: port.to_dict() for port in self.OUTPUT_PORTS},
            "constraints": {c.name: c.to_dict() for c in self.CONSTRAINTS},
            "dependencies": [],
            "risks": [],
        }

    def design_phase(self) -> dict[str, Any]:
        """
        【画】设计阶段

        定义接口契约，返回结构化设计合同。
        """
        self._state.update_phase(NodePhase.DESIGNING_INTERFACE, "Designing interface")

        contract = self._design_phase_impl()
        self._design_contract = contract
        self._state.update_phase(NodePhase.DESIGN_COMPLETE, "Design complete")

        return contract

    def _design_phase_impl(self) -> dict[str, Any]:
        """
        设计阶段实现 (子类可覆盖)
        """
        return {
            "node_id": self.node_id,
            "phase": "design",
            "timestamp": datetime.now().isoformat(),
            "public_api": [],
            "internal_structure": {},
            "event_contracts": {},
        }

    def implement_phase(self) -> None:
        """
        【填】实现阶段

        填充核心逻辑。
        """
        self._state.update_phase(NodePhase.PROCESSING, "Implementing")
        self._implement_phase_impl()

    def _implement_phase_impl(self) -> None:
        """实现阶段实现 (子类可覆盖)"""
        pass

    def verify_phase(self) -> dict[str, Any]:
        """
        【验】验证阶段

        验证实现是否正确。
        """
        self._state.update_phase(NodePhase.VALIDATING_OUTPUTS, "Verifying")

        result = {
            "node_id": self.node_id,
            "phase": "verify",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "input_schema_defined": len(self.INPUT_PORTS) > 0,
                "output_schema_defined": len(self.OUTPUT_PORTS) > 0,
                "constraints_defined": len(self.CONSTRAINTS) >= 0,
                "initialized": self.is_initialized,
            },
        }
        result["passed"] = all(result["checks"].values())

        self._verify_result = result
        return result

    def integrate_phase(self) -> None:
        """
        【连】集成阶段

        与上下游对接。
        """
        self._state.update_phase(NodePhase.INTEGRATING_UPSTREAM, "Integrating upstream")
        self._integrate_phase_impl()
        self._state.update_phase(NodePhase.INTEGRATION_COMPLETE, "Integration complete")

    def _integrate_phase_impl(self) -> None:
        """集成阶段实现 (子类可覆盖)"""
        pass

    def run_fractal_iteration(self) -> dict[str, Any]:
        """
        执行完整的五阶段迭代

        Returns:
            迭代结果
        """
        self._iteration_count += 1

        result = {
            "iteration": self._iteration_count,
            "node_id": self.node_id,
            "timestamp": datetime.now().isoformat(),
            "phases": {},
            "status": "success",
        }

        try:
            # 观察
            start = time.time()
            observe_report = self.observe_phase()
            result["phases"]["observe"] = {"report": observe_report, "duration_ms": (time.time() - start) * 1000}

            # 设计
            start = time.time()
            design_contract = self.design_phase()
            result["phases"]["design"] = {"contract": design_contract, "duration_ms": (time.time() - start) * 1000}

            # 实现
            start = time.time()
            self.implement_phase()
            result["phases"]["implement"] = {"status": "completed", "duration_ms": (time.time() - start) * 1000}

            # 验证
            start = time.time()
            verify_result = self.verify_phase()
            result["phases"]["verify"] = {"result": verify_result, "duration_ms": (time.time() - start) * 1000}

            # 集成
            start = time.time()
            self.integrate_phase()
            result["phases"]["integrate"] = {"status": "completed", "duration_ms": (time.time() - start) * 1000}

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self._logger.error(f"Iteration failed: {e}")

        return result

    # ─────────────────────────────────────────────────────────────────────
    # 属性
    # ─────────────────────────────────────────────────────────────────────

    @property
    def iteration_count(self) -> int:
        """迭代次数"""
        return self._iteration_count

    @property
    def observe_report(self) -> dict | None:
        """观察报告"""
        return self._observe_report

    @property
    def design_contract(self) -> dict | None:
        """设计合同"""
        return self._design_contract

    @property
    def verify_result(self) -> dict | None:
        """验证结果"""
        return self._verify_result

    def get_iteration_summary(self) -> dict[str, Any]:
        """获取迭代摘要"""
        return {
            "node_id": self.node_id,
            "iteration_count": self._iteration_count,
            "last_observe": self._observe_report,
            "last_design": self._design_contract,
            "last_verify": self._verify_result,
        }
