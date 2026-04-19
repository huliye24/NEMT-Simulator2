# 代码规范
> 基于 CTO 的 CODE_STANDARDS.md 细化

## 一、通用规范

### 1.1 代码格式化

| 语言 | 工具 | 配置 |
|------|------|------|
| Python | Black | `pyproject.toml` |
| TypeScript | Prettier | `.prettierrc` |
| CSS | Prettier | 同上 |

### 1.2 命名规范

| 类型 | Python | TypeScript | 示例 |
|------|--------|------------|------|
| 变量 | snake_case | camelCase | `user_name`, `userName` |
| 常量 | UPPER_SNAKE | camelCase | `MAX_RETRY = 3` |
| 函数 | snake_case | camelCase | `get_user()` |
| 类名 | PascalCase | PascalCase | `UserService` |
| 文件 | snake_case | kebab-case | `user_service.py`, `user-service.ts` |

### 1.3 注释规范

```python
# 单行注释：解释"为什么"，不解释"是什么"

# ✅ Good
result = cache.get(key)  # 缓存未命中，查询数据库
if result is None:
    result = fetch_from_db(key)
    cache.set(key, result, ttl=300)

# ❌ Bad
result = cache.get(key)  # 获取缓存
if result is None:  # 如果为空
    result = fetch_from_db(key)  # 从数据库获取
```

### 1.4 Docstring 规范

```python
def calculate_position_size(
    entry_price: float,
    stop_loss: float,
    risk_amount: float
) -> float:
    """
    计算仓位大小

    Args:
        entry_price: 入场价格
        stop_loss: 止损价格
        risk_amount: 风险金额（占总资金比例）

    Returns:
        建议仓位数量

    Raises:
        ValueError: 止损价格 >= 入场价格

    Example:
        >>> calculate_position_size(100, 95, 0.02)
        0.4
    """
    if stop_loss >= entry_price:
        raise ValueError("止损价格必须小于入场价格")
```

## 二、TypeScript 规范

### 2.1 类型定义

```typescript
// ✅ Good: 使用 interface 定义对象
interface Order {
  readonly id: string;
  symbol: string;
  direction: 1 | -1 | 0;
  quantity: number;
  stopLoss?: number;
}

// ✅ Good: 使用 type 定义联合类型
type MarketPhase = 'phase_a' | 'phase_b' | 'phase_c' | 'phase_d';

// ❌ Bad: 使用 any
function processData(data: any) { }

// ✅ Good: 使用 unknown + 类型守卫
function processData(data: unknown) {
  if (isOrder(data)) {
    // 处理
  }
}
```

### 2.2 React 组件

```typescript
// ✅ Good: 使用函数组件 + hooks
interface Props {
  title: string;
  onClick?: () => void;
}

export const Button: React.FC<Props> = ({ title, onClick }) => {
  return (
    <button onClick={onClick} type="button">
      {title}
    </button>
  );
};

// ❌ Bad: 类组件（除非必要）
class Button extends React.Component<Props> { }
```

### 2.3 状态管理

```typescript
// ✅ Good: 使用 Zustand store
interface AppStore {
  phase: MarketPhase;
  setPhase: (phase: MarketPhase) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  phase: 'phase_a',
  setPhase: (phase) => set({ phase }),
}));

// ❌ Bad: 多余的 useState
const [phase, setPhase] = useState('phase_a');
```

## 三、Python 规范

### 3.1 类型注解

```python
from typing import List, Optional, Dict

# ✅ Good: 使用类型注解
def allocate_funds(
    orders: List[Order],
    total: float,
    phase: MarketPhase
) -> AllocationResult:
    ...

# ✅ Good: Optional 用于可选参数
def get_strategy(
    strategy_id: str,
    include_performance: bool = False
) -> Optional[Strategy]:
    ...

# ❌ Bad: 无类型注解
def allocate_funds(orders, total, phase):
    ...
```

### 3.2 异常处理

```python
# ✅ Good: 具体异常 + 上下文
try:
    result = risky_operation()
except ValueError as e:
    logger.error(f"参数错误: {e}")
    raise ConfigurationError(f"无法初始化: {e}") from e

# ❌ Bad: 裸 except
try:
    result = risky_operation()
except:
    pass
```

### 3.3 日志记录

```python
import logging

logger = logging.getLogger(__name__)

# ✅ Good: 结构化日志
logger.info(
    "Order executed",
    extra={
        "order_id": order.id,
        "symbol": order.symbol,
        "price": order.price,
    }
)

# ❌ Bad: 字符串拼接
logger.info(f"Order {order.id} executed at {price}")
```

## 四、Git 规范

### 4.1 Commit 消息

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试
- `chore`: 维护

示例:
```
feat(capital-node): Add PhaseDrivenCapitalManager

Implement phase-based position limits:
- Phase A: 20%
- Phase B: 50%
- Phase C: 70%
- Phase D: 100%

Closes #123
```

### 4.2 Branch 命名

```
<type>/<issue>-<short-description>

feat/123-capital-allocation
fix/456-order-execution
chore/update-deps
```

## 五、测试规范

### 5.1 测试命名

```python
# Python: test_<function_name>_<scenario>
class TestCapitalNode:
    def test_allocate_single_order(self):
        ...

    def test_allocate_empty_orders_returns_zero(self):
        ...
```

```typescript
// TypeScript: it/<should do something>
describe('CapitalNode', () => {
  it('should allocate funds equally', () => {
    // ...
  });

  it('should return zero for empty orders', () => {
    // ...
  });
});
```

### 5.2 测试结构

```python
class TestRiskCalculator:
    def test_calculate_position_size(self):
        # Arrange
        risk_manager = NEMTRiskManager(initial_balance=100000)

        # Act
        position = risk_manager.calculate_position_size(...)

        # Assert
        assert position > 0
        assert position < 1.0
```

## 六、安全规范

- ❌ 禁止硬编码密钥
- ❌ 禁止在注释中包含敏感信息
- ✅ 敏感配置使用环境变量
- ✅ 用户输入必须验证
- ✅ SQL 参数化查询
- ✅ 最小权限原则

---

*基于 CTO CODE_STANDARDS.md 细化*
*创建时间: 2026-04-19*
