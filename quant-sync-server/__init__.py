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
Quant-Sync-Server - 量化工具协议转换中枢
========================================

统一管理 Notion、MATLAB、Python、Go 等异构工具的数据流转。

核心功能:
- Notion 适配器: 读写 Notion 策略/回测/信号数据库
- MATLAB 桥接器: 通过 matlab.engine 执行 NEMT 分析
- 数据转换器: 格式转换与语义压缩
- 信号路由器: 交易信号分发到 Redis/HTTP/Notion

使用方式:

1. MCP 服务器模式 (推荐):
   python server.py

2. Python 直接调用:
   from quant_sync_server import MatlabBridge, NotionAdapter
   bridge = MatlabBridge()
   result = bridge.run_analysis(prices)

3. CLI 模式:
   python main.py --action analyze --prices 50000,51000,52000

快速开始:

1. 配置环境变量:
   export NOTION_TOKEN=your_token
   export NOTION_STRATEGY_DB=your_db_id

2. 启动服务器:
   python quant-sync-server/server.py

3. 在 Cursor 中配置 MCP:
   {
       "mcpServers": {
           "quant-sync": {
               "command": "python",
               "args": ["quant-sync-server/server.py"]
           }
       }
   }
"""

__version__ = "1.0.0"
__author__ = "NEMT Lab"

# 核心组件
from .adapters.notion_adapter import NotionAdapter, StrategyParams, BacktestResult, TradingSignal
from .adapters.matlab_bridge import MatlabBridge, NEMTAnalysisResult
from .transformers.data_transformer import DataTransformer, SemanticSummary
from .routers.signal_router import SignalRouter, SignalGenerator, TradingSignal

# 配置
from .config import config

__all__ = [
    # 适配器
    'NotionAdapter',
    'MatlabBridge',
    # 数据结构
    'StrategyParams',
    'BacktestResult',
    'TradingSignal',
    'NEMTAnalysisResult',
    'SemanticSummary',
    # 工具类
    'DataTransformer',
    'SignalRouter',
    'SignalGenerator',
    # 配置
    'config',
]
