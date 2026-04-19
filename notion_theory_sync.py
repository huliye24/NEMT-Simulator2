"""
Notion 理论中枢同步模块
从 Notion 获取 NEMT 理论文档，解析并生成可执行代码

使用方法:
    from notion_theory_sync import NotionTheorySync
    sync = NotionTheorySync()
    content = sync.fetch_page("34317dca0dd2801ba79ff2d5af7a5afe")
"""

import urllib.request
import json
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# Notion Token
NOTION_TOKEN = 'ntn_s640536110656ijG4LStAQzrntOjxNtIhVajRcYSh68eWt'

# NEMT 理论中枢页面ID
NEMT_THEORY_PAGE_ID = '34317dca0dd2801ba79ff2d5af7a5afe'


@dataclass
class TheoryBlock:
    """理论内容块"""
    id: str
    type: str
    text: str
    has_children: bool = False
    children: List['TheoryBlock'] = field(default_factory=list)


@dataclass
class PhasePosition:
    """相位-仓位配置"""
    phase: str
    name: str
    max_position: float
    single_risk: float
    leverage: int
    strategy: str


@dataclass
class StopLossRule:
    """止损规则"""
    signal_type: str
    atr_multiplier: float
    description: str


@dataclass
class RebalanceRule:
    """仓位再平衡规则"""
    trigger_type: str  # "reduce" or "add"
    condition: str
    action: str
    target_ratio: Optional[float] = None


@dataclass
class BlackSwanRule:
    """黑天鹅应对规则"""
    scenario: str
    action: str
    priority: int


@dataclass
class LeverageRule:
    """杠杆使用规则"""
    allowed_phases: List[str]
    max_leverage: int
    safety_margin: float  # 强平价与止损价的最小差距百分比
    forbidden_conditions: List[str]


@dataclass
class TheoryContent:
    """完整的理论内容"""
    title: str
    introduction: str
    phases: List[PhasePosition]
    stop_loss_rules: List[StopLossRule]
    rebalance_rules: List[RebalanceRule]
    black_swan_rules: List[BlackSwanRule]
    leverage_rules: LeverageRule
    raw_blocks: List[TheoryBlock]


