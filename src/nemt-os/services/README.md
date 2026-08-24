# NEMT Platform - 服务层架构
#
# 微服务边界定义
#
# 服务间通信：
#   - gRPC: 同步调用
#   - Redis Pub/Sub: 事件流
#   - HTTP/REST: API 网关

```
┌─────────────────────────────────────────────────────────────────────┐
│                           API Gateway                                │
│                        (Nginx + REST)                               │
└─────────────────────────────────────────────────────────────────────┘
                    │           │           │           │
        ┌───────────┴───┐ ┌───┴───────┐ ┌─┴───────┐ ┌─┴────────┐
        │               │ │           │ │         │ │          │
┌───────▼───────┐ ┌─────▼──────┐ ┌───▼────┐ ┌──▼───┐ ┌──▼──────┐
│ Market Service │ │Signal Svc │ │Risk Svc│ │Exec  │ │Brain    │
│    (8001)     │ │  (8002)   │ │(8003)  │ │(8004)│ │ Service │
│               │ │           │ │        │ │      │ │(8005)   │
│ • K线数据     │ │ • DCI     │ │ • 仓位 │ │ • 订单│ │ • 决策  │
│ • 实时价格   │ │ • Vortex  │ │ • 止损 │ │ • 持仓│ │ • 学习  │
│ • 深度数据   │ │ • 共振    │ │ • 回撤 │ │ • 成交│ │ • 演化  │
└───────────────┘ └───────────┘ └────────┘ └──────┘ └──────────┘
        │               │           │           │
        └───────────────┴─────┬─────┴───────────┘
                              │
                    ┌────────▼────────┐
                    │   Event Bus      │
                    │ (Redis Pub/Sub) │
                    └─────────────────┘
```

## 服务边界

### Market Service (8001)
```
服务职责：
- 订阅交易所 WebSocket 数据
- K线数据聚合
- 价格/成交量缓存
- 技术指标预计算

订阅事件：
- (无上游依赖)

发布事件：
- market.bar: K线更新
- market.price: 价格更新
- market.candle_closed: 蜡烛图完成
```

### Signal Service (8002)
```
服务职责：
- DCI 指标计算
- Vortex 指标计算
- 共振检测
- 信号生成

订阅事件：
- market.bar: K线数据

发布事件：
- signal.generated: 新信号
- signal.confidence_update: 置信度变化
```

### Risk Service (8003)
```
服务职责：
- 仓位管理
- 止损/止盈检查
- 回撤控制
- 风险评分

订阅事件：
- signal.generated: 新信号

发布事件：
- risk.approved: 风控通过
- risk.rejected: 风控拒绝
- risk.alert: 风控警告
```

### Execution Service (8004)
```
服务职责：
- 订单执行
- 持仓跟踪
- 成交回报处理

订阅事件：
- risk.approved: 风控通过
- risk.rejected: 风控拒绝

发布事件：
- execution.order_sent: 订单发送
- execution.filled: 订单成交
- execution.position_update: 持仓更新
```

### Brain Service (8005)
```
服务职责：
- 决策协调
- 自我演化
- 策略选择

订阅事件：
- execution.position_update: 持仓变化
- risk.alert: 风控警告

发布事件：
- brain.decision: 决策信号
- brain.evolution: 演化事件
```

## 服务发现

每个服务启动时向 Redis 注册：
```python
{
    "service": "market",
    "host": "market-service",
    "port": 8001,
    "status": "healthy",
    "timestamp": "2026-04-28T12:00:00Z"
}
```

## 健康检查

每个服务暴露 `/health` 端点：
- 200 OK: 健康
- 503 Service Unavailable: 不健康
