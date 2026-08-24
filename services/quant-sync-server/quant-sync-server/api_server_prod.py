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
NEMT Quant-Sync FastAPI 生产服务器
=====================================
高性能异步 API 服务器，集成:
- FastAPI (async)
- APScheduler (定时任务)
- SQLite (持久化)
- NLS Solver Fallback (NumPy)

运行方式:
    python api_server_prod.py
    uvicorn api_server_prod:app --host 0.0.0.0 --port 8080 --reload
"""

import os
import sys
import json
import uuid
import logging
import asyncio
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Any, Dict, List
from contextlib import asynccontextmanager

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
# 优先使用本目录下的模块
sys.path.insert(0, str(Path(__file__).parent))

os.environ.setdefault("DATABASE_PATH", str(Path(__file__).parent / "nemt_data.db"))

# 配置结构化日志
from structured_logging import setup_logging, get_logger
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"), use_json=False)

from config import config
from database import get_db, Database
from models import PipelineRun, SignalRecord, ExecutionSession
from data_fetcher import fetch_btc_data

# NLS 求解器 - 自动 fallback
try:
    from adapters.matlab_bridge import MatlabBridge
    MATLAB_AVAILABLE = True
except ImportError:
    MATLAB_AVAILABLE = False

from nls_solver import solve_nls, get_solver, NLSSolver

# Notion / Signal
try:
    from adapters.notion_adapter import NotionAdapter, BacktestResult, TradingSignal as NotionTradingSignal
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False

try:
    from routers.signal_router import SignalRouter, SignalGenerator, SignalType, TradingSignal as RouterTradingSignal
    ROUTER_AVAILABLE = True
except ImportError:
    ROUTER_AVAILABLE = False

# FastAPI
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Body
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
except ImportError:
    print("ERROR: FastAPI not installed. Run: pip install fastapi uvicorn[standard] pydantic")
    sys.exit(1)

logger = get_logger(__name__)

# APScheduler
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers import interval, cron
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger.warning("APScheduler not available. Install: pip install apscheduler")


# ============================================================================
# Pydantic 请求/响应模型
# ============================================================================

class PipelineRunRequest(BaseModel):
    prices: List[float] = Field(..., description="价格序列")
    symbol: str = Field(default="BTCUSDT", description="交易对")
    notion_page_id: Optional[str] = Field(default=None, description="Notion 策略页面 ID")
    params: Optional[Dict[str, Any]] = Field(default=None, description="NEMT 参数")


class ExecutionPredictRequest(BaseModel):
    dci: float = Field(..., description="DCI 值", ge=0, le=1)
    vortex_maturity: float = Field(default=0, description="涡旋成熟度")
    phase: str = Field(default="A", description="市场相位")
    spectral_width: float = Field(default=0, description="谱宽")
    noise_level: float = Field(default=0, description="噪声水平")
    macro_score: float = Field(default=5, description="宏观评分")
    onchain_score: float = Field(default=5, description="链上评分")
    halving_phase: str = Field(default="main_rise", description="减半周期阶段")
    confidence: float = Field(default=0.5, description="信号置信度")
    prices: Optional[List[float]] = Field(default=None, description="价格序列")


class ExecutionEntryRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="会话 ID")
    price: float = Field(..., description="入场价格")
    total_capital: float = Field(default=100000, description="账户资金")
    confidence: float = Field(default=0.5, description="置信度")


class ExecutionExitRequest(BaseModel):
    session_id: str = Field(..., description="会话 ID")
    reason: str = Field(default="manual", description="出场原因")


class ExecutionAddRequest(BaseModel):
    session_id: str = Field(..., description="会话 ID")
    price: float = Field(..., description="加仓价格")
    add_on_size: float = Field(default=0.1, description="加仓比例")


class SignalRequest(BaseModel):
    symbol: str = Field(default="BTCUSDT")
    price: float = Field(...)
    action: str = Field(default="hold")
    confidence: float = Field(default=0.5)
    reason: str = Field(default="")
    spectral_width: float = Field(default=0)
    dci_value: float = Field(default=0)
    vortex_maturity: float = Field(default=0)
    resonance_confidence: float = Field(default=0)
    phase: str = Field(default="A")


# ============================================================================
# 全局状态
# ============================================================================

_scheduler: Optional[Any] = None
_nls_solver: Optional[NLSSolver] = None
_matlab_bridge: Optional[Any] = None
_notion_adapter: Optional[Any] = None
_signal_router: Optional[Any] = None
_signal_generator: Optional[Any] = None
_db: Optional[Database] = None


def _get_db() -> Database:
    """获取数据库实例（懒加载）"""
    global _db
    if _db is None:
        _db = get_db()
    return _db

# 执行框架状态
_execution_state: Dict[str, Any] = {
    "active_session": None,
    "cooling_off_until": None,
    "last_exit_reason": None,
}


# ============================================================================
# 辅助函数
# ============================================================================

def _get_nls_result(prices: List[float], params: Dict) -> Dict[str, Any]:
    """获取 NLS 分析结果，自动选择 MATLAB 或 NumPy"""
    global _nls_solver, _matlab_bridge

    if MATLAB_AVAILABLE and _matlab_bridge is not None:
        try:
            result = _matlab_bridge.run_analysis(prices, params)
            if result.success:
                return {
                    "success": True,
                    "engine": "matlab",
                    "spectral_width": result.spectral_width,
                    "mean_frequency": result.mean_frequency,
                    "num_peaks": len(result.resonance_peaks),
                    "resonance_peaks": result.resonance_peaks,
                    "frequencies": result.frequencies[:100],
                    "spectrum": result.spectrum[:100],
                    "execution_time": result.execution_time,
                }
        except Exception as e:
            logger.warning(f"MATLAB 分析失败，fallback 到 NumPy: {e}")

    result = solve_nls(prices, params)
    result["engine"] = "numpy"
    result["num_peaks"] = len(result.get("resonance_peaks", []))
    return result


def _detect_phase(spectral_width: float, dci_value: float = 0.5) -> str:
    """根据谱宽和 DCI 检测市场相位"""
    if dci_value > 0.65 and spectral_width < 0.05:
        return "D"
    if spectral_width < 0.03:
        return "C"
    if spectral_width < 0.05:
        return "B"
    return "A"


def _generate_execution_card(
    phase: str,
    spectral_width: float,
    dci_value: float,
    confidence: float,
) -> Dict[str, Any]:
    """生成执行卡片"""
    hunting_mode = phase in ("B", "C", "D") and confidence > 0.5

    direction_map = {
        "A": "neutral",
        "B": "neutral",
        "C": "bullish",
        "D": "bullish",
    }

    strategy_map = {
        "A": {"max_pos": 0.20, "single_risk": 0.01, "leverage": 0},
        "B": {"max_pos": 0.50, "single_risk": 0.02, "leverage": 1},
        "C": {"max_pos": 0.70, "single_risk": 0.03, "leverage": 2},
        "D": {"max_pos": 1.00, "single_risk": 0.02, "leverage": 1},
    }

    strategy = strategy_map.get(phase, strategy_map["A"])

    return {
        "hunting_mode": hunting_mode,
        "direction_bias": direction_map.get(phase, "neutral"),
        "cycle_level": "daily" if phase in ("B", "C", "D") else "none",
        "active_signal": None,
        "position": None,
        "pnl": {"value": 0, "pct": 0},
        "phase": phase,
        "strategy": strategy,
        "cooling_off": _execution_state.get("cooling_off_until") is not None,
        "cooling_off_until": _execution_state.get("cooling_off_until"),
    }


# ============================================================================
# 定时任务
# ============================================================================

async def _run_scheduled_pipeline():
    """定时运行 Pipeline"""
    logger.info("[SCHEDULER] 定时 Pipeline 触发")
    try:
        from data_fetcher import fetch_btc_data
        df = fetch_btc_data(interval="1m", limit=500, save_csv=False)
        if df is not None and not df.empty:
            prices = df["close"].values.tolist()
            params = config.nemt_defaults.to_dict()
            result = _get_nls_result(prices, params)
            phase = _detect_phase(
                result.get("spectral_width", 0),
                result.get("dci_value", 0.5),
            )
            logger.info(
                f"[SCHEDULER] Pipeline 完成: 谱宽={result.get('spectral_width', 0):.4f}, "
                f"相位={phase}"
            )
        else:
            logger.warning("[SCHEDULER] 获取数据失败")
    except Exception as e:
        logger.error(f"[SCHEDULER] Pipeline 执行失败: {e}")


async def _run_daily_report():
    """生成每日报告"""
    logger.info("[SCHEDULER] 生成每日报告")
    try:
        db = get_db()
        stats = db.get_signal_stats(since_hours=24)
        runs = db.get_pipeline_runs(limit=100)

        phase_dist = {}
        for r in runs:
            if r.get("market_phase"):
                p = r["market_phase"]
                phase_dist[p] = phase_dist.get(p, 0) + 1

        sw_vals = [r["spectral_width"] for r in runs if r.get("spectral_width")]
        dci_vals = [r["dci_value"] for r in runs if r.get("dci_value")]

        report = {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "total_pipeline_runs": len(runs),
            "total_signals": stats["total"],
            "signals_by_action": stats["by_action"],
            "signals_by_phase": stats["by_phase"],
            "avg_spectral_width": sum(sw_vals) / len(sw_vals) if sw_vals else None,
            "avg_dci_value": sum(dci_vals) / len(dci_vals) if dci_vals else None,
            "phase_distribution": phase_dist,
            "active_sessions": len([s for s in runs if s.get("execution_card")]),
            "report_content": _generate_daily_report_text(stats, runs, phase_dist),
        }

        db.save_daily_report(report)
        logger.info(f"[SCHEDULER] 每日报告已保存")
    except Exception as e:
        logger.error(f"[SCHEDULER] 报告生成失败: {e}")


def _generate_daily_report_text(stats: Dict, runs: List[Dict], phase_dist: Dict) -> str:
    """生成报告文本"""
    lines = [
        f"# NEMT 每日报告 {datetime.now().strftime('%Y-%m-%d')}",
        f"",
        f"## Pipeline 执行",
        f"- 总运行次数: {stats['total']}",
        f"- Buy 信号: {stats['by_action'].get('buy', 0)}",
        f"- Sell 信号: {stats['by_action'].get('sell', 0)}",
        f"- Hold 信号: {stats['by_action'].get('hold', 0)}",
        f"",
        f"## 市场相位分布",
    ]
    for phase, count in sorted(phase_dist.items()):
        phase_names = {"A": "高噪声", "B": "涡旋", "C": "共振", "D": "趋势"}
        lines.append(f"- {phase} ({phase_names.get(phase, phase)}): {count}次")

    sw_vals = [r["spectral_width"] for r in runs if r.get("spectral_width")]
    if sw_vals:
        lines.append(f"")
        lines.append(f"## 指标均值")
        lines.append(f"- 平均谱宽: {sum(sw_vals)/len(sw_vals):.4f}")

    return "\n".join(lines)


def _start_scheduler():
    """启动定时任务调度器"""
    global _scheduler
    if not APSCHEDULER_AVAILABLE:
        logger.warning("APScheduler 不可用，跳过定时任务")
        return

    _scheduler = AsyncIOScheduler()

    # 每 5 分钟运行 Pipeline
    _scheduler.add_job(
        _run_scheduled_pipeline,
        trigger=interval.Minutes(minutes=5),
        id="pipeline_5min",
        name="Pipeline 每5分钟执行",
        replace_existing=True,
        max_instances=1,
    )

    # 每天 00:05 生成日报
    _scheduler.add_job(
        _run_daily_report,
        trigger=cron.HourAndMinute(hour=0, minute=5),
        id="daily_report",
        name="每日报告",
        replace_existing=True,
        max_instances=1,
    )

    _scheduler.start()
    logger.info("[OK] 定时任务调度器已启动")


# ============================================================================
# FastAPI 应用
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _db, _nls_solver, _matlab_bridge, _notion_adapter
    global _signal_router, _signal_generator

    logger.info("=" * 60)
    logger.info("NEMT Quant-Sync FastAPI Server 启动中...")
    logger.info("=" * 60)

    # 初始化数据库
    _db = get_db()
    logger.info(f"  数据库: {_get_db().db_path}")

    # 初始化 NLS 求解器
    _nls_solver = get_solver()
    logger.info(f"  NLS Solver: NumPy (fallback 模式)")

    # 初始化 MATLAB 桥接器
    if MATLAB_AVAILABLE:
        try:
            _matlab_bridge = MatlabBridge()
            if _matlab_bridge.get_engine_info()["available"]:
                logger.info("  MATLAB Engine: 可用")
            else:
                logger.info("  MATLAB Engine: 不可用，使用 NumPy fallback")
        except Exception as e:
            logger.warning(f"  MATLAB 初始化失败: {e}")

    # 初始化 Notion
    if NOTION_AVAILABLE:
        try:
            _notion_adapter = NotionAdapter()
            if _notion_adapter.configured:
                logger.info("  Notion: 已配置")
            else:
                logger.info("  Notion: 未配置 (NOTION_TOKEN 未设置)")
        except Exception as e:
            logger.warning(f"  Notion 初始化失败: {e}")

    # 初始化信号路由器
    if ROUTER_AVAILABLE:
        try:
            _signal_router = SignalRouter()
            _signal_generator = SignalGenerator(_signal_router)
            logger.info("  Signal Router: 已初始化")
        except Exception as e:
            logger.warning(f"  Signal Router 初始化失败: {e}")

    # 启动定时任务
    _start_scheduler()

    logger.info("=" * 60)
    logger.info("NEMT Quant-Sync FastAPI Server 已启动!")
    logger.info(f"  API 文档: http://localhost:8080/docs")
    logger.info("=" * 60)

    yield

    # 关闭
    logger.info("正在关闭服务器...")
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    logger.info("服务器已关闭")


app = FastAPI(
    title="NEMT Quant-Sync API",
    description="NEMT 量化同步中枢 - 生产级 API 服务器",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# 路由
# ============================================================================

# --- 健康检查 ---

@app.get("/health")
async def health_check():
    """健康检查端点 - 云服务商健康探测用"""
    db_health = _get_db().health_check() if _db else {"ok": False, "error": "DB not initialized"}

    scheduler_info = None
    if _scheduler and _scheduler.running:
        jobs = []
        for job in _scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            })
        scheduler_info = {"running": True, "jobs": jobs}
    else:
        scheduler_info = {"running": False}

    return {
        "status": "ok" if db_health.get("ok") else "degraded",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "database": db_health,
            "matlab": _matlab_bridge.get_engine_info() if _matlab_bridge else {"available": False},
            "notion": _notion_adapter.health_check() if _notion_adapter else {"configured": False},
            "scheduler": scheduler_info,
        },
    }


# --- 根路径 ---

@app.get("/")
async def root():
    """API 根路径"""
    return {
        "name": "NEMT Quant-Sync API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "pipeline_run": "POST /api/pipeline/run",
            "pipeline_status": "GET /api/pipeline/status",
            "pipeline_runs": "GET /api/pipeline/runs",
            "execution_predict": "POST /api/execution/predict",
            "execution_entry": "POST /api/execution/entry",
            "execution_exit": "POST /api/execution/exit",
            "execution_add": "POST /api/execution/add",
            "execution_card": "GET /api/execution/card",
            "signals": "GET /api/signals",
            "signals_send": "POST /api/signals/send",
            "daily_reports": "GET /api/reports/daily",
        },
    }


# --- Pipeline ---

@app.post("/api/pipeline/run")
async def run_pipeline(body: PipelineRunRequest):
    """
    运行完整 Pipeline
    Notion读 → NEMT分析 → 信号生成 → 结果展示
    """
    run_id = None
    try:
        run_id = _get_db().create_pipeline_run(
            symbol=body.symbol,
            params=body.params or config.nemt_defaults.to_dict(),
        )

        logs = []
        logs.append({"step": "STEP_1", "message": "开始 NEMT 分析", "level": "INFO"})

        # NEMT 分析
        params = body.params or config.nemt_defaults.to_dict()
        nemt_result = _get_nls_result(body.prices, params)
        logs.append({
            "step": "STEP_2",
            "message": f"NEMT 分析完成 (引擎: {nemt_result.get('engine', 'unknown')})",
            "level": "INFO",
            "data": {"spectral_width": nemt_result.get("spectral_width")},
        })

        spectral_width = nemt_result.get("spectral_width", 0)
        phase = _detect_phase(spectral_width)
        execution_card = _generate_execution_card(
            phase, spectral_width, 0.5, 0.5
        )

        logs.append({
            "step": "STEP_3",
            "message": f"市场相位: {phase}",
            "level": "INFO",
        })

        # 信号生成
        signal_data = {
            "signal_id": f"sig_{int(datetime.now().timestamp() * 1000)}",
            "symbol": body.symbol,
            "action": "hold",
            "direction": "neutral",
            "price": body.prices[-1] if body.prices else 0,
            "confidence": max(0.3, 1.0 - spectral_width * 5),
            "reason": f"谱宽={spectral_width:.4f}, 相位={phase}",
            "spectral_width": spectral_width,
            "phase": phase,
            "indicators": {
                "spectral_width": spectral_width,
                "mean_frequency": nemt_result.get("mean_frequency", 0),
                "num_peaks": nemt_result.get("num_peaks", 0),
            },
        }

        _get_db().create_signal(signal_data, run_id)
        logs.append({"step": "STEP_4", "message": "信号已记录", "level": "SUCCESS"})

        # 写入 Notion (如果配置了)
        if _notion_adapter and body.notion_page_id:
            logs.append({"step": "STEP_5", "message": "跳过 Notion 写入 (未实现)", "level": "INFO"})

        # 更新数据库
        _get_db().update_pipeline_run(
            run_id=run_id,
            spectral_width=spectral_width,
            mean_frequency=nemt_result.get("mean_frequency"),
            num_peaks=nemt_result.get("num_peaks"),
            market_phase=phase,
            execution_card=execution_card,
            success=True,
            logs=logs,
        )

        return {
            "success": True,
            "run_id": run_id,
            "symbol": body.symbol,
            "phase": phase,
            "spectral_width": spectral_width,
            "engine": nemt_result.get("engine", "unknown"),
            "execution_card": execution_card,
            "signal": signal_data,
            "logs": logs,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Pipeline 执行失败: {e}")
        if run_id:
            _get_db().update_pipeline_run(run_id, success=False, error_message=str(e), logs=[])
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pipeline/status")
async def get_pipeline_status():
    """获取系统状态"""
    return {
        "server": "NEMT Quant-Sync FastAPI",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "matlab_available": MATLAB_AVAILABLE,
        "matlab_engine_running": _matlab_bridge.get_engine_info()["running"] if _matlab_bridge else False,
        "notion_configured": _notion_adapter.configured if _notion_adapter else False,
        "scheduler_running": _scheduler.running if _scheduler else False,
    }


@app.get("/api/pipeline/runs")
async def get_pipeline_runs(
    limit: int = Query(default=50, le=500),
    symbol: Optional[str] = Query(default=None),
    since_hours: int = Query(default=24, le=168),
):
    """获取 Pipeline 运行历史"""
    runs = _get_db().get_pipeline_runs(limit=limit, symbol=symbol, since_hours=since_hours)
    return {"total": len(runs), "runs": runs}


# --- Execution ---

@app.post("/api/execution/predict")
async def execution_predict(body: ExecutionPredictRequest):
    """
    运行预测 - 执行框架核心
    """
    try:
        # 检测相位
        phase = _detect_phase(body.spectral_width, body.dci)
        confidence = body.confidence

        # 狩猎模式
        hunting_mode = phase in ("B", "C", "D") and confidence > 0.5

        # 方向偏置
        if body.dci > 0.65:
            direction = "bullish"
        elif body.dci < 0.55:
            direction = "bearish"
        else:
            direction = "neutral"

        # 周期级别
        if body.macro_score >= 7 and confidence > 0.6:
            cycle_level = "monthly"
        elif body.macro_score >= 6 and confidence > 0.5:
            cycle_level = "weekly"
        else:
            cycle_level = "daily"

        # 相位策略
        strategy_map = {
            "A": {"max_pos": 0.20, "single_risk": 0.01, "leverage": 0},
            "B": {"max_pos": 0.50, "single_risk": 0.02, "leverage": 1},
            "C": {"max_pos": 0.70, "single_risk": 0.03, "leverage": 2},
            "D": {"max_pos": 1.00, "single_risk": 0.02, "leverage": 1},
        }
        strategy = strategy_map.get(phase, strategy_map["A"])

        # 信号检查
        signal_type = None
        signal_confidence = 0.0
        if hunting_mode:
            if phase == "C" and 5 <= body.vortex_maturity <= 15 and body.dci >= 0.55:
                signal_type = "vortex_breakout"
                signal_confidence = min(body.vortex_maturity / 10, 1.0)
            elif phase == "B" and 0.08 <= body.noise_level <= 0.15:
                signal_type = "stochastic_resonance"
                signal_confidence = 0.6
            elif phase == "D" and body.dci >= 0.6:
                signal_type = "trend_pullback"
                signal_confidence = body.dci

        card = {
            "hunting_mode": hunting_mode,
            "direction_bias": direction,
            "cycle_level": cycle_level,
            "active_signal": {
                "type": signal_type,
                "confidence": signal_confidence,
                "phase": phase,
            } if signal_type else None,
            "phase": phase,
            "strategy": strategy,
            "position": _execution_state.get("active_session"),
            "pnl": {"value": 0, "pct": 0},
            "macro_scores": {
                "macro": body.macro_score,
                "onchain": body.onchain_score,
                "halving_phase": body.halving_phase,
            },
            "cooling_off": _execution_state.get("cooling_off_until") is not None,
        }

        return {
            "success": True,
            "card": card,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/execution/entry")
async def execution_entry(body: ExecutionEntryRequest):
    """执行入场"""
    try:
        # 冷却期检查
        if _execution_state.get("cooling_off_until"):
            from datetime import datetime as dt
            cool_until = _execution_state["cooling_off_until"]
            if isinstance(cool_until, str):
                cool_until = dt.fromisoformat(cool_until)
            if dt.now() < cool_until:
                remaining = (cool_until - dt.now()).total_seconds() / 3600
                raise HTTPException(
                    status_code=429,
                    detail=f"冷静期，还剩 {remaining:.1f} 小时",
                )

        session_id = body.session_id or str(uuid.uuid4())[:16]
        entry_price = body.price

        # Kelly 仓位计算
        kelly_size = body.confidence * 0.5
        position_size = min(kelly_size, 0.5)  # 最大 50%

        session_data = {
            "session_id": session_id,
            "symbol": "BTCUSDT",
            "direction": "long",
            "phase": "C",
            "entry_price": entry_price,
            "quantity": body.total_capital * position_size / entry_price,
            "stop_loss": entry_price * 0.98,
            "take_profit": entry_price * 1.06,
            "confidence": body.confidence,
            "position_size": position_size,
            "status": "confirmed",
            "cooling_off_until": None,
        }

        _get_db().create_session(session_data)
        _execution_state["active_session"] = session_data

        return {
            "success": True,
            "session_id": session_id,
            "entry_price": entry_price,
            "position_size": position_size,
            "stop_loss": session_data["stop_loss"],
            "take_profit": session_data["take_profit"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/execution/exit")
async def execution_exit(body: ExecutionExitRequest):
    """执行出场"""
    try:
        if _execution_state.get("active_session") is None:
            raise HTTPException(status_code=404, detail="无活跃持仓")

        session = _execution_state["active_session"]

        # 更新数据库
        _get_db().update_session(
            body.session_id,
            is_active=False,
            status="completed",
            last_exit_reason=body.reason,
        )

        # 触发冷静期
        from datetime import datetime as dt
        _execution_state["cooling_off_until"] = (dt.now() + timedelta(hours=24)).isoformat()
        _execution_state["last_exit_reason"] = body.reason
        _execution_state["active_session"] = None

        return {
            "success": True,
            "session_id": body.session_id,
            "exit_reason": body.reason,
            "cooling_off_hours": 24,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/execution/add")
async def execution_add(body: ExecutionAddRequest):
    """加仓"""
    try:
        if not _execution_state.get("active_session"):
            raise HTTPException(status_code=404, detail="无活跃持仓")

        session = _execution_state["active_session"]
        old_entry = session["entry_price"]
        old_qty = session["quantity"]
        add_qty = body.add_on_size

        # 新平均入场价
        new_total = old_entry * old_qty + body.price * add_qty
        new_qty = old_qty + add_qty
        new_entry = new_total / new_qty if new_qty > 0 else old_entry

        session["entry_price"] = new_entry
        session["quantity"] = new_qty
        session["stop_loss"] = min(session["stop_loss"], body.price * 0.97)

        return {
            "success": True,
            "new_entry_price": new_entry,
            "new_quantity": new_qty,
            "new_stop_loss": session["stop_loss"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/execution/card")
async def get_execution_card():
    """获取执行卡片状态"""
    return {
        "card": _execution_state.get("active_session"),
        "cooling_off_until": _execution_state.get("cooling_off_until"),
        "last_exit_reason": _execution_state.get("last_exit_reason"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# --- Signals ---

@app.get("/api/signals")
async def get_signals(
    limit: int = Query(default=50, le=500),
    symbol: Optional[str] = Query(default=None),
):
    """获取信号历史"""
    signals = _get_db().get_signals(limit=limit, symbol=symbol)
    stats = _get_db().get_signal_stats(since_hours=24)
    return {"total": len(signals), "signals": signals, "stats_24h": stats}


@app.post("/api/signals/send")
async def send_signal(body: SignalRequest):
    """发送信号到路由"""
    if not _signal_router:
        return {"success": False, "error": "Signal router not available"}

    signal_data = {
        "signal_id": f"sig_{int(datetime.now().timestamp() * 1000)}",
        "symbol": body.symbol,
        "action": body.action,
        "price": body.price,
        "confidence": body.confidence,
        "reason": body.reason,
        "spectral_width": body.spectral_width,
        "dci_value": body.dci_value,
        "vortex_maturity": body.vortex_maturity,
        "resonance_confidence": body.resonance_confidence,
        "phase": body.phase,
    }

    signal_id = _get_db().create_signal(signal_data)
    return {"success": True, "signal_id": signal_id}


# --- Reports ---

@app.get("/api/reports/daily")
async def get_daily_reports(limit: int = Query(default=30, le=90)):
    """获取每日报告"""
    reports = _get_db().get_daily_reports(limit=limit)
    return {"total": len(reports), "reports": reports}


# --- Scheduler ---

@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """获取调度器状态"""
    if not _scheduler or not _scheduler.running:
        return {"running": False, "jobs": []}

    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "pending": job.pending,
        })

    return {"running": True, "jobs": jobs}


@app.post("/api/scheduler/trigger/{job_id}")
async def trigger_scheduler_job(job_id: str):
    """手动触发定时任务"""
    if not _scheduler or not _scheduler.running:
        raise HTTPException(status_code=503, detail="Scheduler not running")

    job = _scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    await job.func()
    return {"success": True, "job_id": job_id, "message": "Job triggered"}


# ============================================================================
# 启动入口
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="NEMT Quant-Sync FastAPI Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host")
    parser.add_argument("--port", type=int, default=8080, help="Port")
    parser.add_argument("--reload", action="store_true", help="Reload mode")
    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║          NEMT Quant-Sync FastAPI Server                   ║
╠══════════════════════════════════════════════════════════════╣
║  地址: http://{args.host}:{args.port}                         ║
║  文档: http://{args.host}:{args.port}/docs                   ║
║                                                          ║
║  端点:                                                     ║
║    POST /api/pipeline/run   - 运行 Pipeline                ║
║    GET  /api/pipeline/runs - 运行历史                     ║
║    POST /api/execution/predict - 预测                      ║
║    GET  /api/execution/card  - 执行卡片状态               ║
║    GET  /api/signals        - 信号历史                    ║
║    GET  /health             - 健康检查                    ║
╚══════════════════════════════════════════════════════════════╝
""")

    try:
        import uvicorn
        uvicorn.run(
            "api_server_prod:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info",
        )
    except ImportError:
        print("ERROR: uvicorn not installed. Run: pip install 'uvicorn[standard]'")
        sys.exit(1)


if __name__ == "__main__":
    main()
