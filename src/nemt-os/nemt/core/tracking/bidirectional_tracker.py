"""
Bidirectional Tracking System - 双向追溯系统

提供业务与代码的双向追踪能力：
- 需求追踪
- 代码变更关联
- 影响范围分析

版本: v1.0.0
更新: 2026-04-27
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TraceabilityType(Enum):
    """可追溯性类型"""

    REQUIREMENT = "requirement"  # 需求
    DESIGN = "design"  # 设计
    CODE = "code"  # 代码
    TEST = "test"  # 测试
    DOCUMENT = "document"  # 文档


@dataclass
class Requirement:
    """需求"""

    requirement_id: str
    title: str
    description: str
    priority: str = "medium"  # low, medium, high, critical
    status: str = "draft"  # draft, active, implemented, verified, closed

    # 关联
    parent_id: str | None = None
    child_ids: list[str] = field(default_factory=list)
    related_code: list[str] = field(default_factory=list)
    related_tests: list[str] = field(default_factory=list)
    related_docs: list[str] = field(default_factory=list)

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    implemented_at: datetime | None = None
    verified_at: datetime | None = None


@dataclass
class CodeChange:
    """代码变更"""

    change_id: str
    file_path: str
    change_type: str  # add, modify, delete, refactor
    requirement_ids: list[str] = field(default_factory=list)

    # 变更详情
    lines_added: int = 0
    lines_removed: int = 0
    description: str = ""

    # 元数据
    author: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    commit_hash: str = ""
    message: str = ""


@dataclass
class TraceLink:
    """追溯链接"""

    link_id: str
    source_type: TraceabilityType
    source_id: str
    target_type: TraceabilityType
    target_id: str
    link_type: str  # implements, tests, documents, related_to
    description: str = ""

    timestamp: datetime = field(default_factory=datetime.now)


class BidirectionalTracker:
    """
    双向追溯追踪器

    支持：
    - 需求到代码的追踪
    - 代码到需求的追踪
    - 影响范围分析
    """

    def __init__(self):
        self._requirements: dict[str, Requirement] = {}
        self._code_changes: dict[str, CodeChange] = {}
        self._trace_links: dict[str, TraceLink] = {}
        self._lock = threading.RLock()

        # 索引
        self._requirement_by_code: dict[str, list[str]] = {}  # code_path -> requirement_ids
        self._code_by_requirement: dict[str, list[str]] = {}  # requirement_id -> code_paths
        self._impact_cache: dict[str, set[str]] = {}  # requirement_id -> impacted_requirements

    # =============================================================================
    # Requirement Management
    # =============================================================================

    def add_requirement(
        self,
        title: str,
        description: str,
        requirement_id: str | None = None,
        parent_id: str | None = None,
        priority: str = "medium",
    ) -> Requirement:
        """添加需求"""
        with self._lock:
            req_id = requirement_id or f"REQ-{uuid.uuid4().hex[:8].upper()}"
            requirement = Requirement(
                requirement_id=req_id,
                title=title,
                description=description,
                priority=priority,
                parent_id=parent_id,
            )
            self._requirements[req_id] = requirement

            # 更新父子关系
            if parent_id and parent_id in self._requirements:
                if req_id not in self._requirements[parent_id].child_ids:
                    self._requirements[parent_id].child_ids.append(req_id)

            # 清除影响缓存
            self._impact_cache.clear()

            return requirement

    def update_requirement(self, requirement_id: str, **kwargs) -> Requirement | None:
        """更新需求"""
        with self._lock:
            if requirement_id not in self._requirements:
                return None

            req = self._requirements[requirement_id]
            for key, value in kwargs.items():
                if hasattr(req, key):
                    setattr(req, key, value)
            req.updated_at = datetime.now()

            # 清除影响缓存
            self._impact_cache.clear()

            return req

    def get_requirement(self, requirement_id: str) -> Requirement | None:
        """获取需求"""
        with self._lock:
            return self._requirements.get(requirement_id)

    def get_all_requirements(
        self,
        status: str | None = None,
        priority: str | None = None,
    ) -> list[Requirement]:
        """获取所有需求"""
        with self._lock:
            result = list(self._requirements.values())

            if status:
                result = [r for r in result if r.status == status]
            if priority:
                result = [r for r in result if r.priority == priority]

            return sorted(result, key=lambda r: r.created_at)

    def mark_requirement_implemented(
        self,
        requirement_id: str,
        code_path: str,
    ) -> bool:
        """标记需求已实现"""
        with self._lock:
            if requirement_id not in self._requirements:
                return False

            req = self._requirements[requirement_id]
            req.status = "implemented"
            req.implemented_at = datetime.now()

            # 建立关联
            if code_path not in req.related_code:
                req.related_code.append(code_path)

            # 更新索引
            if code_path not in self._requirement_by_code:
                self._requirement_by_code[code_path] = []
            if requirement_id not in self._requirement_by_code[code_path]:
                self._requirement_by_code[code_path].append(requirement_id)

            if requirement_id not in self._code_by_requirement:
                self._code_by_requirement[requirement_id] = []
            if code_path not in self._code_by_requirement[requirement_id]:
                self._code_by_requirement[requirement_id].append(code_path)

            return True

    def mark_requirement_verified(self, requirement_id: str) -> bool:
        """标记需求已验证"""
        with self._lock:
            if requirement_id not in self._requirements:
                return False

            req = self._requirements[requirement_id]
            req.status = "verified"
            req.verified_at = datetime.now()
            return True

    # =============================================================================
    # Code Change Management
    # =============================================================================

    def record_code_change(
        self,
        file_path: str,
        change_type: str,
        requirement_ids: list[str],
        author: str = "",
        message: str = "",
    ) -> CodeChange:
        """记录代码变更"""
        with self._lock:
            change_id = f"CHG-{uuid.uuid4().hex[:8].upper()}"
            change = CodeChange(
                change_id=change_id,
                file_path=file_path,
                change_type=change_type,
                requirement_ids=requirement_ids,
                author=author,
                message=message,
            )
            self._code_changes[change_id] = change

            # 建立双向关联
            for req_id in requirement_ids:
                self.mark_requirement_implemented(req_id, file_path)

            return change

    def get_code_changes(self, requirement_id: str) -> list[CodeChange]:
        """获取需求关联的代码变更"""
        with self._lock:
            return [c for c in self._code_changes.values() if requirement_id in c.requirement_ids]

    def get_requirements_by_code(self, code_path: str) -> list[Requirement]:
        """根据代码获取关联需求"""
        with self._lock:
            req_ids = self._requirement_by_code.get(code_path, [])
            return [self._requirements[r] for r in req_ids if r in self._requirements]

    # =============================================================================
    # Impact Analysis
    # =============================================================================

    def get_impacted_requirements(
        self,
        requirement_id: str,
        depth: int = 3,
    ) -> set[str]:
        """
        获取受影响的同级需求

        Args:
            requirement_id: 需求 ID
            depth: 追溯深度

        Returns:
            受影响的需求 ID 集合
        """
        with self._lock:
            # 检查缓存
            cache_key = f"{requirement_id}:{depth}"
            if cache_key in self._impact_cache:
                return self._impact_cache[cache_key]

            impacted: set[str] = set()
            self._traverse_impact(requirement_id, impacted, depth)

            self._impact_cache[cache_key] = impacted
            return impacted

    def _traverse_impact(
        self,
        requirement_id: str,
        impacted: set[str],
        remaining_depth: int,
    ) -> None:
        """递归追溯影响"""
        if remaining_depth <= 0:
            return

        if requirement_id not in self._requirements:
            return

        req = self._requirements[requirement_id]

        # 追溯兄弟节点
        if req.parent_id:
            parent = self._requirements.get(req.parent_id)
            if parent:
                for child_id in parent.child_ids:
                    if child_id != requirement_id:
                        impacted.add(child_id)
                        self._traverse_impact(child_id, impacted, remaining_depth - 1)

        # 追溯关联需求
        for code_path in req.related_code:
            for related_req_id in self._requirement_by_code.get(code_path, []):
                if related_req_id != requirement_id:
                    impacted.add(related_req_id)

    def analyze_change_impact(
        self,
        file_path: str,
    ) -> dict[str, Any]:
        """
        分析代码变更的影响范围

        Args:
            file_path: 文件路径

        Returns:
            影响分析报告
        """
        with self._lock:
            # 获取关联需求
            related_reqs = self.get_requirements_by_code(file_path)

            # 获取受影响的需求
            impacted_reqs = set()
            for req in related_reqs:
                impacted_reqs.update(self.get_impacted_requirements(req.requirement_id))

            return {
                "file_path": file_path,
                "directly_affected_requirements": [r.requirement_id for r in related_reqs],
                "total_impacted_requirements": len(impacted_reqs),
                "impacted_requirement_ids": list(impacted_reqs),
                "recommended_reviewers": self._get_relevant_reviewers(impacted_reqs),
            }

    def _get_relevant_reviewers(self, requirement_ids: set[str]) -> list[str]:
        """获取相关评审者"""
        reviewers = set()
        for req_id in requirement_ids:
            for change in self.get_code_changes(req_id):
                if change.author:
                    reviewers.add(change.author)
        return list(reviewers)

    # =============================================================================
    # Traceability Reports
    # =============================================================================

    def generate_traceability_matrix(self) -> list[dict[str, Any]]:
        """
        生成追溯矩阵

        Returns:
            追溯矩阵数据
        """
        with self._lock:
            matrix = []

            for req_id, req in self._requirements.items():
                row = {
                    "requirement_id": req_id,
                    "title": req.title,
                    "priority": req.priority,
                    "status": req.status,
                    "implemented": len(req.related_code) > 0,
                    "tested": len(req.related_tests) > 0,
                    "documented": len(req.related_docs) > 0,
                    "code_paths": req.related_code,
                    "test_paths": req.related_tests,
                    "doc_paths": req.related_docs,
                }
                matrix.append(row)

            return sorted(matrix, key=lambda x: (x["priority"], x["requirement_id"]))

    def get_implementation_coverage(self) -> dict[str, Any]:
        """
        获取实现覆盖率

        Returns:
            覆盖率统计
        """
        with self._lock:
            total = len(self._requirements)
            if total == 0:
                return {"total": 0, "implemented": 0, "verified": 0, "coverage": 0}

            implemented = sum(1 for r in self._requirements.values() if r.status in ["implemented", "verified"])
            verified = sum(1 for r in self._requirements.values() if r.status == "verified")

            return {
                "total": total,
                "implemented": implemented,
                "verified": verified,
                "coverage": implemented / total if total > 0 else 0,
                "verification_coverage": verified / implemented if implemented > 0 else 0,
            }

    # =============================================================================
    # Export
    # =============================================================================

    def export(self) -> dict[str, Any]:
        """导出所有追踪数据"""
        with self._lock:
            return {
                "requirements": {k: v.__dict__ for k, v in self._requirements.items()},
                "code_changes": {k: v.__dict__ for k, v in self._code_changes.items()},
                "trace_links": {k: v.__dict__ for k, v in self._trace_links.items()},
                "exported_at": datetime.now().isoformat(),
            }

    def import_(self, data: dict[str, Any]) -> None:
        """导入追踪数据"""
        with self._lock:
            # 导入需求
            for req_id, req_data in data.get("requirements", {}).items():
                self._requirements[req_id] = Requirement(**req_data)

            # 重建索引
            for req_id, req in self._requirements.items():
                for code_path in req.related_code:
                    if code_path not in self._requirement_by_code:
                        self._requirement_by_code[code_path] = []
                    self._requirement_by_code[code_path].append(req_id)


# =============================================================================
# Global Tracker Instance
# =============================================================================

_global_tracker: BidirectionalTracker | None = None


def get_tracker() -> BidirectionalTracker:
    """获取全局追踪器"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = BidirectionalTracker()
    return _global_tracker
