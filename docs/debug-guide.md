# NEMT 调试指南

## 概述

本文档说明如何在 PyCharm 和 GoLand 中调试 NEMT Simulator 项目。

---

## PyCharm 调试 Python 后端

### 1. 打开项目

1. 打开 **PyCharm**
2. `File` → `Open` → 选择 `e:\NEMT Simulator\nemt_os` 文件夹
3. 将 `nemt_os` 设为 **Sources Root**（右键 → Mark Directory as → Sources Root）

### 2. 配置 Python 解释器

1. `File` → `Settings` → `Project: nemt_os` → `Python Interpreter`
2. 选择或创建 Python 3.11 解释器
3. 安装依赖：`pip install -r requirements.txt`

### 3. 配置 Run/Debug Configuration

1. `Run` → `Edit Configurations...`
2. 点击 `+` → `Python`
3. 配置：

```
Name: NEMT Debug
Script path: e:\NEMT Simulator\nemt_os\run_demo.py
Working directory: e:\NEMT Simulator\nemt_os
Python interpreter: Python 3.11
```

4. 点击 `Apply` → `OK`

### 4. 设置断点

按 `Ctrl+F8`（Windows）或 `Cmd+F8`（Mac）在以下位置设置断点：

#### 任务 1-10: 环境验证（无需断点）
直接运行 `run_demo.py`，观察控制台输出即可验证环境。

#### 任务 11-20: ConfigCenter 调试

**断点位置**：`nemt/core/config_center.py`

```python
# 行 30-50: __init__ 初始化
def __init__(self):
    # 设置断点在此

# 行 80-100: load() 配置加载
def load(self, config_path):
    # 设置断点在此

# 行 110-130: get() 配置读取
def get(self, key, default=None):
    # 设置断点在此
```

#### 任务 21-30: EventBus 调试

**断点位置**：`nemt/core/event_bus.py`

```python
# 行 20-40: EventBus.__init__
def __init__(self):
    # 设置断点

# 行 60-80: subscribe()
def subscribe(self, event_type, callback):
    # 设置断点

# 行 90-110: publish()
def publish(self, event_type, data):
    # 设置断点
```

#### 任务 31-45: MarketCapsule 调试

**断点位置**：`nemt/core/market_capsule.py`

```python
# 行 80-100: load_data()
def load_data(self, data):
    # 设置断点

# 行 110-130: get_bar()
def get_bar(self):
    # 设置断点

# 行 140-160: next_bar()
def next_bar(self):
    # 设置断点
```

#### 任务 46-60: SignalCapsule 调试

**断点位置**：`nemt/core/signal_capsule.py`

```python
# 行 80-120: generate_signal()
def generate_signal(self, bar):
    # 设置断点

# 行 130-150: calculate_confidence()
def calculate_confidence(self, signal):
    # 设置断点
```

### 5. 开始调试

1. 在 `run_demo.py` 中设置断点（主入口）
2. 按 `Shift+F9` 或点击调试按钮开始调试
3. 使用调试面板：
   - `F8`: Step Over（跳过）
   - `F7`: Step Into（进入函数）
   - `F9`: Resume（继续到下一个断点）
   - `Ctrl+F8`: 切换断点

### 6. 调试技巧

#### 条件断点
1. 右键断点 → `Condition`
2. 输入条件，例如：`count > 10`

#### 监视变量
1. Debug 面板 → `Watches` → 点击 `+`
2. 输入变量名，如 `config.get("risk.max_drawdown")`

#### Evaluate 表达式
1. Debug 控制台 → 输入表达式
2. 按 `Enter` 执行

---

## GoLand 调试 Go 后端

### 1. 打开项目

1. 打开 **GoLand**
2. `File` → `Open` → 选择 `e:\NEMT Simulator\src\nemt-go` 文件夹
3. 等待 Go modules 加载完成

### 2. 配置 Run/Debug Configuration

