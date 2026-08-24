# Copyright 2026 NEMT Lab
"""
NEMT Memory System - Context Injector
=====================================
会话启动时的记忆注入器（READ Phase）

核心功能：
1. 在每次 Cursor 对话开始时自动运行
2. 从 Notion 和本地存储检索相关记忆
3. 生成结构化的上下文注入文本
4. 支持 RAG 语义检索（基于标签/关键词/时间）

检索策略：
- R1: 项目标签匹配（命中率高）
- R2: 时间衰减（最近 > 历史）
- R3: 失败经验优先（避免重复踩坑）
- R4: 关联决策优先（保持连贯性）

输出格式：
  ## [MEMORY] 最近相关决策 (2条)
  - [Decision] X | 结论: Y | 类型: Z
  - ...

  ## [MEMORY] 相关经验 (1条)
  - [Exp-S] XXX: YYY
  - ...

  ## [MEMORY] 需回顾决策 (1条)
  - [Decision] XXX | 结论: YYY | ⚠️ 需回顾
  - ...
"""

import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


# ============================================================================
# 检索结果
# ============================================================================

@dataclass
class MemoryEntry:
    """单条记忆条目"""
    source: str = ""      # "notion" / "local"
    record_type: str = ""  # "decision" / "experience" / "failure"
    id: str = ""
    title: str = ""
    relevance_score: float = 0.0
    summary: str = ""
    detail: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    url: str = ""

    def to_context_string(self, max_length: int = 400) -> str:
        """格式化为上下文注入字符串"""
        lines = []

        # Header
        type_icon = {"decision": "D", "experience": "E", "failure": "F"}
        icon = type_icon.get(self.record_type, "?")
        header = f"[{icon}] {self.title}"
        lines.append(header)

        # Summary
        if self.summary:
            summary_text = self.summary
            if len(summary_text) > max_length:
                summary_text = summary_text[:max_length] + "..."
            lines.append(f"  {summary_text}")

        # Key metadata
        meta_parts = []
        for key in ['status', 'type', 'decision_type', 'category']:
            if key in self.metadata and self.metadata[key]:
                meta_parts.append(f"{key}={self.metadata[key]}")

        # Tags
        if self.tags:
            meta_parts.append(f"标签: {', '.join(self.tags)}")

        if meta_parts:
            lines.append(f"  [{', '.join(meta_parts)}]")

        # URL
        if self.url:
            lines.append(f"  📎 {self.url}")

        # Detail preview
        if self.detail and self.detail != self.summary:
            detail_preview = self.detail[:200]
            if len(self.detail) > 200:
                detail_preview += "..."
            lines.append(f"  详情: {detail_preview}")

        return "\n".join(lines)


@dataclass
class ContextBundle:
    """一组检索结果（按类型分组）"""
    project_tag: str = ""
    agent_role: str = ""
    session_goal: str = ""
    recent_decisions: List[MemoryEntry] = field(default_factory=list)
    recent_experiences: List[MemoryEntry] = field(default_factory=list)
    active_failures: List[MemoryEntry] = field(default_factory=list)
    needs_review_decisions: List[MemoryEntry] = field(default_factory=list)
    total_entries: int = 0

    def is_empty(self) -> bool:
        return self.total_entries == 0

    def to_context_prompt(self) -> str:
        """格式化为完整的上下文提示"""
        if self.is_empty():
            return ""

        sections = []
        sections.append("--- MEMORY SYSTEM ---")
        sections.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')} MEMORY RETRIEVAL]")
        sections.append("")

        # Project context
        if self.project_tag:
            sections.append(f"**当前项目标签**: `{self.project_tag}`")
        if self.agent_role:
            sections.append(f"**当前角色**: {self.agent_role}")
        if self.session_goal:
            sections.append(f"**会话目标**: {self.session_goal}")
        sections.append("")

        # 需回顾的决策（最重要）
        if self.needs_review_decisions:
            sections.append(f"## ⚠️ 需回顾的决策 ({len(self.needs_review_decisions)}条)")
            for entry in self.needs_review_decisions[:5]:
                sections.append(f"- {entry.to_context_string()}")
            sections.append("")

        # 最近的决策
        if self.recent_decisions:
            sections.append(f"## 📋 最近相关决策 ({len(self.recent_decisions)}条)")
            for entry in self.recent_decisions[:5]:
                sections.append(f"- {entry.to_context_string()}")
            sections.append("")

        # 相关经验
        if self.recent_experiences:
            sections.append(f"## 💡 相关经验 ({len(self.recent_experiences)}条)")
            for entry in self.recent_experiences[:5]:
                sections.append(f"- {entry.to_context_string()}")
            sections.append("")

        # 活跃失败
        if self.active_failures:
            sections.append(f"## 🚨 活跃失败记录 ({len(self.active_failures)}条)")
            for entry in self.active_failures[:5]:
                sections.append(f"- {entry.to_context_string()}")
            sections.append("")

        sections.append("--- END MEMORY ---")
        return "\n".join(sections)


