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
Quant-Sync-Server - MCP 核心服务器
=====================================
统一的协议转换中枢，连接 Notion、MATLAB、Python、Go 等异构工具

架构:
┌────────────────────────────────────────────────────────────────┐
│                      Quant-Sync-Server (MCP)                     │
├────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Notion 适配器 │  │ MATLAB 桥接器 │  │    交易信号路由器     │ │
│  │              │  │              │  │                      │ │
│  │ 策略参数读取  │  │ 引擎管理     │  │ 目标分发             │ │
│  │ 结果写入     │  │ 数据转换     │  │ 冷却期管理           │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
│                              │                                  │
│                    ┌─────────┴─────────┐                      │
│                    │    数据转换器       │                      │
│                    │  (语义压缩)        │                      │
│                    └───────────────────┘                      │
├────────────────────────────────────────────────────────────────┤
│                         MCP 协议层                              │
│  tools/list  │  tools/call  │  initialize  │  notifications  │
└────────────────────────────────────────────────────────────────┘

使用方式:
1. 直接运行: python server.py
2. 作为 MCP 服务器: 配置到 Cursor 的 MCP 设置中

MCP 配置:
{
    "mcpServers": {
        "quant-sync": {
            "command": "python",
            "args": ["quant-sync-server/server.py"]
        }
    }
}
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# 导入核心组件
from quant_sync_server.config import config
from quant_sync_server.adapters.notion_adapter import NotionAdapter, StrategyParams, BacktestResult, TradingSignal
from quant_sync_server.adapters.matlab_bridge import MatlabBridge, NEMTAnalysisResult
from quant_sync_server.transformers.data_transformer import DataTransformer, SemanticSummary
from quant_sync_server.routers.signal_router import SignalRouter, SignalGenerator, TradingSignal as Signal, SignalType

logger = logging.getLogger(__name__)

# ============================================================================
# 工具定义
# ============================================================================
TOOLS = [
    # === 状态查询 ===
    {
        "name": "get_server_info",
        "description": "获取 Quant-Sync-Server 服务器信息，包括各组件状态",
        "inputSchema": {
            "type": "object",
            "properties": {},
        }
    },

    # === Notion 操作 ===
    {
        "name": "notion_read_strategy",
        "description": "从 Notion 页面读取策略参数",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page_id": {
                    "type": "string",
                    "description": "Notion 页面 ID"
                }
            },
            "required": ["page_id"]
        }
    },
    {
        "name": "notion_write_backtest",
        "description": "向 Notion 写入回测结果",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_page_id": {
                    "type": "string",
                    "description": "源策略页面 ID"
                },
                "result": {
                    "type": "object",
                    "description": "回测结果"
                }
            },
            "required": ["source_page_id", "result"]
        }
    },

    # === MATLAB 操作 ===
    {
        "name": "matlab_check_engine",
        "description": "检查 MATLAB 引擎状态",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "matlab_run_analysis",
        "description": "运行 NEMT 分析 (需要 MATLAB 引擎)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prices": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "价格序列"
                },
                "params": {
                    "type": "object",
                    "description": "NEMT 参数 (alpha, beta, noiseLevel, steps, dt, dx)"
                }
            },
            "required": ["prices"]
        }
    },
    {
        "name": "matlab_noise_scan",
        "description": "运行噪声扫描实验",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prices": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "价格序列"
                },
                "noise_levels": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "噪声水平列表"
                }
            },
            "required": ["prices"]
        }
    },
    {
        "name": "matlab_beta_scan",
        "description": "运行非线性扫描实验",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prices": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "价格序列"
                },
                "beta_values": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "β 值列表"
                }
            },
            "required": ["prices"]
        }
    },

    # === 数据转换 ===
    {
        "name": "transform_compress",
        "description": "语义压缩 - 将原始数据转换为摘要",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prices": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "价格序列"
                },
                "nemt_result": {
                    "type": "object",
                    "description": "NEMT 分析结果 (可选)"
                }
            },
            "required": ["prices"]
        }
    },
    {
        "name": "transform_to_matlab",
        "description": "转换为 MATLAB 代码格式",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prices": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "价格序列"
                }
            },
            "required": ["prices"]
        }
    },
    {
        "name": "transform_validate",
        "description": "验证数据完整性",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prices": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "价格序列"
                }
            },
            "required": ["prices"]
        }
    },

    # === 信号路由 ===
    {
        "name": "signal_generate",
        "description": "基于 NEMT 结果生成交易信号",
        "inputSchema": {
            "type": "object",
            "properties": {
                "nemt_result": {
                    "type": "object",
                    "description": "NEMT 分析结果"
                },
                "price": {
                    "type": "number",
                    "description": "当前价格"
                },
                "symbol": {
                    "type": "string",
                    "description": "交易对符号"
                }
            },
            "required": ["nemt_result", "price"]
        }
    },
    {
        "name": "signal_send",
        "description": "发送交易信号到目标",
        "inputSchema": {
            "type": "object",
            "properties": {
                "signal": {
                    "type": "object",
                    "description": "交易信号"
                },
                "targets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "目标列表 (redis, http, notion)"
                }
            },
            "required": ["signal"]
        }
    },
    {
        "name": "signal_history",
        "description": "获取信号历史",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "交易对 (可选)"
                },
                "limit": {
                    "type": "number",
                    "description": "返回数量限制"
                }
            }
        }
    },

    # === 一键分析流程 ===
    {
        "name": "run_full_pipeline",
        "description": "运行完整分析流程：Notion读取 → NEMT分析 → 语义压缩 → 信号生成",
        "inputSchema": {
            "type": "object",
            "properties": {
                "notion_page_id": {
                    "type": "string",
                    "description": "Notion 策略页面 ID"
                },
                "prices": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "价格序列"
                },
                "symbol": {
                    "type": "string",
                    "description": "交易对"
                }
            },
            "required": ["prices"]
        }
    },
]


