# 代码规范
> CTO Agent 维护 | 最后更新: 2026-04-19

---

## 一、Python 代码规范

### 1.1 命名约定

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | 小写下划线 | `nemt_core.py` |
| 类 | 大驼峰 | `NEMTSimulator` |
| 函数 | 小写下划线 | `compute_dci()` |
| 变量 | 小写下划线 | `spectral_width` |
| 常量 | 全大写下划线 | `MAX_POSITION` |
| 私有方法 | 单下划线前缀 | `_compute_laplacian()` |
| 内部变量 | 双下划线前缀 | `__init__()` |

### 1.2 函数规范

```python
def compute_spectral_width(self, spectrum: np.ndarray) -> float:
    """
    计算谱宽

    谱宽 = sqrt(Σ(f - f_mean)²·S(f) / ΣS(f))

    Args:
        spectrum: 频谱数组

    Returns:
        谱宽值
    """
    # 实现
    pass
```

**要求**:
- 所有公共函数必须有docstring
- 参数必须有类型注解
- 返回值必须有类型注解
- docstring使用Google风格

### 1.3 类规范

```python
class NEMTSimulator:
    """非平衡市场理论模拟器"""

    def __init__(self, params: Optional[NEMTParams] = None):
        self.params = params or NEMTParams()
        self._initialized = False

    def initialize_state(self, price_data: np.ndarray) -> np.ndarray:
        """初始化市场状态"""
        pass
```

**要求**:
- 类必须有docstring
- 公开属性必须有类型注解
- 使用 dataclass 管理配置对象

### 1.4 导入规范

```python
# 标准库
import os
import sys
from typing import Dict, List, Optional

# 第三方库
import numpy as np
from scipy.fft import fft

# 本地模块
from .base import BaseStrategy
from .exceptions import ValidationError
```

---

## 二、TypeScript 代码规范

### 2.1 命名约定

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件 | 小写连字符 | `market-data.ts` |
| 类 | 大驼峰 | `MarketPanel` |
| 函数 | 驼峰 | `fetchMarketData()` |
| 变量 | 驼峰 | `currentPrice` |
| 常量 | 全大写下划线 | `MAX_POSITION` |
| 接口 | 大写I前缀 | `IMarketData` |

### 2.2 接口定义

```typescript
interface MarketData {
  timestamp: string;
  symbol: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface TradingSignal {
  type: 'buy' | 'sell' | 'hold';
  symbol: string;
  price: number;
  confidence: number;
}
```

### 2.3 React组件规范

```typescript
import React from 'react';

interface Props {
  title: string;
  onClick?: () => void;
}

export const MarketPanel: React.FC<Props> = ({ title, onClick }) => {
  const [data, setData] = useState<MarketData | null>(null);

  useEffect(() => {
    fetchData().then(setData);
  }, []);

  return <div onClick={onClick}>{title}</div>;
};
```

---

## 三、测试规范

### 3.1 测试文件命名

```
tests/
├── unit/
│   ├── test_nemt_core.py
│   ├── test_nemt_signals.py
│   └── test_nemt_state_machine.py
├── integration/
│   └── test_pipeline.py
└── e2e/
    └── test_full_flow.py
```

### 3.2 测试结构

```python
import pytest
from nemt_core import NEMTSimulator, NEMTParams

class TestNEMTSimulator:
    """NEMTSimulator 单元测试"""

    @pytest.fixture
    def simulator(self):
        """创建测试用的模拟器"""
        params = NEMTParams(alpha=0.1, beta=1.0)
        return NEMTSimulator(params)

    def test_initialize_state(self, simulator):
        """测试状态初始化"""
        prices = np.array([100, 101, 102])
        psi = simulator.initialize_state(prices)

        assert len(psi) == 3
        assert np.mean(psi) == pytest.approx(0)
        assert np.std(psi) == pytest.approx(1)

    def test_spectral_width(self, simulator):
        """测试谱宽计算"""
        # 使用固定seed确保可复现
        np.random.seed(42)
        prices = 50000 + 1000 * np.random.randn(100)

        psi = simulator.initialize_state(prices)
        simulator.evolve(psi, 50)
        freqs, spectrum = simulator.spectral_analysis()
        sw = simulator.compute_spectral_width()

        assert sw > 0
        assert sw < 1
```

### 3.3 测试覆盖率要求

| 模块 | 覆盖率目标 |
|------|-----------|
| nemt_core.py | > 90% |
| nemt_signals.py | > 85% |
| nemt_state_machine.py | > 90% |
| nemt_risk.py | > 80% |
| nemt_execution.py | > 80% |
| **整体** | > 80% |

---

## 四、Git 规范

### 4.1 分支命名

```
feature/<feature-name>      # 新功能
bugfix/<bug-description>     # Bug修复
hotfix/<urgent-fix>         # 紧急修复
chore/<task-description>     # 杂务
```

### 4.2 Commit 消息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试
- `chore`: 杂务

**示例**:
```
feat(model-node): Add NEMT Model Node (Branch 2)

- Add nemt_model_node.py for model layer
- Add enhanced_phase_detector.py
- Add high_performance_nls.py

Closes #123
```

### 4.3 PR 规范

1. PR标题必须符合commit格式
2. 必须包含测试结果
3. 必须通过CI检查
4. 必须有至少1人review

---

## 五、文档规范

### 5.1 Docstring 风格

使用Google风格docstring：

```python
def compute_dci(prices: np.ndarray, n_periods: int = 24) -> float:
    """
    计算方向一致性指数 (DCI)

    DCI = max(U, D) / N
    其中 U = 上涨K线数量, D = 下跌K线数量, N = 总K线数

    Args:
        prices: 价格序列
        n_periods: 计算周期（默认24根K线）

    Returns:
        DCI值，范围 [0, 1]

    Raises:
        ValueError: 当价格数据不足时

    Example:
        >>> prices = np.array([100, 101, 102, 101])
        >>> compute_dci(prices)
        0.75
    """
    pass
```

### 5.2 README 规范

每个模块的README必须包含：

```markdown
# 模块名称

> 简短描述

## 安装
## 使用
## API参考
## 示例
## 测试
```

---

## 六、Lint 检查

### 6.1 Python (ruff)

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N"]
ignore = ["E501"]
```

### 6.2 TypeScript (ESLint)

```json
{
  "extends": ["eslint:recommended", "plugin:@typescript-eslint/recommended"],
  "rules": {
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/explicit-function-return-type": "off"
  }
}
```

---

*违反代码规范的功能不会被合并*
