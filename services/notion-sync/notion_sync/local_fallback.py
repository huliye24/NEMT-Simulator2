# Copyright 2026 NEMT Lab
"""
NEMT Memory System - Local Fallback Storage
==========================================
本地回退存储：Notion 不可用时的记忆保险库

设计原则：
1. Schema 一致：本地 .md 文件结构与 Notion DB Schema 完全对应
2. 永不丢失：写入失败时降级到本地，标记 [PENDING_SYNC]
3. 自动恢复：Notion 恢复后可手动或自动同步
4. 人类可读：.md 文件可以直接打开查看，无需工具

目录结构：
  notion_sync/local_fallback/
    decisions/
      YYYY-MM-DD_HHMMSS_decision_title.md
      [PENDING]_decision_id.md
    experiences/
      YYYY-MM-DD_HHMMSS_experience_title.md
      [PENDING]_experience_id.md
    failures/
      YYYY-MM-DD_HHMMSS_failure_title.md
      [PENDING]_failure_id.md
    sync_log.json          # 同步历史记录
"""

import os
import json
import sys
import uuid
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field

# UTF-8 输出
sys.stdout.reconfigure(encoding='utf-8', errors='replace')


# ============================================================================
# 路径配置
# ============================================================================

def _project_root() -> Path:
    return Path(__file__).parent.parent.resolve()


def _sync_root() -> Path:
    return Path(__file__).parent.resolve()


FALLBACK_ROOT = _sync_root() / "local_fallback"
FALLBACK_DECISIONS = FALLBACK_ROOT / "decisions"
FALLBACK_EXPERIENCES = FALLBACK_ROOT / "experiences"
FALLBACK_FAILURES = FALLBACK_ROOT / "failures"
SYNC_LOG = FALLBACK_ROOT / "sync_log.json"


# ============================================================================
# 数据模型
# ============================================================================

