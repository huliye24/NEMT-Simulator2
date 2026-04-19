# 测试要求
> 各类测试的强制要求和规范

## 一、测试金字塔

```
           ┌───────────┐
           │   E2E     │   ← 少量，端到端
          ┌───────────┐
          │ Integration │   ← 适量，模块集成
         ┌───────────┐
         │   Unit     │   ← 大量，单元测试
        └───────────┘
```

## 二、单元测试要求

### 2.1 覆盖率要求

| 模块 | 最低覆盖率 |
|------|-----------|
| 核心业务逻辑 | 90% |
| 工具函数 | 80% |
| API 路由 | 70% |
| UI 组件 | 50% |

### 2.2 命名规范

**Python**:
```python
class TestCapitalNode:
    def test_allocate_single_order_returns_correct_capital(self):
        ...

    def test_allocate_empty_orders_raises_error(self):
        ...
```

**TypeScript**:
```typescript
describe('CapitalNode', () => {
  it('should allocate funds equally', () => {
    // ...
  });

  it('should return zero for empty orders', () => {
    // ...
  });
});
```

### 2.3 测试结构 (AAA)

```python
def test_calculate_position_size(self):
    # Arrange - 准备测试数据
    risk_manager = NEMTRiskManager(initial_balance=100000)
    entry_price = 67000
    stop_loss = 65000

    # Act - 执行被测函数
    position = risk_manager.calculate_position_size(
        entry_price=entry_price,
        stop_loss=stop_loss
    )

    # Assert - 验证结果
    assert position > 0
    assert position < 1.0
```

### 2.4 Mock 使用

```python
# Good: Mock 外部依赖
def test_fetch_market_data(mocker):
    mock_api = mocker.patch('services.market_api')
    mock_api.return_value = {"price": 67000}
    # ...

# Bad: Mock 内部实现
def test_internal_logic():
    # 不要 Mock 被测模块的内部函数
    ...
```

### 2.5 测试隔离

```python
# Good: 每个测试独立
class TestCalculator:
    def test_add_positive_numbers(self):
        assert calc.add(1, 2) == 3

    def test_add_negative_numbers(self):
        assert calc.add(-1, -2) == -3

# Bad: 测试间依赖
class TestCalculator:
    def test_add_first(self):
        calc.add(1, 2)  # 设置状态
        assert calc.result == 3

    def test_add_second(self):
        # 依赖上一个测试的状态
        assert calc.result == 3
        calc.add(3, 4)
```

## 三、集成测试要求

### 3.1 测试范围

- API 端点
- 数据库操作
- 外部服务集成
- 模块间通信

### 3.2 测试数据

```python
@pytest.fixture
def test_db():
    """创建测试数据库"""
    db = create_test_db()
    yield db
    db.cleanup()

@pytest.fixture
def sample_orders():
    """样例订单数据"""
    return [
        Order(strategy_id="s1", ...),
        Order(strategy_id="s2", ...),
    ]
```

### 3.3 API 测试

```python
def test_create_order_api(test_client):
    response = test_client.post(
        "/api/orders",
        json={"symbol": "BTCUSDT", "quantity": 0.1}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["status"] == "pending"
```

## 四、端到端测试

### 4.1 适用范围

- 关键用户流程
- 支付流程
- 认证流程

### 4.2 测试环境

- 使用独立的测试环境
- 使用 Mock 数据
- 隔离外部依赖

## 五、回归测试

### 5.1 执行时机

- 每次发布前
- 重大重构后
- 依赖更新后

### 5.2 覆盖范围

全量测试套件，包括:
- 单元测试
- 集成测试
- E2E 测试

## 六、性能测试

### 6.1 基准测试

```python
def test_nemt_analysis_performance():
    """NEMT 分析应在 100ms 内完成"""
    start = time.time()
    result = nemt.analyze(prices)
    elapsed = time.time() - start
    
    assert elapsed < 0.1, f"Too slow: {elapsed}s"
```

### 6.2 负载测试

| 场景 | 目标 |
|------|------|
| 并发请求 | 100 req/s |
| 响应时间 | < 200ms (p99) |
| 错误率 | < 1% |

## 七、测试数据管理

### 7.1 测试数据原则

1. **可重复**: 测试可独立运行，不依赖外部状态
2. **可清理**: 测试后清理创建的数据
3. **真实性**: 使用真实的数据结构，避免过度 Mock

### 7.2 Fixture 管理

```python
# conftest.py
import pytest

@pytest.fixture
def mock_market_data():
    return [
        {"timestamp": 1, "price": 67000},
        {"timestamp": 2, "price": 67100},
        {"timestamp": 3, "price": 67200},
    ]
```

## 八、持续集成

### 8.1 CI 检查

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pytest tests/ --cov=src --cov-report=xml
      - name: Coverage
        uses: codecov/codecov-action@v3
```

### 8.2 覆盖率门禁

| 指标 | 阈值 |
|------|------|
| 整体覆盖率 | 80% |
| 关键模块 | 90% |
| 新增代码 | 80% |

## 九、测试反模式

### ❌ 禁止

```python
# Bad: 无断言
def test_something():
    result = calculate()
    # 没有任何断言

# Bad: 断言总是通过
def test_something():
    assert True

# Bad: 依赖时间
def test_timeout():
    time.sleep(10)  # 不要依赖精确时间

# Bad: 全局状态
def test_uses_global():
    global_data.append(x)  # 不要修改全局状态
```

### ✅ 推荐

```python
# Good: 有意义的断言
def test_position_calculation():
    result = calculate_position(...)
    assert result == expected

# Good: 清晰的消息
assert result > 0, "Position should be positive"

# Good: 参数化测试
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert double(input) == expected
```

---

*创建时间: 2026-04-19*
*最后更新: 2026-04-19*
