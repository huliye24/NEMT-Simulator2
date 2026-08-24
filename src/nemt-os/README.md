# NEMT Platform - NEMT 容器化策略运行平台

## 概述

NEMT 是一个高性能的容器化策略运行平台，提供完整的隔离、执行、监控和安全能力。

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

```python
from nemt import NEMTPlatform, CapsuleConfig, CapsuleState

# 创建平台
platform = NEMTPlatform().initialize()

# 创建胶囊
config = CapsuleConfig(name="my_strategy", memory_limit=256)
capsule = platform.capsule_manager.create(config)

# 启动胶囊
capsule.start()

# 运行策略
capsule.execute(strategy_code)

# 停止胶囊
capsule.stop()
```

## 核心模块

### 核心 (nemt.core)
- `Capsule` - 策略执行容器
- `EventBus` - 事件总线
- `DIContainer` - 依赖注入

### 隔离 (nemt.isolation)
- `Sandbox` - 沙箱隔离
- `StrategyIsolation` - 策略隔离
- `ResourceQuota` - 资源配额

### 弹性 (nemt.resilience)
- `CircuitBreaker` - 熔断器
- `RetryPolicy` - 重试策略
- `RateLimiter` - 限流器

### 监控 (nemt.monitoring)
- `MetricsCollector` - 指标收集
- `AlertManager` - 告警管理
- `HealthCheck` - 健康检查

### 配置 (nemt.config)
- `ConfigLoader` - 配置加载
- `FeatureFlag` - 特性开关

### 安全 (nemt.security)
- `SecretManager` - 密钥管理
- `AuditLogger` - 审计日志
- `PermissionManager` - 权限管理
- `TenantContext` - 多租户

### 网关 (nemt.gateway)
- `APIGateway` - API 网关
- `RequestValidator` - 请求验证
- `APIAnalytics` - API 分析

### 市场 (nemt.market)
- `StrategyMarket` - 策略市场

### 运维 (nemt.ops)
- `LogAggregator` - 日志聚合
- `TraceCollector` - 链路追踪
- `Profiler` - 性能分析
- `WorkflowEngine` - 工作流引擎

### 交易 (nemt.trading)
- `StrategySimulator` - 策略模拟
- `OrderExecutor` - 订单执行
- `RiskCalculator` - 风险计算

## 测试

```bash
# 运行验收测试
python -m tests.test_acceptance

# 运行集成测试
python -m tests.test_integration
```

## 版本

当前版本: 2.0.0
