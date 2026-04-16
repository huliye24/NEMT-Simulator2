#!/usr/bin/env python3
# Copyright 2026 NEMT Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Notion 适配器 - Notion ↔ 项目协议转换
=====================================
负责从 Notion 读取策略参数，向 Notion 写入回测结果

Notion 数据结构映射:
- 策略数据库: 存储 NEMT 参数配置
- 回测数据库: 存储回测结果
- 信号数据库: 存储交易信号

使用方式:
    from adapters.notion_adapter import NotionAdapter
    adapter = NotionAdapter()
    params = adapter.read_strategy_params(page_id)
    adapter.write_backtest_result(page_id, results)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..config import config

logger = logging.getLogger(__name__)


# ============================================================================
# Notion 属性类型枚举
# ============================================================================
class PropertyType(Enum):
    """Notion 属性类型"""
    TITLE = "title"
    RICH_TEXT = "rich_text"
    NUMBER = "number"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    DATE = "date"
    CHECKBOX = "checkbox"
    URL = "url"
    EMAIL = "email"
    PHONE_NUMBER = "phone_number"
    FORMULA = "formula"
    RELATION = "relation"
    ROLLUP = "rollup"


# ============================================================================
# 数据结构定义
# ============================================================================
@dataclass
class StrategyParams:
    """策略参数 (Notion → 算法)"""
    name: str = ""
    description: str = ""
    alpha: float = 0.1
    beta: float = 1.0
    noise: float = 0.2
    dt: float = 0.01
    dx: float = 1.0
    steps: int = 200
    n: int = 1000
    data_source: str = "BTCUSDT"
    interval: str = "1m"
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'alpha': self.alpha,
            'beta': self.beta,
            'noiseLevel': self.noise,
            'dt': self.dt,
            'dx': self.dx,
            'steps': self.steps,
            'n': self.n,
            'dataSource': self.data_source,
            'interval': self.interval,
            'enabled': self.enabled,
            'tags': self.tags,
        }

    def to_matlab(self) -> str:
        """转换为 MATLAB 工作区变量"""
        return f"""
% 策略参数: {self.name}
alpha = {self.alpha};
beta = {self.beta};
noise = {self.noise};
dt = {self.dt};
dx = {self.dx};
steps = {self.steps};
n = {self.n};
strategy_name = '{self.name}';
data_source = '{self.data_source}';
interval = '{self.interval}';
"""

    @classmethod
    def from_notion_page(cls, page: Dict) -> 'StrategyParams':
        """从 Notion 页面解析策略参数"""
        params = cls()

        props = page.get('properties', {})

        # 标题
        if 'Name' in props:
            title_prop = props['Name']
            if title_prop.get('type') == 'title':
                texts = title_prop.get('title', [])
                params.name = ''.join(t.get('plain_text', '') for t in texts)

        # 富文本描述
        if 'Description' in props:
            desc_prop = props['Description']
            if desc_prop.get('type') == 'rich_text':
                texts = desc_prop.get('rich_text', [])
                params.description = ''.join(t.get('plain_text', '') for t in texts)

        # 数值参数
        num_fields = ['alpha', 'beta', 'noise', 'dt', 'dx', 'steps', 'n']
        for field_name in num_fields:
            if field_name.title() in props:
                prop = props[field_name.title()]
                if prop.get('type') == 'number':
                    params.__setattr__(field_name, prop.get('number', 0) or 0)

        # 数据源
        if 'DataSource' in props:
            prop = props['DataSource']
            if prop.get('type') == 'select':
                params.data_source = prop.get('select', {}).get('name', 'BTCUSDT')

        if 'Interval' in props:
            prop = props['Interval']
            if prop.get('type') == 'select':
                params.interval = prop.get('select', {}).get('name', '1m')

        # 启用状态
        if 'Enabled' in props:
            prop = props['Enabled']
            if prop.get('type') == 'checkbox':
                params.enabled = prop.get('checkbox', True)

        # 标签
        if 'Tags' in props:
            prop = props['Tags']
            if prop.get('type') == 'multi_select':
                params.tags = [t.get('name', '') for t in prop.get('multi_select', [])]

        # 时间戳
        if 'CreatedAt' in props:
            prop = props['CreatedAt']
            if prop.get('type') == 'date':
                params.created_at = prop.get('date', {}).get('start')

        return params


