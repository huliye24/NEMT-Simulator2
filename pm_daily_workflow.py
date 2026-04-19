#!/usr/bin/env python3
"""
PM Agent - 每日工作流
=====================

PM Agent 每日自动化任务：
1. 拉取最新结果指标
2. 与昨日对比
3. 检查告警阈值
4. 更新每日日志

使用方法:
    python pm_daily_workflow.py
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# 尝试导入策略服务
try:
    from quant_sync_server.strategy_service import create_service, StrategyStatus
    STRATEGY_SERVICE_AVAILABLE = True
except ImportError:
    STRATEGY_SERVICE_AVAILABLE = False


class PMDailyWorkflow:
    """PM每日工作流"""
    
    def __init__(self, results_dir: str = None):
        self.results_dir = results_dir or str(PROJECT_ROOT / "results" / "docs")
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.log_file = Path(self.results_dir) / f"Daily_Results_Log_{self.date}.md"
        
    def run(self):
        """执行每日工作流"""
        print("=" * 60)
        print(f"PM Agent 每日工作流 - {self.date}")
        print("=" * 60)
        
        # 1. 检查策略服务
        print("\n1. 检查策略服务...")
        strategy_info = self.check_strategy_service()
        
        # 2. 收集指标
        print("\n2. 收集系统指标...")
        metrics = self.collect_metrics(strategy_info)
        
        # 3. 检查告警
        print("\n3. 检查告警阈值...")
        alerts = self.check_alerts(metrics)
        
        # 4. 生成日志
        print("\n4. 生成每日日志...")
        self.generate_daily_log(metrics, alerts)
        
        print("\n" + "=" * 60)
        print("每日工作流完成!")
        print("=" * 60)
        
        return {
            "date": self.date,
            "metrics": metrics,
            "alerts": alerts,
            "log_file": str(self.log_file)
        }
    
    def check_strategy_service(self) -> Dict:
        """检查策略服务状态"""
        if not STRATEGY_SERVICE_AVAILABLE:
            return {
                "available": False,
                "message": "策略服务不可用"
            }
        
        try:
            service = create_service()
            stats = service.get_stats()
            return {
                "available": True,
                "stats": stats,
                "strategies": service.list_strategies()
            }
        except Exception as e:
            return {
                "available": False,
                "message": str(e)
            }
    
    def collect_metrics(self, strategy_info: Dict) -> Dict:
        """收集系统指标"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "total_strategies": 0,
                "alive": 0,
                "testing": 0,
                "dormant": 0,
                "dead": 0,
                "avg_score": 0
            },
            "performance": {
                "total_pnl": 0,
                "best_sharpe": 0,
                "best_win_rate": 0,
                "worst_drawdown": 0
            }
        }
        
        if strategy_info.get("available"):
            stats = strategy_info.get("stats", {})
            metrics["system"]["total_strategies"] = stats.get("total", 0)
            metrics["system"]["alive"] = stats.get("alive", 0)
            metrics["system"]["testing"] = stats.get("testing", 0)
            metrics["system"]["dormant"] = stats.get("dormant", 0)
            metrics["system"]["dead"] = stats.get("dead", 0)
            metrics["system"]["avg_score"] = stats.get("avg_score", 0)
            
            # 收集策略表现
            for s in strategy_info.get("strategies", []):
                pnl = s.metrics.total_pnl
                sharpe = s.metrics.sharpe_ratio
                win_rate = s.metrics.win_rate
                drawdown = s.metrics.max_drawdown
                
                metrics["performance"]["total_pnl"] += pnl
                if sharpe > metrics["performance"]["best_sharpe"]:
                    metrics["performance"]["best_sharpe"] = sharpe
                if win_rate > metrics["performance"]["best_win_rate"]:
                    metrics["performance"]["best_win_rate"] = win_rate
                if drawdown > metrics["performance"]["worst_drawdown"]:
                    metrics["performance"]["worst_drawdown"] = drawdown
        
        return metrics
    
    def check_alerts(self, metrics: Dict) -> List[Dict]:
        """检查告警"""
        alerts = []
        
        # 检查回撤
        worst_drawdown = metrics["performance"]["worst_drawdown"]
        if worst_drawdown > 15:
            alerts.append({
                "level": "CRITICAL",
                "type": "drawdown",
                "message": f"最大回撤超限: {worst_drawdown:.1f}%",
                "value": worst_drawdown,
                "threshold": 15
            })
        elif worst_drawdown > 10:
            alerts.append({
                "level": "WARNING",
                "type": "drawdown",
                "message": f"回撤偏高: {worst_drawdown:.1f}%",
                "value": worst_drawdown,
                "threshold": 10
            })
        
        # 检查策略数量
        total = metrics["system"]["total_strategies"]
        if total == 0:
            alerts.append({
                "level": "NOTICE",
                "type": "strategy_pool",
                "message": "策略池为空，请添加策略",
                "value": total
            })
        
        return alerts
    
    def generate_daily_log(self, metrics: Dict, alerts: List[Dict]):
        """生成每日日志"""
        # 策略服务状态
        service_status = "✅ 可用" if metrics else "❌ 不可用"
        
        # 指标表格
        metrics_table = self._format_metrics_table(metrics)
        
        # 告警列表
        alerts_list = self._format_alerts(alerts)
        
        content = f"""# 每日结果日志 (Daily_Results_Log_{self.date})

> 日期: {self.date}
> 生成时间: {datetime.now().strftime("%H:%M:%S")}

## 一、系统状态

| 项目 | 状态 |
|------|------|
| 策略服务 | {service_status} |
| 策略总数 | {metrics['system']['total_strategies']} |
| 活跃策略 | {metrics['system']['alive']} |
| 测试中 | {metrics['system']['testing']} |
| 休眠 | {metrics['system']['dormant']} |
| 淘汰 | {metrics['system']['dead']} |
| 平均评分 | {metrics['system']['avg_score']:.1f} |

## 二、核心指标

{metrics_table}

## 三、告警

{alerts_list}

## 四、待办事项

- [ ] 任务1: 待添加

---

*本日志每日自动生成*
"""
        
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"日志已保存: {self.log_file}")
    
    def _format_metrics_table(self, metrics: Dict) -> str:
        """格式化指标表格"""
        rows = [
            "| 指标 | 值 | 状态 |",
            "|------|-----|------|",
            f"| 总盈亏 | ${metrics['performance']['total_pnl']:.2f} | ⏳ |",
            f"| 最佳夏普 | {metrics['performance']['best_sharpe']:.2f} | ⏳ |",
            f"| 最佳胜率 | {metrics['performance']['best_win_rate']*100:.1f}% | ⏳ |",
            f"| 最大回撤 | {metrics['performance']['worst_drawdown']:.1f}% | ⏳ |",
        ]
        return "\n".join(rows)
    
    def _format_alerts(self, alerts: List[Dict]) -> str:
        """格式化告警"""
        if not alerts:
            return "| 级别 | 内容 | 值 | 阈值 |\n|------|------|-----|------|\n| - | 无告警 | - | - |"
        
        rows = ["| 级别 | 内容 | 值 | 阈值 |", "|------|------|-----|------|"]
        for a in alerts:
            rows.append(f"| {a['level']} | {a['message']} | {a.get('value', '-')} | {a.get('threshold', '-')} |")
        return "\n".join(rows)


def main():
    """主函数"""
    workflow = PMDailyWorkflow()
    result = workflow.run()
    
    print(f"\n📊 结果摘要:")
    print(f"   日期: {result['date']}")
    print(f"   策略数: {result['metrics']['system']['total_strategies']}")
    print(f"   告警数: {len(result['alerts'])}")
    print(f"   日志: {result['log_file']}")


if __name__ == "__main__":
    main()
