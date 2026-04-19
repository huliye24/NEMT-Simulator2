#!/usr/bin/env python3
"""
Strategy Router
==============
策略层 API 路由

端点:
GET  /api/strategy/list          - 策略列表
POST /api/strategy/create         - 创建策略
GET  /api/strategy/{id}          - 获取策略详情
PUT  /api/strategy/{id}          - 更新策略
DELETE /api/strategy/{id}        - 删除策略
POST /api/strategy/{id}/backtest - 运行回测
GET  /api/strategy/{id}/score    - 获取评分
POST /api/strategy/evict         - 触发淘汰评估
GET  /api/strategy/templates     - 获取模板列表
POST /api/strategy/rebalance     - 重新分配权重
GET  /api/strategy/stats         - 策略统计
GET  /api/strategy/events        - 淘汰事件
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import asdict

from strategy_service import (
    StrategyService, StrategyStatus, StrategyType,
    BacktestConfig, StrategyScore, EvictionEvent
)

logger = logging.getLogger(__name__)


# ============================================================================
# 响应构建
# ============================================================================

def success_response(data: Any = None, message: str = None) -> Dict:
    """成功响应"""
    return {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }

def error_response(message: str, code: int = 400) -> Dict:
    """错误响应"""
    return {
        "success": False,
        "error": message,
        "code": code,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# 路由处理
# ============================================================================

class StrategyRouter:
    """策略路由"""
    
    def __init__(self, service: StrategyService):
        self.service = service
    
    # ---- 策略管理 ----
    
    def list_strategies(self, status: str = None) -> Dict:
        """列出策略"""
        try:
            status_enum = StrategyStatus(status) if status else None
            strategies = self.service.list_strategies(status_enum)
            return success_response({
                "strategies": [s.to_dict() for s in strategies],
                "count": len(strategies)
            })
        except Exception as e:
            logger.error(f"列出策略失败: {e}")
            return error_response(str(e))
    
    def create_strategy(self, body: Dict) -> Dict:
        """创建策略"""
        try:
            template = body.get("template")
            name = body.get("name")
            params = body.get("params")
            
            if not template:
                return error_response("缺少 template 参数")
            
            strategy = self.service.create_strategy(template, name, params)
            return success_response(strategy.to_dict(), f"策略 {strategy.name} 创建成功")
        except ValueError as e:
            return error_response(str(e))
        except Exception as e:
            logger.error(f"创建策略失败: {e}")
            return error_response(str(e))
    
    def get_strategy(self, strategy_id: str) -> Dict:
        """获取策略详情"""
        try:
            strategy = self.service.get_strategy(strategy_id)
            if not strategy:
                return error_response(f"策略 {strategy_id} 不存在", 404)
            
            # 同时获取评分
            score = self.service.score_strategy(strategy_id)
            
            return success_response({
                "strategy": strategy.to_dict(),
                "score": score.to_dict() if score else None
            })
        except Exception as e:
            logger.error(f"获取策略失败: {e}")
            return error_response(str(e))
    
    def update_strategy(self, strategy_id: str, body: Dict) -> Dict:
        """更新策略"""
        try:
            strategy = self.service.update_strategy(strategy_id, body)
            if not strategy:
                return error_response(f"策略 {strategy_id} 不存在", 404)
            
            return success_response(strategy.to_dict(), "策略更新成功")
        except Exception as e:
            logger.error(f"更新策略失败: {e}")
            return error_response(str(e))
    
    def delete_strategy(self, strategy_id: str) -> Dict:
        """删除策略"""
        try:
            if self.service.delete_strategy(strategy_id):
                return success_response(None, "策略删除成功")
            return error_response(f"策略 {strategy_id} 不存在", 404)
        except Exception as e:
            logger.error(f"删除策略失败: {e}")
            return error_response(str(e))
    
    # ---- 回测 ----
    
    def run_backtest(self, strategy_id: str, body: Dict) -> Dict:
        """运行回测"""
        try:
            prices = body.get("prices", [])
            if not prices or len(prices) < 50:
                return error_response("需要至少50个价格数据点")
            
            # 构建回测配置
            config = BacktestConfig(
                strategy_id=strategy_id,
                symbol=body.get("symbol", "BTCUSDT"),
                start_date=body.get("start_date", ""),
                end_date=body.get("end_date", ""),
                initial_capital=body.get("initial_capital", 10000),
                slippage_bps=body.get("slippage_bps", 1.0),
                commission_bps=body.get("commission_bps", 5.0)
            )
            
            result = self.service.run_backtest(strategy_id, prices, config)
            if not result:
                return error_response(f"策略 {strategy_id} 不存在", 404)
            
            return success_response(result.to_dict(), "回测完成")
        except Exception as e:
            logger.error(f"回测失败: {e}")
            return error_response(str(e))
    
    # ---- 评分 ----
    
    def get_score(self, strategy_id: str) -> Dict:
        """获取策略评分"""
        try:
            score = self.service.score_strategy(strategy_id)
            if not score:
                return error_response(f"策略 {strategy_id} 不存在", 404)
            
            return success_response(score.to_dict())
        except Exception as e:
            logger.error(f"获取评分失败: {e}")
            return error_response(str(e))
    
    def get_all_scores(self) -> Dict:
        """获取所有策略评分"""
        try:
            scores = self.service.score_all()
            return success_response({
                "scores": [s.to_dict() for s in scores],
                "count": len(scores)
            })
        except Exception as e:
            logger.error(f"获取评分失败: {e}")
            return error_response(str(e))
    
    # ---- 淘汰 ----
    
    def evict(self, strategy_id: str = None) -> Dict:
        """触发淘汰评估"""
        try:
            events = self.service.evaluate_and_evict(strategy_id)
            return success_response({
                "events": [e.to_dict() for e in events],
                "count": len(events)
            }, f"评估了 {len(events)} 个策略")
        except Exception as e:
            logger.error(f"淘汰评估失败: {e}")
            return error_response(str(e))
    
    def get_events(self, limit: int = 10) -> Dict:
        """获取淘汰事件"""
        try:
            events = self.service.get_eviction_events(limit)
            return success_response({
                "events": events,
                "count": len(events)
            })
        except Exception as e:
            logger.error(f"获取事件失败: {e}")
            return error_response(str(e))
    
    # ---- 权重 ----
    
    def rebalance(self, body: Dict) -> Dict:
        """重新分配权重"""
        try:
            mode = body.get("mode", "equal")
            weights = self.service.rebalance_weights(mode)
            return success_response({
                "weights": weights,
                "mode": mode
            }, f"权重已按 {mode} 模式重新分配")
        except Exception as e:
            logger.error(f"权重分配失败: {e}")
            return error_response(str(e))
    
    # ---- 统计 ----
    
    def get_stats(self) -> Dict:
        """获取策略统计"""
        try:
            stats = self.service.get_stats()
            return success_response(stats)
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return error_response(str(e))
    
    # ---- 模板 ----
    
    def get_templates(self) -> Dict:
        """获取策略模板"""
        try:
            templates = self.service.get_templates()
            return success_response({
                "templates": templates,
                "count": len(templates)
            })
        except Exception as e:
            logger.error(f"获取模板失败: {e}")
            return error_response(str(e))
    
    # ---- 批量操作 ----
    
    def batch_backtest(self, body: Dict) -> Dict:
        """批量回测"""
        try:
            strategy_ids = body.get("strategy_ids", [])
            prices = body.get("prices", [])
            
            if not prices or len(prices) < 50:
                return error_response("需要至少50个价格数据点")
            
            results = {}
            for sid in strategy_ids:
                result = self.service.run_backtest(sid, prices)
                if result:
                    results[sid] = result.to_dict()
            
            return success_response({
                "results": results,
                "count": len(results)
            }, f"完成 {len(results)} 个策略的回测")
        except Exception as e:
            logger.error(f"批量回测失败: {e}")
            return error_response(str(e))
    
    def create_batch(self, body: Dict) -> Dict:
        """批量创建策略"""
        try:
            strategies_data = body.get("strategies", [])
            
            results = []
            for data in strategies_data:
                template = data.get("template")
                name = data.get("name")
                params = data.get("params")
                
                if template:
                    s = self.service.create_strategy(template, name, params)
                    results.append(s.to_dict())
            
            return success_response({
                "strategies": results,
                "count": len(results)
            }, f"创建了 {len(results)} 个策略")
        except Exception as e:
            logger.error(f"批量创建失败: {e}")
            return error_response(str(e))
