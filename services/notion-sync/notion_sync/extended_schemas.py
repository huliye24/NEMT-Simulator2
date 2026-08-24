# Copyright 2026 NEMT Lab
"""
NEMT Memory System - Extended Database Schemas
==============================================
扩展的 Notion 数据库 Schema，支撑方案 B 的记忆系统。

数据库列表（相比原 setup_databases.py 新增/扩展）：
1. Decisions  (扩展)   - 添加 conclusion/reason/quality_score 等字段
2. Experiences (新建)  - 经验沉淀数据库
3. Failures    (新建)  - 失败记录数据库（可与 Experience 合并）
4. Tasks       (扩展)  - 添加 decision_ref/blocking_reason 等字段

每个 Schema 是 dataclass，可以被 setup_databases.py 加载和创建。
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ExtendedDecisionSchema:
    """扩展后的决策记录数据库 Schema

    相比原 schema 新增字段：
    - conclusion: 一句话结论 [必须]
    - reason: 决策理由 [必须]
    - quality_score: 质量评分 (low/medium/high)
    - checkpoint: 是否需要定期回顾
    - aligned_principles: 对齐的愿景原则
    - violated_boundaries: 违反的边界
    """
    name: str = "Decisions"
    name_cn: str = "决策记录"
    description: str = "项目决策记录，包含背景、方案、结论和影响分析"
    icon: str = "⚖️"

    @staticmethod
    def get_schema() -> Dict[str, dict]:
        return {
            "名称": {
                "type": "title",
                "name": "名称"
            },
            "结论": {
                "type": "rich_text",
                "name": "结论",
                "description": "一句话结论 [必须填写]"
            },
            "理由": {
                "type": "rich_text",
                "name": "理由",
                "description": "决策理由和上下文 [必须填写]"
            },
            "日期": {
                "type": "date",
                "name": "日期"
            },
            "决策人": {
                "type": "select",
                "name": "决策人",
                "select_options": [
                    {"name": "Founder", "color": "purple"},
                    {"name": "CEO", "color": "red"},
                    {"name": "CTO", "color": "blue"},
                    {"name": "PM", "color": "pink"},
                    {"name": "TechLead", "color": "green"},
                    {"name": "Agent", "color": "gray"}
                ]
            },
            "状态": {
                "type": "select",
                "name": "状态",
                "select_options": [
                    {"name": "提议中", "color": "yellow"},
                    {"name": "已采纳", "color": "green"},
                    {"name": "已拒绝", "color": "red"},
                    {"name": "已替代", "color": "gray"},
                    {"name": "暂停", "color": "orange"}
                ]
            },
            "决策类型": {
                "type": "select",
                "name": "决策类型",
                "select_options": [
                    {"name": "架构", "color": "blue"},
                    {"name": "技术选型", "color": "purple"},
                    {"name": "方案选择", "color": "orange"},
                    {"name": "优先级", "color": "yellow"},
                    {"name": "边界调整", "color": "red"},
                    {"name": "重构", "color": "green"}
                ]
            },
            "质量评分": {
                "type": "select",
                "name": "质量评分",
                "select_options": [
                    {"name": "高", "color": "green"},
                    {"name": "中", "color": "yellow"},
                    {"name": "低", "color": "red"}
                ]
            },
            "需回顾": {
                "type": "checkbox",
                "name": "需回顾",
                "description": "勾选后会在 Checkpoint 中提醒"
            },
            "对齐原则": {
                "type": "multi_select",
                "name": "对齐原则",
                "multi_select_options": [
                    {"name": "策略即有机体", "color": "blue"},
                    {"name": "系统适应市场", "color": "green"},
                    {"name": "风险第一", "color": "red"},
                    {"name": "Kitchen Theory", "color": "orange"}
                ]
            },
            "违反边界": {
                "type": "multi_select",
                "name": "违反边界",
                "multi_select_options": [
                    {"name": "禁止实盘", "color": "red"},
                    {"name": "禁止前端", "color": "orange"},
                    {"name": "禁止付费数据", "color": "yellow"},
                    {"name": "禁止高频", "color": "gray"},
                    {"name": "禁止ML预测", "color": "purple"}
                ]
            },
            "标签": {
                "type": "multi_select",
                "name": "标签",
                "multi_select_options": [
                    {"name": "frontend", "color": "blue"},
                    {"name": "backend", "color": "green"},
                    {"name": "pipeline", "color": "purple"},
                    {"name": "validation", "color": "orange"},
                    {"name": "architecture", "color": "red"},
                    {"name": "core", "color": "yellow"}
                ]
            },
            "同步状态": {
                "type": "select",
                "name": "同步状态",
                "select_options": [
                    {"name": "已同步", "color": "green"},
                    {"name": "待同步", "color": "yellow"},
                    {"name": "同步失败", "color": "red"}
                ]
            },
            "最后同步": {
                "type": "date",
                "name": "最后同步"
            }
        }


@dataclass
class ExperienceSchema:
    """经验沉淀数据库 Schema

    用于记录：
    - solution: 成功解决问题的方案
    - mistake: 犯过的错误和教训
    - diagnostic: 诊断过程和根因分析
    - decision: 决策经验
    - observation: 重要观察
    """
    name: str = "Experiences"
    name_cn: str = "经验沉淀"
    description: str = "Agent 工作经验沉淀，包含成功方案、失败教训、诊断过程"
    icon: str = "🧠"

    @staticmethod
    def get_schema() -> Dict[str, dict]:
        return {
            "名称": {
                "type": "title",
                "name": "名称"
            },
            "类型": {
                "type": "select",
                "name": "类型",
                "select_options": [
                    {"name": "solution", "color": "green"},
                    {"name": "mistake", "color": "red"},
                    {"name": "diagnostic", "color": "orange"},
                    {"name": "decision", "color": "blue"},
                    {"name": "observation", "color": "purple"}
                ]
            },
            "摘要": {
                "type": "rich_text",
                "name": "摘要",
                "description": "一句话总结 [Agent 生成]"
            },
            "详细": {
                "type": "rich_text",
                "name": "详细",
                "description": "详细记录，包含上下文、做法、结果"
            },
            "有用度": {
                "type": "number",
                "name": "有用度",
                "number_format": "number",
                "description": "1-5 分，人类评分"
            },
            "访问次数": {
                "type": "number",
                "name": "访问次数",
                "number_format": "number"
            },
            "标签": {
                "type": "multi_select",
                "name": "标签",
                "multi_select_options": [
                    {"name": "frontend", "color": "blue"},
                    {"name": "backend", "color": "green"},
                    {"name": "pipeline", "color": "purple"},
                    {"name": "validation", "color": "orange"},
                    {"name": "architecture", "color": "red"},
                    {"name": "core", "color": "yellow"},
                    {"name": "notion", "color": "gray"}
                ]
            },
            "创建者": {
                "type": "select",
                "name": "创建者",
                "select_options": [
                    {"name": "Agent", "color": "gray"},
                    {"name": "Human", "color": "blue"},
                    {"name": "Auto", "color": "green"}
                ]
            },
            "已验证": {
                "type": "checkbox",
                "name": "已验证"
            },
            "已过时": {
                "type": "checkbox",
                "name": "已过时"
            },
            "需回顾": {
                "type": "checkbox",
                "name": "需回顾"
            },
            "关联决策": {
                "type": "relation",
                "name": "关联决策",
                "description": "关联的决策记录"
            },
            "同步状态": {
                "type": "select",
                "name": "同步状态",
                "select_options": [
                    {"name": "已同步", "color": "green"},
                    {"name": "待同步", "color": "yellow"},
                    {"name": "同步失败", "color": "red"}
                ]
            },
            "最后同步": {
                "type": "date",
                "name": "最后同步"
            }
        }


@dataclass
class FailureSchema:
    """失败记录数据库 Schema

    与 Experience 互补：
    - Experience: 正面经验（成功、教训）
    - Failure: 系统性追踪（症状、根因、状态）
    可与 Experience 合并为一个 DB，通过 type 区分。
    """
    name: str = "Failures"
    name_cn: str = "失败记录"
    description: str = "验证失败、约束违反、集成问题的追踪记录"
    icon: str = "🚨"

    @staticmethod
    def get_schema() -> Dict[str, dict]:
        return {
            "名称": {
                "type": "title",
                "name": "名称"
            },
            "类别": {
                "type": "select",
                "name": "类别",
                "select_options": [
                    {"name": "validation", "color": "red"},
                    {"name": "integration", "color": "orange"},
                    {"name": "logic", "color": "yellow"},
                    {"name": "data", "color": "blue"},
                    {"name": "boundary", "color": "purple"}
                ]
            },
            "状态": {
                "type": "select",
                "name": "状态",
                "select_options": [
                    {"name": "活跃", "color": "red"},
                    {"name": "调查中", "color": "yellow"},
                    {"name": "已解决", "color": "green"}
                ]
            },
            "症状": {
                "type": "rich_text",
                "name": "症状",
                "description": "问题表现描述"
            },
            "根因": {
                "type": "rich_text",
                "name": "根因",
                "description": "根因分析"
            },
            "解决方案": {
                "type": "rich_text",
                "name": "解决方案",
                "description": "解决方向或已执行的方案"
            },
            "标签": {
                "type": "multi_select",
                "name": "标签",
                "multi_select_options": [
                    {"name": "frontend", "color": "blue"},
                    {"name": "backend", "color": "green"},
                    {"name": "pipeline", "color": "purple"},
                    {"name": "validation", "color": "orange"},
                    {"name": "architecture", "color": "red"}
                ]
            },
            "关联决策": {
                "type": "relation",
                "name": "关联决策"
            },
            "解决时间": {
                "type": "date",
                "name": "解决时间"
            },
            "同步状态": {
                "type": "select",
                "name": "同步状态",
                "select_options": [
                    {"name": "已同步", "color": "green"},
                    {"name": "待同步", "color": "yellow"},
                    {"name": "同步失败", "color": "red"}
                ]
            },
            "最后同步": {
                "type": "date",
                "name": "最后同步"
            }
        }


# ============================================================================
# 扩展后的 Tasks Schema
# ============================================================================

@dataclass
class ExtendedTaskSchema:
    """扩展后的任务数据库 Schema

    相比原 schema 新增字段：
    - decision_ref: 关联的决策
    - phase_tags: 阶段标签
    - blocking_reason: 阻塞原因
    """
    name: str = "Tasks"
    name_cn: str = "任务"
    description: str = "Agent 任务管理"
    icon: str = "📋"

    @staticmethod
    def get_schema() -> Dict[str, dict]:
        return {
            "名称": {
                "type": "title",
                "name": "名称"
            },
            "状态": {
                "type": "select",
                "name": "状态",
                "select_options": [
                    {"name": "待办", "color": "gray"},
                    {"name": "进行中", "color": "yellow"},
                    {"name": "已完成", "color": "green"},
                    {"name": "已取消", "color": "red"},
                    {"name": "阻塞", "color": "orange"}
                ]
            },
            "优先级": {
                "type": "select",
                "name": "优先级",
                "select_options": [
                    {"name": "紧急", "color": "red"},
                    {"name": "高", "color": "orange"},
                    {"name": "中", "color": "yellow"},
                    {"name": "低", "color": "gray"}
                ]
            },
            "负责人": {
                "type": "select",
                "name": "负责人",
                "select_options": [
                    {"name": "Founder", "color": "purple"},
                    {"name": "CEO", "color": "red"},
                    {"name": "CTO", "color": "blue"},
                    {"name": "PM", "color": "pink"},
                    {"name": "TechLead", "color": "green"}
                ]
            },
            "截止日期": {
                "type": "date",
                "name": "截止日期"
            },
            "阶段": {
                "type": "select",
                "name": "阶段",
                "select_options": [
                    {"name": "M1-Backtesting", "color": "blue"},
                    {"name": "M2-BrainLayer", "color": "purple"},
                    {"name": "M3-NotionSync", "color": "green"},
                    {"name": "M4-MultiAgent", "color": "orange"}
                ]
            },
            "阻塞原因": {
                "type": "rich_text",
                "name": "阻塞原因"
            },
            "关联决策": {
                "type": "relation",
                "name": "关联决策"
            },
            "同步状态": {
                "type": "select",
                "name": "同步状态",
                "select_options": [
                    {"name": "已同步", "color": "green"},
                    {"name": "待同步", "color": "yellow"},
                    {"name": "同步失败", "color": "red"}
                ]
            },
            "最后同步": {
                "type": "date",
                "name": "最后同步"
            }
        }


# ============================================================================
# 所有扩展数据库列表
# ============================================================================

ALL_EXTENDED_SCHEMAS = [
    ExtendedDecisionSchema(),
    ExperienceSchema(),
    FailureSchema(),
    ExtendedTaskSchema(),
]


def get_all_schemas() -> List[dict]:
    """获取所有扩展 schema 的 dict 格式（供 setup 使用）"""
    result = []
    for schema in ALL_EXTENDED_SCHEMAS:
        result.append({
            "name": schema.name,
            "name_cn": schema.name_cn,
            "description": schema.description,
            "icon": schema.icon,
            "schema": schema.get_schema()
        })
    return result
