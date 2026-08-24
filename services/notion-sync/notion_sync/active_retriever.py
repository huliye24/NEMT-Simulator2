# Copyright 2026 NEMT Lab
"""
NEMT Memory System - Active Retriever & Checkpoint
================================================
主动检索（R1-R4）和质量控制 + Checkpoint 生成器

R1 (标签匹配): 基于项目标签精确匹配相关记录
R2 (时间衰减): 最近 30 天的记录权重更高
R3 (失败优先): 活跃失败记录权重最高（避免重复踩坑）
R4 (关联决策): 关联已有决策的经验权重更高

Checkpoint 生成器：
- 会话结束时生成结构化摘要
- 自动检测是否有重要决策/经验/失败未记录
- 标记"需回顾"的决策
- 输出可追加到 Obsidian 的格式
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================================
# 检索器
# ============================================================================

class ActiveRetriever:
    """
    主动检索器

    在特定时机主动检索相关记忆，而不是被动等待。

    使用方式：
        retriever = ActiveRetriever()

        # R1: 当用户提到某个标签时
        results = retriever.retrieve_by_tag("validation")

        # R2: 获取本周新增的记录
        results = retriever.retrieve_recent(days=7)

        # R3: 获取所有活跃失败
        results = retriever.retrieve_active_failures()

        # R4: 获取与某决策关联的经验
        results = retriever.retrieve_related_experiences("decision_id_xxx")

        # 综合检索
        results = retriever.smart_retrieve(
            project_tag="pipeline",
            active_failures_only=False,
            limit=10,
        )
    """

    def __init__(self):
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

    def _score_and_sort(self,
                       items: List[Any],
                       project_tag: Optional[str] = None,
                       days: int = 30,
                       failure_boost: bool = True) -> List[Tuple[Any, float]]:
        """对检索结果打分和排序"""
        scored = []
        cutoff = datetime.now() - timedelta(days=days)

        for item in items:
            score = 0.5  # 基础分

            # R2: 时间衰减
            date_str = getattr(item, "date", "") or getattr(item, "created_at", "")
            if date_str:
                try:
                    record_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    days_ago = (datetime.now() - record_date.replace(tzinfo=None)).days
                    score *= 0.5 ** (days_ago / 14)  # 半衰期14天
                except Exception:
                    pass

            # R1: 标签匹配
            item_tags = getattr(item, "tags", []) or []
            if project_tag and project_tag in item_tags:
                score *= 1.5

            # R3: 失败优先
            if failure_boost and getattr(item, "status", "") == "active":
                if hasattr(item, "category") or "failure" in str(type(item)).lower():
                    score *= 2.0

            scored.append((item, score))

        # 排序
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def retrieve_by_tag(self, tag: str, record_type: str = "all", limit: int = 10) -> List[Any]:
        """R1: 按标签检索"""
        results = []

        # Notion
        if self.notion_client and self.notion_client.is_available:
            if record_type in ("all", "decision"):
                decisions = self.notion_client.query_decisions(tags=[tag], limit=limit)
                results.extend(decisions)
            if record_type in ("all", "experience"):
                experiences = self.notion_client.query_experiences(tags=[tag], limit=limit)
                results.extend(experiences)
            if record_type in ("all", "failure"):
                failures = self.notion_client.query_failures(category=tag, limit=limit)
                results.extend(failures)

        # 本地
        if self.local_store:
            if record_type in ("all", "decision"):
                decisions = self.local_store.list_decisions(tag_filter=tag, limit=limit)
                results.extend(decisions)

        return results[:limit]

    def retrieve_recent(self,
                      record_type: str = "all",
                      days: int = 7,
                      limit: int = 10) -> List[Any]:
        """R2: 检索最近的记录"""
        results = []

        if self.notion_client and self.notion_client.is_available:
            if record_type in ("all", "decision"):
                decisions = self.notion_client.query_decisions(since_days=days, limit=limit)
                results.extend(decisions)

        if self.local_store:
            if record_type in ("all", "decision"):
                decisions = self.local_store.get_recent_decisions(since_days=days, limit=limit)
                results.extend(decisions)

        # 排序
        scored = self._score_and_sort(results, days=days, failure_boost=False)
        return [item for item, _ in scored[:limit]]

    def retrieve_active_failures(self, limit: int = 5) -> List[Any]:
        """R3: 检索活跃失败记录"""
        results = []

        if self.notion_client and self.notion_client.is_available:
            failures = self.notion_client.query_failures(active_only=True, limit=limit)
            results.extend(failures)

        return results[:limit]

    def retrieve_related_experiences(self,
                                   decision_id: str,
                                   limit: int = 5) -> List[Any]:
        """R4: 检索与某决策关联的经验"""
        results = []

        if self.notion_client and self.notion_client.is_available:
            experiences = self.notion_client.query_experiences(limit=20)
            for e in experiences:
                related = getattr(e, "related_decisions", []) or []
                if decision_id in related:
                    results.append(e)

        if self.local_store:
            experiences = self.local_store.list_experiences(limit=20)
            for e in experiences:
                related = getattr(e, "related_decisions", []) or []
                if decision_id in related:
                    results.append(e)

        return results[:limit]

    def smart_retrieve(self,
                     project_tag: Optional[str] = None,
                     active_failures_only: bool = False,
                     days: int = 30,
                     limit: int = 10) -> Dict[str, List[Any]]:
        """
        智能综合检索

        Returns:
            {
                "active_failures": [...],   # R3: 最优先
                "recent_decisions": [...],  # R2
                "tagged_records": [...],     # R1
            }
        """
        result = {
            "active_failures": [],
            "recent_decisions": [],
            "tagged_records": [],
        }

        # R3: 活跃失败
        result["active_failures"] = self.retrieve_active_failures(limit=min(limit, 5))

        # R2: 最近决策
        result["recent_decisions"] = self.retrieve_recent(
            record_type="decision",
            days=days,
            limit=min(limit, 5)
        )

        # R1: 标签匹配
        if project_tag:
            result["tagged_records"] = self.retrieve_by_tag(
                project_tag,
                limit=min(limit, 5)
            )

        return result

    def retrieve_needs_review(self, limit: int = 10) -> List[Any]:
        """检索所有标记为"需回顾"的决策"""
        results = []

        if self.notion_client and self.notion_client.is_available:
            decisions = self.notion_client.query_decisions(needs_review=True, limit=limit)
            results.extend(decisions)

        return results[:limit]


# ============================================================================
# 质量控制
# ============================================================================

@dataclass
class QualityGate:
    """质量门槛检查结果"""
    passed: bool
    score: float           # 0.0-1.0
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class QualityController:
    """
    质量控制

    在写入前检查记录质量。

    质量维度：
    - Completeness: 是否填写了必填字段
    - Specificity: 是否包含足够的细节
    - Uniqueness: 是否与已有记录重复
    - Relevance: 是否与当前项目相关
    """

    MIN_TITLE_LENGTH = 5
    MAX_TITLE_LENGTH = 100
    MIN_BODY_LENGTH = 20
    REQUIRED_FIELDS_DECISION = ["title", "conclusion"]

    def check_decision(self, title: str, conclusion: str, reason: str,
                     decision_type: str = "", tags: Optional[List[str]] = None) -> QualityGate:
        """检查决策记录质量"""
        issues = []
        suggestions = []
        score = 1.0

        # Completeness
        if not title or len(title) < self.MIN_TITLE_LENGTH:
            issues.append(f"标题太短（< {self.MIN_TITLE_LENGTH} 字符）")
            score -= 0.3

        if len(title) > self.MAX_TITLE_LENGTH:
            issues.append(f"标题太长（> {self.MAX_TITLE_LENGTH} 字符）")
            score -= 0.1

        if not conclusion:
            issues.append("缺少结论字段")
            score -= 0.3

        # Specificity
        if conclusion and len(conclusion) < 10:
            issues.append("结论内容太短，缺乏细节")
            score -= 0.15

        if reason and len(reason) < 20:
            suggestions.append("理由字段可以更详细一些")
            score -= 0.1

        if not decision_type:
            suggestions.append("建议填写决策类型（architecture/technical/priority）")

        if not tags:
            suggestions.append("建议添加标签以便检索")

        # 特殊检查
        generic_titles = ["test", "测试", "todo", "fix", "bug", "问题"]
        if title.lower() in generic_titles:
            issues.append("标题过于泛化，建议更具体")
            score -= 0.2

        score = max(0.0, min(1.0, score))

        return QualityGate(
            passed=len(issues) == 0 and score >= 0.6,
            score=score,
            issues=issues,
            suggestions=suggestions,
        )

    def check_experience(self, title: str, summary: str, detail: str = "",
                       exp_type: str = "", tags: Optional[List[str]] = None) -> QualityGate:
        """检查经验记录质量"""
        issues = []
        suggestions = []
        score = 1.0

        if not title or len(title) < 5:
            issues.append("标题太短")
            score -= 0.3

        if not summary:
            issues.append("缺少摘要字段")
            score -= 0.3

        if summary and len(summary) < 10:
            issues.append("摘要太短")
            score -= 0.2

        if not exp_type:
            suggestions.append("建议填写类型（solution/mistake/diagnostic）")

        if not tags:
            suggestions.append("建议添加标签")

        score = max(0.0, min(1.0, score))

        return QualityGate(
            passed=len(issues) == 0 and score >= 0.5,
            score=score,
            issues=issues,
            suggestions=suggestions,
        )


# ============================================================================
# Checkpoint 生成器
# ============================================================================

@dataclass
class CheckpointSession:
    """会话 Checkpoint"""
    session_id: str = ""
    session_start: str = ""
    session_end: str = ""
    duration_minutes: int = 0
    agent_role: str = ""
    project_tag: str = ""
    messages_count: int = 0

    decisions_recorded: List[Dict[str, Any]] = field(default_factory=list)
    experiences_recorded: List[Dict[str, Any]] = field(default_factory=list)
    failures_recorded: List[Dict[str, Any]] = field(default_factory=list)

    decisions_detected_not_recorded: List[Dict[str, Any]] = field(default_factory=list)
    experiences_detected_not_recorded: List[Dict[str, Any]] = field(default_factory=list)

    needs_review_decisions: List[str] = field(default_factory=list)
    new_questions: List[str] = field(default_factory=list)

    summary: str = ""
    next_steps: List[str] = field(default_factory=list)


class CheckpointGenerator:
    """
    Checkpoint 生成器

    会话结束时自动调用，生成结构化的会话摘要。

    使用方式：
        checkpoint = CheckpointGenerator()

        session = checkpoint.create_session(
            session_id="session_xxx",
            messages=["message1", "message2", ...],
            agent_role="TechLead",
        )

        # 追加记录
        checkpoint.add_record(session, "decision", {
            "title": "...",
            "notion_id": "...",
            "local_id": "...",
        })

        # 生成输出
        output = checkpoint.generate(session)
        print(output)
    """

    def __init__(self):
        self._current_session: Optional[CheckpointSession] = None

    def create_session(self,
                      session_id: str,
                      session_start: Optional[str] = None,
                      agent_role: str = "",
                      project_tag: str = "") -> CheckpointSession:
        """创建新会话"""
        self._current_session = CheckpointSession(
            session_id=session_id,
            session_start=session_start or datetime.now().isoformat(),
            agent_role=agent_role,
            project_tag=project_tag,
        )
        return self._current_session

    def add_record(self,
                  session: CheckpointSession,
                  record_type: str,
                  record_data: Dict[str, Any]):
        """追加已记录的条目"""
        record_entry = {
            "title": record_data.get("title", ""),
            "id": record_data.get("notion_id", "") or record_data.get("local_id", ""),
            "type": record_type,
        }

        if record_type == "decision":
            session.decisions_recorded.append(record_entry)
        elif record_type == "experience":
            session.experiences_recorded.append(record_entry)
        elif record_type == "failure":
            session.failures_recorded.append(record_entry)

    def add_unrecorded_detection(self,
                                session: CheckpointSession,
                                record_type: str,
                                title: str,
                                confidence: float):
        """追加检测到但未记录的条目"""
        entry = {"title": title, "confidence": confidence}

        if record_type == "decision":
            session.decisions_detected_not_recorded.append(entry)
        elif record_type == "experience":
            session.experiences_detected_not_recorded.append(entry)

    def set_needs_review(self, session: CheckpointSession, decision_titles: List[str]):
        """设置需回顾的决策"""
        session.needs_review_decisions = decision_titles

    def generate(self, session: CheckpointSession) -> str:
        """生成 Checkpoint 报告"""
        lines = []

        # Header
        lines.append("=" * 60)
        lines.append(f"CHECKPOINT REPORT - {session.session_id}")
        lines.append("=" * 60)
        lines.append("")

        # Session info
        lines.append(f"**时间**: {session.session_start} → {datetime.now().isoformat()}")
        if session.agent_role:
            lines.append(f"**角色**: {session.agent_role}")
        if session.project_tag:
            lines.append(f"**项目标签**: {session.project_tag}")
        lines.append(f"**消息数**: {session.messages_count}")
        lines.append("")

        # 已记录的决策
        if session.decisions_recorded:
            lines.append(f"## 📋 已记录的决策 ({len(session.decisions_recorded)}条)")
            for d in session.decisions_recorded:
                lines.append(f"  - [{d['title']}]({d['id']})")
            lines.append("")

        # 已记录的经验
        if session.experiences_recorded:
            lines.append(f"## 💡 已记录的经验 ({len(session.experiences_recorded)}条)")
            for e in session.experiences_recorded:
                lines.append(f"  - [{e['title']}]({e['id']})")
            lines.append("")

        # 已记录的失败
        if session.failures_recorded:
            lines.append(f"## 🚨 已记录的失败 ({len(session.failures_recorded)}条)")
            for f in session.failures_recorded:
                lines.append(f"  - [{f['title']}]({f['id']})")
            lines.append("")

        # 检测到但未记录的
        if session.decisions_detected_not_recorded:
            lines.append(f"## ⚠️ 检测到但未记录的决策 ({len(session.decisions_detected_not_recorded)}条)")
            for d in session.decisions_detected_not_recorded:
                lines.append(f"  - {d['title']} (置信度: {d['confidence']:.0%})")
            lines.append("  建议: 如果重要，请手动记录")
            lines.append("")

        if session.experiences_detected_not_recorded:
            lines.append(f"## ⚠️ 检测到但未记录的经验 ({len(session.experiences_detected_not_recorded)}条)")
            for e in session.experiences_detected_not_recorded:
                lines.append(f"  - {e['title']} (置信度: {e['confidence']:.0%})")
            lines.append("")

        # 需回顾的决策
        if session.needs_review_decisions:
            lines.append(f"## 🔔 需回顾的决策 ({len(session.needs_review_decisions)}条)")
            for title in session.needs_review_decisions:
                lines.append(f"  - {title}")
            lines.append("")

        # 统计摘要
        total_recorded = (
            len(session.decisions_recorded) +
            len(session.experiences_recorded) +
            len(session.failures_recorded)
        )
        total_detected = (
            len(session.decisions_detected_not_recorded) +
            len(session.experiences_detected_not_recorded)
        )

        lines.append("---")
        lines.append(f"**摘要**: 本次会话记录了 {total_recorded} 条，"
                    f"检测到 {total_detected} 条潜在重要内容")
        if total_detected > 0:
            lines.append("**注意**: 有未记录的内容，建议回顾")
        lines.append("")
        lines.append(f"Generated: {datetime.now().isoformat()}")

        return "\n".join(lines)

    def generate_obsidian_format(self, session: CheckpointSession) -> str:
        """生成 Obsidian 格式的 Markdown"""
        lines = []

        # Frontmatter
        date_str = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H:%M:%S")
        lines.append("---")
        lines.append(f"type: checkpoint")
        lines.append(f"date: {date_str}")
        lines.append(f"time: {time_str}")
        lines.append(f"session_id: {session.session_id}")
        if session.agent_role:
            lines.append(f"agent_role: {session.agent_role}")
        if session.project_tag:
            lines.append(f"project_tag: {session.project_tag}")
        lines.append(f"messages_count: {session.messages_count}")
        lines.append(f"decisions_count: {len(session.decisions_recorded)}")
        lines.append(f"experiences_count: {len(session.experiences_recorded)}")
        lines.append(f"failures_count: {len(session.failures_recorded)}")
        lines.append("---")
        lines.append("")

        # Content
        lines.append(f"# Checkpoint - {date_str} {time_str}")
        lines.append("")

        # Stats
        total = (len(session.decisions_recorded) +
                len(session.experiences_recorded) +
                len(session.failures_recorded))
        lines.append(f"本次会话共记录 **{total}** 条记忆。")
        lines.append("")

        if session.decisions_recorded:
            lines.append("## 决策")
            for d in session.decisions_recorded:
                lines.append(f"- [[Decision#{d['title']}]]")
            lines.append("")

        if session.experiences_recorded:
            lines.append("## 经验")
            for e in session.experiences_recorded:
                lines.append(f"- [[Experience#{e['title']}]]")
            lines.append("")

        if session.failures_recorded:
            lines.append("## 失败记录")
            for f in session.failures_recorded:
                lines.append(f"- [[Failure#{f['title']}]]")
            lines.append("")

        if session.needs_review_decisions:
            lines.append("## 需回顾")
            lines.append("> [!WARNING]")
            for title in session.needs_review_decisions:
                lines.append(f"> - [[Decision#{title}]]")
            lines.append("")

        if session.next_steps:
            lines.append("## 下一步")
            for step in session.next_steps:
                lines.append(f"- [ ] {step}")
            lines.append("")

        return "\n".join(lines)


# ============================================================================
# CLI 测试
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("NEMT Active Retriever & Checkpoint Test")
    print("=" * 60)

    # 测试检索器
    print("\n[ActiveRetriever]")
    retriever = ActiveRetriever()
    recent = retriever.retrieve_recent(days=7, limit=5)
    print(f"  Recent decisions: {len(recent)}")
    for r in recent[:3]:
        print(f"    - {getattr(r, 'title', 'N/A')}")

    # 测试质量控制
    print("\n[QualityController]")
    qc = QualityController()
    gate = qc.check_decision(
        title="集成验证层",
        conclusion="方案A更好",
        reason="因为验证应与分析同步",
        decision_type="architecture",
        tags=["pipeline"],
    )
    print(f"  Score: {gate.score:.1%}, Passed: {gate.passed}")
    if gate.issues:
        print(f"  Issues: {', '.join(gate.issues)}")
    if gate.suggestions:
        print(f"  Suggestions: {', '.join(gate.suggestions)}")

    # 测试 Checkpoint
    print("\n[CheckpointGenerator]")
    cg = CheckpointGenerator()
    session = cg.create_session(
        session_id="test_session_001",
        agent_role="TechLead",
        project_tag="notion",
    )
    cg.add_record(session, "decision", {
        "title": "Memory Writer 集成方案",
        "notion_id": "xxx123",
    })
    cg.set_needs_review(session, ["Phase D 检测优化"])

    output = cg.generate(session)
    print(output)
