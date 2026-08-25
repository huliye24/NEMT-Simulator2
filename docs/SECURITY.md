# NEMT Execution Layer 安全指南

## 概述

本文档描述 NEMT Web Alpha 008 Execution Layer 的安全模型和最佳实践。

**核心原则**: 默认安全，渐进授权

---

## API Key 安全

### 权限原则

**允许权限**:
- ✅ Read Data (读取市场数据)
- ✅ Trading (下单交易)

**禁止权限**:
- ❌ Withdraw (提现)
- ❌ Transfer (转账)
- ❌ Sub-account management (子账户管理)

### Key 隔离

| 环境 | 用途 | 权限 |
|------|------|------|
| Production Key | 实盘交易 | Read + Trade |
| Simulation Key | 模拟交易 | Read only |
| Testnet Key | 测试环境 | Read + Trade (测试网) |

### 存储安全

- API Key **禁止**明文存储在代码中
- 使用环境变量或密钥管理服务
- Web Frontend **绝不**直接访问 API Key
- 所有交易所通信通过 Backend 代理

---

## 风险限制

### 默认配置

```python
RiskConfig(
    max_position_size=10000.0,    # 最大单笔仓位 $10,000
    max_position_ratio=0.3,      # 最大仓位比例 30%
    daily_loss_limit=500.0,        # 日亏损限制 $500
    max_leverage=3.0,              # 最大杠杆 3x
    emergency_stop=False,          # 紧急停止开关
)
```

### 风险检查流程

所有订单必须通过 Risk Gate:

1. **紧急停止检查** - 是否触发全局停止
2. **交易对检查** - 是否在允许列表
3. **仓位大小检查** - 是否超过最大仓位
4. **仓位比例检查** - 是否超过账户比例
5. **日亏损检查** - 是否超过日亏损限制

### 紧急停止

```python
# 激活紧急停止
POST /execution/emergency-stop?enable=true

# 效果:
# - 立即停止所有新订单
# - 可选: 取消所有未成交订单
# - 发送通知
```

---

## 执行模式

### 模式层级

```
观察模式 (Observation)
    ↓
模拟模式 (Paper Trading) ← 默认
    ↓
小额执行 (Small Live) ← 需要显式授权
    ↓
完整自动化 (Full Auto) ← 需要多重确认
```

### 模式切换

| 模式 | 条件 | 风险 |
|------|------|------|
| Observation | 只读，无订单 | 无 |
| Paper Trading | 模拟成交，记录日志 | 无 |
| Small Live | 单笔 < $100，日累计 < $500 | 低 |
| Full Auto | 解除所有限制 | 高 |

---

## 订单生命周期

### 记录要求

每个订单必须记录:

```python
{
    "signal": "BUY",           # 原始信号
    "reason": "DCI 72.5, Phase MARKUP",  # 决策原因
    "time": "2026-08-25T10:00:00Z",  # 时间戳
    "risk_checks": [...],       # 风险检查结果
    "result": "FILLED",         # 执行结果
}
```

### 审计追踪

- 所有订单持久化存储
- 支持按时间/交易对/信号查询
- 定期生成执行报告

---

## 安全最佳实践

### 开发阶段

1. **默认 Paper Trading** - 所有开发使用模拟模式
2. **代码审查** - 所有交易相关代码需双人审查
3. **测试覆盖** - 风险检查逻辑 100% 覆盖

### 部署阶段

1. **环境隔离** - 生产/测试完全隔离
2. **监控告警** - 异常交易行为实时告警
3. **备份恢复** - 订单数据定期备份

### 运行阶段

1. **实时监控** - 仓位/盈亏/订单状态监控
2. **定期审计** - 每周执行报告审查
3. **应急预案** - 紧急停止流程演练

---

## 合规要求

### 禁止行为

- 无风控自动交易
- API Key 明文存储
- 绕过 Risk Gate
- 未授权的大额交易

### 必须记录

- 所有订单请求
- 风险检查详情
- 决策原因
- 执行结果

---

## 紧急响应

### 触发条件

- 日亏损超过限制
- 异常交易频率
- 系统错误率升高
- 手动紧急停止

### 响应流程

1. **自动** - Risk Gate 激活紧急停止
2. **通知** - 发送告警通知
3. **审查** - 人工审查交易记录
4. **恢复** - 确认安全后解除停止

---

## 配置示例

### 环境变量

```bash
# API Keys (Backend only)
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here

# Risk Config
RISK_MAX_POSITION_SIZE=10000
RISK_DAILY_LOSS_LIMIT=500
RISK_EMERGENCY_STOP=false

# Trading Mode
TRADING_MODE=PAPER  # PAPER | SMALL_LIVE | FULL
```

### Docker Compose

```yaml
services:
  nemt-backend:
    environment:
      - BINANCE_API_KEY=${BINANCE_API_KEY}
      - BINANCE_API_SECRET=${BINANCE_API_SECRET}
      - TRADING_MODE=PAPER
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
```

---

## 验收标准

- [x] 系统可以连接行情
- [x] 可以生成交易计划
- [x] 默认不执行真实订单
- [x] 所有订单通过 Risk Gate
- [x] API Key 安全存储
- [x] 紧急停止功能可用
- [x] 完整订单记录

---

**版本**: Alpha 008  
**最后更新**: 2026-08-25  
**责任人**: NEMT Security Team
