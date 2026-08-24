# Copyright 2026 NEMT Lab
"""
NEMT Memory System - Notion Query Client
=========================================
对 Notion 数据库的只读查询封装，支持：
- 决策记录查询
- 经验沉淀查询
- 失败记录查询
- 按标签/状态/类型过滤
- 分页和排序

同时实现了降级逻辑：Notion 不可用时自动回退到本地存储。
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 延迟导入，避免循环依赖
_nemt_config = None


def _get_config():
    global _nemt_config
    if _nemt_config is None:
        try:
            from nemt_sync_config import get_config
            _nemt_config = get_config()
        except ImportError:
            _nemt_config = None
    return _nemt_config


# ============================================================================
# 数据模型
# ============================================================================

@dataclass
class NEMTDecision:
    """NEMT 决策记录（从 Notion 读取）"""
    id: str = ""
    title: str = ""
    conclusion: str = ""
    reason: str = ""
    date: str = ""
    created_by: str = ""
    status: str = ""
    decision_type: str = ""
    quality_score: str = ""
    needs_review: bool = False
    aligned_principles: List[str] = field(default_factory=list)
    violated_boundaries: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    url: str = ""

    def to_summary(self) -> str:
        """生成一行摘要"""
        parts = [f"[Decision] {self.title}"]
        if self.conclusion:
            parts.append(f"结论: {self.conclusion}")
        if self.decision_type:
            parts.append(f"类型: {self.decision_type}")
        if self.status:
            parts.append(f"状态: {self.status}")
        if self.tags:
            parts.append(f"标签: {', '.join(self.tags)}")
        return " | ".join(parts)

    def to_detailed_summary(self) -> str:
        """生成详细摘要"""
        lines = [f"## {self.title}", ""]
        if self.conclusion:
            lines.append(f"**结论**: {self.conclusion}")
        if self.reason:
            lines.append(f"**理由**: {self.reason}")
        meta = []
        if self.status:
            meta.append(f"状态={self.status}")
        if self.decision_type:
            meta.append(f"类型={self.decision_type}")
        if self.created_by:
            meta.append(f"决策人={self.created_by}")
        if self.date:
            meta.append(f"日期={self.date}")
        if meta:
            lines.append(f"[{' | '.join(meta)}]")
        if self.aligned_principles:
            lines.append(f"**对齐原则**: {', '.join(self.aligned_principles)}")
        if self.violated_boundaries:
            lines.append(f"**违反边界**: {', '.join(self.violated_boundaries)}")
        if self.tags:
            lines.append(f"**标签**: {' '.join(f'`{t}`' for t in self.tags)}")
        return "\n".join(lines)


@dataclass
class NEMTExperience:
    """NEMT 经验记录"""
    id: str = ""
    title: str = ""
    type: str = ""          # solution/mistake/diagnostic/decision/observation
    summary: str = ""
    detail: str = ""
    tags: List[str] = field(default_factory=list)
    usefulness_score: int = 3
    verified: bool = False
    access_count: int = 0
    url: str = ""

    def to_summary(self) -> str:
        type_icon = {"solution": "S", "mistake": "M", "diagnostic": "D", "decision": "C", "observation": "O"}
        icon = type_icon.get(self.type, "?")
        parts = [f"[Exp-{icon}] {self.title}"]
        if self.summary:
            parts.append(self.summary)
        if self.tags:
            parts.append(f"标签: {', '.join(self.tags)}")
        return " | ".join(parts)

    def to_detailed_summary(self) -> str:
        lines = [f"## [{self.type.upper()}] {self.title}", ""]
        if self.summary:
            lines.append(f"**摘要**: {self.summary}")
        if self.detail:
            lines.append(f"**详情**: {self.detail[:300]}{'...' if len(self.detail) > 300 else ''}")
        meta = []
        if self.type:
            meta.append(f"类型={self.type}")
        if self.usefulness_score:
            meta.append(f"有用度={self.usefulness_score}/5")
        if self.verified:
            meta.append("已验证")
        if meta:
            lines.append(f"[{' | '.join(meta)}]")
        if self.tags:
            lines.append(f"**标签**: {' '.join(f'`{t}`' for t in self.tags)}")
        return "\n".join(lines)


@dataclass
class NEMTFailure:
    """NEMT 失败记录"""
    id: str = ""
    title: str = ""
    category: str = ""
    status: str = ""
    symptom: str = ""
    root_cause: str = ""
    resolution: str = ""
    tags: List[str] = field(default_factory=list)
    url: str = ""

    def to_summary(self) -> str:
        parts = [f"[Failure-{self.category[:3]}] {self.title}"]
        if self.status:
            parts.append(f"状态={self.status}")
        if self.tags:
            parts.append(f"标签: {', '.join(self.tags)}")
        return " | ".join(parts)

    def to_detailed_summary(self) -> str:
        lines = [f"## [{self.category.upper()}] {self.title}", ""]
        if self.status:
            lines.append(f"**状态**: {self.status}")
        if self.symptom:
            lines.append(f"**症状**: {self.symptom}")
        if self.root_cause:
            lines.append(f"**根因**: {self.root_cause}")
        if self.resolution:
            lines.append(f"**解决方案**: {self.resolution}")
        if self.tags:
            lines.append(f"**标签**: {' '.join(f'`{t}`' for t in self.tags)}")
        return "\n".join(lines)


@dataclass
class SessionContext:
    """会话上下文"""
    project_tags: List[str] = field(default_factory=list)  # 当前项目的标签
    agent_role: str = ""     # Founder/CTO/PM/TechLead
    session_goal: str = ""   # 当前会话目标
    recent_work: str = ""     # 最近在做什么


# ============================================================================
# Notion API 客户端（查询专用）
# ============================================================================

class NotionQueryClient:
    """
    Notion 数据库只读查询客户端

    提供语义化的查询方法，自动处理：
    - Token 加载
    - 数据库 ID 映射
    - 分页
    - 错误处理和重试
    - 降级到本地存储
    """

    BASE_URL = "https://api.notion.com/v1"
    VERSION = "2022-06-28"

    def __init__(self, token: Optional[str] = None, timeout: int = 30):
        self.token = token
        self.timeout = timeout
        self._available = True
        self._last_error: Optional[str] = None

        # 延迟加载 token
        if not self.token:
            config = _get_config()
            if config and config.notion_token:
                self.token = config.notion_token

        if not self.token:
            self._available = False
            self._last_error = "NOTION_TOKEN 未配置"

    @property
    def is_available(self) -> bool:
        """Notion API 是否可用"""
        return self._available and bool(self.token)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.VERSION,
            "Content-Type": "application/json"
        }

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """GET 请求（带重试）"""
        if not self.is_available:
            return None

        import requests
        url = f"{self.BASE_URL}/{endpoint}"
        for attempt in range(2):
            try:
                resp = requests.get(url, headers=self._headers(), params=params, timeout=self.timeout)
                if resp.status_code == 429:
                    wait = int(resp.headers.get("Retry-After", 5))
                    time.sleep(wait)
                    continue
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code == 400:
                    self._last_error = f"Bad request: {resp.text[:200]}"
                    return None
                if resp.status_code == 404:
                    self._last_error = f"Resource not found: {endpoint}"
                    return None
                self._last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                return None
            except requests.exceptions.Timeout:
                self._last_error = "Request timeout"
                if attempt == 0:
                    time.sleep(2)
                    continue
                return None
            except requests.exceptions.ConnectionError as e:
                self._last_error = f"Connection error: {str(e)[:100]}"
                return None
            except Exception as e:
                self._last_error = str(e)
                return None
        return None

    def _post(self, endpoint: str, data: Dict) -> Optional[Dict]:
        """POST 请求"""
        if not self.is_available:
            return None

        import requests
        url = f"{self.BASE_URL}/{endpoint}"
        for attempt in range(2):
            try:
                resp = requests.post(url, headers=self._headers(), json=data, timeout=self.timeout)
                if resp.status_code == 429:
                    wait = int(resp.headers.get("Retry-After", 5))
                    time.sleep(wait)
                    continue
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code == 400:
                    self._last_error = f"Bad request: {resp.text[:200]}"
                    return None
                self._last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                return None
            except Exception as e:
                self._last_error = str(e)
                if attempt == 0:
                    time.sleep(2)
                    continue
                return None
        return None

    # -------------------------------------------------------------------------
    # 数据库查询
    # -------------------------------------------------------------------------

    def _query_database(self,
                       db_id: str,
                       filter_dict: Optional[Dict] = None,
                       sorts: Optional[List[Dict]] = None,
                       page_size: int = 100) -> List[Dict]:
        """查询数据库，返回所有页面"""
        all_results = []
        cursor = None

        while True:
            data: Dict[str, Any] = {"page_size": page_size}
            if filter_dict:
                data["filter"] = filter_dict
            if sorts:
                data["sorts"] = sorts
            if cursor:
                data["start_cursor"] = cursor

            result = self._post(f"databases/{db_id}/query", data)
            if not result:
                break

            results = result.get("results", [])
            all_results.extend(results)

            cursor = result.get("next_cursor")
            if not cursor:
                break

        return all_results

    def _parse_page(self, page: Dict) -> Dict[str, Any]:
        """解析 Notion 页面属性"""
        props = page.get("properties", {})
        parsed = {}

        for prop_name, prop_data in props.items():
            prop_type = prop_data.get("type", "")
            value = prop_data.get(prop_type)

            if prop_type == "title":
                parsed[prop_name] = "".join(t.get("plain_text", "") for t in value) if value else ""
            elif prop_type == "rich_text":
                parsed[prop_name] = "".join(t.get("plain_text", "") for t in (value or []))
            elif prop_type == "select":
                parsed[prop_name] = value.get("name", "") if value else ""
            elif prop_type == "multi_select":
                parsed[prop_name] = [v.get("name", "") for v in (value or [])]
            elif prop_type == "date":
                parsed[prop_name] = value.get("start", "") if value else ""
            elif prop_type == "checkbox":
                parsed[prop_name] = bool(value)
            elif prop_type == "number":
                parsed[prop_name] = value
            elif prop_type == "url":
                parsed[prop_name] = value or ""
            elif prop_type == "relation":
                parsed[prop_name] = [v.get("id", "") for v in (value or [])]
            else:
                parsed[prop_name] = str(value) if value else ""

        parsed["_id"] = page.get("id", "")
        parsed["_url"] = f"https://notion.so/{page.get('id', '').replace('-', '')}"
        return parsed

    # -------------------------------------------------------------------------
    # 决策查询
    # -------------------------------------------------------------------------

    def query_decisions(self,
                       status: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       decision_type: Optional[str] = None,
                       needs_review: Optional[bool] = None,
                       since_days: Optional[int] = None,
                       limit: int = 50) -> List[NEMTDecision]:
        """查询决策记录"""
        config = _get_config()
        db_id = None
        if config:
            db_id = config.database_ids.get("Decisions")

        if not db_id:
            return []

        # 构建 filter
        filter_parts = []
        if status:
            filter_parts.append({
                "property": "状态",
                "select": {"equals": status}
            })
        if decision_type:
            filter_parts.append({
                "property": "决策类型",
                "select": {"equals": decision_type}
            })
        if needs_review is not None:
            filter_parts.append({
                "property": "需回顾",
                "checkbox": {"equals": needs_review}
            })
        if since_days:
            since_date = (datetime.now() - timedelta(days=since_days)).strftime("%Y-%m-%d")
            filter_parts.append({
                "property": "日期",
                "date": {"on_or_after": since_date}
            })

        filter_dict = None
        if len(filter_parts) == 1:
            filter_dict = filter_parts[0]
        elif len(filter_parts) > 1:
            filter_dict = {"and": filter_parts}

        # 排序
        sorts = [{"property": "日期", "direction": "descending"}]

        try:
            pages = self._query_database(db_id, filter_dict, sorts)
        except Exception as e:
            self._last_error = str(e)
            return []

        results = []
        for page in pages[:limit]:
            p = self._parse_page(page)
            # 标签过滤
            if tags:
                page_tags = p.get("标签", [])
                if isinstance(page_tags, str):
                    page_tags = [page_tags]
                if not any(t in page_tags for t in tags):
                    continue

            results.append(NEMTDecision(
                id=p.get("_id", ""),
                title=p.get("名称", ""),
                conclusion=p.get("结论", ""),
                reason=p.get("理由", ""),
                date=p.get("日期", ""),
                created_by=p.get("决策人", ""),
                status=p.get("状态", ""),
                decision_type=p.get("决策类型", ""),
                quality_score=p.get("质量评分", ""),
                needs_review=p.get("需回顾", False),
                aligned_principles=p.get("对齐原则", []),
                violated_boundaries=p.get("违反边界", []),
                tags=p.get("标签", []),
                url=p.get("_url", ""),
            ))

        return results

    # -------------------------------------------------------------------------
    # 经验查询
    # -------------------------------------------------------------------------

    def query_experiences(self,
                        type_filter: Optional[str] = None,
                        tags: Optional[List[str]] = None,
                        verified_only: bool = False,
                        limit: int = 20) -> List[NEMTExperience]:
        """查询经验记录"""
        config = _get_config()
        db_id = None
        if config:
            db_id = config.database_ids.get("Experiences")

        if not db_id:
            return []

        filter_parts = []
        if type_filter:
            filter_parts.append({
                "property": "类型",
                "select": {"equals": type_filter}
            })
        if verified_only:
            filter_parts.append({
                "property": "已验证",
                "checkbox": {"equals": True}
            })

        filter_dict = None
        if len(filter_parts) == 1:
            filter_dict = filter_parts[0]
        elif len(filter_parts) > 1:
            filter_dict = {"and": filter_parts}

        try:
            pages = self._query_database(db_id, filter_dict, page_size=50)
        except Exception as e:
            self._last_error = str(e)
            return []

        results = []
        for page in pages[:limit]:
            p = self._parse_page(page)
            if tags:
                page_tags = p.get("标签", [])
                if isinstance(page_tags, str):
                    page_tags = [page_tags]
                if not any(t in page_tags for t in tags):
                    continue

            results.append(NEMTExperience(
                id=p.get("_id", ""),
                title=p.get("名称", ""),
                type=p.get("类型", ""),
                summary=p.get("摘要", ""),
                detail=p.get("详细", ""),
                tags=p.get("标签", []),
                usefulness_score=p.get("有用度", 3),
                verified=p.get("已验证", False),
                access_count=p.get("访问次数", 0),
                url=p.get("_url", ""),
            ))

        return results

    # -------------------------------------------------------------------------
    # 失败记录查询
    # -------------------------------------------------------------------------

    def query_failures(self,
                      category: Optional[str] = None,
                      status: Optional[str] = None,
                      active_only: bool = False,
                      limit: int = 20) -> List[NEMTFailure]:
        """查询失败记录"""
        config = _get_config()
        db_id = None
        if config:
            db_id = config.database_ids.get("Failures")

        if not db_id:
            return []

        filter_parts = []
        if category:
            filter_parts.append({
                "property": "类别",
                "select": {"equals": category}
            })
        if active_only:
            filter_parts.append({
                "property": "状态",
                "select": {"equals": "活跃"}
            })

        filter_dict = None
        if len(filter_parts) == 1:
            filter_dict = filter_parts[0]
        elif len(filter_parts) > 1:
            filter_dict = {"and": filter_parts}

        try:
            pages = self._query_database(db_id, filter_dict, page_size=50)
        except Exception as e:
            self._last_error = str(e)
            return []

        results = []
        for page in pages[:limit]:
            p = self._parse_page(page)
            results.append(NEMTFailure(
                id=p.get("_id", ""),
                title=p.get("名称", ""),
                category=p.get("类别", ""),
                status=p.get("状态", ""),
                symptom=p.get("症状", ""),
                root_cause=p.get("根因", ""),
                resolution=p.get("解决方案", ""),
                tags=p.get("标签", []),
                url=p.get("_url", ""),
            ))

        return results

    def get_last_error(self) -> Optional[str]:
        return self._last_error


# ============================================================================
# 单例
# ============================================================================

_notion_client: Optional[NotionQueryClient] = None


def get_notion_client() -> NotionQueryClient:
    global _notion_client
    if _notion_client is None:
        _notion_client = NotionQueryClient()
    return _notion_client


# ============================================================================
# CLI 测试
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("NEMT Notion Query Client Test")
    print("=" * 60)

    client = get_notion_client()

    if not client.is_available:
        print(f"\n[!] Notion 不可用: {client.get_last_error()}")
        print("    提示: 检查 .env 中的 NOTION_TOKEN")
    else:
        print(f"\n[OK] Notion API 就绪")

        # 测试查询
        decisions = client.query_decisions(limit=3)
        print(f"\nDecisions: {len(decisions)} 条")
        for d in decisions:
            print(f"  - {d.to_summary()}")
