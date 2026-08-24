# Copyright 2026 NEMT Lab
"""
NEMT Memory System - Memory Writer
==================================
记忆写入引擎，处理 T1-T5 触发器

T1: 显式触发（用户说"记录这个决定"）
T2: 决策隐式触发（做了技术选择/架构决策）
T3: 经验隐式触发（成功解决了一个问题）
T4: 错误隐式触发（捕获到编译错误/运行时异常）
T5: 定时触发（会话结束时自动检查是否有未记录的重要信息）

设计原则：
- Notion 优先：优先写入 Notion
- 降级回退：Notion 不可用时写入本地 Markdown
- 防重复：检查最近 N 条记录，避免重复写入
- 质量门槛：只有超过阈值的记录才写入

使用方式：
    writer = MemoryWriter()

    # T1: 显式记录决策
    decision_id = writer.record_decision(
        title="集成验证层到 Pipeline",
        conclusion="方案A（嵌入Pipeline）更合适",
        reason="验证应与分析同步",
        decision_type="architecture",
        tags=["pipeline", "validation"],
    )

    # T2: 自动捕获技术决策
    writer.maybe_record_technical_decision(
        title="选择 TypeScript 验证引擎",
        conclusion="TypeScript 与 Pipeline 同语言，集成成本最低",
        reason="...对话内容...",
    )

    # T3: 记录经验
    writer.record_experience(
        title="Spectral Width 数值不稳定",
        type="mistake",
        summary="NLS 求解器对极端价格序列产生 overflow",
        detail="根因：价格序列方差过大... 解决方案：Override spectral width...",
        tags=["validation", "core"],
    )

    # T4: 记录失败
    writer.record_failure(
        title="Phase D 检测持续失效",
        category="validation",
        symptom="批量验证中 Phase D 准确率仅 25%",
        root_cause="determinePhase 逻辑过于依赖 DCI，忽略了 spectral_width",
        resolution="重构 determinePhase，优先使用 spectral_width 阈值",
        tags=["pipeline", "validation"],
    )

    # T5: 会话结束检查
    writer.session_end_check(session_transcript="...")
"""

import os
import re
import sys
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

# 确保可以直接运行或作为包导入
_self_dir = os.path.dirname(os.path.abspath(__file__))
if _self_dir not in sys.path:
    sys.path.insert(0, _self_dir)

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


# ============================================================================
# 触发器定义
# ============================================================================

@dataclass
class TriggerResult:
    """触发器执行结果"""
    triggered: bool
    trigger_type: str       # T1/T2/T3/T4/T5
    record_type: str        # decision/experience/failure
    title: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0  # 0.0-1.0
    reason: str = ""        # 为什么触发
    skip_reason: str = ""   # 为什么跳过
    written: bool = False
    notion_id: str = ""
    local_id: str = ""


# ============================================================================
# T1-T5 触发器引擎
# ============================================================================