@dataclass
class BacktestResult:
    """回测结果 (算法 → Notion)"""
    strategy_name: str = ""
    strategy_id: str = ""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    spectral_width: float = 0.0
    mean_frequency: float = 0.0
    num_resonance_peaks: int = 0
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_notion_properties(self) -> Dict[str, Any]:
        """转换为 Notion 数据库属性"""
        return {
            'Name': {
                'title': [{'text': {'content': f"{self.strategy_name} - {self.timestamp[:10]}"}}]
            },
            'Strategy': {
                'rich_text': [{'text': {'content': self.strategy_name}}]
            },
            'TotalTrades': {
                'number': self.total_trades
            },
            'WinRate': {
                'number': round(self.win_rate, 2)
            },
            'TotalPnL': {
                'number': round(self.total_pnl, 2)
            },
            'MaxDrawdown': {
                'number': round(self.max_drawdown, 2)
            },
            'ProfitFactor': {
                'number': round(self.profit_factor, 2)
            },
            'SharpeRatio': {
                'number': round(self.sharpe_ratio, 2)
            },
            'SpectralWidth': {
                'number': round(self.spectral_width, 6)
            },
            'MeanFrequency': {
                'number': round(self.mean_frequency, 6)
            },
            'ResonancePeaks': {
                'number': self.num_resonance_peaks
            },
            'ExecutionTime': {
                'number': round(self.execution_time, 2)
            },
        }

    @classmethod
    def from_matlab_result(cls, strategy_name: str, strategy_id: str,
                           matlab_result: Dict) -> 'BacktestResult':
        """从 MATLAB 结果创建回测结果"""
        result = cls()
        result.strategy_name = strategy_name
        result.strategy_id = strategy_id
        result.timestamp = datetime.now().isoformat()

        # 提取 MATLAB 结果
        if 'spectralWidth' in matlab_result:
            result.spectral_width = float(matlab_result['spectralWidth'])
        if 'meanFrequency' in matlab_result:
            result.mean_frequency = float(matlab_result['meanFrequency'])
        if 'numPeaks' in matlab_result:
            result.num_resonance_peaks = int(matlab_result['numPeaks'])

        # 如果有交易统计
        if 'totalTrades' in matlab_result:
            result.total_trades = int(matlab_result['totalTrades'])
        if 'winRate' in matlab_result:
            result.win_rate = float(matlab_result['winRate'])
        if 'totalPnL' in matlab_result:
            result.total_pnl = float(matlab_result['totalPnL'])
        if 'maxDrawdown' in matlab_result:
            result.max_drawdown = float(matlab_result['maxDrawdown'])

        return result


@dataclass
class TradingSignal:
    """交易信号 (算法 → Notion / Go)"""
    symbol: str = ""
    action: str = ""  # 'buy', 'sell', 'hold'
    price: float = 0.0
    quantity: float = 0.0
    confidence: float = 0.0
    strategy_name: str = ""
    reason: str = ""
    indicators: Dict[str, float] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'action': self.action,
            'price': self.price,
            'quantity': self.quantity,
            'confidence': self.confidence,
            'strategy_name': self.strategy_name,
            'reason': self.reason,
            'indicators': self.indicators,
            'timestamp': self.timestamp,
        }

    def to_go_signal(self) -> Dict[str, Any]:
        """转换为 Go 服务器信号格式"""
        return {
            'symbol': self.symbol,
            'side': self.action.upper(),  # BUY, SELL
            'price': self.price,
            'qty': self.quantity,
            'signal_id': f"{self.strategy_name}_{int(datetime.now().timestamp())}",
            'metadata': {
                'confidence': self.confidence,
                'reason': self.reason,
                'indicators': self.indicators,
            }
        }


