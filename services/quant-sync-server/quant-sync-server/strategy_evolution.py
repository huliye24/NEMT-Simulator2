#!/usr/bin/env python3
"""
NEMT Strategy Evolution Service
==============================
策略演化历史服务

功能：
1. 记录策略生命周期事件
2. 查询演化历史
3. 生成时间线

使用方法:
    python strategy_evolution.py --port 8005

端口: 8005
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
import sqlite3

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(Name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# 事件类型
# ============================================================================

class EvolutionEventType(Enum):
    """演化事件类型"""
    CREATED = "created"       # 创建
    UPDATED = "updated"       # 更新
    SCORED = "scored"        # 评分
    EVICTED = "evicted"      # 淘汰
    ACTIVATED = "activated"   # 激活
    BACKTEST = "backtest"    # 回测
    PARAM_CHANGED = "param_changed"  # 参数变更


# ============================================================================
# 数据结构
# ============================================================================

@dataclass
class EvolutionEvent:
    """演化事件"""
    id: str
    strategy_id: str
    strategy_name: str
    event_type: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    old_score: Optional[float] = None
    new_score: Optional[float] = None
    old_weight: Optional[float] = None
    new_weight: Optional[float] = None
    metadata: Dict = field(default_factory=dict)
    timestamp: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EvolutionEvent":
        return cls(**data)


@dataclass
class StrategySnapshot:
    """策略快照"""
    strategy_id: str
    strategy_name: str
    status: str
    score: float
    capital_weight: float
    metrics: Dict
    timestamp: str


@dataclass
class EvolutionStats:
    """演化统计"""
    total_events: int
    events_by_type: Dict[str, int]
    events_by_strategy: Dict[str, int]
    avg_events_per_strategy: float
    period_start: str
    period_end: str


# ============================================================================
# 演化历史管理器
# ============================================================================

class EvolutionManager:
    """策略演化历史管理器"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化管理器
        
        Args:
            db_path: 数据库路径
        """
        if db_path is None:
            db_path = PROJECT_ROOT / 'quant-sync-server' / 'evolution.db'
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 演化事件表
        c.execute("""
            CREATE TABLE IF NOT EXISTS evolution_events (
                id TEXT PRIMARY KEY,
                strategy_id TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                old_status TEXT,
                new_status TEXT,
                old_score REAL,
                new_score REAL,
                old_weight REAL,
                new_weight REAL,
                metadata TEXT,
                timestamp TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_strategy_id 
            ON evolution_events(strategy_id)
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON evolution_events(timestamp)
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_event_type 
            ON evolution_events(event_type)
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"初始化演化历史数据库: {self.db_path}")
    
    def record_event(
        self,
        strategy_id: str,
        strategy_name: str,
        event_type: EvolutionEventType | str,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        old_score: Optional[float] = None,
        new_score: Optional[float] = None,
        old_weight: Optional[float] = None,
        new_weight: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> EvolutionEvent:
        """
        记录演化事件
        
        Args:
            strategy_id: 策略ID
            strategy_name: 策略名称
            event_type: 事件类型
            old_status: 原状态
            new_status: 新状态
            old_score: 原评分
            new_score: 新评分
            old_weight: 原权重
            new_weight: 新权重
            metadata: 额外数据
        
        Returns:
            EvolutionEvent: 创建的事件
        """
        import uuid
        
        event = EvolutionEvent(
            id=str(uuid.uuid4())[:12],
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            event_type=event_type.value if isinstance(event_type, EvolutionEventType) else event_type,
            old_status=old_status,
            new_status=new_status,
            old_score=old_score,
            new_score=new_score,
            old_weight=old_weight,
            new_weight=new_weight,
            metadata=metadata or {},
            timestamp=datetime.now().isoformat()
        )
        
        # 保存到数据库
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO evolution_events 
            (id, strategy_id, strategy_name, event_type, old_status, new_status,
             old_score, new_score, old_weight, new_weight, metadata, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.id,
            event.strategy_id,
            event.strategy_name,
            event.event_type,
            event.old_status,
            event.new_status,
            event.old_score,
            event.new_score,
            event.old_weight,
            event.new_weight,
            json.dumps(event.metadata),
            event.timestamp
        ))
        conn.commit()
        conn.close()
        
        logger.info(f"记录演化事件: {event.event_type} - {event.strategy_name}")
        
        return event
    
    def get_history(
        self,
        strategy_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[EvolutionEvent]:
        """
        获取演化历史
        
        Args:
            strategy_id: 策略ID过滤
            event_type: 事件类型过滤
            limit: 返回数量限制
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            List[EvolutionEvent]: 事件列表
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 构建查询
        conditions = []
        params = []
        
        if strategy_id:
            conditions.append("strategy_id = ?")
            params.append(strategy_id)
        
        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        
        if start_date:
            conditions.append("timestamp >= ?")
            params.append(start_date)
        
        if end_date:
            conditions.append("timestamp <= ?")
            params.append(end_date)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        c.execute(f"""
            SELECT * FROM evolution_events
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        """, (*params, limit))
        
        rows = c.fetchall()
        conn.close()
        
        events = []
        for row in rows:
            events.append(EvolutionEvent(
                id=row[0],
                strategy_id=row[1],
                strategy_name=row[2],
                event_type=row[3],
                old_status=row[4],
                new_status=row[5],
                old_score=row[6],
                new_score=row[7],
                old_weight=row[8],
                new_weight=row[9],
                metadata=json.loads(row[10]) if row[10] else {},
                timestamp=row[11]
            ))
        
        return events
    
    def get_strategy_timeline(self, strategy_id: str) -> List[EvolutionEvent]:
        """
        获取策略的时间线
        
        Args:
            strategy_id: 策略ID
        
        Returns:
            List[EvolutionEvent]: 按时间排序的事件列表
        """
        return self.get_history(strategy_id=strategy_id, limit=1000)
    
    def get_stats(
        self,
        days: int = 30,
        strategy_id: Optional[str] = None
    ) -> EvolutionStats:
        """
        获取演化统计
        
        Args:
            days: 统计天数
            strategy_id: 策略ID过滤
        
        Returns:
            EvolutionStats: 统计信息
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 时间范围
        end_date = datetime.now().isoformat()
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # 基础条件
        conditions = ["timestamp >= ?"]
        params = [start_date]
        
        if strategy_id:
            conditions.append("strategy_id = ?")
            params.append(strategy_id)
        
        where_clause = " AND ".join(conditions)
        
        # 总事件数
        c.execute(f"""
            SELECT COUNT(*) FROM evolution_events
            WHERE {where_clause}
        """, params)
        total_events = c.fetchone()[0]
        
        # 按类型统计
        c.execute(f"""
            SELECT event_type, COUNT(*) 
            FROM evolution_events
            WHERE {where_clause}
            GROUP BY event_type
        """, params)
        events_by_type = dict(c.fetchall())
        
        # 按策略统计
        c.execute(f"""
            SELECT strategy_id, COUNT(*) 
            FROM evolution_events
            WHERE {where_clause}
            GROUP BY strategy_id
        """, params)
        events_by_strategy = dict(c.fetchall())
        
        conn.close()
        
        # 计算平均
        unique_strategies = len(events_by_strategy)
        avg_per_strategy = total_events / unique_strategies if unique_strategies > 0 else 0
        
        return EvolutionStats(
            total_events=total_events,
            events_by_type=events_by_type,
            events_by_strategy=events_by_strategy,
            avg_events_per_strategy=avg_per_strategy,
            period_start=start_date,
            period_end=end_date
        )
    
    def get_recent_alerts(
        self,
        hours: int = 24,
        alert_types: Optional[List[str]] = None
    ) -> List[EvolutionEvent]:
        """
        获取最近的警告事件
        
        Args:
            hours: 过去几小时
            alert_types: 警告类型列表
        
        Returns:
            List[EvolutionEvent]: 警告事件列表
        """
        if alert_types is None:
            alert_types = [EvolutionEventType.EVICTED.value, "dormant", "dead"]
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        start_date = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        placeholders = ",".join(["?" for _ in alert_types])
        c.execute(f"""
            SELECT * FROM evolution_events
            WHERE timestamp >= ? AND event_type IN ({placeholders})
            ORDER BY timestamp DESC
        """, (start_date, *alert_types))
        
        rows = c.fetchall()
        conn.close()
        
        events = []
        for row in rows:
            events.append(EvolutionEvent(
                id=row[0],
                strategy_id=row[1],
                strategy_name=row[2],
                event_type=row[3],
                old_status=row[4],
                new_status=row[5],
                old_score=row[6],
                new_score=row[7],
                old_weight=row[8],
                new_weight=row[9],
                metadata=json.loads(row[10]) if row[10] else {},
                timestamp=row[11]
            ))
        
        return events
    
    def delete_old_events(self, days: int = 90) -> int:
        """
        删除旧事件
        
        Args:
            days: 保留多少天的数据
        
        Returns:
            int: 删除的事件数量
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        c.execute("""
            DELETE FROM evolution_events
            WHERE timestamp < ?
        """, (cutoff_date,))
        
        deleted = c.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"删除 {deleted} 条旧事件")
        
        return deleted


# ============================================================================
# Flask API
# ============================================================================

def create_app(manager: EvolutionManager):
    """创建 Flask 应用"""
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    
    @app.route('/api/evolution', methods=['GET'])
    def get_history():
        """获取演化历史"""
        try:
            strategy_id = request.args.get('strategy_id')
            event_type = request.args.get('event_type')
            limit = int(request.args.get('limit', 100))
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            events = manager.get_history(
                strategy_id=strategy_id,
                event_type=event_type,
                limit=limit,
                start_date=start_date,
                end_date=end_date
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'events': [e.to_dict() for e in events],
                    'count': len(events)
                }
            })
        except Exception as e:
            logger.error(f"获取演化历史失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/evolution/timeline/<strategy_id>', methods=['GET'])
    def get_timeline(strategy_id):
        """获取策略时间线"""
        try:
            events = manager.get_strategy_timeline(strategy_id)
            return jsonify({
                'success': True,
                'data': {
                    'strategy_id': strategy_id,
                    'events': [e.to_dict() for e in events],
                    'count': len(events)
                }
            })
        except Exception as e:
            logger.error(f"获取时间线失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/evolution/stats', methods=['GET'])
    def get_stats():
        """获取统计信息"""
        try:
            days = int(request.args.get('days', 30))
            strategy_id = request.args.get('strategy_id')
            
            stats = manager.get_stats(days=days, strategy_id=strategy_id)
            
            return jsonify({
                'success': True,
                'data': asdict(stats)
            })
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/evolution/alerts', methods=['GET'])
    def get_alerts():
        """获取警告"""
        try:
            hours = int(request.args.get('hours', 24))
            
            events = manager.get_recent_alerts(hours=hours)
            
            return jsonify({
                'success': True,
                'data': {
                    'events': [e.to_dict() for e in events],
                    'count': len(events)
                }
            })
        except Exception as e:
            logger.error(f"获取警告失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/evolution/record', methods=['POST'])
    def record_event():
        """记录事件"""
        try:
            data = request.get_json()
            
            event = manager.record_event(
                strategy_id=data['strategy_id'],
                strategy_name=data['strategy_name'],
                event_type=data['event_type'],
                old_status=data.get('old_status'),
                new_status=data.get('new_status'),
                old_score=data.get('old_score'),
                new_score=data.get('new_score'),
                old_weight=data.get('old_weight'),
                new_weight=data.get('new_weight'),
                metadata=data.get('metadata')
            )
            
            return jsonify({
                'success': True,
                'data': event.to_dict()
            })
        except Exception as e:
            logger.error(f"记录事件失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/health', methods=['GET'])
    def health():
        """健康检查"""
        return jsonify({'status': 'ok'})
    
    return app


# ============================================================================
# 主函数
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='NEMT Strategy Evolution Service')
    parser.add_argument('--port', type=int, default=8005, help='端口号')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='主机地址')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    parser.add_argument('--db', type=str, help='数据库路径')
    
    args = parser.parse_args()
    
    # 创建管理器
    manager = EvolutionManager(db_path=args.db)
    
    # 创建并运行应用
    app = create_app(manager)
    
    logger.info(f"启动演化历史服务: {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)
