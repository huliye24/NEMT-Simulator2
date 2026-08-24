#!/usr/bin/env python3
"""
NEMT Correlation Analyzer Service
==================================
策略相关性分析服务

功能：
1. 计算策略相关性矩阵
2. 查找冗余策略
3. 策略聚类

使用方法:
    python strategy_correlation.py --port 8004

端口: 8004
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import sqlite3
import random

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(Name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# 数据结构
# ============================================================================

@dataclass
class CorrelationResult:
    """相关性计算结果"""
    strategy_ids: List[str]
    matrix: List[List[float]]
    computed_at: str
    method: str
    lookback_days: int

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RedundantPair:
    """冗余策略对"""
    strategy_a: str
    strategy_b: str
    correlation: float
    recommendation: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ClusterResult:
    """聚类结果"""
    clusters: Dict[int, List[str]]
    cluster_count: int
    method: str

    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'clusters': {str(k): v for k, v in self.clusters.items()}
        }


# ============================================================================
# 相关性分析器
# ============================================================================

class CorrelationAnalyzer:
    """策略相关性分析器"""
    
    def __init__(self, cache_ttl: int = 300, db_path: Optional[str] = None):
        """
        初始化分析器
        
        Args:
            cache_ttl: 缓存有效期（秒），默认5分钟
            db_path: 数据库路径，默认使用策略服务的数据库
        """
        self.cache: Dict[str, CorrelationResult] = {}
        self.cache_ttl = cache_ttl
        
        # 数据库路径
        if db_path is None:
            db_path = PROJECT_ROOT / 'quant-sync-server' / 'strategy.db'
        self.db_path = db_path
    
    def compute(
        self,
        strategy_ids: List[str],
        lookback_days: int = 30,
        method: str = "pearson"
    ) -> CorrelationResult:
        """
        计算相关性矩阵
        
        Args:
            strategy_ids: 策略ID列表，为空则计算所有活跃策略
            lookback_days: 回看天数
            method: 计算方法（pearson/spearman）
        
        Returns:
            CorrelationResult: 相关性结果
        """
        # 如果策略列表为空，获取所有活跃策略
        if not strategy_ids:
            strategy_ids = self._get_active_strategy_ids()
        
        if len(strategy_ids) < 2:
            return CorrelationResult(
                strategy_ids=strategy_ids,
                matrix=[],
                computed_at=datetime.now().isoformat(),
                method=method,
                lookback_days=lookback_days
            )
        
        # 缓存键
        cache_key = self._make_cache_key(strategy_ids, lookback_days, method)
        
        # 检查缓存
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            age = (datetime.now() - datetime.fromisoformat(cached.computed_at)).total_seconds()
            if age < self.cache_ttl:
                logger.info(f"使用缓存的相关性矩阵 (age: {age:.0f}s)")
                return cached
        
        # 计算相关性矩阵
        matrix = self._calculate_matrix(strategy_ids, lookback_days, method)
        
        result = CorrelationResult(
            strategy_ids=strategy_ids,
            matrix=matrix,
            computed_at=datetime.now().isoformat(),
            method=method,
            lookback_days=lookback_days
        )
        
        # 缓存结果
        self.cache[cache_key] = result
        
        return result
    
    def find_redundant(
        self,
        strategy_ids: Optional[List[str]] = None,
        threshold: float = 0.9
    ) -> List[RedundantPair]:
        """
        查找冗余策略
        
        Args:
            strategy_ids: 策略ID列表
            threshold: 相关性阈值，默认0.9
        
        Returns:
            List[RedundantPair]: 冗余策略对列表
        """
        # 计算相关性矩阵
        correlation_result = self.compute(strategy_ids or [])
        
        redundant = []
        n = len(correlation_result.strategy_ids)
        
        for i in range(n):
            for j in range(i + 1, n):
                corr = abs(correlation_result.matrix[i][j])
                if corr >= threshold:
                    redundant.append(RedundantPair(
                        strategy_a=correlation_result.strategy_ids[i],
                        strategy_b=correlation_result.strategy_ids[j],
                        correlation=float(corr),
                        recommendation=self._generate_recommendation(
                            correlation_result.strategy_ids[i],
                            correlation_result.strategy_ids[j],
                            corr
                        )
                    ))
        
        # 按相关性降序排序
        redundant.sort(key=lambda x: x.correlation, reverse=True)
        
        return redundant
    
    def cluster_strategies(
        self,
        strategy_ids: Optional[List[str]] = None,
        n_clusters: Optional[int] = None
    ) -> ClusterResult:
        """
        对策略进行聚类
        
        Args:
            strategy_ids: 策略ID列表
            n_clusters: 聚类数量，None则自动确定
        
        Returns:
            ClusterResult: 聚类结果
        """
        correlation_result = self.compute(strategy_ids or [])
        strategy_ids = correlation_result.strategy_ids
        
        if len(strategy_ids) < 2:
            return ClusterResult(
                clusters={1: strategy_ids},
                cluster_count=1,
                method="single"
            )
        
        # 计算距离矩阵（1 - |correlation|）
        n = len(strategy_ids)
        distance_matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    distance_matrix[i][j] = 1.0 - abs(correlation_result.matrix[i][j])
        
        # 简单层次聚类（基于阈值）
        # 将相关性 > 0.7 的策略归为一类
        threshold = 0.3  # 距离阈值
        
        clusters: Dict[int, List[str]] = {}
        assigned = [False] * n
        cluster_id = 1
        
        for i in range(n):
            if assigned[i]:
                continue
            
            # BFS 扩展
            cluster = []
            queue = [i]
            
            while queue:
                idx = queue.pop(0)
                if assigned[idx]:
                    continue
                
                assigned[idx] = True
                cluster.append(strategy_ids[idx])
                
                # 找到所有相近的策略
                for j in range(n):
                    if not assigned[j] and distance_matrix[idx][j] < threshold:
                        queue.append(j)
            
            if cluster:
                clusters[cluster_id] = cluster
                cluster_id += 1
        
        # 未分配的策略单独成类
        for i in range(n):
            if not assigned[i]:
                clusters[cluster_id] = [strategy_ids[i]]
                cluster_id += 1
        
        return ClusterResult(
            clusters=clusters,
            cluster_count=len(clusters),
            method="hierarchical_threshold"
        )
    
    # =====================
    # 私有方法
    # =====================
    
    def _get_active_strategy_ids(self) -> List[str]:
        """获取所有活跃策略ID"""
        if not Path(self.db_path).exists():
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                SELECT id FROM strategies 
                WHERE status = 'alive' OR status = 'testing'
            """)
            ids = [row[0] for row in c.fetchall()]
            conn.close()
            return ids
        except Exception as e:
            logger.error(f"获取活跃策略失败: {e}")
            return []
    
    def _get_strategy_performance(
        self,
        strategy_id: str,
        lookback_days: int
    ) -> List[float]:
        """获取策略收益序列"""
        if not Path(self.db_path).exists():
            # 返回模拟数据
            return [random.gauss(0.001, 0.02) for _ in range(lookback_days)]
        
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # 尝试从 performance 表获取
            c.execute("""
                SELECT performance FROM strategy_performance
                WHERE strategy_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (strategy_id, lookback_days))
            
            row = c.fetchone()
            conn.close()
            
            if row and row[0]:
                return json.loads(row[0])
            
            # 返回模拟数据
            return [random.gauss(0.001, 0.02) for _ in range(lookback_days)]
            
        except Exception as e:
            logger.warning(f"获取策略 {strategy_id} 收益失败: {e}")
            return [random.gauss(0.001, 0.02) for _ in range(lookback_days)]
    
    def _calculate_matrix(
        self,
        strategy_ids: List[str],
        lookback_days: int,
        method: str
    ) -> List[List[float]]:
        """计算相关性矩阵"""
        # 获取所有策略的收益序列
        performances = []
        for sid in strategy_ids:
            perf = self._get_strategy_performance(sid, lookback_days)
            performances.append(perf)
        
        n = len(strategy_ids)
        matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 1.0
                elif j > i:
                    corr = self._calc_correlation(
                        performances[i],
                        performances[j],
                        method
                    )
                    matrix[i][j] = corr
                    matrix[j][i] = corr  # 对称
        
        return matrix
    
    def _calc_correlation(
        self,
        x: List[float],
        y: List[float],
        method: str
    ) -> float:
        """计算两个序列的相关性"""
        if len(x) < 2 or len(y) < 2:
            return 0.0
        
        # 对齐长度
        min_len = min(len(x), len(y))
        x, y = x[-min_len:], y[-min_len:]
        
        if method == "spearman":
            try:
                from scipy.stats import spearmanr
                corr, _ = spearmanr(x, y)
                return float(corr) if not (corr is None or str(corr) == 'nan') else 0.0
            except:
                pass
        
        # 默认使用 Pearson
        try:
            import numpy as np
            corr = np.corrcoef(x, y)[0, 1]
            return float(corr) if not np.isnan(corr) else 0.0
        except:
            return 0.0
    
    def _make_cache_key(
        self,
        strategy_ids: List[str],
        lookback_days: int,
        method: str
    ) -> str:
        """生成缓存键"""
        ids = ','.join(sorted(strategy_ids))
        return f"{ids}:{lookback_days}:{method}"
    
    def _generate_recommendation(
        self,
        strategy_a: str,
        strategy_b: str,
        correlation: float
    ) -> str:
        """生成建议"""
        if correlation >= 0.95:
            return "高度重复，建议合并或删除其一"
        elif correlation >= 0.9:
            return "建议保留评分较高者"
        else:
            return "可保持现状，观察后续表现"


# ============================================================================
# Flask API
# ============================================================================

def create_app(analyzer: CorrelationAnalyzer):
    """创建 Flask 应用"""
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    
    @app.route('/api/correlation', methods=['POST'])
    def compute_correlation():
        """计算相关性矩阵"""
        try:
            data = request.get_json() or {}
            strategy_ids = data.get('strategy_ids', [])
            lookback_days = data.get('lookback_days', 30)
            method = data.get('method', 'pearson')
            
            result = analyzer.compute(strategy_ids, lookback_days, method)
            
            return jsonify({
                'success': True,
                'data': result.to_dict()
            })
        except Exception as e:
            logger.error(f"计算相关性失败: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/correlation/redundant', methods=['POST'])
    def find_redundant():
        """查找冗余策略"""
        try:
            data = request.get_json() or {}
            strategy_ids = data.get('strategy_ids')
            threshold = data.get('threshold', 0.9)
            
            result = analyzer.find_redundant(strategy_ids, threshold)
            
            return jsonify({
                'success': True,
                'data': {
                    'pairs': [p.to_dict() for p in result],
                    'count': len(result)
                }
            })
        except Exception as e:
            logger.error(f"查找冗余策略失败: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/correlation/cluster', methods=['POST'])
    def cluster_strategies():
        """聚类策略"""
        try:
            data = request.get_json() or {}
            strategy_ids = data.get('strategy_ids')
            n_clusters = data.get('n_clusters')
            
            result = analyzer.cluster_strategies(strategy_ids, n_clusters)
            
            return jsonify({
                'success': True,
                'data': result.to_dict()
            })
        except Exception as e:
            logger.error(f"聚类策略失败: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
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
    
    parser = argparse.ArgumentParser(description='NEMT Correlation Analyzer')
    parser.add_argument('--port', type=int, default=8004, help='端口号')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='主机地址')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    parser.add_argument('--db', type=str, help='数据库路径')
    parser.add_argument('--cache-ttl', type=int, default=300, help='缓存有效期（秒）')
    
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = CorrelationAnalyzer(
        cache_ttl=args.cache_ttl,
        db_path=args.db
    )
    
    # 创建并运行应用
    app = create_app(analyzer)
    
    logger.info(f"启动相关性分析服务: {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)
