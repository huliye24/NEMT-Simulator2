#!/usr/bin/env python3
"""
Quant-Sync HTTP API Server
==========================
将 MCP 工具暴露为 REST API，供前端调用

支持：
- POST /api/pipeline/run - 运行完整流程
- GET  /api/pipeline/status - 获取状态
- GET  /api/notion/strategies - 获取策略列表
- POST /api/notion/strategy/{id} - 读取单个策略
- POST /api/notion/backtest - 写入回测结果
- GET  /api/signals - 获取信号历史
- POST /api/signals/send - 发送信号

使用方式:
    python api_server.py --port 8080
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from functools import wraps
import time

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
SERVER_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(SERVER_ROOT))

# 尝试导入 MCP 组件
try:
    # 直接从同目录导入
    import config
    import adapters.notion_adapter as notion_adapter
    import adapters.matlab_bridge as matlab_bridge
    import transformers.data_transformer as data_transformer
    import routers.signal_router as signal_router
    
    # 简化别名
    NotionAdapter = notion_adapter.NotionAdapter
    StrategyParams = notion_adapter.StrategyParams
    BacktestResult = notion_adapter.BacktestResult
    TradingSignal = notion_adapter.TradingSignal
    MatlabBridge = matlab_bridge.MatlabBridge
    NEMTAnalysisResult = matlab_bridge.NEMTAnalysisResult
    DataTransformer = data_transformer.DataTransformer
    SignalRouter = signal_router.SignalRouter
    SignalGenerator = signal_router.SignalGenerator
    
    MCP_AVAILABLE = True
except ImportError as e:
    logging.warning(f"MCP组件导入失败: {e}，使用模拟模式")
    MCP_AVAILABLE = False

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# 导入策略服务
from routers.strategy_router import StrategyRouter
from strategy_service import StrategyService

logger = logging.getLogger(__name__)

# ============================================================================
# 策略服务初始化
# ============================================================================

# 策略服务实例
_strategy_service = None
_strategy_router = None

def get_strategy_service() -> StrategyService:
    """获取策略服务实例"""
    global _strategy_service, _strategy_router
    if _strategy_service is None:
        _strategy_service = StrategyService()
        _strategy_router = StrategyRouter(_strategy_service)
    return _strategy_service

def get_strategy_router() -> StrategyRouter:
    """获取策略路由实例"""
    global _strategy_router
    if _strategy_router is None:
        get_strategy_service()  # 确保服务已初始化
    return _strategy_router

# ============================================================================
# 模拟数据（当 MCP 不可用时）
# ============================================================================

class MockData:
    """模拟数据，用于测试"""

    @staticmethod
    def get_mock_strategy() -> Dict:
        return {
            "success": True,
            "data": {
                "name": "BTC默认策略",
                "description": "默认NEMT策略配置",
                "alpha": 0.1,
                "beta": 1.0,
                "noise": 0.2,
                "dt": 0.01,
                "dx": 1.0,
                "steps": 200,
                "n": 1000,
                "dataSource": "BTCUSDT",
                "interval": "1m",
                "enabled": True,
                "tags": ["默认", "BTC"]
            }
        }

    @staticmethod
    def get_mock_nemt_result() -> Dict:
        return {
            "success": True,
            "data": {
                "spectralWidth": 0.0234,
                "meanFrequency": 0.1567,
                "numPeaks": 3,
                "resonancePeaks": [0.1, 0.25, 0.4],
                "spectrum": [0.01 * i for i in range(100)],
                "frequencies": [i * 0.01 for i in range(100)]
            }
        }

    @staticmethod
    def get_mock_signal() -> Dict:
        return {
            "success": True,
            "data": {
                "id": f"sig_{int(time.time())}",
                "symbol": "BTCUSDT",
                "type": "vortex_breakout",
                "direction": "bullish",
                "price": 67500.00,
                "confidence": 0.75,
                "reason": "涡旋成熟度: 7.5/10",
                "timestamp": datetime.now().isoformat(),
                "phase": "PHASE_B_VORTEX",
                "indicators": {
                    "dci": 0.68,
                    "spectralWidth": 0.0234,
                    "vortexMaturity": 7.5,
                    "resonanceConfidence": 0.65
                }
            }
        }


# ============================================================================
# Pipeline 执行器
# ============================================================================

class PipelineExecutor:
    """
    流水线执行器
    ==================
    封装完整的 Notion → NEMT → Signal 流程
    """

    def __init__(self):
        if MCP_AVAILABLE:
            self.notion = NotionAdapter()
            self.matlab = MatlabBridge()
            self.transformer = DataTransformer()
            self.signal_router = SignalRouter()
            self.signal_generator = SignalGenerator(self.signal_router)
        else:
            self.notion = None
            self.matlab = None
            self.transformer = None
            self.signal_router = None
            self.signal_generator = None

        # 执行日志
        self.logs: List[Dict] = []

    def clear_logs(self):
        """清空日志"""
        self.logs = []

    def add_log(self, level: str, step: str, message: str, data: Any = None):
        """添加日志"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "step": step,
            "message": message,
            "data": data
        }
        self.logs.append(entry)
        logger.info(f"[{step}] {message}")

    def run_full_pipeline(self, prices: List[float], symbol: str = "BTCUSDT",
                          notion_page_id: str = None) -> Dict:
        """
        运行完整流程

        Args:
            prices: 价格序列
            symbol: 交易对
            notion_page_id: Notion 策略页面 ID（可选）

        Returns:
            完整执行结果
        """
        self.clear_logs()
        result = {
            "success": True,
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "logs": [],
            "steps": {}
        }

        # Step 1: 读取策略参数
        self.add_log("INFO", "STEP_1_READ", "从Notion读取策略参数...")
        params = {}

        if notion_page_id and self.notion:
            strategy = self.notion.read_strategy_params(notion_page_id)
            if strategy:
                params = strategy.to_dict()
                self.add_log("SUCCESS", "STEP_1_READ", f"策略读取成功: {strategy.name}", params)
            else:
                self.add_log("WARNING", "STEP_1_READ", "策略读取失败，使用默认参数")
                params = MockData.get_mock_strategy()["data"]
        else:
            params = MockData.get_mock_strategy()["data"]
            self.add_log("INFO", "STEP_1_READ", "使用默认策略参数", params)

        result["steps"]["read_strategy"] = {"success": True, "params": params}

        # Step 2: NEMT 分析
        self.add_log("INFO", "STEP_2_NEMT", "开始NEMT分析...")
        nemt_result = None

        if self.matlab:
            try:
                nemt_result = self.matlab.run_analysis(prices, params)
                if nemt_result.success:
                    self.add_log("SUCCESS", "STEP_2_NEMT", "NEMT分析完成",
                                {"spectralWidth": nemt_result.spectral_width,
                                 "numPeaks": nemt_result.num_peaks})
                else:
                    self.add_log("ERROR", "STEP_2_NEMT", f"NEMT分析失败: {nemt_result.error}")
                    result["success"] = False
            except Exception as e:
                self.add_log("ERROR", "STEP_2_NEMT", f"NEMT分析异常: {str(e)}")
                result["success"] = False
        else:
            # 使用模拟结果
            time.sleep(0.5)  # 模拟计算时间
            mock_result = MockData.get_mock_nemt_result()["data"]
            
            # 创建可调用对象
            class MockNEMTResult:
                def __init__(self, data):
                    self._data = data
                    self.success = True
                    self.spectral_width = data['spectralWidth']
                    self.mean_frequency = data['meanFrequency']
                    self.num_peaks = data['numPeaks']
                    self.resonance_peaks = data['resonancePeaks']
                    self.spectrum = data['spectrum']
                    self.freqs = data['frequencies']
                def to_dict(self):
                    return self._data
            
            nemt_result = MockNEMTResult(mock_result)
            self.add_log("SUCCESS", "STEP_2_NEMT", "NEMT分析完成（模拟）", mock_result)

        if nemt_result and nemt_result.success:
            result["steps"]["nemt_analysis"] = {
                "success": True,
                "data": nemt_result.to_dict() if hasattr(nemt_result, 'to_dict') else nemt_result
            }

            # Step 3: 语义压缩
            self.add_log("INFO", "STEP_3_COMPRESS", "语义压缩...")
            if self.transformer:
                self.transformer.load_prices(prices)
                summary = self.transformer.compress_to_summary(nemt_result.to_dict())
                self.add_log("SUCCESS", "STEP_3_COMPRESS", "压缩完成",
                           {"summary": summary.summary[:50] + "..." if len(summary.summary) > 50 else summary.summary})
                result["steps"]["semantic_compress"] = {"success": True, "summary": summary.to_dict()}
            else:
                result["steps"]["semantic_compress"] = {"success": True, "summary": {"summary": "模拟压缩"}}

            # Step 4: 信号生成
            self.add_log("INFO", "STEP_4_SIGNAL", "生成交易信号...")
            current_price = prices[-1] if prices else 0

            if self.signal_generator:
                signal = self.signal_generator.generate_from_nemt(
                    nemt_result.to_dict(), current_price, symbol
                )
                if signal:
                    self.add_log("SUCCESS", "STEP_4_SIGNAL", f"信号生成成功: {signal.action}",
                               signal.to_dict())
                    result["steps"]["signal_generate"] = {"success": True, "signal": signal.to_dict()}

                    # Step 5: 信号分发
                    self.add_log("INFO", "STEP_5_SEND", "分发交易信号...")
                    if self.signal_router:
                        send_results = self.signal_router.send(signal)
                        success = any(send_results.values())
                        self.add_log("SUCCESS" if success else "WARNING", "STEP_5_SEND",
                                   f"信号分发完成: {send_results}", send_results)
                        result["steps"]["signal_send"] = {"success": success, "results": send_results}
                else:
                    self.add_log("WARNING", "STEP_4_SIGNAL", "未生成有效信号")
                    result["steps"]["signal_generate"] = {"success": False, "signal": None}
            else:
                # 使用模拟信号
                mock_signal = MockData.get_mock_signal()["data"]
                mock_signal["price"] = current_price
                self.add_log("SUCCESS", "STEP_4_SIGNAL", "信号生成完成（模拟）", mock_signal)
                result["steps"]["signal_generate"] = {"success": True, "signal": mock_signal}
                result["steps"]["signal_send"] = {"success": True, "results": {"notion": True}}

            # Step 6: 回写 Notion
            self.add_log("INFO", "STEP_6_WRITE", "回测结果写入Notion...")
            if notion_page_id and self.notion:
                backtest = BacktestResult.from_matlab_result(
                    params.get("name", "策略"),
                    notion_page_id,
                    nemt_result.to_dict()
                )
                page_id = self.notion.write_backtest_result(notion_page_id, backtest)
                if page_id:
                    self.add_log("SUCCESS", "STEP_6_WRITE", f"回测结果已写入: {page_id}")
                    result["steps"]["write_backtest"] = {"success": True, "page_id": page_id}
                else:
                    self.add_log("WARNING", "STEP_6_WRITE", "回写失败（可能未配置数据库）")
                    result["steps"]["write_backtest"] = {"success": False}
            else:
                self.add_log("INFO", "STEP_6_WRITE", "跳过Notion回写（无页面ID）")
                result["steps"]["write_backtest"] = {"success": True, "note": "skipped"}

        # 最终日志
        if result["success"]:
            self.add_log("SUCCESS", "COMPLETE", "完整流程执行成功！")
        else:
            self.add_log("ERROR", "COMPLETE", "流程执行中遇到错误")

        result["logs"] = self.logs
        return result

    def get_status(self) -> Dict:
        """获取系统状态"""
        strategy_stats = get_strategy_service().get_stats()
        
        status = {
            "server": "Quant-Sync API",
            "version": "1.1.0",
            "timestamp": datetime.now().isoformat(),
            "mcp_available": MCP_AVAILABLE,
            "strategy_service": {
                "total_strategies": strategy_stats.get("total", 0),
                "alive": strategy_stats.get("alive", 0),
                "testing": strategy_stats.get("testing", 0),
                "dormant": strategy_stats.get("dormant", 0),
                "dead": strategy_stats.get("dead", 0),
                "avg_score": strategy_stats.get("avg_score", 0)
            },
            "components": {}
        }

        if MCP_AVAILABLE:
            status["components"] = {
                "notion": self.notion.health_check() if self.notion else {"error": "not initialized"},
                "matlab": self.matlab.get_engine_info() if self.matlab else {"error": "not initialized"},
            }
        else:
            status["components"] = {
                "notion": {"mode": "mock"},
                "matlab": {"mode": "mock"}
            }

        return status


