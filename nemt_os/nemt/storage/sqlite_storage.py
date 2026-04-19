"""
SQLite 数据存储层
提供 K线数据、策略数据、回测结果的持久化
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Iterator
from contextlib import contextmanager
from dataclasses import asdict

from ..market_providers.base import KLine


class SQLiteStorage:
    """
    SQLite 存储管理器
    
    负责:
    1. K线数据存储
    2. 策略配置存储
    3. 回测结果存储
    4. 信号历史存储
    """

    def __init__(self, db_path: str = "data/nemt_storage.db"):
        """
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_dir()

        # 为内存数据库使用共享连接
        if db_path == ':memory:':
            self._shared_conn = sqlite3.connect(':memory:', check_same_thread=False)
            self._shared_conn.row_factory = sqlite3.Row
        else:
            self._shared_conn = None

        self._init_tables()

    def _ensure_dir(self) -> None:
        """确保目录存在"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _get_connection(self):
        """获取数据库连接的上下文管理器"""
        if self._shared_conn is not None:
            # 使用共享连接
            try:
                yield self._shared_conn
            except Exception:
                raise
        else:
            # 使用文件数据库
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

    def close(self):
        """关闭数据库连接"""
        if self._shared_conn is not None:
            self._shared_conn.close()
            self._shared_conn = None

    def _init_tables(self) -> None:
        """初始化数据库表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # K线数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS klines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, interval, timestamp)
                )
            """)
            
            # 创建K线索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_klines_symbol_interval_time
                ON klines(symbol, interval, timestamp)
            """)
            
            # 策略配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    params TEXT NOT NULL,
                    status TEXT DEFAULT 'alive',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 策略性能表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    sharpe_ratio REAL,
                    max_drawdown REAL,
                    win_rate REAL,
                    total_pnl REAL,
                    score REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
                )
            """)
            
            # 回测结果表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backtest_id TEXT UNIQUE NOT NULL,
                    strategy_id TEXT,
                    config TEXT NOT NULL,
                    metrics TEXT,
                    equity_curve TEXT,
                    trades TEXT,
                    status TEXT DEFAULT 'pending',
                    started_at TEXT,
                    completed_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 信号历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT UNIQUE NOT NULL,
                    signal_type TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    confidence REAL,
                    reason TEXT,
                    price REAL,
                    metadata TEXT,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 系统配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print(f"[Storage] Database initialized: {self.db_path}")

    # ==================== K线数据操作 ====================

    def save_klines(self, klines: List[KLine]) -> int:
        """
        批量保存K线数据
        
        Args:
            klines: K线数据列表
            
        Returns:
            int: 保存的记录数
        """
        if not klines:
            return 0
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            data = [
                (
                    k.symbol, k.interval, 
                    k.timestamp.isoformat() if isinstance(k.timestamp, datetime) else str(k.timestamp),
                    k.open, k.high, k.low, k.close, k.volume
                )
                for k in klines
            ]
            
            cursor.executemany("""
                INSERT OR REPLACE INTO klines 
                (symbol, interval, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            
            conn.commit()
            return cursor.rowcount

    def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[KLine]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            interval: K线周期
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
            
        Returns:
            List[KLine]: K线数据列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM klines WHERE symbol = ? AND interval = ?"
            params: List[Any] = [symbol, interval]
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())
            
            query += " ORDER BY timestamp ASC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            klines = []
            for row in cursor.fetchall():
                klines.append(KLine(
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row['volume'],
                    symbol=row['symbol'],
                    interval=row['interval']
                ))
            
            return klines

    def get_klines_iterator(
        self,
        symbol: str,
        interval: str = "1h",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        batch_size: int = 1000
    ) -> Iterator[List[KLine]]:
        """
        分批获取K线数据（用于大数据量）
        
        Args:
            symbol: 交易对
            interval: K线周期
            start_time: 开始时间
            end_time: 结束时间
            batch_size: 每批数量
            
        Yields:
            Iterator[List[KLine]]: K线数据批次
        """
        offset = 0
        while True:
            batch = self.get_klines(
                symbol, interval, start_time, end_time, 
                limit=batch_size
            )
            if not batch:
                break
            
            yield batch
            
            if len(batch) < batch_size:
                break
                
            offset += batch_size

    # ==================== 策略操作 ====================

    def save_strategy(
        self,
        strategy_id: str,
        name: str,
        strategy_type: str,
        params: Dict[str, Any],
        status: str = "alive"
    ) -> bool:
        """保存策略配置"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO strategies 
                (strategy_id, name, type, params, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (strategy_id, name, strategy_type, json.dumps(params), status, datetime.now().isoformat()))
            conn.commit()
            return cursor.rowcount > 0

    def get_strategy(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """获取策略配置"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM strategies WHERE strategy_id = ?", (strategy_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'strategy_id': row['strategy_id'],
                    'name': row['name'],
                    'type': row['type'],
                    'params': json.loads(row['params']),
                    'status': row['status'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            return None

    def list_strategies(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出所有策略"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM strategies"
            params: List[Any] = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            
            strategies = []
            for row in cursor.fetchall():
                strategies.append({
                    'strategy_id': row['strategy_id'],
                    'name': row['name'],
                    'type': row['type'],
                    'params': json.loads(row['params']),
                    'status': row['status'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            return strategies

    def update_strategy_status(self, strategy_id: str, status: str) -> bool:
        """更新策略状态"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE strategies 
                SET status = ?, updated_at = ?
                WHERE strategy_id = ?
            """, (status, datetime.now().isoformat(), strategy_id))
            conn.commit()
            return cursor.rowcount > 0

    # ==================== 回测操作 ====================

    def save_backtest(
        self,
        backtest_id: str,
        strategy_id: Optional[str],
        config: Dict[str, Any],
        metrics: Optional[Dict[str, Any]] = None,
        equity_curve: Optional[List[float]] = None,
        trades: Optional[List[Dict[str, Any]]] = None,
        status: str = "completed"
    ) -> bool:
        """保存回测结果"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO backtests 
                (backtest_id, strategy_id, config, metrics, equity_curve, trades, status, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                backtest_id,
                strategy_id,
                json.dumps(config),
                json.dumps(metrics) if metrics else None,
                json.dumps(equity_curve) if equity_curve else None,
                json.dumps(trades) if trades else None,
                status,
                datetime.now().isoformat()
            ))
            conn.commit()
            return cursor.rowcount > 0

    def get_backtest(self, backtest_id: str) -> Optional[Dict[str, Any]]:
        """获取回测结果"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM backtests WHERE backtest_id = ?", (backtest_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'backtest_id': row['backtest_id'],
                    'strategy_id': row['strategy_id'],
                    'config': json.loads(row['config']),
                    'metrics': json.loads(row['metrics']) if row['metrics'] else None,
                    'equity_curve': json.loads(row['equity_curve']) if row['equity_curve'] else None,
                    'trades': json.loads(row['trades']) if row['trades'] else None,
                    'status': row['status'],
                    'started_at': row['started_at'],
                    'completed_at': row['completed_at'],
                    'created_at': row['created_at']
                }
            return None

    def list_backtests(self, limit: int = 100) -> List[Dict[str, Any]]:
        """列出回测结果"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM backtests 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            backtests = []
            for row in cursor.fetchall():
                backtests.append({
                    'backtest_id': row['backtest_id'],
                    'strategy_id': row['strategy_id'],
                    'config': json.loads(row['config']),
                    'metrics': json.loads(row['metrics']) if row['metrics'] else None,
                    'status': row['status'],
                    'completed_at': row['completed_at'],
                    'created_at': row['created_at']
                })
            
            return backtests

    # ==================== 信号操作 ====================

    def save_signal(
        self,
        signal_id: str,
        signal_type: str,
        direction: str,
        symbol: str,
        confidence: float,
        reason: str,
        price: float,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """保存信号"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO signals 
                (signal_id, signal_type, direction, symbol, confidence, reason, price, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_id,
                signal_type,
                direction,
                symbol,
                confidence,
                reason,
                price,
                json.dumps(metadata) if metadata else None,
                (timestamp or datetime.now()).isoformat()
            ))
            conn.commit()
            return cursor.rowcount > 0

    def get_signals(
        self,
        symbol: Optional[str] = None,
        signal_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取信号历史"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM signals WHERE 1=1"
            params: List[Any] = []
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            
            if signal_type:
                query += " AND signal_type = ?"
                params.append(signal_type)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            signals = []
            for row in cursor.fetchall():
                signals.append({
                    'signal_id': row['signal_id'],
                    'signal_type': row['signal_type'],
                    'direction': row['direction'],
                    'symbol': row['symbol'],
                    'confidence': row['confidence'],
                    'reason': row['reason'],
                    'price': row['price'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else None,
                    'timestamp': row['timestamp'],
                    'created_at': row['created_at']
                })
            
            return signals

    # ==================== 系统配置 ====================

    def set_config(self, key: str, value: Any) -> bool:
        """设置系统配置"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO system_config (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, json.dumps(value), datetime.now().isoformat()))
            conn.commit()
            return cursor.rowcount > 0

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取系统配置"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM system_config WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return json.loads(row['value'])
            return default

    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有系统配置"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM system_config")
            
            configs = {}
            for row in cursor.fetchall():
                configs[row['key']] = json.loads(row['value'])
            
            return configs


def init_database(db_path: str = "data/nemt_storage.db") -> SQLiteStorage:
    """初始化数据库"""
    return SQLiteStorage(db_path)
