# NEMT Simulator - Electron Desktop Application

## 项目结构

```
NEMT-Simulator/
├── src/
│   ├── desktop/           # Electron 主进程 (TypeScript)
│   │   ├── main/         # 主进程模块
│   │   │   ├── index.ts  # 应用入口
│   │   │   ├── window.ts # 窗口管理
│   │   │   ├── menu.ts  # 菜单管理
│   │   │   ├── tray.ts  # 系统托盘
│   │   │   └── ipc.ts   # IPC 通信
│   │   ├── preload/      # 预加载脚本
│   │   │   └── index.ts
│   │   └── shared/       # 共享类型定义
│   │       └── types.ts
│   │
│   ├── web/              # React 前端
│   │
│   ├── gateway/          # Go HTTP/gRPC 网关
│   │   ├── cmd/gateway/  # 入口
│   │   └── go.mod
│   │
│   ├── collector/         # Go 数据采集
│   ├── scheduler/         # Go 任务调度
│   │
│   ├── gateway-pkg/       # Go 共享包
│   │   └── pkg/
│   │
│   └── nemt-os/          # Python 量化引擎
│       ├── nemt/         # 核心模块
│       ├── services/     # 服务层
│       ├── tests/        # 测试
│       └── grpc_server.py # gRPC 入口
│
├── configs/              # 配置文件
├── build/               # 构建资源
├── dist/                # 构建输出
├── release/             # 发布包
├── Makefile            # 构建入口
└── package.json        # 前端依赖
```

## 快速开始

### 安装依赖

```bash
# 安装前端依赖
npm install

# 安装 Go 依赖
cd src/gateway && go mod download
cd src/collector && go mod download
cd src/scheduler && go mod download

# 安装 Python 依赖
cd src/nemt-os
pip install -r requirements.txt
```

### 开发模式

```bash
# 启动完整开发环境
make dev

# 或单独启动
npm run dev:web      # 启动 React 开发服务器
npm run dev:desktop  # 启动 Electron
```

### 构建

```bash
# 构建全部
make build

# 单独构建
make build-web       # 构建 React 前端
make build-desktop   # 构建 Electron
make build-gateway   # 构建 Go 网关
```

### 打包

```bash
# 打包全部平台
make package

# 单独打包
make package:win     # Windows
make package:mac     # macOS
make package:linux   # Linux
```

## 架构说明

### Electron 主进程

负责：
- 窗口管理
- 系统菜单
- 系统托盘
- 子进程管理 (Go Gateway + Python Engine)
- IPC 通信

### Go Gateway

高性能 HTTP/gRPC 网关：
- REST API (策略、胶囊、回测管理)
- WebSocket 实时行情
- gRPC 通信 Python 引擎

### Python Engine

量化核心引擎：
- NEMT 分形迭代框架
- 胶囊架构
- 市场数据处理

## 配置

配置文件位于 `configs/` 目录：

- `dev.yaml` - 开发环境
- `prod.yaml` - 生产环境

## 构建产物

- `dist/` - 构建中间产物
- `release/` - 最终安装包

## 技术栈

- **Electron** - 桌面应用框架
- **React + TypeScript** - 前端
- **Go** - 微服务 (Gateway, Collector, Scheduler)
- **Python** - 量化引擎
- **gRPC** - 服务间通信