# ============================================================================
# Notion API 客户端
# ============================================================================
class NotionClient:
    """Notion API 封装 (使用 requests 直接调用)"""

    BASE_URL = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Notion-Version': self.NOTION_VERSION,
        }

    def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """发送 HTTP 请求到 Notion API"""
        import requests

        url = f"{self.BASE_URL}/{endpoint}"
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            json=data,
            timeout=30
        )

        if response.status_code >= 400:
            logger.error(f"Notion API 错误: {response.status_code} - {response.text}")
            raise Exception(f"Notion API 错误: {response.status_code}")

        return response.json()

    def get_page(self, page_id: str) -> Dict:
        """获取页面"""
        return self._request('GET', f"pages/{page_id}")

    def get_database(self, database_id: str, filter: Dict = None,
                     sorts: List = None) -> Dict:
        """查询数据库"""
        data = {}
        if filter:
            data['filter'] = filter
        if sorts:
            data['sorts'] = sorts
        return self._request('POST', f"databases/{database_id}/query", data)

    def create_page(self, parent_id: str, properties: Dict,
                    children: List = None) -> Dict:
        """创建页面"""
        data = {
            'parent': {'page_id': parent_id} if len(parent_id) > 30 else {'database_id': parent_id},
            'properties': properties,
        }
        if children:
            data['children'] = children
        return self._request('POST', 'pages', data)

    def update_page(self, page_id: str, properties: Dict) -> Dict:
        """更新页面"""
        return self._request('PATCH', f"pages/{page_id}", {'properties': properties})


