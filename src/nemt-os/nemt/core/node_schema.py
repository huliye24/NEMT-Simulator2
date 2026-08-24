"""
Node Schema - 节点模式定义

定义"什么是合法的节点"的规则。

三层架构：
  Schema (规则) → State (数据) → Prompt (语言)

核心原则：
  State 解决"现在是什么"
  Schema 解决"什么是合法的现在"
"""

from enum import Enum
from typing import Any

import jsonschema


class NodeType(Enum):
    """节点类型"""

    SOURCE = "source"  # 数据源节点
    PROCESSOR = "processor"  # 处理节点
    DECISION = "decision"  # 决策节点
    ACTION = "action"  # 执行节点
    MONITOR = "monitor"  # 监控节点


class NodeStatus(Enum):
    """节点状态"""

    CREATED = "created"
    INITIALIZED = "initialized"
    RUNNING = "running"
    IDLE = "idle"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


class Severity(Enum):
    """严重程度"""

    P0 = "P0"  # 阻塞
    P1 = "P1"  # 重要
    P2 = "P2"  # 改进
    P3 = "P3"  # 长期


# ═══════════════════════════════════════════════════════════════════════════════
# NODE SCHEMA - 定义合法节点的模板
# ═══════════════════════════════════════════════════════════════════════════════