@dataclass
class DecisionRecord:
    """决策记录（对应 Notion Decisions DB）"""
    title: str = ""
    conclusion: str = ""          # [必须] 一句话结论
    reason: str = ""               # [必须] 决策理由
    date: str = ""                # ISO 格式日期
    created_by: str = "Agent"     # Founder/CEO/CTO/PM/TechLead/Agent
    status: str = "adopted"      # proposed/adopted/rejected/superseded/paused
    decision_type: str = "architecture"  # architecture/technical/priority/boundary
    quality_score: str = "medium"  # high/medium/low
    needs_review: bool = False
    aligned_principles: List[str] = field(default_factory=list)
    violated_boundaries: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    related_experiences: List[str] = field(default_factory=list)  # 本地 ID 列表
    related_tasks: List[str] = field(default_factory=list)
    sync_status: str = "synced"  # synced/pending/failed
    local_id: str = ""             # 本地唯一 ID（UUID）
    notion_id: str = ""           # Notion 页面 ID（同步后填入）
    created_at: str = ""          # ISO 时间戳
    updated_at: str = ""          # ISO 时间戳
    pending_reason: str = ""       # 失败原因（如果有）

    def __post_init__(self):
        if not self.local_id:
            self.local_id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def filename(self) -> str:
        """生成文件名"""
        status_prefix = "[PENDING] " if self.sync_status == "pending" else ""
        title_slug = self.title[:30].replace("/", "-").replace("\\", "-").replace(":", "-").strip()
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        return f"{status_prefix}{ts}_{title_slug}.md"

    def to_frontmatter(self) -> str:
        """转换为 Markdown YAML frontmatter"""
        lines = ["---", "type: decision"]
        for key, value in asdict(self).items():
            if value is None:
                continue
            if isinstance(value, list):
                if value:
                    lines.append(f"{key}:")
                    for v in value:
                        lines.append(f"  - {v}")
                else:
                    lines.append(f"{key}: []")
            elif isinstance(value, bool):
                lines.append(f"{key}: {str(value).lower()}")
            elif value:
                lines.append(f"{key}: \"{value}\"")
        lines.append("---")
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """转换为完整 Markdown"""
        content = [self.to_frontmatter(), ""]

        if self.title:
            content.append(f"# {self.title}")
            content.append("")

        if self.conclusion:
            content.append(f"**结论**: {self.conclusion}")
            content.append("")

        if self.reason:
            content.append(f"**理由**: {self.reason}")
            content.append("")

        # 元信息表格
        meta_rows = [
            ("状态", self.status),
            ("类型", self.decision_type),
            ("创建者", self.created_by),
            ("质量", self.quality_score),
            ("日期", self.date),
            ("ID", self.local_id),
            ("同步状态", self.sync_status),
        ]
        if self.pending_reason:
            meta_rows.append(("失败原因", self.pending_reason))

        if meta_rows:
            content.append("| 属性 | 值 |")
            content.append("|------|-----|")
            for k, v in meta_rows:
                content.append(f"| {k} | {v} |")

        if self.tags:
            content.append("")
            content.append(f"**标签**: {' '.join(f'`{t}`' for t in self.tags)}")

        if self.aligned_principles:
            content.append("")
            content.append(f"**对齐原则**: {', '.join(self.aligned_principles)}")

        if self.related_experiences:
            content.append("")
            content.append(f"**关联经验**: {', '.join(self.related_experiences)}")

        if self.sync_status == "pending":
            content.append("")
            content.append("> [PENDING_SYNC] 此记录尚未同步到 Notion")

        return "\n".join(content)

    @classmethod
    def from_frontmatter(cls, content: str) -> Optional['DecisionRecord']:
        """从 Markdown frontmatter 解析"""
        try:
            import re
            match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if not match:
                return None

            data = {}
            lines = match.group(1).split("\n")
            current_key = None
            in_list = False

            for line in lines:
                if not line.strip() or line.startswith("#"):
                    continue
                if ':' in line:
                    if in_list:
                        in_list = False
                    key, _, value = line.partition(':')
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if value.startswith('[') and value.endswith(']'):
                        value = []
                    if value == "[]":
                        value = []
                    data[key] = value
                    current_key = key
                elif line.strip().startswith('- ') and current_key:
                    val = line.strip()[1:].strip()
                    if current_key not in data:
                        data[current_key] = []
                    if isinstance(data[current_key], list):
                        data[current_key].append(val)

            # 布尔值转换
            for bool_key in ['needs_review']:
                if bool_key in data:
                    data[bool_key] = data[bool_key] == 'true'

            # 列表值转换
            for list_key in ['aligned_principles', 'violated_boundaries', 'tags',
                           'related_experiences', 'related_tasks']:
                if list_key in data and not isinstance(data[list_key], list):
                    data[list_key] = []

            # 过滤掉 None 值
            data = {k: v for k, v in data.items() if v is not None and v != ''}

            return cls(**{k: v for k, v in data.items()
                         if k in cls.__dataclass_fields__})
        except Exception:
            return None


@dataclass
class ExperienceRecord:
    """经验记录（对应 Notion Experiences DB）"""
    title: str = ""
    type: str = "solution"         # solution/mistake/diagnostic/decision/observation
    summary: str = ""             # 一句话总结 [Agent 生成]
    detail: str = ""              # 详细记录
    tags: List[str] = field(default_factory=list)
    created_by: str = "Agent"     # Agent/Human/Auto
    usefulness_score: int = 3     # 1-5
    access_count: int = 0
    verified: bool = False
    obsolete: bool = False
    needs_review: bool = False
    related_decisions: List[str] = field(default_factory=list)
    sync_status: str = "synced"
    local_id: str = ""
    notion_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    pending_reason: str = ""

    def __post_init__(self):
        if not self.local_id:
            self.local_id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def filename(self) -> str:
        status_prefix = "[PENDING] " if self.sync_status == "pending" else ""
        type_prefix = f"[{self.type}] "
        title_slug = self.title[:25].replace("/", "-").replace("\\", "-").replace(":", "-").strip()
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        return f"{status_prefix}{type_prefix}{ts}_{title_slug}.md"

    def to_frontmatter(self) -> str:
        lines = ["---", f"type: experience"]
        for key, value in asdict(self).items():
            if value is None:
                continue
            if isinstance(value, list):
                if value:
                    lines.append(f"{key}:")
                    for v in value:
                        lines.append(f"  - {v}")
                else:
                    lines.append(f"{key}: []")
            elif isinstance(value, bool):
                lines.append(f"{key}: {str(value).lower()}")
            elif value:
                lines.append(f"{key}: \"{value}\"")
        lines.append("---")
        return "\n".join(lines)

    def to_markdown(self) -> str:
        content = [self.to_frontmatter(), ""]
        if self.title:
            content.append(f"# {self.type.upper()}: {self.title}")
            content.append("")

        if self.summary:
            content.append(f"**摘要**: {self.summary}")
            content.append("")

        if self.detail:
            content.append("## 详细")
            content.append(self.detail)
            content.append("")

        if self.tags:
            content.append(f"**标签**: {' '.join(f'`{t}`' for t in self.tags)}")
            content.append("")

        if self.related_decisions:
            content.append(f"**关联决策**: {', '.join(self.related_decisions)}")
            content.append("")

        if self.sync_status == "pending":
            content.append("> [PENDING_SYNC] 此记录尚未同步到 Notion")

        return "\n".join(content)


