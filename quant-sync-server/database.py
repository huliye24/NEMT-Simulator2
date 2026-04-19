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
SQLite 数据库管理
"""

import os
import json
import uuid
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

try:
    from .models import Base, PipelineRun, SignalRecord, ExecutionSession, DailyReport, ConfigSync
except ImportError:
    from models import Base, PipelineRun, SignalRecord, ExecutionSession, DailyReport, ConfigSync


logger = logging.getLogger(__name__)


class Database:
    """
    SQLite 数据库管理
    """

    _instance = None

    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = None):
        if self._initialized:
            return
        self._initialized = True

        if db_path is None:
            db_path = os.getenv("DATABASE_PATH", str(Path(__file__).parent / "nemt_data.db"))

        self.db_path = db_path
        self.db_dir = str(Path(db_path).parent)

        os.makedirs(self.db_dir, exist_ok=True)

        db_url = f"sqlite:///{db_path}"
        self.engine = create_engine(
            db_url,
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

        logger.info(f"[OK] 数据库已初始化: {db_path}")

    @contextmanager
    def get_session(self) -> Session:
        """获取数据库会话"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # =====================
    # Pipeline Run
    # =====================

    def create_pipeline_run(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1m",
        params: Dict[str, Any] = None,
    ) -> str:
        """创建 Pipeline Run 记录，返回 run_id"""
        run_id = str(uuid.uuid4())[:16]
        params = params or {}

        with self.get_session() as session:
            run = PipelineRun(
                run_id=run_id,
                symbol=symbol,
                interval=interval,
                alpha=params.get("alpha", 0.1),
                beta=params.get("beta", 1.0),
                noise=params.get("noiseLevel", params.get("noise", 0.2)),
                steps=params.get("steps", 200),
                n=params.get("n", 128),
                success=False,
                started_at=datetime.now(timezone.utc),
            )
            session.add(run)
        return run_id

    def update_pipeline_run(
        self,
        run_id: str,
        spectral_width: float = None,
        mean_frequency: float = None,
        num_peaks: int = None,
        market_phase: str = None,
        dci_value: float = None,
        dci_direction: str = None,
        execution_card: Dict = None,
        success: bool = True,
        error_message: str = None,
        logs: List[Dict] = None,
    ) -> bool:
        """更新 Pipeline Run 结果"""
        with self.get_session() as session:
            run = session.query(PipelineRun).filter_by(run_id=run_id).first()
            if not run:
                return False

            if spectral_width is not None:
                run.spectral_width = spectral_width
            if mean_frequency is not None:
                run.mean_frequency = mean_frequency
            if num_peaks is not None:
                run.num_peaks = num_peaks
            if market_phase is not None:
                run.market_phase = market_phase
            if dci_value is not None:
                run.dci_value = dci_value
            if dci_direction is not None:
                run.dci_direction = dci_direction
            if execution_card is not None:
                run.execution_card = execution_card

            run.success = success
            run.error_message = error_message
            run.completed_at = datetime.now(timezone.utc)

            if logs:
                run.logs = json.dumps(logs, ensure_ascii=False)

        return True

    def get_pipeline_runs(
        self,
        limit: int = 50,
        symbol: str = None,
        since_hours: int = None,
    ) -> List[Dict]:
        """获取 Pipeline Run 列表"""
        with self.get_session() as session:
            q = session.query(PipelineRun)
            if symbol:
                q = q.filter_by(symbol=symbol)
            if since_hours:
                from datetime import timedelta
                cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
                q = q.filter(PipelineRun.started_at >= cutoff)

            runs = q.order_by(PipelineRun.started_at.desc()).limit(limit).all()
            return [self._run_to_dict(r) for r in runs]

    def _run_to_dict(self, run: PipelineRun) -> Dict:
        logs = run.logs
        if isinstance(logs, str):
            try:
                logs = json.loads(logs)
            except Exception:
                logs = None

        return {
            "run_id": run.run_id,
            "symbol": run.symbol,
            "interval": run.interval,
            "spectral_width": run.spectral_width,
            "mean_frequency": run.mean_frequency,
            "num_peaks": run.num_peaks,
            "market_phase": run.market_phase,
            "dci_value": run.dci_value,
            "dci_direction": run.dci_direction,
            "execution_card": run.execution_card,
            "success": run.success,
            "error_message": run.error_message,
            "logs": logs,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        }

    # =====================
    # Signal Record
    # =====================

    def create_signal(
        self,
        signal_data: Dict[str, Any],
        pipeline_run_id: str = None,
    ) -> str:
        """创建信号记录"""
        signal_id = signal_data.get("signal_id", f"sig_{int(datetime.now().timestamp() * 1000)}")

        with self.get_session() as session:
            record = SignalRecord(
                signal_id=signal_id,
                symbol=signal_data.get("symbol", "BTCUSDT"),
                action=signal_data.get("action", signal_data.get("type", "hold")),
                direction=signal_data.get("direction"),
                price=signal_data.get("price"),
                stop_loss=signal_data.get("stop_loss"),
                take_profit=signal_data.get("take_profit"),
                confidence=signal_data.get("confidence"),
                signal_type=signal_data.get("type"),
                reason=signal_data.get("reason"),
                spectral_width=signal_data.get("spectral_width"),
                dci_value=signal_data.get("dci_value"),
                vortex_maturity=signal_data.get("vortex_maturity"),
                resonance_confidence=signal_data.get("resonance_confidence"),
                phase=signal_data.get("phase"),
                indicators=signal_data.get("indicators"),
            )
            session.add(record)
        return signal_id

    def get_signals(self, limit: int = 100, symbol: str = None) -> List[Dict]:
        """获取信号列表"""
        with self.get_session() as session:
            q = session.query(SignalRecord)
            if symbol:
                q = q.filter_by(symbol=symbol)

            records = q.order_by(SignalRecord.created_at.desc()).limit(limit).all()
            return [self._signal_to_dict(r) for r in records]

    def _signal_to_dict(self, rec: SignalRecord) -> Dict:
        return {
            "signal_id": rec.signal_id,
            "symbol": rec.symbol,
            "action": rec.action,
            "direction": rec.direction,
            "price": rec.price,
            "stop_loss": rec.stop_loss,
            "take_profit": rec.take_profit,
            "confidence": rec.confidence,
            "signal_type": rec.signal_type,
            "reason": rec.reason,
            "spectral_width": rec.spectral_width,
            "dci_value": rec.dci_value,
            "vortex_maturity": rec.vortex_maturity,
            "resonance_confidence": rec.resonance_confidence,
            "phase": rec.phase,
            "indicators": rec.indicators,
            "sent_to_redis": rec.sent_to_redis,
            "sent_to_notion": rec.sent_to_notion,
            "created_at": rec.created_at.isoformat() if rec.created_at else None,
        }

    def get_signal_stats(self, since_hours: int = 24) -> Dict:
        """获取信号统计"""
        with self.get_session() as session:
            from datetime import timedelta
            cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)

            records = session.query(SignalRecord).filter(
                SignalRecord.created_at >= cutoff
            ).all()

            total = len(records)
            by_action = {}
            by_phase = {}

            for rec in records:
                by_action[rec.action] = by_action.get(rec.action, 0) + 1
                if rec.phase:
                    by_phase[rec.phase] = by_phase.get(rec.phase, 0) + 1

            return {
                "total": total,
                "by_action": by_action,
                "by_phase": by_phase,
                "since_hours": since_hours,
            }

    # =====================
    # Execution Session
    # =====================

    def create_session(self, session_data: Dict[str, Any]) -> str:
        """创建执行会话"""
        session_id = session_data.get("session_id", str(uuid.uuid4())[:16])

        with self.get_session() as session:
            sess = ExecutionSession(
                session_id=session_id,
                symbol=session_data.get("symbol", "BTCUSDT"),
                direction=session_data.get("direction"),
                signal_type=session_data.get("signal_type"),
                phase=session_data.get("phase"),
                entry_price=session_data.get("entry_price"),
                quantity=session_data.get("quantity"),
                stop_loss=session_data.get("stop_loss"),
                take_profit=session_data.get("take_profit"),
                confidence=session_data.get("confidence"),
                position_size=session_data.get("position_size"),
                status=session_data.get("status", "waiting"),
                cooling_off_until=session_data.get("cooling_off_until"),
            )
            session.add(sess)
        return session_id

    def update_session(self, session_id: str, **kwargs) -> bool:
        """更新执行会话"""
        with self.get_session() as session:
            sess = session.query(ExecutionSession).filter_by(session_id=session_id).first()
            if not sess:
                return False

            for key, value in kwargs.items():
                if hasattr(sess, key) and key not in ("id", "session_id"):
                    setattr(sess, key, value)

            sess.updated_at = datetime.now(timezone.utc)
        return True

    def get_active_session(self, symbol: str = "BTCUSDT") -> Optional[Dict]:
        """获取活跃会话"""
        with self.get_session() as session:
            sess = session.query(ExecutionSession).filter_by(
                symbol=symbol, is_active=True
            ).first()
            if not sess:
                return None

            return {
                "session_id": sess.session_id,
                "symbol": sess.symbol,
                "direction": sess.direction,
                "signal_type": sess.signal_type,
                "phase": sess.phase,
                "entry_price": sess.entry_price,
                "entry_time": sess.entry_time.isoformat() if sess.entry_time else None,
                "quantity": sess.quantity,
                "stop_loss": sess.stop_loss,
                "take_profit": sess.take_profit,
                "trailing_stop": sess.trailing_stop,
                "current_price": sess.current_price,
                "unrealized_pnl": sess.unrealized_pnl,
                "unrealized_pnl_pct": sess.unrealized_pnl_pct,
                "confidence": sess.confidence,
                "position_size": sess.position_size,
                "status": sess.status,
                "add_positions": sess.add_positions,
                "cooling_off_until": sess.cooling_off_until.isoformat() if sess.cooling_off_until else None,
                "last_exit_reason": sess.last_exit_reason,
                "created_at": sess.created_at.isoformat() if sess.created_at else None,
            }

    # =====================
    # Daily Report
    # =====================

    def save_daily_report(self, report_data: Dict[str, Any]) -> bool:
        """保存每日报告"""
        report_date = report_data.get("report_date", datetime.now().strftime("%Y-%m-%d"))

        with self.get_session() as session:
            existing = session.query(DailyReport).filter_by(report_date=report_date).first()
            if existing:
                for key, value in report_data.items():
                    if hasattr(existing, key) and key != "id":
                        setattr(existing, key, value)
                existing.generated_at = datetime.now(timezone.utc)
            else:
                report = DailyReport(
                    report_date=report_date,
                    total_pipeline_runs=report_data.get("total_pipeline_runs", 0),
                    total_signals=report_data.get("total_signals", 0),
                    signals_by_action=report_data.get("signals_by_action"),
                    signals_by_phase=report_data.get("signals_by_phase"),
                    avg_spectral_width=report_data.get("avg_spectral_width"),
                    avg_dci_value=report_data.get("avg_dci_value"),
                    phase_distribution=report_data.get("phase_distribution"),
                    active_sessions=report_data.get("active_sessions"),
                    total_trades=report_data.get("total_trades"),
                    report_content=report_data.get("report_content"),
                )
                session.add(report)
        return True

    def get_daily_reports(self, limit: int = 30) -> List[Dict]:
        """获取每日报告"""
        with self.get_session() as session:
            reports = session.query(DailyReport).order_by(
                DailyReport.report_date.desc()
            ).limit(limit).all()
            return [
                {
                    "report_date": r.report_date,
                    "total_pipeline_runs": r.total_pipeline_runs,
                    "total_signals": r.total_signals,
                    "signals_by_action": r.signals_by_action,
                    "signals_by_phase": r.signals_by_phase,
                    "avg_spectral_width": r.avg_spectral_width,
                    "avg_dci_value": r.avg_dci_value,
                    "phase_distribution": r.phase_distribution,
                    "report_content": r.report_content,
                    "generated_at": r.generated_at.isoformat() if r.generated_at else None,
                }
                for r in reports
            ]

    # =====================
    # Config Sync
    # =====================

    def log_config_sync(self, source: str, key: str, old_value: Any, new_value: Any):
        """记录配置同步"""
        with self.get_session() as session:
            sync = ConfigSync(
                source=source,
                config_key=key,
                old_value=old_value,
                new_value=new_value,
            )
            session.add(sync)

    # =====================
    # 健康检查
    # =====================

    def health_check(self) -> Dict[str, Any]:
        """数据库健康检查"""
        try:
            with self.get_session() as session:
                total_runs = session.query(PipelineRun).count()
                total_signals = session.query(SignalRecord).count()
                active_sessions = session.query(ExecutionSession).filter_by(is_active=True).count()

                size_bytes = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

                return {
                    "ok": True,
                    "db_path": self.db_path,
                    "size_mb": round(size_bytes / (1024 * 1024), 2),
                    "total_pipeline_runs": total_runs,
                    "total_signals": total_signals,
                    "active_sessions": active_sessions,
                }
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
            }


# 全局实例
_db_instance: Optional[Database] = None


def get_db() -> Database:
    """获取数据库单例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