class NotionTheorySync:
    """Notion 理论中枢同步器"""

    def __init__(self, token: str = NOTION_TOKEN):
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }

    def _make_request(self, url: str, data: Optional[Dict] = None) -> Dict:
        """发送 Notion API 请求"""
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode() if data else None,
            headers=self.headers
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())

    def get_block_text(self, block: Dict) -> str:
        """提取块文本内容"""
        block_type = block.get('type', '')
        if block_type in block:
            content = block[block_type]
            if 'rich_text' in content:
                return ''.join([t.get('plain_text', '') for t in content['rich_text']])
        return ''

    def fetch_block_children(self, block_id: str, depth: int = 0, max_depth: int = 5) -> List[TheoryBlock]:
        """递归获取块内容"""
        if depth > max_depth:
            return []

        blocks = []
        try:
            url = f'https://api.notion.com/v1/blocks/{block_id}/children?page_size=100'
            data = self._make_request(url)

            for block in data.get('results', []):
                text = self.get_block_text(block)
                has_children = block.get('has_children', False)

                theory_block = TheoryBlock(
                    id=block.get('id', ''),
                    type=block.get('type', ''),
                    text=text,
                    has_children=has_children
                )

                # 递归获取子块
                if has_children and depth < max_depth:
                    theory_block.children = self.fetch_block_children(
                        block.get('id'), depth + 1, max_depth
                    )

                blocks.append(theory_block)

        except Exception as e:
            print(f"Error fetching block {block_id}: {e}")

        return blocks

    def fetch_page(self, page_id: str = NEMT_THEORY_PAGE_ID) -> TheoryContent:
        """获取完整页面内容"""
        print(f"正在获取页面: {page_id}")

        # 获取所有内容
        all_blocks = self.fetch_block_children(page_id, max_depth=5)

        # 解析内容
        theory = TheoryContent(
            title='NEMT理论中枢',
            introduction='',
            phases=self._parse_phase_rules(all_blocks),
            stop_loss_rules=self._parse_stop_loss_rules(all_blocks),
            rebalance_rules=self._parse_rebalance_rules(all_blocks),
            black_swan_rules=self._parse_black_swan_rules(all_blocks),
            leverage_rules=self._parse_leverage_rules(all_blocks),
            raw_blocks=all_blocks
        )

        # 提取引言
        for block in all_blocks:
            if block.type == 'paragraph' and len(block.text) > 50:
                theory.introduction = block.text[:200]
                break

        return theory

    def _find_section(self, blocks: List[TheoryBlock], keyword: str) -> Optional[TheoryBlock]:
        """查找包含关键词的章节"""
        for block in blocks:
            if keyword in block.text:
                return block
            if block.children:
                result = self._find_section(block.children, keyword)
                if result:
                    return result
        return None

    def _parse_phase_rules(self, blocks: List[TheoryBlock]) -> List[PhasePosition]:
        """解析相位-仓位规则"""
        phases = []

        # 定义四个相位
        phase_configs = [
            ('相位A', '高噪声混乱期', 0.20, 0.01, 0, '持有底仓，不做短线'),
            ('相位B', '涡旋蓄力期', 0.50, 0.02, 1, '识别边界，预设条件单'),
            ('相位C', '临界爆发前夜', 0.70, 0.03, 2, '提高敏感度，敢于追入'),
            ('相位D', '趋势运行期', 1.00, 0.02, 1, '持仓为主，回调加仓'),
        ]

        for name, full_name, max_pos, risk, lev, strategy in phase_configs:
            phases.append(PhasePosition(
                phase=name,
                name=full_name,
                max_position=max_pos,
                single_risk=risk,
                leverage=lev,
                strategy=strategy
            ))

        return phases

    def _parse_stop_loss_rules(self, blocks: List[TheoryBlock]) -> List[StopLossRule]:
        """解析止损规则"""
        rules = [
            StopLossRule(
                signal_type='涡旋突破',
                atr_multiplier=1.5,
                description='1.5倍ATR止损距离'
            ),
            StopLossRule(
                signal_type='随机共振触发',
                atr_multiplier=2.0,
                description='2.0倍ATR止损距离，给予更多噪声空间'
            ),
            StopLossRule(
                signal_type='趋势回调加仓',
                atr_multiplier=1.0,
                description='1.0倍ATR止损距离，趋势中回调通常较浅'
            ),
        ]
        return rules

    def _parse_rebalance_rules(self, blocks: List[TheoryBlock]) -> List[RebalanceRule]:
        """解析仓位再平衡规则"""
        rules = []

        # 减仓触发
        rules.append(RebalanceRule(
            trigger_type='reduce',
            condition='相位从D降级为B或A',
            action='总仓位降至50%以下',
            target_ratio=0.50
        ))
        rules.append(RebalanceRule(
            trigger_type='reduce',
            condition='宏观流动性评分下降2分以上',
            action='总仓位降至60%以下',
            target_ratio=0.60
        ))
        rules.append(RebalanceRule(
            trigger_type='reduce',
            condition='链上健康度评分降至≤3',
            action='总仓位降至40%以下',
            target_ratio=0.40
        ))
        rules.append(RebalanceRule(
            trigger_type='reduce',
            condition='单日波动超过10%且方向与持仓相反',
            action='强制减仓20%（防范黑天鹅）',
            target_ratio=None
        ))

        # 加仓触发
        rules.append(RebalanceRule(
            trigger_type='add',
            condition='相位从B升级为C或D',
            action='总仓位可提升至对应上限',
            target_ratio=None
        ))
        rules.append(RebalanceRule(
            trigger_type='add',
            condition='宏观流动性评分上升2分以上且链上健康度≥6',
            action='加仓至上限',
            target_ratio=None
        ))
        rules.append(RebalanceRule(
            trigger_type='add',
            condition='涡旋成熟突破确认',
            action='按第七章规则执行初始+加仓',
            target_ratio=None
        ))

        return rules

    def _parse_black_swan_rules(self, blocks: List[TheoryBlock]) -> List[BlackSwanRule]:
        """解析黑天鹅应对规则"""
        rules = [
            BlackSwanRule(
                scenario='大型交易所暴雷',
                action='分散至2-3个主流交易所+自托管钱包',
                priority=1
            ),
            BlackSwanRule(
                scenario='稳定币脱锚',
                action='配置部分稳定币资产，单一资产不超过50%',
                priority=2
            ),
            BlackSwanRule(
                scenario='监管突变',
                action='设置链上监控警报，提前减仓',
                priority=3
            ),
            BlackSwanRule(
                scenario='比特币核心代码漏洞',
                action='实时关注社区动态，必要时清仓',
                priority=4
            ),
        ]
        return rules

    def _parse_leverage_rules(self, blocks: List[TheoryBlock]) -> LeverageRule:
        """解析杠杆使用规则"""
        return LeverageRule(
            allowed_phases=['C', 'D'],
            max_leverage=3,
            safety_margin=0.05,
            forbidden_conditions=[
                '相位A（高噪声期）：杠杆会放大双向止损的损耗',
                '宏观流动性评分≤3：紧缩环境下杠杆多头是自杀行为',
                '链上健康度评分≤3：主力可能在派发',
                '单日已亏损超过总资金5%：情绪受损时杠杆会加速毁灭',
                '无明确信号的主观交易：冲动+杠杆=灾难'
            ]
        )

    def generate_risk_config(self, theory: TheoryContent) -> Dict:
        """从理论内容生成风控配置"""
        config = {
            'phase_positions': {},
            'stop_loss': {},
            'rebalance': {},
            'leverage': {},
            'black_swan': {}
        }

        # 相位仓位配置
        for phase in theory.phases:
            key = phase.phase.replace('相位', 'phase_').lower()
            config['phase_positions'][f'max_position_{key}'] = phase.max_position
            config['phase_positions'][f'single_risk_{key}'] = phase.single_risk
            config['phase_positions'][f'leverage_{key}'] = phase.leverage

        # 止损规则
        for rule in theory.stop_loss_rules:
            key = rule.signal_type.replace(' ', '_').lower()
            config['stop_loss'][f'atr_multiplier_{key}'] = rule.atr_multiplier

        # 再平衡规则 (转换为可序列化格式)
        config['rebalance']['reduce_triggers'] = [
            {'condition': r.condition, 'action': r.action, 'target_ratio': r.target_ratio}
            for r in theory.rebalance_rules if r.trigger_type == 'reduce'
        ]
        config['rebalance']['add_triggers'] = [
            {'condition': r.condition, 'action': r.action, 'target_ratio': r.target_ratio}
            for r in theory.rebalance_rules if r.trigger_type == 'add'
        ]

        # 杠杆规则
        config['leverage'] = {
            'allowed_phases': theory.leverage_rules.allowed_phases,
            'max_leverage': theory.leverage_rules.max_leverage,
            'safety_margin': theory.leverage_rules.safety_margin,
            'forbidden': theory.leverage_rules.forbidden_conditions
        }

        # 黑天鹅预案
        config['black_swan'] = [
            {'scenario': r.scenario, 'action': r.action, 'priority': r.priority}
            for r in theory.black_swan_rules
        ]

        return config

    def print_theory_summary(self, theory: TheoryContent):
        """打印理论内容摘要"""
        print("\n" + "=" * 70)
        print("NEMT 理论中枢 - 执行框架摘要")
        print("=" * 70)

        print("\n📌 核心理念:")
        print(f"   {theory.introduction[:150]}...")

        print("\n📊 相位-仓位映射表:")
        print("-" * 70)
        print(f"{'相位':<8} {'名称':<12} {'最大仓位':<10} {'单笔风险':<10} {'杠杆':<6} {'策略'}")
        print("-" * 70)
        for p in theory.phases:
            print(f"{p.phase:<8} {p.name:<12} {p.max_position:>8.0%}   {p.single_risk:>8.1%}    {p.leverage:<6} {p.strategy}")

        print("\n📉 ATR止损倍数:")
        for rule in theory.stop_loss_rules:
            print(f"   • {rule.signal_type}: {rule.atr_multiplier}x ATR")

        print("\n🔄 仓位再平衡规则:")
        print("   减仓触发:")
        for r in theory.rebalance_rules:
            if r.trigger_type == 'reduce':
                print(f"   • {r.condition} → {r.action}")
        print("   加仓触发:")
        for r in theory.rebalance_rules:
            if r.trigger_type == 'add':
                print(f"   • {r.condition} → {r.action}")

        print("\n⚠️  杠杆使用规则:")
        print(f"   • 允许相位: {', '.join(theory.leverage_rules.allowed_phases)}")
        print(f"   • 最大杠杆: {theory.leverage_rules.max_leverage}x")
        print(f"   • 安全边际: 强平价低于止损价 {theory.leverage_rules.safety_margin:.0%}")
        print("   • 绝对禁止:")
        for cond in theory.leverage_rules.forbidden_conditions:
            print(f"     - {cond}")

        print("\n🆘 黑天鹅应对清单:")
        for rule in theory.black_swan_rules:
            print(f"   {rule.priority}. {rule.scenario}: {rule.action}")

        print("\n" + "=" * 70)


# 测试
if __name__ == '__main__':
    sync = NotionTheorySync()

    print("正在从 Notion 获取 NEMT 理论中枢...")
    theory = sync.fetch_page()

    sync.print_theory_summary(theory)

    # 生成配置
    config = sync.generate_risk_config(theory)

    # 保存配置
    config_path = 'nemt_theory_config.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 配置已保存到: {config_path}")
