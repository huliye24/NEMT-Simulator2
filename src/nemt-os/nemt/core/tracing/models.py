"""
Tracing Models - 追溯数据模型

定义追溯系统的数据模型。

版本: v1.0.0
更新: 2026-04-27
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TraceLevel(Enum):
    """追溯级别"""

    BUSINESS = "business"  # 业务级追溯
    CODE = "code"  # 代码级追溯
    OPERATION = "operation"  # 操作级追溯


class OperationType(Enum):
    """操作类型"""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    READ = "read"
    EXECUTE = "execute"


@dataclass
class BusinessTrace:
    """业务追溯"""

    trace_id: str
    business_context: str  # 业务场景
    requirement_id: str  # 关联需求
    description: str

    # 关联
    code_locations: list[str] = field(default_factory=list)  # 代码位置
    test_cases: list[str] = field(default_factory=list)  # 测试用例
    documents: list[str] = field(default_factory=list)  # 文档

    # 元数据
    trace_level: TraceLevel = TraceLevel.BUSINESS
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CodeTrace:
    """代码追溯"""

    trace_id: str
    file_path: str
    class_name: str
    method_name: str

    # 关联
    business_contexts: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)

    # 代码信息
    line_number: int = 0
    code_snippet: str = ""

    # 变更历史
    change_history: list[dict] = field(default_factory=list)

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)


@dataclass
class OperationTrace:
    """操作追溯"""

    trace_id: str
    operation_type: OperationType
    entity_type: str
    entity_id: str

    # 操作详情
    operation_data: dict[str, Any] = field(default_factory=dict)
    before_state: dict[str, Any] | None = None
    after_state: dict[str, Any] | None = None

    # 上下文
    operator: str = ""  # 操作人
    session_id: str = ""
    request_id: str = ""

    # 关联
    business_trace_id: str | None = None
    code_trace_ids: list[str] = field(default_factory=list)

    # 元数据
    trace_level: TraceLevel = TraceLevel.OPERATION
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0
    result: str = "success"  # success, failure, partial


@dataclass
class TraceLink:
    """追溯链接"""

    link_id: str
    source_type: str  # business, code, operation
    source_id: str
    target_type: str
    target_id: str
    link_type: str  # implements, tests, documents, related_to

    # 链接强度
    strength: float = 1.0  # 0-1

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    verified: bool = False


@dataclass
class TraceSearchCriteria:
    """追溯搜索条件"""

    requirement_ids: list[str] = field(default_factory=list)
    file_paths: list[str] = field(default_factory=list)
    entity_types: list[str] = field(default_factory=list)
    trace_levels: list[TraceLevel] = field(default_factory=list)
    date_from: datetime | None = None
    date_to: datetime | None = None
    keywords: list[str] = field(default_factory=list)


@dataclass
class TraceabilityIndex:
    """追溯索引"""

    # 需求到代码的映射
    requirement_to_code: dict[str, list[str]] = field(default_factory=dict)  # req_id -> file_paths

    # 代码到需求的映射
    code_to_requirement: dict[str, list[str]] = field(default_factory=dict)  # file_path -> req_ids

    # 业务到测试的映射
    business_to_test: dict[str, list[str]] = field(default_factory=dict)  # business_id -> test_paths

    # 最后更新时间
    last_updated: datetime = field(default_factory=datetime.now)
