# NEMT量化系统 · 调试与审查清单

> 版本: v0.1 | 更新: 2026-04-19 | 状态: 🚧 进行中

---

## 1. Node 审查清单

### 1.1 MarketLayer 审查清单

```markdown
## MarketLayer 审查

### 数据获取
- [ ] K线数据格式正确 (OHLCV)
- [ ] 时间戳正确 (UTC)
- [ ] 数据完整性检查
- [ ] 支持多种时间周期 (1m, 5m, 15m, 1h, 4h, 1d)

### 错误处理
- [ ] 网络错误重试 (最多3次)
- [ ] API限流处理
- [ ] 数据异常返回错误码
- [ ] 日志记录完整

### 性能
- [ ] 缓存机制
- [ ] 并发请求优化
- [ ] 响应时间 < 100ms

### 文件: `data_fetcher.py`
```

### 1.2 NEMTCore 审查清单

```markdown
## NEMTCore 审查

### 算法正确性
- [ ] NLS方程数值求解正确
- [ ] Euler方法实现正确
- [ ] FFT变换结果验证
- [ ] 谱宽计算公式正确

### 参数边界
- [ ] alpha: 0.01 ~ 0.5
- [ ] beta: 0.1 ~ 2.0
- [ ] noise: 0.0 ~ 1.0
- [ ] dt: 0.001 ~ 0.1
- [ ] dx: 0.1 ~ 2.0
- [ ] steps: 100 ~ 1000

### 性能
- [ ] 向量化计算 (NumPy)
- [ ] 内存占用合理
- [ ] 执行时间 < 500ms

### 单元测试
- [ ] test_initialize_state
- [ ] test_evolve
- [ ] test_analyze_spectrum
- [ ] test_detect_resonance

### 文件: `nemt_core.py`
```

### 1.3 SignalLayer 审查清单

```markdown
## SignalLayer 审查

### DCI计算
- [ ] 价格变化方向正确
- [ ] 一致性窗口设置合理 (默认20)
- [ ] 返回值范围 0.0 ~ 1.0

### 涡旋检测 (4条件)
- [ ] 条件1: 价格突破 (收盘 > 20日高点)
- [ ] 条件2: 谱宽异常 (spectralWidth < 阈值)
- [ ] 条件3: 频率集中 (meanFrequency 集中)
- [ ] 条件4: 时间窗口 (3天内满足)
- [ ] 4条件至少满足3个

### 随机共振检测 (3条件)
- [ ] 条件1: 噪声匹配 (噪声水平适中)
- [ ] 条件2: 非线性增强 (信号增益 > 阈值)
- [ ] 条件3: 时间同步 (信号与噪声同步)
- [ ] 3条件全部满足

### 信号生成
- [ ] buy/sell/hold 信号正确
- [ ] confidence 0.0 ~ 1.0
- [ ] 指标完整 (DCI, spectralWidth, vortexScore, etc.)

### 文件: `nemt_signals.py`
```

### 1.4 RiskLayer 审查清单

```markdown
## RiskLayer 审查

### 相位仓位
- [ ] Phase A: maxPosition = 0.20
- [ ] Phase B: maxPosition = 0.50
- [ ] Phase C: maxPosition = 0.70
- [ ] Phase D: maxPosition = 1.00

### ATR止损
- [ ] 涡旋突破: 1.5x ATR
- [ ] 随机共振: 2.0x ATR
- [ ] 趋势回调: 1.0x ATR
- [ ] 止损价格计算正确

### 杠杆管理
- [ ] Phase A: 0x (禁止杠杆)
- [ ] Phase B: 1x
- [ ] Phase C: 2x
- [ ] Phase D: 1x
- [ ] 安全边际: 强平价 > 止损价 * 1.05

### 回撤控制
- [ ] 绿: < 5% (正常)
- [ ] 黄: 5-10% (警戒)
- [ ] 橙: 10-20% (警告)
- [ ] 红: > 20% (强制降仓)

### 文件: `nemt_risk.py`
```

### 1.5 ExecutionLayer 审查清单

```markdown
## ExecutionLayer 审查

### 四步流程
- [ ] Step 1: predict() 正确生成预测
- [ ] Step 2: generate_entry_signal() 生成入场信号
- [ ] Step 3: validate_entry() 验证清单通过
- [ ] Step 4: add_position() 仓位管理

### 验证清单
- [ ] 相位支持 (不支持则拒绝)
- [ ] 风险可接受
- [ ] 无反向信号
- [ ] 数据新鲜 (< 5分钟)

### 止盈止损
- [ ] 动态止盈 (跟随趋势)
- [ ] ATR止损
- [ ] 保本止损 (盈利后)

### 离场决策
- [ ] 止损触发
- [ ] 止盈触发
- [ ] 趋势反转
- [ ] 相位变化

### 文件: `nemt_execution.py`
```

---

## 2. 代码质量审查清单

### 2.1 正确性检查

```markdown
## 正确性检查

### 功能实现
- [ ] 代码实现了需求文档中的功能
- [ ] 每个接口函数都有实现
- [ ] 返回值格式正确

### 边界条件
- [ ] 空值处理 (None, [], {})
- [ ] 极值处理 (0, 负数, 极大数)
- [ ] 重复调用安全
- [ ] 并发安全

### 错误处理
- [ ] try-except 捕获异常
- [ ] 错误码定义清晰
- [ ] 错误日志记录
- [ ] 错误恢复机制
```

### 2.2 可读性检查