# ============================================================================
# 上下文注入器
# ============================================================================

class ContextInjector:
    """
    上下文注入器

    策略 R1-R4:
    - R1 (标签匹配): 基于项目标签精确匹配
    - R2 (时间衰减): 最近 7 天的记录权重更高
    - R3 (失败优先): 活跃失败记录权重最高
    - R4 (关联优先): 关联已有决策的经验权重更高

    使用方式：

    injector = ContextInjector()

    # 自动检测项目标签（从当前目录/文件推断）
    bundle = injector.inject(
        project_tag="frontend",    # 可选，自动推断
        agent_role="TechLead",     # 可选
        session_goal="实现验证层",  # 可选
        tags=["pipeline", "validation"],  # 精确匹配标签
    )

    # 生成注入文本
    context_text = bundle.to_context_prompt()

    # 直接打印（用于调试）
    bundle.print_summary()
    """

    def __init__(self, use_local_fallback: bool = True):
        self.use_local_fallback = use_local_fallback
        self._notion_client = None
        self._local_store = None

    @property
    def notion_client(self):
        if self._notion_client is None:
            try:
                from notion_query import get_notion_client
                self._notion_client = get_notion_client()
            except ImportError:
                self._notion_client = None
        return self._notion_client

    @property
    def local_store(self):
        if self._local_store is None:
            try:
                from local_fallback import get_local_store
                self._local_store = get_local_store()
            except ImportError:
                self._local_store = None
        return self._local_store

    def _infer_project_tag(self) -> Optional[str]:
        """从当前工作目录推断项目标签"""
        import os
        cwd = os.getcwd().lower()

        tag_map = {
            "web": "frontend",
            "frontend": "frontend",
            "nemt_signals": "core",
            "nemt_core": "core",
            "pipeline": "pipeline",
            "validation": "validation",
            "notion_sync": "notion",
            "nemt_os": "backend",
            "direction_4": "validation",
        }

        for key, tag in tag_map.items():
            if key in cwd:
                return tag
        return None

    def _time_decay_score(self, date_str: str, half_life_days: int = 14) -> float:
        """计算时间衰减分数"""
        if not date_str:
            return 0.5  # 无日期，默认中间值
        try:
            record_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if isinstance(record_date, str):
                record_date = datetime.fromisoformat(record_date)
            days_ago = (datetime.now() - record_date.replace(tzinfo=None)).days
            return 0.5 ** (days_ago / half_life_days)
        except Exception:
            return 0.5

    def _build_decision_entry(self, d, source: str) -> MemoryEntry:
        """从决策记录构建 MemoryEntry"""
        metadata = {
            "status": getattr(d, "status", ""),
            "decision_type": getattr(d, "decision_type", ""),
            "date": getattr(d, "date", ""),
            "created_by": getattr(d, "created_by", ""),
            "quality_score": getattr(d, "quality_score", ""),
            "needs_review": getattr(d, "needs_review", False),
        }
        return MemoryEntry(
            source=source,
            record_type="decision",
            id=getattr(d, "id", "") or getattr(d, "local_id", ""),
            title=getattr(d, "title", ""),
            summary=getattr(d, "conclusion", ""),
            detail=getattr(d, "reason", ""),
            tags=getattr(d, "tags", []) or getattr(d, "aligned_principles", []),
            metadata=metadata,
            url=getattr(d, "url", ""),
            relevance_score=0.5,
        )

    def _build_experience_entry(self, e, source: str) -> MemoryEntry:
        """从经验记录构建 MemoryEntry"""
        metadata = {
            "type": getattr(e, "type", ""),
            "usefulness_score": getattr(e, "usefulness_score", 3),
            "verified": getattr(e, "verified", False),
        }
        return MemoryEntry(
            source=source,
            record_type="experience",
            id=getattr(e, "id", "") or getattr(e, "local_id", ""),
            title=getattr(e, "title", ""),
            summary=getattr(e, "summary", ""),
            detail=getattr(e, "detail", ""),
            tags=getattr(e, "tags", []),
            metadata=metadata,
            url=getattr(e, "url", ""),
            relevance_score=0.5,
        )

    def _build_failure_entry(self, f, source: str) -> MemoryEntry:
        """从失败记录构建 MemoryEntry"""
        metadata = {
            "category": getattr(f, "category", ""),
            "status": getattr(f, "status", ""),
        }
        return MemoryEntry(
            source=source,
            record_type="failure",
            id=getattr(f, "id", "") or getattr(f, "local_id", ""),
            title=getattr(f, "title", ""),
            summary=getattr(f, "symptom", ""),
            detail=f"根因: {getattr(f, 'root_cause', '')}\n解决方案: {getattr(f, 'resolution', '')}",
            tags=getattr(f, "tags", []),
            metadata=metadata,
            url=getattr(f, "url", ""),
            relevance_score=0.5,
        )

    def inject(self,
              project_tag: Optional[str] = None,
              agent_role: Optional[str] = None,
              session_goal: Optional[str] = None,
              tags: Optional[List[str]] = None,
              limit: int = 5) -> ContextBundle:
        """
        执行记忆注入

        Args:
            project_tag: 项目标签（frontend/core/pipeline/validation/notion）
            agent_role: 当前 Agent 角色
            session_goal: 当前会话目标
            tags: 精确匹配标签
            limit: 每类最多返回条目数

        Returns:
            ContextBundle: 包含所有检索结果
        """
        bundle = ContextBundle(
            project_tag=project_tag or self._infer_project_tag() or "",
            agent_role=agent_role or "",
            session_goal=session_goal or "",
        )

        effective_tags = tags or [project_tag] if project_tag else []

        # ---- 1. 需回顾的决策（R3: 最重要，优先返回）----
        self._inject_needs_review_decisions(bundle, effective_tags, limit)

        # ---- 2. 最近相关决策（R1+R2）----
        self._inject_recent_decisions(bundle, effective_tags, limit)

        # ---- 3. 相关经验（R1+R4）----
        self._inject_recent_experiences(bundle, effective_tags, limit)

        # ---- 4. 活跃失败记录（R3: 避免重复踩坑）----
        self._inject_active_failures(bundle, effective_tags, limit)

        # 汇总
        bundle.total_entries = (
            len(bundle.recent_decisions) +
            len(bundle.recent_experiences) +
            len(bundle.active_failures) +
            len(bundle.needs_review_decisions)
        )

        return bundle

    def _inject_needs_review_decisions(self, bundle: ContextBundle,
                                      tags: List[str], limit: int):
        """R3: 注入需回顾的决策"""
        # Notion
        if self.notion_client and self.notion_client.is_available:
            try:
                decisions = self.notion_client.query_decisions(
                    needs_review=True, limit=limit
                )
                for d in decisions:
                    entry = self._build_decision_entry(d, "notion")
                    entry.metadata["needs_review"] = True
                    entry.relevance_score = 1.0  # 最高优先级
                    bundle.needs_review_decisions.append(entry)
            except Exception:
                pass

        # 本地回退
        if self.local_store and bundle.needs_review_decisions:
            pass  # 本地目前没有 needs_review 标记的决策

    def _inject_recent_decisions(self, bundle: ContextBundle,
                               tags: List[str], limit: int):
        """R1+R2: 注入最近相关决策"""
        # Notion
        if self.notion_client and self.notion_client.is_available:
            try:
                decisions = self.notion_client.query_decisions(
                    tags=tags if tags else None,
                    since_days=30,
                    limit=limit
                )
                for d in decisions:
                    entry = self._build_decision_entry(d, "notion")
                    # R2: 时间衰减
                    entry.relevance_score = self._time_decay_score(entry.metadata.get("date", ""))
                    bundle.recent_decisions.append(entry)
            except Exception:
                pass

        # 本地回退
        if self.local_store:
            try:
                local_decisions = self.local_store.get_recent_decisions(
                    since_days=30, limit=limit
                )
                for d in local_decisions:
                    entry = self._build_decision_entry(d, "local")
                    bundle.recent_decisions.append(entry)
            except Exception:
                pass

        # 去重（按标题）
        seen = set()
        unique = []
        for entry in bundle.recent_decisions:
            if entry.title not in seen:
                seen.add(entry.title)
                unique.append(entry)
        bundle.recent_decisions = unique[:limit]

    def _inject_recent_experiences(self, bundle: ContextBundle,
                                  tags: List[str], limit: int):
        """R1+R4: 注入相关经验"""
        # Notion
        if self.notion_client and self.notion_client.is_available:
            try:
                experiences = self.notion_client.query_experiences(
                    tags=tags if tags else None,
                    limit=limit
                )
                for e in experiences:
                    entry = self._build_experience_entry(e, "notion")
                    # R1: 标签匹配权重
                    if tags and any(t in entry.tags for t in tags):
                        entry.relevance_score = 0.9
                    bundle.recent_experiences.append(entry)
            except Exception:
                pass

        # 本地回退
        if self.local_store:
            try:
                local_exp = self.local_store.list_experiences(limit=limit)
                for e in local_exp:
                    entry = self._build_experience_entry(e, "local")
                    bundle.recent_experiences.append(entry)
            except Exception:
                pass

        # 去重
        seen = set()
        unique = []
        for entry in bundle.recent_experiences:
            if entry.title not in seen:
                seen.add(entry.title)
                unique.append(entry)
        bundle.recent_experiences = unique[:limit]

    def _inject_active_failures(self, bundle: ContextBundle,
                              tags: List[str], limit: int):
        """R3: 注入活跃失败记录"""
        # Notion
        if self.notion_client and self.notion_client.is_available:
            try:
                failures = self.notion_client.query_failures(
                    active_only=True, limit=limit
                )
                for f in failures:
                    entry = self._build_failure_entry(f, "notion")
                    entry.relevance_score = 0.95  # 高优先级
                    bundle.active_failures.append(entry)
            except Exception:
                pass

        # 本地回退
        if self.local_store:
            # 本地目前不支持 failure 查询，暂时跳过
            pass

    def inject_from_session_context(self) -> ContextBundle:
        """
        从当前会话环境自动推断上下文

        自动推断：
        - 项目标签：从 cwd 推断
        - Agent 角色：从 git 用户名推断（如果有）
        """
        import os
        cwd = os.getcwd()

        # 从目录名推断标签
        project_tag = self._infer_project_tag()

        return self.inject(
            project_tag=project_tag,
            tags=[project_tag] if project_tag else None,
        )

    def print_summary(self, bundle: ContextBundle):
        """打印摘要（用于调试）"""
        print(f"\n[Context Injector] Retrieved {bundle.total_entries} entries")
        print(f"  Project tag: {bundle.project_tag or '(auto-inferred)'}")
        print(f"  Decisions: {len(bundle.recent_decisions)}")
        print(f"  Experiences: {len(bundle.recent_experiences)}")
        print(f"  Failures: {len(bundle.active_failures)}")
        print(f"  Needs Review: {len(bundle.needs_review_decisions)}")

        if not bundle.is_empty():
            print("\n--- Context Preview ---")
            print(bundle.to_context_prompt())


# ============================================================================
# 单例
# ============================================================================

_context_injector: Optional[ContextInjector] = None


def get_context_injector() -> ContextInjector:
    global _context_injector
    if _context_injector is None:
        _context_injector = ContextInjector()
    return _context_injector


# ============================================================================
# CLI 测试
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("NEMT Context Injector - Test Run")
    print("=" * 60)

    injector = get_context_injector()
    bundle = injector.inject_from_session_context()
    injector.print_summary(bundle)