# 全局执行器实例
_executor = PipelineExecutor()


# ============================================================================
# HTTP 请求处理器
# ============================================================================

class APIHandler(BaseHTTPRequestHandler):
    """HTTP API 处理器"""

    def _send_json(self, status: int, data: Dict):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def _parse_body(self) -> Dict:
        """解析请求体"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            body = self.rfile.read(content_length)
            return json.loads(body.decode('utf-8'))
        return {}

    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self._send_json(200, {"status": "ok"})

    def do_GET(self):
        """处理 GET 请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # 根路径
        if path == "/" or path == "":
            self._send_json(200, {
                "name": "Quant-Sync API",
                "version": "1.0.0",
                "endpoints": {
                    "POST /api/pipeline/run": "运行完整流程",
                    "GET  /api/pipeline/status": "获取系统状态",
                    "GET  /api/notion/strategies": "获取策略列表",
                    "POST /api/notion/strategy/{id}": "读取单个策略",
                    "POST /api/notion/backtest": "写入回测结果",
                    "GET  /api/signals": "获取信号历史",
                    "POST /api/signals/send": "发送信号"
                }
            })
            return

        # 系统状态
        if path == "/api/pipeline/status":
            status = _executor.get_status()
            self._send_json(200, status)
            return

        # 信号历史
        if path == "/api/signals":
            limit = int(query.get('limit', [10])[0])
            # 从 signal_router 获取历史或返回空列表
            if MCP_AVAILABLE and _executor.signal_router:
                history = _executor.signal_router.get_history(None, limit)
                signals = [s.to_dict() for s in history]
            else:
                signals = []
            self._send_json(200, {"success": True, "signals": signals})
            return

        # ===== 策略管理 API =====
        
        # 策略列表
        if path == "/api/strategy/list":
            status = query.get('status', [None])[0]
            result = get_strategy_router().list_strategies(status)
            self._send_json(200, result)
            return

        # 策略模板列表
        if path == "/api/strategy/templates":
            result = get_strategy_router().get_templates()
            self._send_json(200, result)
            return

        # 策略统计
        if path == "/api/strategy/stats":
            result = get_strategy_router().get_stats()
            self._send_json(200, result)
            return

        # 所有策略评分
        if path == "/api/strategy/scores":
            result = get_strategy_router().get_all_scores()
            self._send_json(200, result)
            return

        # 淘汰事件
        if path == "/api/strategy/events":
            limit = int(query.get('limit', [10])[0])
            result = get_strategy_router().get_events(limit)
            self._send_json(200, result)
            return

        # 404
        self._send_json(404, {"error": f"路径未找到: {path}"})

    def do_POST(self):
        """处理 POST 请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._parse_body()

        # 运行完整流程
        if path == "/api/pipeline/run":
            prices = body.get("prices", [])
            symbol = body.get("symbol", "BTCUSDT")
            notion_page_id = body.get("notion_page_id")

            if not prices:
                self._send_json(400, {"error": "缺少 prices 参数"})
                return

            result = _executor.run_full_pipeline(prices, symbol, notion_page_id)
            self._send_json(200 if result["success"] else 500, result)
            return

        # 读取策略
        if path == "/api/notion/strategy":
            page_id = body.get("page_id")
            if not page_id:
                self._send_json(400, {"error": "缺少 page_id"})
                return

            if MCP_AVAILABLE and _executor.notion:
                strategy = _executor.notion.read_strategy_params(page_id)
                if strategy:
                    self._send_json(200, {"success": True, "data": strategy.to_dict()})
                else:
                    self._send_json(404, {"error": "策略未找到"})
            else:
                self._send_json(200, MockData.get_mock_strategy())
            return

        # 写入回测结果
        if path == "/api/notion/backtest":
            source_page_id = body.get("source_page_id")
            result_data = body.get("result", {})

            if not source_page_id:
                self._send_json(400, {"error": "缺少 source_page_id"})
                return

            if MCP_AVAILABLE and _executor.notion:
                backtest = BacktestResult.from_matlab_result(
                    result_data.get("name", "策略"),
                    source_page_id,
                    result_data
                )
                page_id = _executor.notion.write_backtest_result(source_page_id, backtest)
                self._send_json(200, {"success": bool(page_id), "page_id": page_id})
            else:
                self._send_json(200, {"success": True, "page_id": "mock_page_id"})
            return

        # 发送信号
        if path == "/api/signals/send":
            signal_data = body.get("signal", {})

            if MCP_AVAILABLE and _executor.signal_router:
                signal = TradingSignal()
                signal.symbol = signal_data.get("symbol", "BTCUSDT")
                signal.price = signal_data.get("price", 0)
                signal.confidence = signal_data.get("confidence", 0.5)
                signal.action = SignalType.HOLD

                results = _executor.signal_router.send(signal)
                self._send_json(200, {"success": True, "results": results})
            else:
                self._send_json(200, {"success": True, "results": {"mock": True}})
            return

        # ===== 策略管理 API =====
        
        # 创建策略
        if path == "/api/strategy/create":
            template = body.get("template")
            name = body.get("name")
            params = body.get("params")
            result = get_strategy_router().create_strategy({
                "template": template,
                "name": name,
                "params": params
            })
            status = 200 if result.get("success") else 400
            self._send_json(status, result)
            return

        # 获取策略详情
        if path == "/api/strategy/get":
            strategy_id = body.get("strategy_id")
            if not strategy_id:
                self._send_json(400, {"error": "缺少 strategy_id"})
                return
            result = get_strategy_router().get_strategy(strategy_id)
            self._send_json(200, result)
            return

        # 更新策略
        if path == "/api/strategy/update":
            strategy_id = body.get("strategy_id")
            updates = body.get("updates", {})
            if not strategy_id:
                self._send_json(400, {"error": "缺少 strategy_id"})
                return
            result = get_strategy_router().update_strategy(strategy_id, updates)
            status = 200 if result.get("success") else 400
            self._send_json(status, result)
            return

        # 删除策略
        if path == "/api/strategy/delete":
            strategy_id = body.get("strategy_id")
            if not strategy_id:
                self._send_json(400, {"error": "缺少 strategy_id"})
                return
            result = get_strategy_router().delete_strategy(strategy_id)
            self._send_json(200, result)
            return

        # 运行回测
        if path == "/api/strategy/backtest":
            strategy_id = body.get("strategy_id")
            prices = body.get("prices", [])
            config = body.get("config", {})
            if not strategy_id:
                self._send_json(400, {"error": "缺少 strategy_id"})
                return
            if not prices or len(prices) < 50:
                self._send_json(400, {"error": "需要至少50个价格数据点"})
                return
            # 合并配置
            body["strategy_id"] = strategy_id
            body["prices"] = prices
            for k, v in config.items():
                if k not in body:
                    body[k] = v
            result = get_strategy_router().run_backtest(strategy_id, body)
            status = 200 if result.get("success") else 400
            self._send_json(status, result)
            return

        # 获取策略评分
        if path == "/api/strategy/score":
            strategy_id = body.get("strategy_id")
            if not strategy_id:
                self._send_json(400, {"error": "缺少 strategy_id"})
                return
            result = get_strategy_router().get_score(strategy_id)
            self._send_json(200, result)
            return

        # 触发淘汰评估
        if path == "/api/strategy/evict":
            strategy_id = body.get("strategy_id")
            result = get_strategy_router().evict(strategy_id)
            self._send_json(200, result)
            return

        # 重新分配权重
        if path == "/api/strategy/rebalance":
            mode = body.get("mode", "equal")
            result = get_strategy_router().rebalance({"mode": mode})
            self._send_json(200, result)
            return

        # 批量回测
        if path == "/api/strategy/batch_backtest":
            result = get_strategy_router().batch_backtest(body)
            status = 200 if result.get("success") else 400
            self._send_json(status, result)
            return

        # 批量创建策略
        if path == "/api/strategy/batch_create":
            result = get_strategy_router().create_batch(body)
            status = 200 if result.get("success") else 400
            self._send_json(status, result)
            return

        # 404
        self._send_json(404, {"error": f"路径未找到: {path}"})

    def log_message(self, format, *args):
        """自定义日志格式"""
        logger.info(f"{self.address_string()} - {format % args}")


# ============================================================================
# 主函数
# ============================================================================

def main():
    """启动 HTTP API 服务器"""
    import argparse

    parser = argparse.ArgumentParser(description="Quant-Sync HTTP API Server")
    parser.add_argument("--port", type=int, default=8080, help="服务器端口")
    parser.add_argument("--host", type=str, default="localhost", help="服务器主机")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    args = parser.parse_args()

    # 配置日志
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    # 启动服务器
    server = HTTPServer((args.host, args.port), APIHandler)

    print(f"""
