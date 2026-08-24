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
数据库模型定义
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    Text, JSON, Index, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum


Base = declarative_base()


class MarketPhaseDB(str, enum.Enum):
    PHASE_A_NOISE = "A"
    PHASE_B_VORTEX = "B"
    PHASE_C_RESONANCE = "C"
    PHASE_D_TREND = "D"


class SignalActionDB(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"


class ExecutionStatusDB(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    TRIGGERED = "triggered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class PipelineRun(Base):
    """Pipeline 执行记录"""
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), unique=True, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, default="BTCUSDT")
    interval = Column(String(10), nullable=False, default="1m")

    # 参数快照
    alpha = Column(Float, nullable=False, default=0.1)
    beta = Column(Float, nullable=False, default=1.0)
    noise = Column(Float, nullable=False, default=0.2)
    steps = Column(Integer, nullable=False, default=200)
    n = Column(Integer, nullable=False, default=128)

    # 分析结果
    spectral_width = Column(Float, nullable=True)
    mean_frequency = Column(Float, nullable=True)
    num_peaks = Column(Integer, nullable=True, default=0)

    # 相位
    market_phase = Column(String(1), nullable=True)

    # DCI
    dci_value = Column(Float, nullable=True)
    dci_direction = Column(String(20), nullable=True)

    # 执行卡片快照
    execution_card = Column(JSON, nullable=True)

    # 状态
    success = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    logs = Column(JSON, nullable=True)

    # 时间
    started_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_pipeline_runs_started", "started_at"),
        Index("ix_pipeline_runs_symbol_phase", "symbol", "market_phase"),
    )


class SignalRecord(Base):
    """交易信号记录"""
    __tablename__ = "signal_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(String(64), unique=True, nullable=False, index=True)
    pipeline_run_id = Column(Integer, ForeignKey("pipeline_runs.id"), nullable=True)

    symbol = Column(String(20), nullable=False, default="BTCUSDT")
    action = Column(String(10), nullable=False)
    direction = Column(String(20), nullable=True)

    price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)

    confidence = Column(Float, nullable=True)
    signal_type = Column(String(30), nullable=True)
    reason = Column(Text, nullable=True)

    # NEMT 关联指标
    spectral_width = Column(Float, nullable=True)
    dci_value = Column(Float, nullable=True)
    vortex_maturity = Column(Float, nullable=True)
    resonance_confidence = Column(Float, nullable=True)
    phase = Column(String(1), nullable=True)

    # 指标详情
    indicators = Column(JSON, nullable=True)

    # 发送状态
    sent_to_redis = Column(Boolean, nullable=False, default=False)
    sent_to_notion = Column(Boolean, nullable=False, default=False)

    # 时间
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    __table_args__ = (
        Index("ix_signal_records_created", "created_at"),
        Index("ix_signal_records_symbol_action", "symbol", "action"),
    )


class ExecutionSession(Base):
    """执行会话（持仓管理）"""
    __tablename__ = "execution_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)

    symbol = Column(String(20), nullable=False, default="BTCUSDT")

    # 当前状态
    is_active = Column(Boolean, nullable=False, default=True)
    status = Column(String(20), nullable=False, default="waiting")

    # 方向
    direction = Column(String(20), nullable=True)
    signal_type = Column(String(30), nullable=True)
    phase = Column(String(1), nullable=True)

    # 入场
    entry_price = Column(Float, nullable=True)
    entry_time = Column(DateTime(timezone=True), nullable=True)
    quantity = Column(Float, nullable=True)
    entry_signals_confirmed = Column(JSON, nullable=True)

    # 止损/止盈
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    trailing_stop = Column(Float, nullable=True)

    # 当前状态
    current_price = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, nullable=True)
    unrealized_pnl_pct = Column(Float, nullable=True)

    # 加仓记录
    add_positions = Column(JSON, nullable=True)

    # 风控
    confidence = Column(Float, nullable=True)
    position_size = Column(Float, nullable=True)

    # 冷却
    cooling_off_until = Column(DateTime(timezone=True), nullable=True)
    last_exit_reason = Column(Text, nullable=True)

    # 时间
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_execution_sessions_active", "is_active", "symbol"),
    )


class DailyReport(Base):
    """每日报告"""
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(String(10), unique=True, nullable=False, index=True)

    # 统计
    total_pipeline_runs = Column(Integer, nullable=False, default=0)
    total_signals = Column(Integer, nullable=False, default=0)
    signals_by_action = Column(JSON, nullable=True)
    signals_by_phase = Column(JSON, nullable=True)

    # 指标均值
    avg_spectral_width = Column(Float, nullable=True)
    avg_dci_value = Column(Float, nullable=True)

    # 相位分布
    phase_distribution = Column(JSON, nullable=True)

    # 执行
    active_sessions = Column(Integer, nullable=True)
    total_trades = Column(Integer, nullable=True)

    # 报告内容
    report_content = Column(Text, nullable=True)

    # 时间
    generated_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    __table_args__ = (
        Index("ix_daily_reports_date", "report_date"),
    )


class ConfigSync(Base):
    """配置同步记录"""
    __tablename__ = "config_syncs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(20), nullable=False)  # 'notion', 'file'
    config_key = Column(String(50), nullable=False)

    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)

    synced_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    __table_args__ = (
        Index("ix_config_syncs_key", "config_key"),
    )
