#!/usr/bin/env python3
"""
一键方案生成器
==============

根据项目当前状态和上下文，自动生成技术方案并可选择存入Notion。

使用方法:
    # 生成方案并输出JSON
    python design_generator.py

    # 生成方案并保存到Notion
    python design_generator.py --save

    # 指定方案类型
    python design_generator.py --type "BrainLayer实现"

    # 交互式生成
    python design_generator.py --interactive

    # 查看历史方案
    python design_generator.py --list
"""

import os
import sys
import json
import urllib.request
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

# 配置
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "ntn_s640536110656ijG4LStAQzrntOjxNtIhVajRcYSh68eWt")
NOTION_SCHEMES_DB = os.getenv("NOTION_SCHEMES_DB", "")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

BASE_URL = "https://api.notion.com/v1"


# ============================================================================
# 数据结构
# ============================================================================

@dataclass
class DesignScheme:
    """设计方案"""
    scheme_name: str
    background: str
    design_decisions: List[str]
    affected_modules: List[str]
    interface_changes: str
    acceptance_criteria: List[str]
    estimated_hours: int
    markdown_explanation: str
    reviewer: str = ""
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# ============================================================================
# 项目上下文分析
# ============================================================================

PROJECT_CONTEXT = {
    "project_name": "NEMT量化系统",
    "project_type": "量化交易系统",
    "core_modules": [
        "nemt_core.py - NLS方程核心算法",
        "nemt_signals.py - 信号指标",
        "nemt_state_machine.py - 四相位状态机",
        "nemt_risk.py - 风险管理",
        "nemt_execution.py - 执行框架",
        "nemt_onchain.py - 链上数据",
        "data_fetcher.py - 数据获取",
        "visualizer.py - 可视化"
    ],
    "pending_modules": [
        "brain_layer.py - 大脑层 (待实现)",
        "evolution_layer.py - 进化层 (待实现)",
        "backtest_engine.py - 回测引擎 (待实现)"
    ],
    "recent_issues": [],
    "current_milestone": "v0.1 - 核心验证",
    "next_milestone": "v0.2 - 风控完善"
}


def analyze_project_status() -> Dict[str, Any]:
    """分析项目当前状态"""
    return {
        "project": PROJECT_CONTEXT,
        "timestamp": datetime.now().isoformat(),
        "analysis": {
            "completed_modules": len(PROJECT_CONTEXT["core_modules"]),
            "pending_modules": len(PROJECT_CONTEXT["pending_modules"]),
            "ready_for": ["BrainLayer", "EvolutionLayer", "BacktestEngine"]
        }
    }


# ============================================================================
# 方案生成器
# ============================================================================