@dataclass
class FailureRecord:
    """失败记录（对应 Notion Failures DB）"""
    title: str = ""
    category: str = "validation"     # validation/integration/logic/data/boundary
    status: str = "active"        # active/investigated/resolved
    symptom: str = ""
    root_cause: str = ""
    resolution: str = ""
    tags: List[str] = field(default_factory=list)
    related_decisions: List[str] = field(default_factory=list)
    resolved_at: str = ""
    sync_status: str = "synced"
    local_id: str = ""
    notion_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    pending_reason: str = ""

    def __post_init__(self):
        if not self.local_id:
            self.local_id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def filename(self) -> str:
        status_prefix = "[PENDING] " if self.sync_status == "pending" else ""
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        return f"{status_prefix}[{self.category}]_{ts}_{self.local_id}.md"

    def to_markdown(self) -> str:
        content = [self.to_frontmatter(), ""]
        if self.title:
            content.append(f"# [{self.category.upper()}] {self.title}")
            content.append("")

        content.append(f"**状态**: {self.status}")
        content.append("")

        if self.symptom:
            content.append(f"**症状**: {self.symptom}")
            content.append("")

        if self.root_cause:
            content.append(f"**根因**: {self.root_cause}")
            content.append("")

        if self.resolution:
            content.append(f"**解决方案**: {self.resolution}")
            content.append("")

        if self.related_decisions:
            content.append(f"**关联决策**: {', '.join(self.related_decisions)}")
            content.append("")

        if self.sync_status == "pending":
            content.append("> [PENDING_SYNC] 此记录尚未同步到 Notion")

        return "\n".join(content)

    def to_frontmatter(self) -> str:
        lines = ["---", f"type: failure"]
        for key, value in asdict(self).items():
            if value is None:
                continue
            if isinstance(value, list):
                if value:
                    lines.append(f"{key}:")
                    for v in value:
                        lines.append(f"  - {v}")
                else:
                    lines.append(f"{key}: []")
            elif isinstance(value, bool):
                lines.append(f"{key}: {str(value).lower()}")
            elif value:
                lines.append(f"{key}: \"{value}\"")
        lines.append("---")
        return "\n".join(lines)


# ============================================================================
# 同步日志
# ============================================================================

@dataclass
class SyncLogEntry:
    timestamp: str = ""
    direction: str = ""   # local_to_notion / notion_to_local
    record_type: str = ""  # decision/experience/failure
    local_id: str = ""
    notion_id: str = ""
    status: str = ""    # success/failed
    error: str = ""
    retry_count: int = 0


