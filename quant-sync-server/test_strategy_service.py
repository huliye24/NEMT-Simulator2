#!/usr/bin/env python3
"""
测试策略服务
"""

import sys
sys.path.insert(0, '.')

from strategy_service import create_service, StrategyStatus
import numpy as np

def main():
    print("=" * 60)
    print("NEMT 策略服务测试")
    print("=" * 60)
    
    # 创建服务
    service = create_service("test_strategy.db")
    
    # 1. 获取模板
    print("\n1. 获取策略模板:")
    templates = service.get_templates()
    for t in templates:
        print(f"   - {t['name']} ({t['type']})")
    
    # 2. 创建策略
    print("\n2. 创建策略:")
    strategies = []
    for i, tmpl in enumerate(templates[:3]):
        s = service.create_strategy(tmpl['id'], f"测试策略{i+1}")
        strategies.append(s)
        print(f"   - 创建: {s.name} ({s.id})")
    
    # 3. 列出策略
    print("\n3. 策略列表:")
    all_strategies = service.list_strategies()
    print(f"   共 {len(all_strategies)} 个策略")
    
    # 4. 生成模拟数据
    print("\n4. 生成模拟价格数据:")
    np.random.seed(42)
    prices = 67000 + np.cumsum(np.random.randn(500) * 100)
    print(f"   生成 {len(prices)} 个数据点")
    print(f"   价格范围: {prices.min():.2f} - {prices.max():.2f}")
    
    # 5. 运行回测
    print("\n5. 运行回测:")
    for s in strategies:
        result = service.run_backtest(s.id, list(prices))
        print(f"   - {s.name}: 收益 {result.return_pct:.2f}%, 夏普 {result.sharpe_ratio:.2f}, 胜率 {result.win_rate*100:.1f}%")
    
    # 6. 评分
    print("\n6. 策略评分:")
    scores = service.score_all()
    for score in scores:
        print(f"   - {score.strategy_id}: 总分 {score.total_score:.1f} ({score.reasoning})")
    
    # 7. 淘汰评估
    print("\n7. 淘汰评估:")
    events = service.evaluate_and_evict()
    for event in events:
        print(f"   - {event.strategy_name}: {event.action} (评分 {event.score_before:.1f} -> {event.score_after:.1f})")
    
    # 8. 重新分配权重
    print("\n8. 权重分配 (按评分):")
    weights = service.rebalance_weights("score")
    for sid, weight in weights.items():
        print(f"   - {sid}: {weight:.2f}%")
    
    # 9. 统计
    print("\n9. 策略统计:")
    stats = service.get_stats()
    print(f"   总数: {stats['total']}")
    print(f"   活跃: {stats['alive']}")
    print(f"   测试中: {stats['testing']}")
    print(f"   休眠: {stats['dormant']}")
    print(f"   淘汰: {stats['dead']}")
    print(f"   平均评分: {stats['avg_score']:.1f}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