class DesignSchemeGenerator:
    """方案生成器"""

    def __init__(self, context: Dict[str, Any] = None):
        self.context = context or analyze_project_status()

    def generate_brain_layer_scheme(self) -> DesignScheme:
        """生成 BrainLayer 实现方案"""
        return DesignScheme(
            scheme_name="BrainLayer Node 实现 - 策略权重与资金调度",
            background="""
当前 NEMT 系统已完成核心算法层 (NEMTCore)、信号层 (SignalLayer)、风控层 (RiskLayer)、
执行层 (ExecutionLayer)，但缺少大脑层 (BrainLayer) 来统一协调各层决策。

BrainLayer 的职责：
1. 策略权重分配 - 根据历史表现和当前市场状态动态分配策略权重
2. 资金调度管理 - 多策略间的资金分配和紧急预留
3. 风险模式切换 - 根据市场状态切换正常/警戒/紧急模式
4. 策略生死判断 - 评估策略表现，决定暂停/恢复/淘汰

这是 v0.2 里程碑的核心任务。
            """,
            design_decisions=[
                "决策1: 采用分层权重架构 - 将策略分为核心策略(60%)和卫星策略(40%)，核心策略权重相对稳定，卫星策略根据近期表现动态调整",
                "决策2: 引入资金调度中心 - 统一管理所有策略的资金分配，设置10%紧急备用金，剩余90%按权重分配",
                "决策3: 三级风险模式 - 正常模式(标准风控)、警戒模式(收紧20%仓位)、紧急模式(降仓50%+)，根据最大回撤自动切换",
                "决策4: 评分淘汰机制 - 每周计算策略评分，连续2周低于阈值自动标记，由人工确认是否淘汰"
            ],
            affected_modules=[
                "BrainLayer (新增)",
                "StrategyLayer (需改造)",
                "RiskLayer (需集成)",
                "ExecutionLayer (需集成)"
            ],
            interface_changes="""
// BrainLayer 接口
interface IBrainLayer {
    // 策略权重管理
    calculate_weights(strategies: Strategy[]): Weights
    adjust_weights(performance: Performance[]): Weights

    // 资金调度
    allocateFunds(total: number): Allocation
    reserveEmergency(): number

    // 风险模式
    getRiskMode(): 'normal' | 'warning' | 'emergency'
    switchMode(mode: RiskMode): void

    // 策略管理
    scoreStrategy(strategy: Strategy): Score
    shouldTerminate(strategy: Strategy): boolean
}
            """,
            acceptance_criteria=[
                "BrainLayer 可独立运行单元测试",
                "权重计算结果可复现",
                "资金分配不超过账户总额",
                "风险模式切换有明确日志",
                "策略评分与历史数据一致",
                "与现有ExecutionLayer无缝集成"
            ],
            estimated_hours=16,
            markdown_explanation="""
# BrainLayer 实现方案

## 概述

BrainLayer 是 NEMT 系统的大脑，负责协调各层决策，实现策略的动态管理和资金的智能调度。

## 模块结构

```
BrainLayer/
├── __init__.py
├── weights.py       # 策略权重管理
├── allocation.py    # 资金调度
├── risk_mode.py    # 风险模式切换
└── scoring.py       # 策略评分
```

## 核心算法

### 1. 权重计算
```python
def calculate_weights(strategies: List[Strategy]) -> Dict[str, float]:
    """
    基于历史表现和近期表现计算策略权重
    - 历史夏普比率 (权重40%)
    - 近30天胜率 (权重30%)
    - 相关性调整 (权重30%)
    """
```

### 2. 资金分配
```python
def allocate_funds(total: float, weights: Dict[str, float]) -> Dict[str, float]:
    """
    按权重分配资金，预留紧急备用金
    - 总资金 * 0.9 = 可用资金
    - 可用资金 * 策略权重 = 策略资金
    """
```

## 实施计划

| 阶段 | 任务 | 工时 |
|------|------|------|
| 1 | 接口定义 | 2h |
| 2 | 权重计算 | 4h |
| 3 | 资金分配 | 3h |
| 4 | 风险模式 | 3h |
| 5 | 策略评分 | 2h |
| 6 | 集成测试 | 2h |
| **合计** | | **16h** |
            """
        )

    def generate_backtest_scheme(self) -> DesignScheme:
        """生成回测引擎方案"""
        return DesignScheme(
            scheme_name="BacktestEngine 实现 - 历史数据回测框架",
            background="""
NEMT 系统目前只能进行实时交易模拟，缺少历史回测能力。
回测引擎是量化系统的基础组件，用于验证策略在历史数据上的表现。

回测引擎的职责：
1. 历史数据回放 - 模拟历史市场环境
2. 模拟交易执行 - 订单撮合、滑点计算、手续费
3. 性能指标计算 - 夏普比率、最大回撤、胜率等
4. 回测报告生成 - 可视化结果、统计分析
            """,
            design_decisions=[
                "决策1: 基于事件驱动的回测 - 比向量回测更精确，支持复杂策略逻辑",
                "决策2: 滑点模型 - 采用固定滑点(0.1%) + 流动性调整",
                "决策3: 手续费模型 - 按交易对设置不同费率，支持maker/taker",
                "决策4: 多数据源支持 - Binance/OKX/CSV文件"
            ],
            affected_modules=[
                "BacktestEngine (新增)",
                "NEMTCore (复用)",
                "SignalLayer (复用)",
                "RiskLayer (复用)"
            ],
            interface_changes="""
class BacktestEngine:
    def __init__(self, config: BacktestConfig):
        self.config = config

    def run(self, strategy: Strategy, data: pd.DataFrame) -> BacktestResult:
        '''运行回测'''

    def get_equity_curve(self) -> pd.Series:
        '''获取权益曲线'''

    def get_trades(self) -> List[Trade]:
        '''获取交易记录'''

    def get_metrics(self) -> PerformanceMetrics:
        '''获取性能指标'''
            """,
            acceptance_criteria=[
                "支持至少1年的BTC历史数据回测",
                "回测结果与实时模拟一致",
                "支持多策略同时回测",
                "生成HTML回测报告",
                "回测速度 > 1000 bars/秒"
            ],
            estimated_hours=24
        )

    def generate_scheme(self, scheme_type: str = None) -> DesignScheme:
        """根据类型生成方案"""
        schemes = {
            "brain_layer": self.generate_brain_layer_scheme,
            "backtest": self.generate_backtest_scheme,
        }

        if scheme_type and scheme_type.lower() in schemes:
            return schemes[scheme_type.lower()]()

        # 默认返回优先级最高的方案
        return self.generate_brain_layer_scheme()


# ============================================================================
# Notion 集成
# ============================================================================