class TriggerEngine:
    """
    T1-T5 触发器引擎

    每个触发器有两个核心方法：
    - detect(): 从上下文中检测是否触发
    - should_write(): 检测通过后，判断是否值得写入（质量门槛）
    """

    # 防重复窗口（小时）：在此窗口内的相似记录不会被重复写入
    DEDUP_WINDOW_HOURS = 24

    # 最小置信度阈值：低于此值的记录不写入
    MIN_CONFIDENCE = 0.6

    # 关键词模式
    DECISION_PATTERNS = [
        r"决定\s*[\uff1a:]\s*(\S.{0,100})",
        r"选择\s*[\uff1a:]\s*(\S.{0,100})",
        r"采纳\s*[\uff1a:]\s*(\S.{0,100})",
        r"采用\s*[\uff1a:]\s*(\S.{0,100})",
        r"方案\s*[ABab][\uff1a:]\s*(\S.{0,100})",
        r"决策\s*[\uff1a:]\s*(\S.{0,100})",
        r"implement|implementing|implemented|implementation",
        r"Option\s*[ABab][\uff1a:]\s*(\S.{0,100})",
        r"choose|chose|choice",
        r"adopt|adopting|adopted",
        r"decide|deciding|decided",
    ]

    SUCCESS_PATTERNS = [
        r"修复了?\s*(.*)",
        r"解决了?\s*(.*)",
        r"成功了?\s*(.*)",
        r"完成\s*(.*)",
        r"working|works|fixed|solved",
        r"成功\s*[\uff1a:]\s*(.*)",
        r"解决了?\s*[\uff1a:]\s*(.*)",
    ]

    ERROR_PATTERNS = [
        r"error\s*[\uff1a:]\s*(.*)",
        r"failed\s*[\uff1a:]\s*(.*)",
        r"异常\s*[\uff1a:]\s*(.*)",
        r"失败\s*[\uff1a:]\s*(.*)",
        r"SyntaxError|RuntimeError|TypeError|ImportError",
        r"TypeScript.*error|tsc.*error|error\s+TS\d+",
    ]

    EXPLICIT_RECORD_TRIGGERS = [
        "记录", "写下来", "memori", "remember",
        "记一下", "保存这个", "capture", "log this",
    ]

    def __init__(self):
        self._recent_titles: List[tuple[str, datetime]] = []  # (title, timestamp)

    def _is_duplicate(self, title: str) -> bool:
        """检查是否重复"""
        title_normalized = title.lower().strip()
        now = datetime.now()

        # 清理旧记录
        self._recent_titles = [
            (t, dt) for t, dt in self._recent_titles
            if (now - dt).total_seconds() < self.DEDUP_WINDOW_HOURS * 3600
        ]

        for existing_title, _ in self._recent_titles:
            if existing_title.lower().strip() == title_normalized:
                return True

        self._recent_titles.append((title, now))
        return False

    def _extract_title_from_text(self, text: str, patterns: List[str]) -> Optional[str]:
        """从文本中提取标题"""
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extracted = match.group(1).strip()
                    if len(extracted) > 5:
                        return extracted[:80]
            except Exception:
                pass
        return None

    # -------------------------------------------------------------------------
    # T1: 显式触发
    # -------------------------------------------------------------------------

    def detect_T1(self, user_message: str, agent_response: str = "") -> TriggerResult:
        """T1: 用户显式要求记录"""
        combined = f"{user_message} {agent_response}".lower()

        triggered = any(trigger in combined for trigger in self.EXPLICIT_RECORD_TRIGGERS)

        if not triggered:
            return TriggerResult(triggered=False, trigger_type="T1", record_type="decision")

        # 尝试提取内容
        title = None
        decision_type = "general"

        # 尝试从上下文中提取
        for pattern in self.DECISION_PATTERNS:
            title = self._extract_title_from_text(user_message + " " + agent_response, [pattern])
            if title:
                break

        if not title:
            title = user_message[:60].strip()

        # 判断类型
        if any(k in combined for k in ["架构", "architecture", "方案", "option"]):
            decision_type = "architecture"
        elif any(k in combined for k in ["技术", "technical", "选型"]):
            decision_type = "technical"
        elif any(k in combined for k in ["优先", "priority"]):
            decision_type = "priority"

        return TriggerResult(
            triggered=True,
            trigger_type="T1",
            record_type="decision",
            title=title,
            content={
                "decision_type": decision_type,
                "confidence": 0.95,
            },
            confidence=0.95,
            reason="用户显式请求记录",
        )

    # -------------------------------------------------------------------------
    # T2: 决策隐式触发
    # -------------------------------------------------------------------------

    def detect_T2(self, user_message: str, agent_response: str) -> TriggerResult:
        """T2: 技术决策隐式触发"""
        combined = f"{user_message} {agent_response}"

        # 检测决策相关关键词
        decision_keywords = [
            "方案", "选项", "选择", "决定", "采纳",
            "implement", "option", "choose", "adopt", "decide",
            "方案A", "方案B", "Option A", "Option B",
        ]
        has_decision = any(kw in combined for kw in decision_keywords)
        has_code = len(agent_response) > 200  # 大量代码 = 做了实现决策

        if not (has_decision or has_code):
            return TriggerResult(triggered=False, trigger_type="T2", record_type="decision")

        # 提取决策内容
        title = None
        for pattern in self.DECISION_PATTERNS:
            title = self._extract_title_from_text(combined, [pattern])
            if title:
                break

        if not title:
            title = agent_response[:60].strip() if agent_response else user_message[:60].strip()

        # 判断决策类型
        decision_type = "general"
        if any(k in combined for k in ["架构", "layer", "component", "service"]):
            decision_type = "architecture"
        elif any(k in combined for k in ["技术", "language", "framework", "tool"]):
            decision_type = "technical"
        elif any(k in combined for k in ["验证", "validation", "constraint"]):
            decision_type = "validation"
        elif any(k in combined for k in ["pipeline", "pipeline", "流程"]):
            decision_type = "pipeline"

        # 提取结论（agent 响应中的肯定性语句）
        conclusion = ""
        positive_patterns = [
            r"（方案\w）", r"（option\s*\w）",
            r"更合适", r"更好", r"采用", r"使用",
            r"is better", r"choose", r"adopt", r"implement",
        ]
        for pattern in positive_patterns:
            match = re.search(pattern, agent_response)
            if match:
                conclusion = match.group(0)
                break

        confidence = 0.7 if has_decision else 0.5

        return TriggerResult(
            triggered=True,
            trigger_type="T2",
            record_type="decision",
            title=title,
            content={
                "decision_type": decision_type,
                "conclusion": conclusion,
                "confidence": confidence,
            },
            confidence=confidence,
            reason=f"检测到技术决策（类型={decision_type}）",
        )

    # -------------------------------------------------------------------------
    # T3: 经验隐式触发
    # -------------------------------------------------------------------------

    def detect_T3(self, agent_response: str) -> TriggerResult:
        """T3: 成功经验隐式触发"""
        # 检测成功信号
        success_keywords = [
            "修复了", "解决了", "成功了", "完成",
            "working", "works", "fixed", "solved", "completed",
            "✅", "success", "done",
        ]
        has_success = any(kw in agent_response for kw in success_keywords)
        has_fix = "fix" in agent_response.lower() and "error" in agent_response.lower()

        if not (has_success or has_fix):
            return TriggerResult(triggered=False, trigger_type="T3", record_type="experience")

        # 提取成功内容
        title = None
        for pattern in self.SUCCESS_PATTERNS:
            title = self._extract_title_from_text(agent_response, [pattern])
            if title:
                break

        if not title:
            # 从第一行提取
            first_line = agent_response.split("\n")[0][:60].strip()
            title = first_line if first_line else "解决了一个问题"

        exp_type = "solution"
        if "fix" in agent_response.lower():
            exp_type = "mistake"  # 修复错误 = 教训

        confidence = 0.75 if has_fix else 0.65

        return TriggerResult(
            triggered=True,
            trigger_type="T3",
            record_type="experience",
            title=title,
            content={
                "type": exp_type,
                "summary": title,
                "detail": agent_response[:500],
                "confidence": confidence,
            },
            confidence=confidence,
            reason="检测到成功经验",
        )

    # -------------------------------------------------------------------------
    # T4: 错误隐式触发
    # -------------------------------------------------------------------------

    def detect_T4(self, agent_response: str) -> TriggerResult:
        """T4: 错误/失败隐式触发"""
        # 检测错误信号
        error_keywords = [
            "error", "Error", "failed", "Failed", "异常",
            "失败", "SyntaxError", "RuntimeError", "TypeError",
            "ImportError", "Exception", "Traceback",
            "❌", "FAIL", "failed",
        ]
        has_error = any(kw in agent_response for kw in error_keywords)

        if not has_error:
            return TriggerResult(triggered=False, trigger_type="T4", record_type="failure")

        # 提取错误信息
        error_type = "general"
        for et in ["SyntaxError", "TypeError", "ImportError", "RuntimeError", "ValidationError"]:
            if et in agent_response:
                error_type = et.lower()
                break

        # 提取错误标题
        title = None
        for pattern in self.ERROR_PATTERNS:
            title = self._extract_title_from_text(agent_response, [pattern])
            if title:
                break

        if not title:
            title = f"{error_type.upper()} in response"

        # 提取错误详情
        detail_lines = []
        for line in agent_response.split("\n"):
            if any(kw in line for kw in error_keywords):
                detail_lines.append(line.strip())
            if len(detail_lines) >= 10:
                break
        detail = "\n".join(detail_lines[:5])

        return TriggerResult(
            triggered=True,
            trigger_type="T4",
            record_type="failure",
            title=title[:80],
            content={
                "category": "logic" if "error" in error_type else "general",
                "symptom": detail[:200],
                "status": "active",
                "confidence": 0.9,
            },
            confidence=0.9,
            reason=f"检测到错误（类型={error_type}）",
        )

    # -------------------------------------------------------------------------
    # T5: 定时触发（会话结束）
    # -------------------------------------------------------------------------

    def detect_T5(self, session_messages: List[str]) -> List[TriggerResult]:
        """T5: 会话结束检查

        分析整个会话，判断是否有值得记录的但尚未触发的内容。
        返回可能触发的记录列表（可能为空）。
        """
        results = []
        combined = "\n".join(session_messages)

        # 检查是否有重要但未记录的决策
        decision_count = 0
        for pattern in self.DECISION_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                decision_count += 1

        # 如果会话中有大量决策提及，可能需要总结
        if decision_count >= 3:
            results.append(TriggerResult(
                triggered=True,
                trigger_type="T5",
                record_type="decision",
                title=f"会话总结：{decision_count}个技术决策",
                content={
                    "decision_type": "summary",
                    "confidence": 0.5,
                    "session_messages": session_messages,
                },
                confidence=0.5,
                reason=f"会话中有 {decision_count} 个决策相关讨论",
            ))

        return results