# ============================================================================
# MCP 服务器
# ============================================================================
class QuantSyncServer:
    """
    Quant-Sync-Server MCP 服务器
    ==============================

    通过 stdin/stdout 与 MCP 客户端通信
    """

    def __init__(self):
        # 初始化组件
        self.notion = NotionAdapter()
        self.matlab = MatlabBridge()
        self.transformer = DataTransformer()
        self.signal_router = SignalRouter()
        self.signal_generator = SignalGenerator(self.signal_router)

        self._initialized = False

    # ------------------------------------------------------------------------
    # MCP 协议处理
    # ------------------------------------------------------------------------
    def handle_request(self, request: Dict) -> Optional[Dict]:
        """处理 MCP 请求"""
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")

        response = {"jsonrpc": "2.0", "id": req_id}

        try:
            if method == "initialize":
                response["result"] = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True}
                    },
                    "serverInfo": {
                        "name": "quant-sync",
                        "version": "1.0.0"
                    }
                }
                self._initialized = True

            elif method == "tools/list":
                response["result"] = {"tools": TOOLS}

            elif method == "tools/call":
                result = self._handle_tool_call(
                    params.get("name", ""),
                    params.get("arguments", {})
                )
                response["result"] = {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]
                }

            elif method == "notifications/initialized":
                response = None

            else:
                response["error"] = {"code": -32601, "message": f"方法未找到: {method}"}

        except Exception as e:
            logger.error(f"处理请求失败: {e}")
            response["error"] = {"code": -32603, "message": str(e)}

        return response

    def _handle_tool_call(self, tool_name: str, args: Dict) -> Dict:
        """处理工具调用"""
        logger.info(f"🔧 调用工具: {tool_name}")

        # === 状态查询 ===
        if tool_name == "get_server_info":
            return self._get_server_info()

        # === Notion 操作 ===
        elif tool_name == "notion_read_strategy":
            return self.notion.read_strategy_params(args.get("page_id", ""))

        elif tool_name == "notion_write_backtest":
            result = BacktestResult.from_matlab_result(
                args.get("result", {}).get("strategy_name", ""),
                args.get("source_page_id", ""),
                args.get("result", {})
            )
            page_id = self.notion.write_backtest_result(args.get("source_page_id", ""), result)
            return {"success": bool(page_id), "page_id": page_id}

        # === MATLAB 操作 ===
        elif tool_name == "matlab_check_engine":
            info = self.matlab.get_engine_info()
            return info

        elif tool_name == "matlab_run_analysis":
            prices = args.get("prices", [])
            params = args.get("params", {})
            result = self.matlab.run_analysis(prices, params)
            return result.to_dict()

        elif tool_name == "matlab_noise_scan":
            prices = args.get("prices", [])
            noise_levels = args.get("noise_levels", [0.01, 0.05, 0.1, 0.2, 0.5])
            results = self.matlab.run_noise_scan(prices, noise_levels)
            return {
                "results": [r.to_dict() for r in results]
            }

        elif tool_name == "matlab_beta_scan":
            prices = args.get("prices", [])
            beta_values = args.get("beta_values", [0.1, 0.5, 1.0, 2.0, 5.0])
            results = self.matlab.run_beta_scan(prices, beta_values)
            return {
                "results": [r.to_dict() for r in results]
            }

        # === 数据转换 ===
        elif tool_name == "transform_compress":
            prices = args.get("prices", [])
            nemt_result = args.get("nemt_result", {})
            self.transformer.load_prices(prices)
            summary = self.transformer.compress_to_summary(nemt_result)
            return summary.to_dict()

        elif tool_name == "transform_to_matlab":
            prices = args.get("prices", [])
            self.transformer.load_prices(prices)
            return {"matlab_code": self.transformer.to_matlab_matrix()}

        elif tool_name == "transform_validate":
            prices = args.get("prices", [])
            self.transformer.load_prices(prices)
            valid, errors = self.transformer.validate()
            return {"valid": valid, "errors": errors}

        # === 信号路由 ===
        elif tool_name == "signal_generate":
            nemt_result = args.get("nemt_result", {})
            price = args.get("price", 0)
            symbol = args.get("symbol", "BTCUSDT")
            signal = self.signal_generator.generate_from_nemt(nemt_result, price, symbol)
            return signal.to_dict() if signal else {"error": "信号生成失败"}

        elif tool_name == "signal_send":
            # 构建信号对象
            signal_data = args.get("signal", {})
            signal = TradingSignal()
            signal.symbol = signal_data.get("symbol", "BTCUSDT")
            signal.price = signal_data.get("price", 0)
            signal.confidence = signal_data.get("confidence", 0.5)
            if hasattr(SignalType, signal_data.get("action", "hold").upper()):
                signal.action = SignalType(signal_data.get("action", "hold").upper())

            targets = args.get("targets", None)
            results = self.signal_router.send(signal, targets)
            return {"success": any(results.values()), "results": results}

        elif tool_name == "signal_history":
            symbol = args.get("symbol")
            limit = args.get("limit", 100)
            history = self.signal_router.get_history(symbol, limit)
            return {"signals": [s.to_dict() for s in history]}

        # === 一键流程 ===
        elif tool_name == "run_full_pipeline":
            return self._run_full_pipeline(args)

        else:
            return {"error": f"未知工具: {tool_name}"}

    # ------------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------------
    def _get_server_info(self) -> Dict:
        """获取服务器信息"""
        return {
            "server": "Quant-Sync-Server",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "notion": self.notion.health_check(),
                "matlab": self.matlab.get_engine_info(),
                "redis": {
                    "host": config.redis.host,
                    "port": config.redis.port,
                },
            },
            "signal_router": self.signal_router.get_stats(),
        }

    def _run_full_pipeline(self, args: Dict) -> Dict:
        """运行完整流程"""
        results = {
            "success": True,
            "steps": [],
        }

        # Step 1: 读取策略参数
        notion_page_id = args.get("notion_page_id")
        if notion_page_id:
            params = self.notion.read_strategy_params(notion_page_id)
            if params:
                results["steps"].append({
                    "step": "notion_read",
                    "success": True,
                    "params": params.to_dict(),
                })
            else:
                results["steps"].append({
                    "step": "notion_read",
                    "success": False,
                    "error": "读取 Notion 失败",
                })
                results["success"] = False
                return results

        # Step 2: 运行 NEMT 分析
        prices = args.get("prices", [])
        params_dict = params.to_dict() if notion_page_id and params else {}
        nemt_result = self.matlab.run_analysis(prices, params_dict)
        if nemt_result.success:
            results["steps"].append({
                "step": "nemt_analysis",
                "success": True,
                "result": nemt_result.to_dict(),
            })
        else:
            results["steps"].append({
                "step": "nemt_analysis",
                "success": False,
                "error": nemt_result.error,
            })
            results["success"] = False
            return results

        # Step 3: 语义压缩
        self.transformer.load_prices(prices)
        summary = self.transformer.compress_to_summary(nemt_result.to_dict())
        results["steps"].append({
            "step": "semantic_compress",
            "success": True,
            "summary": summary.to_dict(),
        })

        # Step 4: 生成信号
        symbol = args.get("symbol", "BTCUSDT")
        price = prices[-1] if prices else 0
        signal = self.signal_generator.generate_from_nemt(
            nemt_result.to_dict(), price, symbol
        )
        if signal:
            results["steps"].append({
                "step": "signal_generate",
                "success": True,
                "signal": signal.to_dict(),
            })

            # Step 5: 发送信号
            send_results = self.signal_router.send(signal)
            results["steps"].append({
                "step": "signal_send",
                "success": any(send_results.values()),
                "results": send_results,
            })
        else:
            results["steps"].append({
                "step": "signal_generate",
                "success": False,
            })

        return results


# ============================================================================
# 主循环
# ============================================================================
def main():
    """MCP 服务器主循环"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    print("Quant-Sync-Server 已启动", file=sys.stderr)
    print(f"MATLAB 引擎可用: {config.matlab.engine_available}", file=sys.stderr)
    print(f"Notion 已配置: {bool(config.notion.token)}", file=sys.stderr)
    print(f"Redis: {config.redis.host}:{config.redis.port}", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    server = QuantSyncServer()

    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
                response = server.handle_request(request)

                if response:
                    print(json.dumps(response, ensure_ascii=False))
                    sys.stdout.flush()

            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": f"JSON解析错误: {str(e)}"},
                    "id": None
                }
                print(json.dumps(error_response, ensure_ascii=False))
                sys.stdout.flush()

    except KeyboardInterrupt:
        print("\n正在关闭服务器...", file=sys.stderr)
    except Exception as e:
        print(f"服务器错误: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
