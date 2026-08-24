"""
CapsuleNode - 胶囊节点融合基类

融合现有 Capsule 系统 + Node Schema 验证层 + AI 可读状态

核心公式：
  Capsule (事件驱动 + 五阶段迭代 + 健康检查)
      +
  Node Schema (验证 + AI 可读状态)
      =
  CapsuleNode (完整 AI-native 系统)
"""

from .base import (
    # 基类
    CapsuleNode,
    # 枚举
    CapsuleNodeState,
    ConstraintSchema,
    FractalCapsuleNode,
    HealthStatus,
    NodePhase,
    NodeState,
    # Schema
    PortSchema,
    # 注册表
    SchemaRegistry,
    # 验证
    ValidationError,
    ValidationResult,
    # 版本
    __version__,
)

__all__ = [
    # 版本
    "__version__",
    # 枚举
    "CapsuleNodeState",
    "HealthStatus",
    "NodePhase",
    # Schema
    "PortSchema",
    "ConstraintSchema",
    "NodeState",
    # 验证
    "ValidationError",
    "ValidationResult",
    # 注册表
    "SchemaRegistry",
    # 基类
    "CapsuleNode",
    "FractalCapsuleNode",
]