# ============================================================================
# 记忆写入器
# ============================================================================

class MemoryWriter:
    """
    记忆写入器

    整合触发器引擎、Notion 客户端、本地回退存储。
    提供统一的写入接口。

    使用方式：
        writer = MemoryWriter()

        # 写入决策
        result = writer.write_decision(
            title="...",
            conclusion="...",
            reason="...",
            decision_type="architecture",
        )
        if result.written:
            print(f"已写入 Notion: {result.notion_id}")
        else:
            print(f"已写入本地: {result.local_id}")
    """

    def __init__(self):
        self._trigger_engine = TriggerEngine()
        self._notion_client = None
        self._local_store = None
        self._notion_write_client = None

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

    def _get_notion_write_client(self):
        """获取 Notion 写入客户端（与查询客户端不同，需要创建页面）"""
        if self._notion_write_client is None:
            config = None
            try:
                from nemt_sync_config import get_config
                config = get_config()
            except ImportError:
                pass

            if not config or not config.notion_token:
                return None

            import requests
            self._notion_write_client = requests
            self._write_token = config.notion_token

        return self._notion_write_client

    def _write_to_notion(self, db_name: str, properties: Dict, page_content: List[Dict]) -> Optional[str]:
        """写入 Notion 数据库"""
        config = None
        try:
            from nemt_sync_config import get_config
            config = get_config()
        except ImportError:
            pass

        if not config or not config.notion_token:
            return None

        db_id = config.database_ids.get(db_name)
        if not db_id:
            return None

        import requests
        url = f"https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {config.notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        # 构建 parent
        parent = {"database_id": db_id}

        # 构建 properties
        page_props = {}
        for key, value in properties.items():
            if value is None or value == "":
                continue

            if key == "名称":
                page_props[key] = {
                    "title": [{"text": {"content": str(value)}}]
                }
            elif isinstance(value, bool):
                page_props[key] = {"checkbox": value}
            elif isinstance(value, (int, float)):
                page_props[key] = {"number": value}
            elif isinstance(value, list) and value and isinstance(value[0], str):
                page_props[key] = {
                    "multi_select": [{"name": v} for v in value]
                }
            elif isinstance(value, str):
                page_props[key] = {
                    "select": {"name": value}
                } if value else {}

        data = {
            "parent": parent,
            "properties": page_props,
        }

        # 添加 children blocks
        if page_content:
            data["children"] = page_content

        try:
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            if resp.status_code == 200:
                result = resp.json()
                return result.get("id")
            else:
                print(f"[MemoryWriter] Notion 写入失败: {resp.status_code} {resp.text[:200]}")
                return None
        except Exception as e:
            print(f"[MemoryWriter] Notion 写入异常: {e}")
            return None

    # -------------------------------------------------------------------------
    # 写入决策
    # -------------------------------------------------------------------------

    def write_decision(self,
                     title: str,
                     conclusion: str = "",
                     reason: str = "",
                     decision_type: str = "general",
                     status: str = "adopted",
                     tags: Optional[List[str]] = None,
                     needs_review: bool = False,
                     aligned_principles: Optional[List[str]] = None,
                     override_notion: bool = False,
                     ) -> TriggerResult:
        """
        写入决策记录

        流程：
        1. 检查重复
        2. 优先写入 Notion
        3. Notion 失败则降级到本地
        """
        # 检查重复
        if self._trigger_engine._is_duplicate(title):
            return TriggerResult(
                triggered=True,
                trigger_type="T1",
                record_type="decision",
                title=title,
                skip_reason="重复记录（24小时窗口内）",
                confidence=1.0,
            )

        # 准备属性
        properties = {
            "名称": title,
            "结论": conclusion,
            "理由": reason,
            "决策类型": decision_type,
            "状态": status,
            "同步状态": "pending",
        }
        if tags:
            properties["标签"] = tags
        if needs_review:
            properties["需回顾"] = True
        if aligned_principles:
            properties["对齐原则"] = aligned_principles

        result = TriggerResult(
            triggered=True,
            trigger_type="T1",
            record_type="decision",
            title=title,
            content={
                "conclusion": conclusion,
                "reason": reason,
                "decision_type": decision_type,
                "tags": tags or [],
            },
            confidence=0.9,
            reason="显式写入",
        )

        # 写入 Notion
        if not override_notion:
            notion_id = self._write_to_notion("Decisions", properties, [])
            if notion_id:
                result.written = True
                result.notion_id = notion_id
                return result

        # 降级到本地
        try:
            from local_fallback import DecisionRecord
            record = DecisionRecord(
                title=title,
                conclusion=conclusion,
                reason=reason,
                decision_type=decision_type,
                status=status,
                tags=tags or [],
                needs_review=needs_review,
                aligned_principles=aligned_principles or [],
                sync_status="pending",
            )
            if self.local_store:
                self.local_store.write_decision(record)
                result.written = True
                result.local_id = record.local_id
            else:
                result.skip_reason = "本地存储不可用"
        except Exception as e:
            result.skip_reason = f"本地写入失败: {e}"

        return result

    # -------------------------------------------------------------------------
    # 写入经验
    # -------------------------------------------------------------------------

    def write_experience(self,
                       title: str,
                       exp_type: str = "solution",
                       summary: str = "",
                       detail: str = "",
                       tags: Optional[List[str]] = None,
                       related_decisions: Optional[List[str]] = None,
                       override_notion: bool = False,
                       ) -> TriggerResult:
        """写入经验记录"""
        # 检查重复
        if self._trigger_engine._is_duplicate(title):
            return TriggerResult(
                triggered=True,
                trigger_type="T3",
                record_type="experience",
                title=title,
                skip_reason="重复记录",
                confidence=1.0,
            )

        properties = {
            "名称": title,
            "类型": exp_type,
            "摘要": summary,
            "详细": detail,
            "同步状态": "pending",
        }
        if tags:
            properties["标签"] = tags

        result = TriggerResult(
            triggered=True,
            trigger_type="T3",
            record_type="experience",
            title=title,
            content={
                "type": exp_type,
                "summary": summary,
                "detail": detail,
                "tags": tags or [],
            },
            confidence=0.8,
            reason="经验写入",
        )

        # 写入 Notion
        if not override_notion:
            notion_id = self._write_to_notion("Experiences", properties, [])
            if notion_id:
                result.written = True
                result.notion_id = notion_id
                return result

        # 降级到本地
        try:
            from local_fallback import ExperienceRecord
            record = ExperienceRecord(
                title=title,
                type=exp_type,
                summary=summary,
                detail=detail,
                tags=tags or [],
                related_decisions=related_decisions or [],
                sync_status="pending",
            )
            if self.local_store:
                self.local_store.write_experience(record)
                result.written = True
                result.local_id = record.local_id
            else:
                result.skip_reason = "本地存储不可用"
        except Exception as e:
            result.skip_reason = f"本地写入失败: {e}"

        return result

    # -------------------------------------------------------------------------
    # 写入失败记录
    # -------------------------------------------------------------------------

    def write_failure(self,
                    title: str,
                    category: str = "general",
                    symptom: str = "",
                    root_cause: str = "",
                    resolution: str = "",
                    status: str = "active",
                    tags: Optional[List[str]] = None,
                    override_notion: bool = False,
                    ) -> TriggerResult:
        """写入失败记录"""
        # 检查重复
        if self._trigger_engine._is_duplicate(title):
            return TriggerResult(
                triggered=True,
                trigger_type="T4",
                record_type="failure",
                title=title,
                skip_reason="重复记录",
                confidence=1.0,
            )

        properties = {
            "名称": title,
            "类别": category,
            "状态": status,
            "症状": symptom,
            "根因": root_cause,
            "解决方案": resolution,
            "同步状态": "pending",
        }
        if tags:
            properties["标签"] = tags

        result = TriggerResult(
            triggered=True,
            trigger_type="T4",
            record_type="failure",
            title=title,
            content={
                "category": category,
                "symptom": symptom,
                "root_cause": root_cause,
                "resolution": resolution,
                "tags": tags or [],
            },
            confidence=0.9,
            reason="失败记录写入",
        )

        # 写入 Notion
        if not override_notion:
            notion_id = self._write_to_notion("Failures", properties, [])
            if notion_id:
                result.written = True
                result.notion_id = notion_id
                return result

        # 降级到本地
        try:
            from local_fallback import FailureRecord
            record = FailureRecord(
                title=title,
                category=category,
                status=status,
                symptom=symptom,
                root_cause=root_cause,
                resolution=resolution,
                tags=tags or [],
                sync_status="pending",
            )
            if self.local_store:
                self.local_store.write_failure(record)
                result.written = True
                result.local_id = record.local_id
            else:
                result.skip_reason = "本地存储不可用"
        except Exception as e:
            result.skip_reason = f"本地写入失败: {e}"

        return result

    # -------------------------------------------------------------------------
    # 自动触发检测
    # -------------------------------------------------------------------------

    def auto_detect(self,
                  user_message: str,
                  agent_response: str,
                  session_messages: Optional[List[str]] = None) -> List[TriggerResult]:
        """
        自动检测所有触发器

        在每次 Agent 响应后调用此方法。
        """
        results = []

        # T1: 显式触发
        r = self._trigger_engine.detect_T1(user_message, agent_response)
        if r.triggered and r.confidence >= self._trigger_engine.MIN_CONFIDENCE:
            results.append(r)

        # T2: 决策隐式触发
        r = self._trigger_engine.detect_T2(user_message, agent_response)
        if r.triggered and r.confidence >= self._trigger_engine.MIN_CONFIDENCE:
            if not self._trigger_engine._is_duplicate(r.title):
                results.append(r)

        # T3: 经验隐式触发
        r = self._trigger_engine.detect_T3(agent_response)
        if r.triggered and r.confidence >= self._trigger_engine.MIN_CONFIDENCE:
            if not self._trigger_engine._is_duplicate(r.title):
                results.append(r)

        # T4: 错误隐式触发
        r = self._trigger_engine.detect_T4(agent_response)
        if r.triggered and r.confidence >= self._trigger_engine.MIN_CONFIDENCE:
            if not self._trigger_engine._is_duplicate(r.title):
                results.append(r)

        # T5: 会话结束
        if session_messages:
            t5_results = self._trigger_engine.detect_T5(session_messages)
            for r in t5_results:
                if r.confidence >= self._trigger_engine.MIN_CONFIDENCE:
                    results.append(r)

        return results

    def auto_write(self,
                  user_message: str,
                  agent_response: str,
                  session_messages: Optional[List[str]] = None,
                  dry_run: bool = False) -> List[TriggerResult]:
        """
        自动检测并写入所有触发器

        Args:
            dry_run: True = 只检测不写入（用于测试）
        """
        detected = self.auto_detect(user_message, agent_response, session_messages)
        written_results = []

        for result in detected:
            if dry_run:
                written_results.append(result)
                continue

            # 执行写入
            if result.record_type == "decision":
                write_result = self.write_decision(
                    title=result.title,
                    decision_type=result.content.get("decision_type", "general"),
                    conclusion=result.content.get("conclusion", ""),
                    reason=result.content.get("reason", ""),
                    tags=result.content.get("tags", []),
                )
                result.written = write_result.written
                result.notion_id = write_result.notion_id
                result.local_id = write_result.local_id

            elif result.record_type == "experience":
                write_result = self.write_experience(
                    title=result.title,
                    exp_type=result.content.get("type", "solution"),
                    summary=result.content.get("summary", ""),
                    detail=result.content.get("detail", ""),
                    tags=result.content.get("tags", []),
                )
                result.written = write_result.written
                result.notion_id = write_result.notion_id
                result.local_id = write_result.local_id

            elif result.record_type == "failure":
                write_result = self.write_failure(
                    title=result.title,
                    category=result.content.get("category", "general"),
                    symptom=result.content.get("symptom", ""),
                    root_cause=result.content.get("root_cause", ""),
                    resolution=result.content.get("resolution", ""),
                    tags=result.content.get("tags", []),
                )
                result.written = write_result.written
                result.notion_id = write_result.notion_id
                result.local_id = write_result.local_id

            written_results.append(result)

        return written_results


