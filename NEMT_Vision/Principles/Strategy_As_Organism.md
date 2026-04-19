# 策略即生物体 (Strategy As Organism)

> "每个策略都有生命周期——出生、成长、衰老、死亡。系统需要管理这个过程。"

---

## 核心理念

在传统量化交易中，策略被视为"工具"——可以被精确设计、持久使用。但在NEMT系统中，我们采用完全不同的视角：

**策略是生物体，不是规则集。**

---

## 什么是"生物体"视角？

### 对比：工具 vs 生物体

| 维度 | 传统工具观 | 生物体观 |
|------|------------|----------|
| 创建 | 一次性设计完成 | 从简单开始，逐渐演化 |
| 生命周期 | 理论上永久 | 有明确的生老病死 |
| 维护 | 需要人工干预 | 需要环境支持 |
| 失效 | 突然崩溃 | 有预警信号 |
| 替换 | 人工选择 | 自动淘汰 |
| 适应 | 不适应 | 持续适应 |

### 生物体策略的特征

1. **出生 (Creation)**
   - 从简单策略开始
   - 在回测中验证可行性
   - 通过初始筛选进入系统

2. **成长 (Growth)**
   - 在实盘/模拟中获得反馈
   - 根据市场表现调整权重
   - 学习新的市场模式

3. **成熟 (Maturity)**
   - 稳定贡献收益
   - 成为组合的核心部分
   - 提供稳定的风险调整收益

4. **衰老 (Decay)**
   - 收益开始下降
   - 最大回撤增加
   - 市场适应性降低

5. **死亡 (Death)**
   - 被淘汰机制移除
   - 资源释放给新策略
   - 保留经验教训

---

## 策略生态系统

```
                    ┌──────────────┐
                    │   新策略池    │  <- 候选策略等待入场
                    └──────┬───────┘
                           │ 验证通过
                           ▼
                    ┌──────────────┐
                    │   活跃策略    │  <- 正在运行的策略
                    │   (3-8个)    │
                    └──────┬───────┘
                           │ 表现下降
                           ▼
                    ┌──────────────┐
                    │   观察期      │  <- 被监控但不参与组合
                    └──────┬───────┘
                           │ 持续低迷
                           ▼
                    ┌──────────────┐
                    │   淘汰区      │  <- 即将被移除
                    └──────────────┘
```

---

## 策略生命周期的量化指标

### 出生标准

- 回测年化收益 > 5%
- 最大回撤 < 15%
- Sharpe Ratio > 0.8
- 样本外表现与样本内差异 < 20%

### 成长信号

- 连续4周正收益
- Sharpe Ratio持续提升
- 与其他策略相关性下降

### 衰老指标

- 连续4周负收益
- Sharpe Ratio < 0.5
- 与市场相关性异常变化

### 死亡标准

- 最大回撤超过阈值
- 连续8周表现低于基准
- 被新策略取代

---

## 生物体策略的优势

### 1. 适应性更强

生物体能够感知环境变化并调整行为。策略同样需要：
- 感知市场状态（趋势/震荡）
- 感知自身状态（表现好/差）
- 感知其他策略状态（竞争/互补）

### 2. 自我平衡

生态系统有内在的平衡机制：
- 不会某单一物种统治整个系统
- 资源（资金）自动流向高效策略
- 低效策略自然淘汰

### 3. 持续进化

生物体通过遗传和变异进化：
- 新策略从旧策略"继承"有效因子
- 随机变异产生新思路
- 自然选择保留优秀个体

---

## 实践：策略管理器

```python
class StrategyOrganism:
    """策略生物体"""
    
    def __init__(self, strategy, config):
        self.strategy = strategy
        self.state = "born"  # born, growing, mature, decaying, dead
        self.fitness_score = 0.0
        self.age = 0  # 存活天数
        self.max_age = config.get("max_age", 365)
        self.performance_history = []
        
    def assess_fitness(self, market_data):
        """评估当前适应性"""
        current_performance = self.strategy.evaluate(market_data)
        self.performance_history.append(current_performance)
        
        # 计算适应性分数
        self.fitness_score = calculate_fitness(
            returns=current_performance.returns,
            max_drawdown=current_performance.max_drawdown,
            sharpe=current_performance.sharpe_ratio,
            age=self.age
        )
        
        return self.fitness_score
    
    def update_state(self):
        """更新生命周期状态"""
        if self.state == "born":
            if self.fitness_score > 0.6:
                self.state = "growing"
        elif self.state == "growing":
            if self.fitness_score > 0.8:
                self.state = "mature"
            elif self.fitness_score < 0.3:
                self.state = "decaying"
        elif self.state == "mature":
            if self.fitness_score < 0.4:
                self.state = "decaying"
        elif self.state == "decaying":
            if self.fitness_score < 0.2 or self.age > self.max_age:
                self.state = "dead"
                
        self.age += 1
```

---

## 与其他原则的关系

- [[Kitchen_First]] - 策略的"厨房"是回测引擎和监控基础设施
- [[Risk_Above_Return]] - 每个策略都必须通过风控审核才能出生

---

*相关文档: [[VISION]] | [[Kitchen_First]] | [[Risk_Above_Return]]*