NODE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Node",
    "description": "NEMT 节点模式 - 定义什么是合法的节点",
    "type": "object",
    "required": ["id", "name", "type", "version", "status"],
    "properties": {
        # ─────────────────────────────────────────────────────────────
        # 身份 (必须)
        # ─────────────────────────────────────────────────────────────
        "id": {"type": "string", "pattern": "^[a-z_][a-z0-9_]*$", "description": "节点唯一标识，snake_case"},
        "name": {"type": "string", "minLength": 1, "maxLength": 100, "description": "节点人类可读名称"},
        "type": {"type": "string", "enum": [t.value for t in NodeType], "description": "节点类型"},
        "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$", "description": "语义化版本"},
        "status": {"type": "string", "enum": [s.value for s in NodeStatus], "description": "当前状态"},
        # ─────────────────────────────────────────────────────────────
        # 描述 (可选)
        # ─────────────────────────────────────────────────────────────
        "description": {"type": "string", "maxLength": 500, "description": "节点功能描述"},
        "module": {"type": "string", "description": "所属模块路径"},
        "tags": {"type": "array", "items": {"type": "string"}, "description": "标签"},
        # ─────────────────────────────────────────────────────────────
        # 接口 (必须)
        # ─────────────────────────────────────────────────────────────
        "interface": {
            "type": "object",
            "required": ["inputs", "outputs"],
            "properties": {
                "inputs": {"type": "array", "minItems": 0, "items": {"$ref": "#/definitions/Port"}},
                "outputs": {"type": "array", "minItems": 0, "items": {"$ref": "#/definitions/Port"}},
            },
        },
        # ─────────────────────────────────────────────────────────────
        # 约束 (可选)
        # ─────────────────────────────────────────────────────────────
        "constraints": {
            "type": "object",
            "properties": {
                "immutable": {"type": "object", "description": "不可变约束"},
                "runtime": {"type": "object", "description": "运行时约束"},
                "validation": {"type": "array", "description": "验证规则"},
            },
        },
        # ─────────────────────────────────────────────────────────────
        # 状态 (必须)
        # ─────────────────────────────────────────────────────────────
        "state": {
            "type": "object",
            "required": ["phase"],
            "properties": {
                "phase": {"type": "string", "description": "当前阶段"},
                "data": {"type": "object", "description": "节点数据"},
                "metrics": {"type": "object", "description": "指标数据"},
                "last_update": {"type": "string", "format": "date-time", "description": "最后更新时间"},
            },
        },
        # ─────────────────────────────────────────────────────────────
        # 依赖 (可选)
        # ─────────────────────────────────────────────────────────────
        "dependencies": {
            "type": "object",
            "properties": {
                "upstream": {"type": "array", "items": {"type": "string"}},
                "downstream": {"type": "array", "items": {"type": "string"}},
            },
        },
        # ─────────────────────────────────────────────────────────────
        # 技术债 (可选)
        # ─────────────────────────────────────────────────────────────
        "debt": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "issue": {"type": "string"},
                "severity": {"type": "string", "enum": [s.value for s in Severity]},
                "constraint": {"type": "string"},
            },
        },
    },
    "definitions": {
        "Port": {
            "type": "object",
            "required": ["name", "type"],
            "properties": {
                "name": {"type": "string", "pattern": "^[a-z_][a-z0-9_]*$"},
                "type": {"type": "string", "description": "数据类型"},
                "required": {"type": "boolean", "default": False},
                "format": {"type": "string"},
                "description": {"type": "string"},
                "schema": {"type": "object", "description": "数据 schema"},
            },
        }
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# 输入/输出模式 - 常用数据类型
# ═══════════════════════════════════════════════════════════════════════════════

PORT_SCHEMAS = {
    # 市场数据
    "raw_feed": {
        "type": "object",
        "required": ["symbol", "price", "timestamp"],
        "properties": {
            "symbol": {"type": "string"},
            "price": {"type": "number"},
            "volume": {"type": "number"},
            "timestamp": {"type": "integer"},
        },
    },
    "ohlcv": {
        "type": "object",
        "required": ["symbol", "open", "high", "low", "close", "volume"],
        "properties": {
            "symbol": {"type": "string"},
            "timestamp": {"type": "integer"},
            "open": {"type": "number"},
            "high": {"type": "number"},
            "low": {"type": "number"},
            "close": {"type": "number"},
            "volume": {"type": "number"},
        },
    },
    # 信号
    "signal": {
        "type": "object",
        "required": ["signal_id", "direction", "confidence"],
        "properties": {
            "signal_id": {"type": "string"},
            "symbol": {"type": "string"},
            "direction": {"type": "string", "enum": ["LONG", "SHORT", "NEUTRAL"]},
            "signal_type": {"type": "string", "enum": ["ENTRY", "EXIT", "STOP_LOSS", "TAKE_PROFIT"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "timestamp": {"type": "integer"},
        },
    },
    # 订单
    "order": {
        "type": "object",
        "required": ["order_id", "direction", "size"],
        "properties": {
            "order_id": {"type": "string"},
            "symbol": {"type": "string"},
            "direction": {"type": "string", "enum": ["LONG", "SHORT"]},
            "order_type": {"type": "string", "enum": ["MARKET", "LIMIT", "STOP"]},
            "size": {"type": "number", "minimum": 0},
            "price": {"type": "number"},
            "stop_loss": {"type": "number"},
            "take_profit": {"type": "number"},
        },
    },
    # 执行结果
    "fill": {
        "type": "object",
        "required": ["order_id", "fill_id", "size", "fill_price"],
        "properties": {
            "order_id": {"type": "string"},
            "fill_id": {"type": "string"},
            "symbol": {"type": "string"},
            "size": {"type": "number"},
            "fill_price": {"type": "number"},
            "fees": {"type": "number"},
            "slippage": {"type": "number"},
            "timestamp": {"type": "integer"},
        },
    },
    # 持仓
    "portfolio": {
        "type": "object",
        "properties": {
            "total_value": {"type": "number"},
            "available_balance": {"type": "number"},
            "positions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "size": {"type": "number"},
                        "entry_price": {"type": "number"},
                        "current_price": {"type": "number"},
                    },
                },
            },
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# 约束模式
# ═══════════════════════════════════════════════════════════════════════════════

CONSTRAINT_SCHEMAS = {
    "max_lines": {"type": "integer", "minimum": 1, "description": "最大行数"},
    "max_latency_ms": {"type": "integer", "minimum": 0, "description": "最大延迟(毫秒)"},
    "min_confidence": {"type": "number", "minimum": 0, "maximum": 1, "description": "最小置信度"},
    "max_position_size": {"type": "number", "minimum": 0, "description": "最大仓位"},
    "max_drawdown": {"type": "number", "minimum": 0, "maximum": 1, "description": "最大回撤"},
    "required_fields": {"type": "array", "items": {"type": "string"}, "description": "必需字段"},
}


# ═══════════════════════════════════════════════════════════════════════════════
# 验证函数
# ═══════════════════════════════════════════════════════════════════════════════


def validate_node(node_data: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    验证节点数据是否符合 Schema

    Args:
        node_data: 节点数据

    Returns:
        (是否合法, 错误列表)
    """
    errors = []

    try:
        jsonschema.validate(node_data, NODE_SCHEMA)
        return True, []
    except jsonschema.exceptions.ValidationError as e:
        return False, [str(e.message)]
    except jsonschema.exceptions.SchemaError as e:
        return False, [f"Schema error: {e.message}"]


def validate_port_data(port_name: str, data: Any) -> tuple[bool, str | None]:
    """
    验证端口数据是否符合预期 schema

    Args:
        port_name: 端口名称
        data: 数据

    Returns:
        (是否合法, 错误信息)
    """
    if port_name in PORT_SCHEMAS:
        try:
            jsonschema.validate(data, PORT_SCHEMAS[port_name])
            return True, None
        except jsonschema.exceptions.ValidationError as e:
            return False, f"{port_name}: {e.message}"

    return True, None  # 没有预定义 schema，默认通过


def validate_transition(from_status: NodeStatus, to_status: NodeStatus) -> bool:
    """
    验证状态转换是否合法

    Args:
        from_status: 当前状态
        to_status: 目标状态

    Returns:
        是否合法
    """
    VALID_TRANSITIONS = {
        NodeStatus.CREATED: [NodeStatus.INITIALIZED],
        NodeStatus.INITIALIZED: [NodeStatus.RUNNING, NodeStatus.STOPPED],
        NodeStatus.RUNNING: [NodeStatus.IDLE, NodeStatus.ERROR, NodeStatus.STOPPED],
        NodeStatus.IDLE: [NodeStatus.RUNNING, NodeStatus.PAUSED, NodeStatus.STOPPED],
        NodeStatus.PAUSED: [NodeStatus.IDLE, NodeStatus.STOPPED],
        NodeStatus.ERROR: [NodeStatus.IDLE, NodeStatus.STOPPED],
        NodeStatus.STOPPED: [],
    }

    return to_status in VALID_TRANSITIONS.get(from_status, [])


# ═══════════════════════════════════════════════════════════════════════════════
# 导出
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    "NodeType",
    "NodeStatus",
    "Severity",
    "NODE_SCHEMA",
    "PORT_SCHEMAS",
    "CONSTRAINT_SCHEMAS",
    "validate_node",
    "validate_port_data",
    "validate_transition",
]