class SyncLog:
    """同步历史日志"""

    def __init__(self):
        self.entries: List[SyncLogEntry] = []
        self._load()

    def _load(self):
        if SYNC_LOG.exists():
            try:
                with open(SYNC_LOG, encoding='utf-8') as f:
                    raw = json.load(f)
                    self.entries = [SyncLogEntry(**e) for e in raw.get("entries", [])]
            except Exception:
                pass

    def _save(self):
        SYNC_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(SYNC_LOG, 'w', encoding='utf-8') as f:
            json.dump({
                "last_updated": datetime.now().isoformat(),
                "total_entries": len(self.entries),
                "entries": [asdict(e) for e in self.entries[-100:]]  # 只保留最近100条
            }, f, ensure_ascii=False, indent=2)

    def add(self, entry: SyncLogEntry):
        entry.timestamp = datetime.now().isoformat()
        self.entries.append(entry)
        self._save()

    def get_pending(self, record_type: Optional[str] = None) -> List[SyncLogEntry]:
        """获取所有失败的同步记录"""
        return [
            e for e in self.entries
            if e.status == "failed"
            and (record_type is None or e.record_type == record_type)
        ]


# ============================================================================
# 本地存储管理器
# ============================================================================

class LocalFallbackStore:
    """
    本地回退存储管理器

    提供与 Notion API 一致的接口，但在 Notion 不可用时自动降级到本地。

    使用方式：
        store = LocalFallbackStore()

        # 写入（自动降级）
        decision = DecisionRecord(title="集成验证层", conclusion="...", reason="...")
        success = store.write_decision(decision)
        if not success:
            print(f"已降级到本地: {decision.filename()}")

        # 读取
        decisions = store.list_decisions(limit=5, status_filter="adopted")

        # 检索
        results = store.search_decisions("验证层")

        # 同步
        store.sync_pending()
    """

    def __init__(self):
        self._ensure_dirs()
        self.sync_log = SyncLog()

    def _ensure_dirs(self):
        """确保所有目录存在"""
        for d in [FALLBACK_ROOT, FALLBACK_DECISIONS, FALLBACK_EXPERIENCES, FALLBACK_FAILURES]:
            d.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # 写入操作
    # -------------------------------------------------------------------------

    def write_decision(self, record: DecisionRecord, target_dir: Optional[Path] = None) -> bool:
        """写入决策记录到本地"""
        target = target_dir or FALLBACK_DECISIONS
        filepath = target / record.filename()
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(record.to_markdown())
            self.sync_log.add(SyncLogEntry(
                direction="local_only",
                record_type="decision",
                local_id=record.local_id,
                status="success",
            ))
            return True
        except Exception as e:
            record.sync_status = "failed"
            record.pending_reason = str(e)
            print(f"[LocalFallback] 写入失败: {e}")
            return False

    def write_experience(self, record: ExperienceRecord) -> bool:
        """写入经验记录到本地"""
        filepath = FALLBACK_EXPERIENCES / record.filename()
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(record.to_markdown())
            self.sync_log.add(SyncLogEntry(
                direction="local_only",
                record_type="experience",
                local_id=record.local_id,
                status="success",
            ))
            return True
        except Exception as e:
            print(f"[LocalFallback] 写入经验失败: {e}")
            return False

    def write_failure(self, record: FailureRecord) -> bool:
        """写入失败记录到本地"""
        filepath = FALLBACK_FAILURES / record.filename()
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(record.to_markdown())
            self.sync_log.add(SyncLogEntry(
                direction="local_only",
                record_type="failure",
                local_id=record.local_id,
                status="success",
            ))
            return True
        except Exception as e:
            print(f"[LocalFallback] 写入失败记录失败: {e}")
            return False

    # -------------------------------------------------------------------------
    # 读取操作
    # -------------------------------------------------------------------------

    def _read_markdown_file(self, filepath: Path) -> Optional[Any]:
        """读取 Markdown 文件，返回对应类型的记录"""
        try:
            with open(filepath, encoding='utf-8') as f:
                content = f.read()

            if "type: decision" in content[:200]:
                return DecisionRecord.from_frontmatter(content)
            elif "type: experience" in content[:200]:
                # Experience 不需要 from_frontmatter（暂时用简化版）
                return self._parse_experience(content)
            elif "type: failure" in content[:200]:
                return self._parse_failure(content)
            return None
        except Exception:
            return None

    def _parse_experience(self, content: str) -> Optional[ExperienceRecord]:
        """从 Markdown 解析 ExperienceRecord"""
        try:
            import re
            match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if not match:
                return None
            data = {}
            lines = match.group(1).split("\n")
            for line in lines:
                if ':' in line and not line.strip().startswith('-'):
                    key, _, value = line.partition(':')
                    data[key.strip()] = value.strip().strip('"')
            for list_key in ['tags', 'related_decisions']:
                if list_key in data and not isinstance(data.get(list_key), list):
                    data[list_key] = []
            return ExperienceRecord(**{k: v for k, v in data.items()
                                     if k in ExperienceRecord.__dataclass_fields__})
        except Exception:
            return None

    def _parse_failure(self, content: str) -> Optional[FailureRecord]:
        """从 Markdown 解析 FailureRecord"""
        try:
            import re
            match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if not match:
                return None
            data = {}
            lines = match.group(1).split("\n")
            for line in lines:
                if ':' in line and not line.strip().startswith('-'):
                    key, _, value = line.partition(':')
                    data[key.strip()] = value.strip().strip('"')
            for list_key in ['tags', 'related_decisions']:
                if list_key in data and not isinstance(data.get(list_key), list):
                    data[list_key] = []
            return FailureRecord(**{k: v for k, v in data.items()
                                  if k in FailureRecord.__dataclass_fields__})
        except Exception:
            return None

    def list_decisions(self,
                      limit: int = 20,
                      status_filter: Optional[str] = None,
                      tag_filter: Optional[str] = None,
                      include_pending: bool = True) -> List[DecisionRecord]:
        """列出决策记录"""
        results = []
        for filepath in sorted(FALLBACK_DECISIONS.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
            if not include_pending and "[PENDING]" in filepath.name:
                continue
            record = self._read_markdown_file(filepath)
            if record:
                if status_filter and record.status != status_filter:
                    continue
                if tag_filter and tag_filter not in record.tags:
                    continue
                results.append(record)
                if len(results) >= limit:
                    break
        return results

    def search_decisions(self,
                        query: str,
                        limit: int = 10) -> List[DecisionRecord]:
        """全文搜索决策记录"""
        query_lower = query.lower()
        results = []
        for filepath in FALLBACK_DECISIONS.glob("*.md"):
            try:
                with open(filepath, encoding='utf-8') as f:
                    content = f.read().lower()
                if query_lower in content:
                    record = self._read_markdown_file(filepath)
                    if record:
                        results.append(record)
                        if len(results) >= limit:
                            break
            except Exception:
                pass
        return results

    def get_recent_decisions(self,
                            since_days: int = 7,
                            limit: int = 5) -> List[DecisionRecord]:
        """获取最近的决策（按时间排序）"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=since_days)
        results = []
        for filepath in sorted(FALLBACK_DECISIONS.glob("*.md"),
                              key=lambda p: p.stat().st_mtime, reverse=True):
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            if mtime < cutoff:
                break
            record = self._read_markdown_file(filepath)
            if record and record.status != "rejected":
                results.append(record)
                if len(results) >= limit:
                    break
        return results

    def get_pending_decisions(self) -> List[DecisionRecord]:
        """获取所有待同步的决策"""
        results = []
        for filepath in FALLBACK_DECISIONS.glob("[PENDING]_*.md"):
            record = self._read_markdown_file(filepath)
            if record:
                results.append(record)
        return results

    def list_experiences(self,
                        type_filter: Optional[str] = None,
                        limit: int = 20) -> List[ExperienceRecord]:
        """列出经验记录"""
        results = []
        for filepath in sorted(FALLBACK_EXPERIENCES.glob("*.md"),
                              key=lambda p: p.stat().st_mtime, reverse=True):
            record = self._read_markdown_file(filepath)
            if record:
                if type_filter and record.type != type_filter:
                    continue
                results.append(record)
                if len(results) >= limit:
                    break
        return results

    def search_experiences(self, query: str, limit: int = 5) -> List[ExperienceRecord]:
        """搜索经验记录"""
        query_lower = query.lower()
        results = []
        for filepath in FALLBACK_EXPERIENCES.glob("*.md"):
            try:
                with open(filepath, encoding='utf-8') as f:
                    content = f.read().lower()
                if query_lower in content:
                    record = self._read_markdown_file(filepath)
                    if record:
                        results.append(record)
                        if len(results) >= limit:
                            break
            except Exception:
                pass
        return results

    def get_pending_count(self) -> Dict[str, int]:
        """获取各类型待同步记录数"""
        return {
            "decisions": len(list(FALLBACK_DECISIONS.glob("[PENDING]_*.md"))) +
                        len(list(FALLBACK_DECISIONS.glob("**/[PENDING]_*.md"))),
            "experiences": len(list(FALLBACK_EXPERIENCES.glob("[PENDING]_*.md"))) +
                          len(list(FALLBACK_EXPERIENCES.glob("**/[PENDING]_*.md"))),
            "failures": len(list(FALLBACK_FAILURES.glob("[PENDING]_*.md"))) +
                       len(list(FALLBACK_FAILURES.glob("**/[PENDING]_*.md"))),
        }

    def resolve_pending(self, record_type: str, local_id: str, notion_id: str) -> bool:
        """标记本地记录已同步到 Notion"""
        folder_map = {
            "decision": FALLBACK_DECISIONS,
            "experience": FALLBACK_EXPERIENCES,
            "failure": FALLBACK_FAILURES,
        }
        folder = folder_map.get(record_type)
        if not folder:
            return False

        for filepath in folder.glob("[PENDING]_*.md"):
            record = self._read_markdown_file(filepath)
            if record and record.local_id == local_id:
                record.notion_id = notion_id
                record.sync_status = "synced"
                # 重命名文件，去掉 [PENDING] 前缀
                new_name = filepath.name.replace("[PENDING] ", "", 1)
                new_path = filepath.parent / new_name
                with open(new_path, 'w', encoding='utf-8') as f:
                    f.write(record.to_markdown())
                filepath.unlink()
                self.sync_log.add(SyncLogEntry(
                    direction="local_to_notion",
                    record_type=record_type,
                    local_id=local_id,
                    notion_id=notion_id,
                    status="success",
                ))
                return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计"""
        def count_files(glob_pattern):
            return len(list(glob_pattern))

        return {
            "decisions_total": count_files(FALLBACK_DECISIONS.glob("*.md")),
            "decisions_pending": count_files(FALLBACK_DECISIONS.glob("[PENDING]_*.md")),
            "experiences_total": count_files(FALLBACK_EXPERIENCES.glob("*.md")),
            "experiences_pending": count_files(FALLBACK_EXPERIENCES.glob("[PENDING]_*.md")),
            "failures_total": count_files(FALLBACK_FAILURES.glob("*.md")),
            "failures_pending": count_files(FALLBACK_FAILURES.glob("[PENDING]_*.md")),
            "last_sync": self.sync_log.entries[-1].timestamp if self.sync_log.entries else None,
            "total_sync_entries": len(self.sync_log.entries),
        }


# ============================================================================
# 单例
# ============================================================================

_local_store: Optional[LocalFallbackStore] = None


def get_local_store() -> LocalFallbackStore:
    global _local_store
    if _local_store is None:
        _local_store = LocalFallbackStore()
    return _local_store


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("NEMT Local Fallback Storage")
    print("=" * 60)

    store = get_local_store()
    stats = store.get_stats()

    print(f"\n[Fallback Storage]")
    print(f"  Decisions: {stats['decisions_total']} total, {stats['decisions_pending']} pending")
    print(f"  Experiences: {stats['experiences_total']} total, {stats['experiences_pending']} pending")
    print(f"  Failures: {stats['failures_total']} total, {stats['failures_pending']} pending")
    print(f"  Last sync: {stats['last_sync'] or 'never'}")

    pending = store.get_pending_count()
    total_pending = sum(pending.values())
    if total_pending > 0:
        print(f"\n[!] 有 {total_pending} 条记录待同步到 Notion")
        for k, v in pending.items():
            if v > 0:
                print(f"  - {k}: {v}")
    else:
        print("\n[OK] 没有待同步记录")

    print("\n[Recent Decisions]")
    recent = store.get_recent_decisions(limit=3)
    if recent:
        for r in recent:
            print(f"  [{r.status}] {r.title[:40]}")
    else:
        print("  (无记录)")