def save_to_notion(scheme: DesignScheme, database_id: str = None) -> Optional[str]:
    """保存方案到 Notion"""
    db_id = database_id or NOTION_SCHEMES_DB
    if not db_id:
        print("⚠️  未配置 NOTION_SCHEMES_DB，请手动保存")
        return None

    properties = {
        "方案名称": {
            "title": [{"text": {"content": scheme.scheme_name}}]
        },
        "状态": {"select": {"name": "📝 草案"}},
        "创建时间": {"date": {"start": datetime.now().isoformat()}},
        "审阅人": {"rich_text": [{"text": {"content": scheme.reviewer or "待指定"}}]},
        "背景": {"rich_text": [{"text": {"content": scheme.background.strip()}}]},
        "设计决策": {"rich_text": [{"text": {"content": "\n".join(scheme.design_decisions)}}]},
        "影响模块": {"multi_select": [{"name": m} for m in scheme.affected_modules]},
        "接口变更": {"rich_text": [{"text": {"content": scheme.interface_changes}}]},
        "验收标准": {"rich_text": [{"text": {"content": "\n".join(scheme.acceptance_criteria)}}]},
        "预估工时": {"number": scheme.estimated_hours},
        "详细说明": {"rich_text": [{"text": {"content": scheme.markdown_explanation}}]}
    }

    try:
        url = f"{BASE_URL}/pages"
        data = json.dumps({
            "parent": {"database_id": db_id},
            "properties": properties
        }).encode()

        req = urllib.request.Request(url, data=data, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            page_id = result.get("id", "")
            print(f"✅ 方案已保存到 Notion")
            print(f"   页面ID: {page_id}")
            print(f"   链接: https://notion.so/{page_id.replace('-', '')}")
            return page_id
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return None


def list_schemes_from_notion(database_id: str = None, status: str = None) -> List[Dict]:
    """从 Notion 列出方案"""
    db_id = database_id or NOTION_SCHEMES_DB
    if not db_id:
        print("⚠️  未配置 NOTION_SCHEMES_DB")
        return []

    filter_data = None
    if status:
        filter_data = {
            "property": "状态",
            "select": {"equals": status}
        }

    try:
        url = f"{BASE_URL}/databases/{db_id}/query"
        data = json.dumps({
            "filter": filter_data,
            "sorts": [{"timestamp": "created_time", "direction": "descending"}]
        }).encode()

        req = urllib.request.Request(url, data=data, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())

            schemes = []
            for page in result.get("results", []):
                props = page.get("properties", {})

                title = ""
                if "方案名称" in props and props["方案名称"].get("title"):
                    title = "".join([t.get("plain_text", "") for t in props["方案名称"]["title"]])

                scheme_status = ""
                if "状态" in props and props["状态"].get("select"):
                    scheme_status = props["状态"]["select"].get("name", "")

                hours = props.get("预估工时", {}).get("number", 0)

                schemes.append({
                    "id": page.get("id", ""),
                    "name": title,
                    "status": scheme_status,
                    "hours": hours,
                    "created": page.get("created_time", "")[:10]
                })

            return schemes
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return []


# ============================================================================
# CLI
# ============================================================================

def main():
    if len(sys.argv) < 2:
        # 默认：生成并输出
        generator = DesignSchemeGenerator()
        scheme = generator.generate_scheme()
        print(scheme.to_json())
        return

    cmd = sys.argv[1]

    if cmd == "--list":
        # 列出历史方案
        schemes = list_schemes_from_notion()
        print(f"\n{'='*60}")
        print(f"历史方案 ({len(schemes)} 个)")
        print(f"{'='*60}")

        for s in schemes:
            print(f"\n• {s['name']}")
            print(f"  状态: {s['status']}")
            print(f"  预估: {s['hours']}小时")
            print(f"  创建: {s['created']}")
            print(f"  ID: {s['id']}")

    elif cmd == "--save":
        # 生成并保存到 Notion
        generator = DesignSchemeGenerator()
        scheme = generator.generate_scheme()
        save_to_notion(scheme)

    elif cmd == "--type":
        # 指定类型
        if len(sys.argv) < 3:
            print("用法: python design_generator.py --type <类型>")
            print("可用类型: brain_layer, backtest")
            return

        scheme_type = sys.argv[2]
        generator = DesignSchemeGenerator()
        scheme = generator.generate_scheme(scheme_type)
        print(scheme.to_json())

    elif cmd == "--interactive":
        # 交互式生成
        print("\n" + "="*60)
        print("交互式方案生成器")
        print("="*60)

        print("\n请选择方案类型:")
        print("  1. BrainLayer 实现")
        print("  2. BacktestEngine 实现")
        print("  3. EvolutionLayer 实现")
        print("  4. 自定义方案")

        choice = input("\n请输入选项 (1-4): ").strip()

        type_map = {
            "1": "brain_layer",
            "2": "backtest"
        }

        generator = DesignSchemeGenerator()
        scheme_type = type_map.get(choice, None)
        scheme = generator.generate_scheme(scheme_type)

        print("\n" + "="*60)
        print("生成的方案:")
        print("="*60)
        print(scheme.to_json())

        save = input("\n是否保存到 Notion? (y/n): ").strip().lower()
        if save == "y":
            save_to_notion(scheme)

    else:
        print(f"未知命令: {cmd}")
        print("\n用法:")
        print("  python design_generator.py              # 生成方案并输出JSON")
        print("  python design_generator.py --list        # 列出历史方案")
        print("  python design_generator.py --save        # 生成并保存到Notion")
        print("  python design_generator.py --type brain_layer  # 指定方案类型")
        print("  python design_generator.py --interactive # 交互式生成")


if __name__ == "__main__":
    main()