1. `Run` → `Edit Configurations...`
2. 点击 `+` → `Go Build`
3. 配置 Gateway 服务：

```
Name: Gateway Debug
Files: cmd/gateway/main.go
Working directory: e:\NEMT Simulator\src\nemt-go
Program arguments: --config configs/gateway.yaml
```

4. 配置 Collector 服务：

```
Name: Collector Debug
Files: cmd/collector/main.go
Working directory: e:\NEMT Simulator\src\nemt-go
```

### 3. 设置断点

按 `Ctrl+F8` 设置断点：

#### 任务 201-220: Gateway main.go

**断点位置**：`cmd/gateway/main.go`

```go
// 行 1-50: main()
func main() {
    // 设置断点在此
}

// 行 50-100: initServer()
func initServer() {
    // 设置断点
}
```

#### 任务 221-240: Handler 调试

**断点位置**：`pkg/gateway/handler.go`

```go
// 行 50-100: HandleRequest()
func (h *Handler) HandleRequest(ctx context.Context, req *Request) (*Response, error) {
    // 设置断点
}

// 行 100-150: RouteRequest()
func (h *Handler) RouteRequest(req *Request) error {
    // 设置断点
}
```

#### 任务 241-260: Strategy 调试

**断点位置**：`pkg/gateway/strategy.go`

```go
// 行 50-100: CreateStrategy()
func (h *Handler) CreateStrategy(ctx context.Context, req *StrategyRequest) (*StrategyResponse, error) {
    // 设置断点
}
```

### 4. 开始调试

1. 选择配置（如 `Gateway Debug`）
2. 按 `Shift+F9` 开始调试
3. 使用调试面板：
   - `F8`: Step Over
   - `F7`: Step Into
   - `Shift+F8`: Step Out
   - `Ctrl+F8`: 切换断点

### 5. 调试技巧

#### 日志断点
1. 右键断点 → `Log` → 选择要输出的变量
2. 可以在不中断的情况下输出变量值

#### 条件断点
1. 右键断点 → `Condition`
2. 输入条件，如 `request.ID != ""`

#### 调试子进程
```
Environment variables: GODEBUG=追其者=1
```

---

## 推荐的调试顺序

### 第1阶段: Python 基础（任务 1-50）

```
1. 运行 run_demo.py 验证环境
2. 断点: config_center.py → get() 观察配置读取
3. 断点: event_bus.py → publish() 观察事件发布
4. 断点: capsule_manager.py → register() 观察胶囊注册
```

### 第2阶段: Python 胶囊（任务 51-100）

```
5. 断点: market_capsule.py → load_data() 观察数据加载
6. 断点: signal_capsule.py → generate_signal() 观察信号生成
7. 断点: risk_capsule.py → check_risk() 观察风控检查
8. 断点: execution_capsule.py → place_order() 观察订单执行
```

### 第3阶段: Go Gateway（任务 201-230）

```
9. 断点: main.go → main() 观察服务启动
10. 断点: handler.go → HandleRequest() 观察请求处理
11. 断点: strategy.go → CreateStrategy() 观察策略创建
```

---

## 常见问题

### Python 调试

**Q: 找不到模块 `nemt`**
```
A: 右键 nemt 文件夹 → Mark Directory as → Sources Root
```

**Q: 断点变成灰色（未激活）**
```
A: 检查 Python 解释器是否正确配置
```

### Go 调试

**Q: Go modules 未加载**
```
A: 在终端运行: go mod tidy
```

**Q: 断点变成空心圆**
```
A: 确保使用调试模式编译: go build -gcflags="-N -l"
```

---

## 调试状态更新

完成调试后，请在 `docs/debug-plan-500.md` 中更新任务状态：

| 符号 | 含义 |
|------|------|
| `[x]` | 已完成，通过 |
| `[!]` | 发现问题，需要修复 |
| `[~]` | 部分完成 |
| `[?]` | 需要更多信息 |

---

*最后更新: 2026-05-03*
