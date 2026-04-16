# Quant-Sync-Server

量化工具协议转换中枢 - 将 Notion、MATLAB、Python、Go 等异构工具统一连接。

## 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     Quant-Sync-Server (MCP)                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Notion 适配器│  │ MATLAB 桥接器│  │    交易信号路由器    │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                              │                                   │
│                    ┌─────────┴─────────┐                        │
│                    │    数据转换器       │                        │
│                    │  (语义压缩)        │                        │
│                    └───────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

## 安装

```bash
# 安装依赖
pip install numpy redis requests

# MATLAB Engine API
# 在 MATLAB 中运行: >> engine.start_matlab
# 或: cd $MATLABROOT/extern/engines/python && python setup.py install
```

## 配置

创建 `.env` 文件:

```env
NOTION_TOKEN=your_notion_token
NOTION_STRATEGY_DB=your_strategy_db_id
NOTION_BACKTEST_DB=your_backtest_db_id
NOTION_SIGNAL_DB=your_signal_db_id
REDIS_HOST=redis
REDIS_PORT=6379
```

## 使用

### 1. MCP 服务器模式

在 Cursor 中配置 `.cursor/mcp.json`:

```json
{
    "mcpServers": {
        "quant-sync": {
            "command": "python",
            "args": ["quant-sync-server/server.py"]
        }
    }
}
```

### 2. CLI 模式

```bash
# 查看状态
python quant-sync-server/main.py --action status

# 分析数据
python quant-sync-server/main.py --action analyze --prices 50000,51000,52000

# 运行演示
python quant-sync-server/main.py --action demo
```

### 3. Python 直接调用

```python
from quant_sync_server import MatlabBridge, NotionAdapter

# MATLAB 分析
bridge = MatlabBridge()
result = bridge.run_analysis([50000, 51000, 52000])
print(result.spectral_width)

# Notion 读取
notion = NotionAdapter()
params = notion.read_strategy_params("page_id")
```

## 核心组件

| 组件 | 文件 | 功能 |
|:---|:---|:---|
| Notion 适配器 | `adapters/notion_adapter.py` | 读写 Notion 策略/回测数据库 |
| MATLAB 桥接器 | `adapters/matlab_bridge.py` | 通过 matlab.engine 执行 NEMT 分析 |
| 数据转换器 | `transformers/data_transformer.py` | 格式转换与语义压缩 |
| 信号路由器 | `routers/signal_router.py` | 交易信号分发到各目标 |

## 工具列表

- `get_server_info` - 获取服务器状态
- `notion_read_strategy` - 从 Notion 读取策略
- `notion_write_backtest` - 向 Notion 写入回测结果
- `matlab_check_engine` - 检查 MATLAB 引擎
- `matlab_run_analysis` - 运行 NEMT 分析
- `matlab_noise_scan` - 噪声扫描实验
- `matlab_beta_scan` - 非线性扫描实验
- `transform_compress` - 语义压缩
- `signal_generate` - 生成交易信号
- `run_full_pipeline` - 一键执行完整流程

## License

Apache 2.0
