#!/usr/bin/env python3
"""
NEMT Cloud Memory Reader
========================
从 Obsidian Vault 读取记忆上下文，按时间窗口过滤，组装成可注入的文本片段。

核心逻辑（S11 Hook + S4 Obsidian 直读 混合方案）：
1. 扫描 Obsidian Vault 中的 MD 文件
2. 按时间窗口过滤（最近N天修改的页面）
3. 优先级排序：项目愿景 > 活跃任务 > 决策记录 > 一般笔记
4. 组装上下文片段并返回
"""

import os
import re
import json
import hashlib
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
import urllib.request
import urllib.error


# ============================================================================
# 配置
# ============================================================================

@dataclass
class MemoryConfig:
    """记忆系统配置"""
    # Obsidian Vault 路径
    vault_path: str = "/root/obsidian_vault/NEMT_Notion"

    # 时间窗口（天）
    time_window_days: int = 7

    # 最大注入 token 数（估算：1 token ≈ 4 字符）
    max_chars: int = 8000

    # 优先级目录
    priority_dirs: dict = field(default_factory=lambda: {
        "愿景管理系统": 1,
        "NEMT_Vision": 1,
        "NEMT架构": 2,
        "NEMT_Agent_System": 2,
        "Agent_Collaboration": 3,
        "决策记录": 3,
        "Decisions": 3,
        "NEMT理论": 4,
        "Strategy_Notes": 4,
        "PM_Resources": 5,
        "其他": 6,
    })

    # 排除的文件/目录
    exclude_patterns: list = field(default_factory=lambda: [
        ".obsidian",
        "__pycache__",
        ".git",
        "node_modules",
        "YYYY-MM-DD",
        "YYYY-WXX",
        "YYYY-MM",
        "Template",
        "template",
        "README",
    ])

    # 重要文件关键词（这些文件优先级提升）
    important_keywords: list = field(default_factory=lambda: [
        "VISION", "愿景", "原则", "Principles", "边界", "Boundaries",
        "决策", "Decision", "里程碑", "Milestone",
        "CTO", "CEO", "PM", "TechLead", "任务", "Task",
        "进度", "Progress", "当前", "Current",
    ])

    # 要读取的顶层目录（None = 全部）
    top_level_dirs: list = field(default_factory=lambda: [
        "愿景管理系统",
        "NEMT_Vision",
        "NEMT架构",
        "NEMT_Agent_System",
        "Strategy_Notes",
    ])

    def get_priority(self, file_path: str) -> int:
        """根据文件路径获取优先级（数字越小优先级越高）"""
        for priority_dir, p in self.priority_dirs.items():
            if priority_dir in file_path:
                # 如果路径包含重要关键词，优先级提升
                for kw in self.important_keywords:
                    if kw.lower() in file_path.lower():
                        return max(1, p - 1)
                return p

        # 默认优先级
        for kw in self.important_keywords:
            if kw.lower() in file_path.lower():
                return 3

        return self.priority_dirs.get("其他", 6)


# ============================================================================
# 记忆上下文项
# ============================================================================

@dataclass
class MemoryItem:
    """单个记忆条目"""
    title: str
    path: str
    content: str
    priority: int
    modified_time: datetime
    relevance_score: float = 0.0
    category: str = ""

    @property
    def priority_key(self):
        """用于排序的复合键：(priority, -modified_time, -relevance)"""
        return (self.priority, -self.modified_time.timestamp(), -self.relevance_score)

    def to_context_str(self, max_chars: int = 2000) -> str:
        """转换为可注入的上下文字符串"""
        # 截断长内容
        content = self.content
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n... [内容已截断，完整内容见: {self.path}]"

        lines = [
            f"## {self.title}",
            f"[{self.category}] {self.path}",
            f"最后修改: {self.modified_time.strftime('%Y-%m-%d %H:%M')}",
            "",
            content,
            "",
            "---",
            "",
        ]
        return "\n".join(lines)


# ============================================================================
# Obsidian 读取器
# ============================================================================