╔════════════════════════════════════════════════════════════╗
║           Quant-Sync HTTP API Server v1.1.0               ║
╠════════════════════════════════════════════════════════════╣
║  地址: http://{args.host}:{args.port}                          ║
║  文档: http://{args.host}:{args.port}/                          ║
║                                                            ║
║  端点:                                                     ║
║    === Pipeline ===                                        ║
║    POST /api/pipeline/run    - 运行完整流程                ║
║    GET  /api/pipeline/status - 获取系统状态                ║
║                                                            ║
║    === 策略管理 ===                                        ║
║    GET  /api/strategy/list    - 策略列表                   ║
║    POST /api/strategy/create  - 创建策略                   ║
║    GET  /api/strategy/get    - 获取策略详情               ║
║    POST /api/strategy/update - 更新策略                   ║
║    POST /api/strategy/delete - 删除策略                   ║
║                                                            ║
║    === 回测 ===                                            ║
║    POST /api/strategy/backtest     - 回测策略              ║
║    POST /api/strategy/batch_backtest - 批量回测            ║
║                                                            ║
║    === 评分与淘汰 ===                                      ║
║    GET  /api/strategy/scores   - 所有评分                  ║
║    POST /api/strategy/score    - 获取策略评分              ║
║    POST /api/strategy/evict   - 触发淘汰评估              ║
║    GET  /api/strategy/events  - 淘汰事件                  ║
║                                                            ║
║    === 权重 ===                                            ║
║    POST /api/strategy/rebalance - 重新分配权重             ║
║                                                            ║
║    === 其他 ===                                            ║
║    GET  /api/strategy/templates - 策略模板                  ║
║    GET  /api/strategy/stats    - 策略统计                  ║
║    GET  /api/signals           - 信号历史                   ║
║    POST /api/signals/send     - 发送信号                   ║
╚════════════════════════════════════════════════════════════╝
""")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        server.shutdown()


if __name__ == "__main__":
    main()
