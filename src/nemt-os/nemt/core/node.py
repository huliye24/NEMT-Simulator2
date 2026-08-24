"""
Node - 节点基类

基于 Schema 的节点实现。
每个节点都是一个"自描述单元"：
  - 代码 (执行)
  - 状态 (数据)
  - Schema (规则)

核心原则：
  State 解决"现在是什么"
  Schema 解决"什么是合法的现在"
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .node_schema import (
    NodeStatus,
    NodeType,
    validate_node,
    validate_port_data,
    validate_transition,
)


@dataclass
class Port:
    """端口定义"""

    name: str
    type: str
    required: bool = False
    schema: dict | None = None
    description: str = ""


@dataclass
class NodeMetadata:
    """节点元数据"""

    id: str
    name: str
    type: NodeType
    version: str = "1.0.0"
    description: str = ""
    module: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "version": self.version,
            "description": self.description,
            "module": self.module,
            "tags": self.tags,
        }


class Node(ABC):
    """
    节点基类

    所有节点必须继承此类。
    每个节点自带：
      - NODE: 元数据字典 (AI 可直接读取)
      - ports: 端口定义 (输入/输出)
      - state: 当前状态
      - validate(): Schema 验证
      - setup(): 初始化
      - exec(): 执行
      - shutdown(): 清理

    使用方式：

    class MarketNode(Node):
        NODE = {
            "id": "market_node",
            "name": "Market Data",
            "type": "source",
            ...
        }

        def exec(self, inputs):
            return {"ohlcv": {...}}

    # AI 可以直接读取
    print(MarketNode.NODE["status"])
    """

    # ─────────────────────────────────────────────────────────────
    # 必须定义 (子类覆盖)
    # ─────────────────────────────────────────────────────────────
    NODE: dict[str, Any] = {
        "id": "base_node",
        "name": "Base Node",
        "type": "processor",
        "version": "1.0.0",
        "status": "created",
    }

    # ─────────────────────────────────────────────────────────────
    # 端口定义
    # ─────────────────────────────────────────────────────────────
    INPUT_PORTS: list[Port] = []
    OUTPUT_PORTS: list[Port] = []

    # ─────────────────────────────────────────────────────────────
    # 内部状态
    # ─────────────────────────────────────────────────────────────
    _status: NodeStatus = NodeStatus.CREATED
    _state: dict[str, Any] = field(default_factory=dict)
    _logger: logging.Logger = field(default_factory=logging.getLogger)
    _history: list[dict] = field(default_factory=list)
    _errors: list[str] = field(default_factory=list)

    def __init__(self):
        self._status = NodeStatus.CREATED
        self._state = self.NODE.get("state", {}).copy()
        self._history = []
        self._logger = logging.getLogger(f"node.{self.NODE.get('id', 'unknown')}")
        self._errors = []

        # 验证 Schema
        if not validate_node(self.NODE):
            self._logger.warning(f"Node {self.NODE.get('id')} has invalid schema")

    # ─────────────────────────────────────────────────────────────
    # 属性
    # ─────────────────────────────────────────────────────────────
    @property
    def id(self) -> str:
        return self.NODE["id"]

    @property
    def name(self) -> str:
        return self.NODE["name"]

    @property
    def status(self) -> NodeStatus:
        return self._status

    @property
    def state(self) -> dict[str, Any]:
        return self._state.copy()

    @property
    def is_running(self) -> bool:
        return self._status == NodeStatus.RUNNING

    @property
    def is_error(self) -> bool:
        return self._status == NodeStatus.ERROR

    # ─────────────────────────────────────────────────────────────
    # 生命周期
    # ─────────────────────────────────────────────────────────────
    def setup(self) -> "Node":
        """
        初始化节点

        Returns:
            self (支持链式调用)
        """
        if not validate_transition(self._status, NodeStatus.INITIALIZED):
            raise RuntimeError(f"Cannot setup from {self._status.value}")

        self._transition(NodeStatus.INITIALIZED, "setup")
        self._logger.info(f"{self.id} initialized")
        return self

    @abstractmethod
    def exec(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        执行节点逻辑

        Args:
            inputs: 输入数据

        Returns:
            输出数据
        """
        pass

    def shutdown(self) -> "Node":
        """
        清理节点

        Returns:
            self (支持链式调用)
        """
        self._transition(NodeStatus.STOPPED, "shutdown")
        self._logger.info(f"{self.id} shutdown")
        return self

    def pause(self) -> "Node":
        """暂停"""
        self._transition(NodeStatus.PAUSED, "pause")
        return self

    def resume(self) -> "Node":
        """恢复"""
        self._transition(NodeStatus.IDLE, "resume")
        return self

    # ─────────────────────────────────────────────────────────────
    # 状态管理
    # ─────────────────────────────────────────────────────────────
    def update_state(self, key: str, value: Any) -> None:
        """
        更新状态

        Args:
            key: 状态键
            value: 新值
        """
        old_value = self._state.get(key)
        self._state[key] = value
        self._state["last_update"] = datetime.now().isoformat()

        self._history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action": "state_update",
                "key": key,
                "old_value": old_value,
                "new_value": value,
            }
        )

    def get_state(self, key: str, default: Any = None) -> Any:
        """获取状态"""
        return self._state.get(key, default)

    def reset_state(self) -> None:
        """重置状态"""
        self._state = self.NODE.get("state", {}).copy()
        self._state["last_update"] = datetime.now().isoformat()

    # ─────────────────────────────────────────────────────────────
    # 验证
    # ─────────────────────────────────────────────────────────────
    def validate_input(self, inputs: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        验证输入

        Args:
            inputs: 输入数据

        Returns:
            (是否合法, 错误列表)
        """
        errors = []

        # 检查必需端口
        for port in self.INPUT_PORTS:
            if port.required and port.name not in inputs:
                errors.append(f"Missing required input: {port.name}")

            # 验证端口数据 schema
            if port.name in inputs:
                valid, error = validate_port_data(port.type, inputs[port.name])
                if not valid:
                    errors.append(error)

        return len(errors) == 0, errors

    def validate_output(self, outputs: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        验证输出

        Args:
            outputs: 输出数据

        Returns:
            (是否合法, 错误列表)
        """
        errors = []

        for port in self.OUTPUT_PORTS:
            if port.name in outputs:
                valid, error = validate_port_data(port.type, outputs[port.name])
                if not valid:
                    errors.append(error)

        return len(errors) == 0, errors

    # ─────────────────────────────────────────────────────────────
    # 执行流程
    # ─────────────────────────────────────────────────────────────
    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        运行节点 (完整流程)

        Args:
            inputs: 输入数据

        Returns:
            输出数据
        """
        # 1. 验证输入
        valid, errors = self.validate_input(inputs)
        if not valid:
            self._transition(NodeStatus.ERROR, f"input validation failed: {errors}")
            raise ValueError(f"Input validation failed: {errors}")

        # 2. 切换到运行状态
        self._transition(NodeStatus.RUNNING, "run")

        try:
            # 3. 执行逻辑
            outputs = self.exec(inputs)

            # 4. 验证输出
            valid, errors = self.validate_output(outputs)
            if not valid:
                self._transition(NodeStatus.ERROR, f"output validation failed: {errors}")
                raise ValueError(f"Output validation failed: {errors}")

            # 5. 切换到空闲状态
            self._transition(NodeStatus.IDLE, "run completed")

            return outputs

        except Exception as e:
            self._errors.append(str(e))
            self._transition(NodeStatus.ERROR, str(e))
            raise

    # ─────────────────────────────────────────────────────────────
    # 内部方法
    # ─────────────────────────────────────────────────────────────
    def _transition(self, new_status: NodeStatus, reason: str = "") -> None:
        """状态转换"""
        old_status = self._status

        if not validate_transition(old_status, new_status):
            self._logger.warning(f"Invalid transition: {old_status.value} -> {new_status.value}")

        self._status = new_status
        self._state["last_update"] = datetime.now().isoformat()

        self._history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action": "status_change",
                "old_status": old_status.value,
                "new_status": new_status.value,
                "reason": reason,
            }
        )

        self._logger.debug(f"{self.id}: {old_status.value} -> {new_status.value} ({reason})")

    def _record_error(self, error: str) -> None:
        """记录错误"""
        self._errors.append(error)
        self._logger.error(f"{self.id}: {error}")

    # ─────────────────────────────────────────────────────────────
    # 导出
    # ─────────────────────────────────────────────────────────────
    def export(self) -> dict[str, Any]:
        """
        导出节点状态

        Returns:
            完整状态
        """
        return {
            "node": self.NODE,
            "status": self._status.value,
            "state": self._state,
            "history": self._history[-100:],
            "errors": self._errors[-10:],
        }

    def __repr__(self) -> str:
        return f"<Node {self.id} status={self._status.value}>"