class ObsidianReader:
    """从 Obsidian Vault 读取记忆"""

    def __init__(self, config: MemoryConfig = None):
        self.config = config or MemoryConfig()

    def get_modified_time(self, path: Path) -> Optional[datetime]:
        """获取文件修改时间"""
        try:
            stat = path.stat()
            return datetime.fromtimestamp(stat.st_mtime)
        except (OSError, ValueError):
            return None

    def is_excluded(self, path: str) -> bool:
        """检查是否应排除此文件"""
        path_lower = path.lower()
        for pattern in self.config.exclude_patterns:
            if pattern.lower() in path_lower:
                return True
        return False

    def read_markdown_file(self, path: Path) -> Optional[str]:
        """读取 Markdown 文件内容"""
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except (OSError, UnicodeDecodeError):
            return None

    def extract_title(self, content: str, path: Path) -> str:
        """从 Markdown 内容或文件名提取标题"""
        # 尝试从 YAML front matter 提取 title
        fm_match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
        if fm_match:
            title_match = re.search(r"title:\s*['\"]?(.+?)['\"]?\n", fm_match.group(1))
            if title_match:
                return title_match.group(1).strip()

        # 尝试从第一个 # 标题提取
        h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()

        # 使用文件名作为标题
        return path.stem

    def extract_category(self, path: str) -> str:
        """根据路径提取分类"""
        parts = Path(path).parts
        if len(parts) >= 2:
            return parts[-2] if parts[-1] == parts[-1].lower() else parts[-2]
        return Path(path).stem

    def should_include_dir(self, dir_path: Path) -> bool:
        """检查是否应该包含此目录"""
        if not self.config.top_level_dirs:
            return True

        dir_name = dir_path.name
        for top_dir in self.config.top_level_dirs:
            if top_dir in dir_name or dir_name in top_dir:
                return True

        # 总是包含顶级目录
        if str(dir_path).count(os.sep) < 4:
            return True

        return False

    def scan_vault(self, query: str = "") -> list[MemoryItem]:
        """扫描 Vault 并返回记忆条目列表"""
        items = []
        vault = Path(self.config.vault_path)
        cutoff_time = datetime.now() - timedelta(days=self.config.time_window_days)

        if not vault.exists():
            return items

        for md_file in vault.rglob("*.md"):
            if self.is_excluded(str(md_file)):
                continue

            # 时间过滤：总是包含重要文件，即使超出时间窗口
            mtime = self.get_modified_time(md_file)
            if mtime is None:
                continue

            is_important = any(
                kw.lower() in str(md_file).lower()
                for kw in self.config.important_keywords
            )

            if mtime < cutoff_time and not is_important:
                continue

            content = self.read_markdown_file(md_file)
            if not content:
                continue

            # 内容过滤：如果有 query，计算相关性
            relevance = 0.0
            if query:
                query_lower = query.lower()
                content_lower = content.lower()
                query_words = query_lower.split()

                # 精确匹配加分
                if query_lower in content_lower:
                    relevance += 5.0
                # 单词匹配
                for word in query_words:
                    if word in content_lower:
                        relevance += 1.0

                # 如果相关性太低，跳过
                if relevance < 0.5:
                    continue

            title = self.extract_title(content, md_file)
            priority = self.config.get_priority(str(md_file))
            category = self.extract_category(str(md_file))

            item = MemoryItem(
                title=title,
                path=str(md_file),
                content=content,
                priority=priority,
                modified_time=mtime,
                relevance_score=relevance,
                category=category,
            )
            items.append(item)

        return items

    def build_context(self, items: list[MemoryItem], query: str = "", max_chars: int = 8000) -> str:
        """从记忆条目构建上下文字符串"""
        # 排序：优先级高的在前
        sorted_items = sorted(items, key=lambda x: x.priority_key)

        # 如果有 query，提升相关性高的条目
        if query:
            # 相关性权重稍低，确保优先级仍然主导
            sorted_items = sorted(
                sorted_items,
                key=lambda x: (x.priority * 0.7, -x.relevance_score * 0.3, -x.modified_time.timestamp())
            )

        context_parts = []
        total_chars = 0

        for item in sorted_items:
            # 根据优先级决定单条最大长度
            if item.priority <= 2:
                limit = 3000
            elif item.priority <= 3:
                limit = 2000
            else:
                limit = 1000

            context_str = item.to_context_str(max_chars=limit)
            if total_chars + len(context_str) > max_chars:
                # 尝试只添加标题摘要
                summary = f"## {item.title}\n[已截断，略]\n"
                if total_chars + len(summary) <= max_chars:
                    context_parts.append(summary)
                break

            context_parts.append(context_str)
            total_chars += len(context_str)

        return "\n".join(context_parts)


# ============================================================================
# 主函数
# ============================================================================

def get_memory_context(
    query: str = "",
    max_chars: int = 8000,
    time_window_days: int = 7,
    vault_path: str = None
) -> str:
    """
    获取记忆上下文字符串

    Args:
        query: 当前消息查询（用于相关性过滤）
        max_chars: 最大字符数
        time_window_days: 时间窗口（天）
        vault_path: Obsidian Vault 路径

    Returns:
        格式化的上下文字符串，可直接注入到 system prompt
    """
    config = MemoryConfig(
        time_window_days=time_window_days,
        max_chars=max_chars,
        vault_path=vault_path or os.environ.get(
            "OBSIDIAN_VAULT_PATH",
            "/root/obsidian_vault/NEMT_Notion"
        )
    )

    reader = ObsidianReader(config)
    items = reader.scan_vault(query=query)
    context = reader.build_context(items, query=query, max_chars=max_chars)

    return context


def get_memory_summary() -> dict:
    """获取记忆摘要"""
    config = MemoryConfig()
    reader = ObsidianReader(config)
    items = reader.scan_vault()

    by_priority = {}
    for item in items:
        p = item.priority
        if p not in by_priority:
            by_priority[p] = []
        by_priority[p].append({
            "title": item.title,
            "path": item.path,
            "modified": item.modified_time.isoformat(),
            "category": item.category,
        })

    return {
        "total": len(items),
        "by_priority": {str(k): len(v) for k, v in by_priority.items()},
        "recent_items": [
            {"title": i.title, "modified": i.modified_time.isoformat(), "priority": i.priority}
            for i in sorted(items, key=lambda x: -x.modified_time.timestamp())[:10]
        ]
    }


if __name__ == "__main__":
    import sys

    query = ""
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])

    context = get_memory_context(query=query)
    print("=== MEMORY CONTEXT ===")
    print(context)
    print("=== END MEMORY CONTEXT ===")