# ============================================================================
# Notion 适配器主类
# ============================================================================
class NotionAdapter:
    """
    Notion 适配器 - 协议转换的核心适配层
    ======================================

    功能:
    1. 从 Notion 读取策略参数 (Notion → 算法)
    2. 向 Notion 写入回测结果 (算法 → Notion)
    3. 同步交易信号 (算法 → Notion)

    使用流程:
    1. 初始化: adapter = NotionAdapter()
    2. 读取策略: params = adapter.read_strategy_params(page_id)
    3. 运行回测: result = run_backtest(params)
    4. 写入结果: adapter.write_backtest_result(page_id, result)
    """

    def __init__(self, token: str = None):
        """
        初始化适配器

        Args:
            token: Notion API Token (默认从环境变量读取)
        """
        self.token = token or os.getenv("NOTION_TOKEN", "")
        self.client = NotionClient(self.token) if self.token else None
        self.configured = bool(self.token)

        if not self.configured:
            logger.warning("⚠️  Notion 未配置，请设置 NOTION_TOKEN 环境变量")

    # ------------------------------------------------------------------------
    # 策略参数读取 (Notion → 算法)
    # ------------------------------------------------------------------------
    def read_strategy_params(self, page_id: str) -> Optional[StrategyParams]:
        """
        从 Notion 页面读取策略参数

        Args:
            page_id: Notion 页面 ID

        Returns:
            StrategyParams 对象，失败返回 None
        """
        if not self.client:
            logger.error("Notion 客户端未初始化")
            return None

        try:
            page = self.client.get_page(page_id)
            params = StrategyParams.from_notion_page(page)
            logger.info(f"📖 读取策略参数: {params.name}")
            return params
        except Exception as e:
            logger.error(f"读取 Notion 页面失败: {e}")
            return None

    def read_all_strategies(self, database_id: str = None) -> List[StrategyParams]:
        """
        从数据库读取所有策略

        Args:
            database_id: 策略数据库 ID

        Returns:
            策略参数列表
        """
        if not self.client:
            logger.error("Notion 客户端未初始化")
            return []

        db_id = database_id or os.getenv("NOTION_STRATEGY_DB", "")
        if not db_id:
            logger.error("未指定策略数据库 ID")
            return []

        try:
            response = self.client.get_database(db_id)
            strategies = []

            for page in response.get('results', []):
                params = StrategyParams.from_notion_page(page)
                if params.enabled:
                    strategies.append(params)

            logger.info(f"📖 从 Notion 读取了 {len(strategies)} 个策略")
            return strategies

        except Exception as e:
            logger.error(f"读取策略数据库失败: {e}")
            return []

    # ------------------------------------------------------------------------
    # 回测结果写入 (算法 → Notion)
    # ------------------------------------------------------------------------
    def write_backtest_result(self, source_page_id: str,
                               result: BacktestResult) -> Optional[str]:
        """
        向 Notion 写入回测结果

        Args:
            source_page_id: 源策略页面 ID (用于关联)
            result: 回测结果

        Returns:
            创建的页面 ID，失败返回 None
        """
        if not self.client:
            logger.error("Notion 客户端未初始化")
            return None

        db_id = os.getenv("NOTION_BACKTEST_DB", "")
        if not db_id:
            logger.warning("未配置 NOTION_BACKTEST_DB，跳过写入 Notion")
            return None

        try:
            properties = result.to_notion_properties()
            # 添加与源策略的关联
            properties['Strategy'] = {
                'relation': [source_page_id]
            }

            page = self.client.create_page(db_id, properties)
            page_id = page.get('id', '')
            logger.info(f"✅ 回测结果已写入 Notion: {page_id}")
            return page_id

        except Exception as e:
            logger.error(f"写入回测结果失败: {e}")
            return None

    # ------------------------------------------------------------------------
    # 信号写入 (算法 → Notion / Redis)
    # ------------------------------------------------------------------------
    def write_signal(self, signal: TradingSignal) -> bool:
        """
        写入交易信号

        Args:
            signal: 交易信号

        Returns:
            是否成功
        """
        if not self.client:
            logger.error("Notion 客户端未初始化")
            return False

        db_id = os.getenv("NOTION_SIGNAL_DB", "")
        if not db_id:
            logger.warning("未配置 NOTION_SIGNAL_DB，跳过写入 Notion")
            return False

        try:
            properties = {
                'Name': {
                    'title': [{'text': {'content': f"{signal.symbol} {signal.action}"}}]
                },
                'Symbol': {
                    'select': {'name': signal.symbol}
                },
                'Action': {
                    'select': {'name': signal.action.capitalize()}
                },
                'Price': {
                    'number': signal.price
                },
                'Confidence': {
                    'number': round(signal.confidence * 100, 1)
                },
                'Reason': {
                    'rich_text': [{'text': {'content': signal.reason}}]
                },
            }

            self.client.create_page(db_id, properties)
            logger.info(f"✅ 信号已写入 Notion: {signal.symbol} {signal.action}")
            return True

        except Exception as e:
            logger.error(f"写入信号失败: {e}")
            return False

    # ------------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------------
    def get_database_schema(self, database_id: str) -> Dict:
        """获取数据库结构定义"""
        if not self.client:
            return {}

        try:
            response = self._request('GET', f"databases/{database_id}")
            return response.get('properties', {})
        except Exception as e:
            logger.error(f"获取数据库结构失败: {e}")
            return {}

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            'configured': self.configured,
            'token_set': bool(self.token),
            'strategy_db': bool(os.getenv("NOTION_STRATEGY_DB", "")),
            'backtest_db': bool(os.getenv("NOTION_BACKTEST_DB", "")),
            'signal_db': bool(os.getenv("NOTION_SIGNAL_DB", "")),
        }


# ============================================================================
# 便捷函数
# ============================================================================
def create_notion_adapter(token: str = None) -> NotionAdapter:
    """创建 Notion 适配器"""
    return NotionAdapter(token)


# ============================================================================
# 单元测试
# ============================================================================
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # 测试配置检查
    adapter = NotionAdapter()
    health = adapter.health_check()
    print(f"Notion 适配器状态: {json.dumps(health, indent=2, ensure_ascii=False)}")
