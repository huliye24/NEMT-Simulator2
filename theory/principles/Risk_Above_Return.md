# 风险优先原则 (Risk Above Return)

> "追求收益是本能，控制风险是智慧。在NEMT系统中，风控永远是第一优先级。"

---

## 核心原则

**在任何情况下，风险控制都优先于追求收益。**

这不是一个可以妥协的原则，也不是一个"尽量遵守"的建议。这是一条不可逾越的红线。

---

## 为什么风险优先？

### 1. 生存是第一要务

在金融市场中，生存是第一要务。

- **数学不对称性**: 亏损50%需要盈利100%才能回本
- **黑天鹅风险**: 极端事件虽然罕见，但破坏力巨大
- **复利效应**: 保护本金是复利增长的基础

### 2. 风险与收益的真相

许多人误解了风险与收益的关系：

```
高风险 ≠ 高收益
高风险 = 高潜在收益 AND 高潜在损失

真正的智慧 = 在可控风险下追求合理收益
```

### 3. 系统性崩溃的代价

一次灾难性损失可能摧毁整个系统：

- 50%回撤需要100%收益来弥补
- 80%回撤需要400%收益来弥补
- 90%回撤意味着几乎不可能恢复

---

## NEMT系统的风控层次

### 第一层：策略级风控

每个策略都必须遵守的风控规则：

```python
class StrategyRiskControl:
    """策略级风控"""
    
    MAX_SINGLE_TRADE_LOSS = 0.02  # 单笔交易最大亏损2%
    MAX_DAILY_LOSS = 0.05        # 单日最大亏损5%
    MAX_POSITION_SIZE = 0.20      # 单品种最大仓位20%
    
    def pre_trade_check(self, trade):
        """交易前检查"""
        # 检查仓位是否超限
        if trade.position_size > self.MAX_POSITION_SIZE:
            return False, "仓位超限"
            
        # 检查是否会导致日内亏损超限
        if self.current_daily_loss + trade.potential_loss > self.MAX_DAILY_LOSS:
            return False, "日内亏损超限"
            
        return True, "通过"
```

### 第二层：策略组合风控

多个策略同时运行时的风控：

```python
class PortfolioRiskControl:
    """组合级风控"""
    
    MAX_PORTFOLIO_DRAWDOWN = 0.15      # 组合最大回撤15%
    MAX_CORRELATION = 0.7              # 策略间最大相关性
    MIN_STRATEGIES = 3                 # 最少策略数量
    
    def check_portfolio_risk(self, portfolio):
        """检查组合风险"""
        # 检查整体回撤
        if portfolio.current_drawdown > self.MAX_PORTFOLIO_DRAWDOWN:
            return False, "组合回撤超限，建议减仓"
            
        # 检查策略相关性
        correlations = calculate_correlations(portfolio.strategies)
        if any(c > self.MAX_CORRELATION for c in correlations):
            return False, "策略相关性过高"
            
        return True, "通过"
```

### 第三层：系统性风控

整个系统的最后防线：

```python
class SystemRiskControl:
    """系统性风控"""
    
    EMERGENCY_STOP_DRAWDOWN = 0.20     # 紧急止损回撤线
    CIRCUIT_BREAKER_WINDOW = 7         # 熔断窗口(天)
    CIRCUIT_BREAKER_THRESHOLD = 0.10   # 熔断阈值(10%亏损)
    
    def check_emergency_conditions(self, system):
        """检查紧急情况"""
        # 检查是否触发紧急止损
        if system.total_drawdown > self.EMERGENCY_STOP_DRAWDOWN:
            return "EMERGENCY_STOP", "触发紧急止损，系统暂停"
            
        # 检查是否需要熔断
        recent_loss = system.get_recent_loss(self.CIRCUIT_BREAKER_WINDOW)
        if recent_loss > self.CIRCUIT_BREAKER_THRESHOLD:
            return "CIRCUIT_BREAKER", "触发熔断，暂停入场"
            
        return "NORMAL", "系统正常运行"
```

---

## 风控检查清单

### 策略上线前

- [ ] 单策略回测最大回撤 < 15%
- [ ] 单策略 Sharpe Ratio > 0.8
- [ ] 样本外表现与样本内差异 < 20%
- [ ] 极端行情(2008/2020)下回撤可接受

### 每日开盘前

- [ ] 检查隔夜风险事件
- [ ] 确认风控系统正常运行
- [ ] 评估当日市场风险等级
- [ ] 确认各策略仓位状态

### 交易执行中

- [ ] 每笔交易经过风控审核
- [ ] 实时监控仓位变化
- [ ] 监控日内亏损情况
- [ ] 及时响应风控警报

### 收盘后

- [ ] 生成风控日报
- [ ] 记录任何风控触发事件
- [ ] 分析风控有效性
- [ ] 更新风险管理建议

---

## 禁止事项（绝对红线）

### 🚫 绝对禁止

1. **禁止绕过风控下单** - 即使"确定会涨"也不行
2. **禁止手动干预风控参数** - 除非紧急情况并记录
3. **禁止单策略重仓** - 任何单一策略仓位不超过20%
4. **禁止追涨杀跌** - 违背策略逻辑的交易一律禁止
5. **禁止在熔断后继续交易** - 必须等待系统恢复

### ⚠️ 需要特别审批

1. 临时调整风控参数 - 需要创始人批准
2. 策略快速上线 - 需要额外风控审查
3. 跨品种大额交易 - 需要组合风控确认

---

## 风控仪表盘指标

| 指标 | 正常 | 警告 | 危险 |
|------|------|------|------|
| 组合回撤 | < 5% | 5-10% | > 10% |
| 单日亏损 | < 2% | 2-5% | > 5% |
| 策略相关性 | < 0.5 | 0.5-0.7 | > 0.7 |
| 有效策略数 | > 4 | 2-4 | < 2 |

---

## 案例：为什么风控优先？

### 案例1：长期资本管理(LTCM)

- 诺贝尔奖得主创立的量化基金
- 1998年俄罗斯债务违约
- 4个月内亏损45亿美元
- 最终被接管

**教训**: 高杠杆 + 低相关性假设 + 黑天鹅 = 灾难

### 案例2：骑士资本(Knight Capital)

- 2012年8月1日
- 软件bug导致4.4亿美元亏损
- 45分钟内交易所要求停止
- 公司股价暴跌70%

**教训**: 技术故障 + 缺乏熔断 = 快速崩溃

### 案例3：保护本金的数学

| 起始资金 | 年收益 | 10年后 | 20年后 |
|---------|--------|--------|--------|
| 100万 | 20% | 619万 | 3834万 |
| 100万 | 30% (高风险) | 1379万 | 1.9亿 |
| 100万 | 20% (某年亏损50%) | 309万 | 957万 |
| 100万 | 30% (某年亏损50%) | 689万 | 4749万 |

**教训**: 一次大幅回撤对长期复利有巨大伤害

---

## 与其他原则的关系

- [[Strategy_As_Organism]] - 策略的"衰老"和"死亡"由风控机制触发
- [[Kitchen_First]] - 风控是厨房的核心基础设施

---

*相关文档: [[VISION]] | [[Strategy_As_Organism]] | [[Kitchen_First]]*