```markdown
## 可读性检查

### 命名规范
- [ ] 变量名: 英文 + 驼峰 (如 `spectralWidth`)
- [ ] 函数名: 动词 + 名词 (如 `calculateDCI`)
- [ ] 类名: 名词 + 大驼峰 (如 `SignalLayer`)
- [ ] 常量: 全大写 + 下划线 (如 `MAX_POSITION`)

### 注释质量
- [ ] 关键逻辑有注释 (WHY, not WHAT)
- [ ] 函数 docstring 完整
- [ ] 复杂算法有说明

### 代码结构
- [ ] 单个函数 < 50 行
- [ ] if/for 嵌套 < 3 层
- [ ] 类职责单一
- [ ] 模块划分清晰
```

### 2.3 可维护性检查

```markdown
## 可维护性检查

### 代码复用
- [ ] 重复代码已抽取为函数
- [ ] 公共工具类 (utils/)
- [ ] 无硬编码配置

### 依赖管理
- [ ] 配置外置 (config.py)
- [ ] API 抽象为接口
- [ ] 数据库抽象为DAO

### 日志记录
- [ ] 关键步骤有日志
- [ ] 日志级别正确 (DEBUG/INFO/WARN/ERROR)
- [ ] 无敏感信息泄露
```

### 2.4 性能检查

```markdown
## 性能检查

### 算法复杂度
- [ ] 无 O(n²) 或更高复杂度的循环
- [ ] 列表/字典操作高效
- [ ] 无重复计算

### 资源使用
- [ ] 内存占用合理
- [ ] 无内存泄漏
- [ ] 连接池复用

### 缓存策略
- [ ] 可缓存结果已缓存
- [ ] 缓存失效机制
```

---

## 3. 调试记录模板

### 3.1 调试记录

```markdown
## 调试记录 #___

**日期**: YYYY-MM-DD
**问题描述**: _________________
**定位方法**: _________________
**根本原因**: _________________
**修复方案**: _________________
**验证结果**: ✅ 通过 / ❌ 未通过
**新增测试用例**: 是 / 否

### 涉及模块
- [ ] MarketLayer
- [ ] NEMTCore
- [ ] SignalLayer
- [ ] RiskLayer
- [ ] ExecutionLayer

### 代码变更
```python
# 修改前
...

# 修改后
...
```
```

### 3.2 审查会议记录

```markdown
## 审查会议 #___

**时间**: YYYY-MM-DD HH:MM
**审查范围**: 文件/模块/PR链接
**参与者**: ______

### 总体评价
- [ ] ✅ 接受
- [ ] 🔄 需修改 (___处)
- [ ] ❌ 拒绝

### 讨论要点
1. ________
2. ________
3. ________

### 行动项
- [ ] 修改人: ______，截止: ______，内容: ______
- [ ] 修改人: ______，截止: ______，内容: ______

### 审查结论
- [ ] 通过
- [ ] 有条件通过
- [ ] 重新审查
```

---

## 4. 常见Bug速查表

### 4.1 数据类Bug

| Bug | 症状 | 解决方案 |
|-----|------|----------|
| 空数据 | IndexError, KeyError | 添加空值检查 |
| 格式错误 | 数值计算异常 | 数据类型转换 |
| 时区问题 | 时间戳不一致 | 统一UTC |
| 缺失字段 | KeyError | 默认值处理 |

### 4.2 算法类Bug

| Bug | 症状 | 解决方案 |
|-----|------|----------|
| 除零错误 | ZeroDivisionError | 添加分母检查 |
| 数组越界 | IndexError | 边界检查 |
| 类型不匹配 | TypeError | 类型转换 |
| 精度丢失 | 计算结果不准 | 使用Decimal |

### 4.3 性能类Bug

| Bug | 症状 | 解决方案 |
|-----|------|----------|
| 内存泄漏 | 内存持续增长 | 及时释放 |
| 死循环 | 程序卡死 | 添加超时 |
| 重复计算 | CPU占用高 | 添加缓存 |

---

## 5. CI/CD审查流水线

```yaml
# GitHub Actions 审查流水线
name: Code Review Pipeline

on:
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install flake8 mypy pytest
      - name: Lint with flake8
        run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
      - name: Type check with mypy
        run: mypy nemt_core.py nemt_signals.py nemt_risk.py nemt_execution.py

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run unit tests
        run: pytest tests/ -v --cov=.
      - name: Check coverage
        run: coverage report --fail-under=80

  review:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - name: Generate review report
        run: echo "All checks passed. Ready for code review."
```

---

## 6. 审查统计

### 6.1 审查通过率

| Node | 代码行数 | 测试覆盖 | 审查状态 |
|------|----------|----------|----------|
| NEMTCore | ~500 | 85% | ✅ 通过 |
| SignalLayer | ~400 | 80% | ✅ 通过 |
| RiskLayer | ~350 | 75% | 🔄 待审查 |
| ExecutionLayer | ~300 | 70% | 🔄 待审查 |
| OnChainLayer | ~250 | 60% | 🔄 待审查 |

### 6.2 Bug统计

| 类型 | 数量 | 已修复 | 待修复 |
|------|------|--------|--------|
| 数据类 | 5 | 4 | 1 |
| 算法类 | 3 | 3 | 0 |
| 性能类 | 2 | 1 | 1 |
| 安全类 | 0 | 0 | 0 |

---

## 7. 一句话总结

> 调试是让代码跑起来，审查是让代码活下去。
> 两者都是"写完代码"的必要步骤，不是可选项。