# ============================================================================
# 单例
# ============================================================================

_memory_writer: Optional[MemoryWriter] = None


def get_memory_writer() -> MemoryWriter:
    global _memory_writer
    if _memory_writer is None:
        _memory_writer = MemoryWriter()
    return _memory_writer


# ============================================================================
# CLI 测试
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("NEMT Memory Writer - Trigger Test")
    print("=" * 60)

    writer = get_memory_writer()
    engine = TriggerEngine()

    # 测试用例
    test_cases = [
        ("T1", "把这次讨论记录下来", "好的，我来实现方案A..."),
        ("T2", "我们应该选择哪个方案？", "方案A更好..."),
        ("T3", "", "✅ 修复了 spectral width 的问题"),
        ("T4", "", "❌ TypeError: 'NoneType' object has no attribute..."),
    ]

    for t_type, user_msg, agent_resp in test_cases:
        if t_type == "T1":
            result = engine.detect_T1(user_msg, agent_resp)
        elif t_type == "T2":
            result = engine.detect_T2(user_msg, agent_resp)
        elif t_type == "T3":
            result = engine.detect_T3(agent_resp)
        elif t_type == "T4":
            result = engine.detect_T4(agent_resp)
        else:
            continue

        print(f"\n[{t_type}] triggered={result.triggered}, confidence={result.confidence:.2f}")
        if result.triggered:
            print(f"  title: {result.title}")
            print(f"  reason: {result.reason}")
            print(f"  type: {result.record_type}")

    print("\n" + "=" * 60)
    print("Write Test")
    print("=" * 60)

    # 测试写入（会写入本地）
    result = writer.write_decision(
        title="测试决策：Memory Writer 集成验证层",
        conclusion="方案A（嵌入Pipeline）更合适",
        reason="验证应与分析同步执行",
        decision_type="architecture",
        tags=["pipeline", "validation"],
    )
    print(f"\n写入结果: written={result.written}")
    if result.written:
        if result.notion_id:
            print(f"  Notion ID: {result.notion_id}")
        if result.local_id:
            print(f"  Local ID: {result.local_id}")
    if result.skip_reason:
        print(f"  跳过: {result.skip_reason}")
