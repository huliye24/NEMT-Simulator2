# NEMT Simulator - Electron 工业化重构执行计划

> **架构愿景**: 把没有完成的完成
>
> **目标**: 将 Electron 项目从"能跑"提升到"工业化生产"级别
>
> **状态**: ✅ 主要步骤已完成 (2026-05-04)
>
> **完成进度**: 22/28 步骤已完成

---

## 一、现状诊断

### 1.1 已完成的工作

| 模块 | 状态 | 说明 |
|------|------|------|
| 项目结构 | ✅ | main.ts, preload.ts, 子模块目录 |
| WindowManager | ✅ | 窗口管理、状态持久化 |
| MenuManager | ✅ | 应用菜单、中文界面 |
| TrayManager | ✅ | 系统托盘、快捷操作 |
| IPCClient | ✅ | Go Gateway HTTP/WS通信 |
| TypeScript | ✅ | 编译配置、类型定义 |
| 构建脚本 | ✅ | npm scripts, 启动脚本, electron-builder配置 |
| Python Bridge | ✅ | electron_bridge.py, gRPC服务 |
| Go Workspace | ✅ | src/go.work, 服务发现配置 |
| gRPC连接池 | ✅ | src/gateway-pkg/pkg/grpcpool |
| 热重载支持 | ✅ | src/desktop/main/hotReload.ts |
| WebSocket Hook | ✅ | src/web/hooks/useLocalMarket.ts |
| 桌面适配器 | ✅ | src/web/platform/desktopAdapter.ts |
| Python生命周期 | ✅ | src/nemt-os/nemt/lifecycle.py |
| 日志集成 | ✅ | src/nemt-os/nemt/logging_integration.py |
| 打包配置 | ✅ | electron-builder.yml, build-go.bat, build-python.bat |
| 测试框架 | ✅ | vitest配置, 测试用例 |

### 1.2 缺失的关键功能

```
┌─────────────────────────────────────────────────────────────────┐
│                    NEMT Electron 工业化缺口                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔴 Critical (阻塞发布)                                          │
│  └── 全部完成 ✅                                                 │
│                                                                 │
│  🟡 Important (提升体验)                                         │
│  ├── Auto-updater (自动更新) - 待实现                           │
│  ├── Deep links (nemt:// 协议) - 待实现                         │
│  ├── 本地通知系统 - 已部分实现                                    │
│  ├── 全局快捷键 - 已部分实现                                      │
│  └── 崩溃报告 - 待实现                                           │
│                                                                 │
│  🟢 Nice to have (工程化)                                        │
│  ├── 单元测试 / E2E 测试 - 已配置框架                             │
│  ├── CI/CD 集成 - 待完善                                         │
│  ├── Build 优化 - 待完善                                         │
│  └── 文档完善 - 待完善                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、执行计划 (30 步)

### Phase 1: 核心 IPC 通道 (Step 1-8)

#### Step 1: 完善 Python IPC Handlers
**目标**: 在 main.ts 中注册完整的 Python 通信通道

```typescript
// main.ts 需要添加的 handlers:
'python:execute'    // 执行 Python 命令
'python:getStatus'  // 获取 Python 进程状态
'python:start'       // 启动 Python 子进程
'python:stop'        // 停止 Python 子进程
'python:restart'     // 重启 Python 子进程
```

#### Step 2: 实现 Python 子进程管理
**目标**: 创建 PythonProcessManager 类

```
职责:
├── spawn(): 启动 Python 进程
├── kill(): 停止进程
├── restart(): 重启进程
├── send(command): 发送命令
├── onOutput(callback): 输出回调
└── getStatus(): 进程状态
```

#### Step 3: 完善 electron_bridge.py
**目标**: 实现 JSON-RPC over stdin/stdout

```python
# nemt_os/nemt/container/electron_bridge.py
class ElectronBridge:
    - read_commands()  # 读取主进程命令
    - write_response() # 写入响应
    - execute_command() # 执行命令
    - 事件: setup, execute, cleanup
```

#### Step 4: 完善 Preload API
**目标**: 实现所有声明的 API

```typescript
// 已在 preload.ts 声明但未实现的:
- python.execute()
- python.getStatus()
- python.onLog()
- python.onError()
- python.onStatus()
- file.save()
- data.fetchMarketData()
- system.getStats()
```

#### Step 5: 数据持久化配置
**目标**: 配置 electron-store

```typescript
// 存储配置:
{
  "userPreferences": { ... },
  "recentFiles": [...],
  "windowState": { ... },
  "strategyCache": { ... }
}
```

#### Step 6: IPC 错误处理
**目标**: 统一的错误处理机制

```
- 超时处理 (30s timeout)
- 重试机制 (3 retries)
- 断线重连
- 错误日志记录
```

#### Step 7: Python 进程监控
**目标**: 健康检查与自动恢复

```
- 定期 ping/pong
- 进程崩溃检测
- 自动重启策略
```

#### Step 8: 通道集成测试
**目标**: 验证所有 IPC 通道工作正常

```
测试用例:
- Python 启动/停止
- 命令执行与响应
- 错误传播
- 并发请求
```

---

### Phase 2: 桌面原生功能 (Step 9-16)

#### Step 9: 全局快捷键
**目标**: 全局快捷键支持

```typescript
// 快捷键配置:
CmdOrCtrl+Shift+N  // 新建模拟
CmdOrCtrl+Shift+S  // 快速保存
CmdOrCtrl+Shift+R  // 重新运行
F7                 // 噪声扫描
F8                 // 非线性扫描
```

#### Step 10: Deep Links (nemt://)
**目标**: 支持 URL 协议打开应用

```typescript
// 注册协议: nemt://
// 支持的 URL:
// - nemt://open?file=path
// - nemt://strategy/id
// - nemt://backtest/id
```

#### Step 11: 本地通知
**目标**: 系统通知支持

```typescript
interface NotificationOptions {
  title: string;
  body: string;
  icon?: string;
  silent?: boolean;
  urgency?: 'low' | 'normal' | 'critical';
}
```

#### Step 12: 文件关联
**目标**: 注册文件类型关联

```json
// Windows:
".nemt" -> NEMT Simulator
".csv"  -> NEMT Simulator (可选)
```

#### Step 13: 拖放支持
**目标**: 支持拖放文件

```
支持的文件:
- .csv (市场数据)
- .json (策略配置)
- .nemt (NEMT 项目文件)
```

#### Step 14: 系统信息面板
**目标**: 资源监控 UI

```
显示:
- CPU 使用率
- 内存占用
- Python 进程状态
- 网络延迟
```

#### Step 15: 自动更新配置
**目标**: electron-updater 集成

```typescript
// 更新流程:
1. 检查更新 (启动时 + 定时)
2. 下载更新 (后台)
3. 提示用户安装
4. 自动安装 (下次启动)
```

#### Step 16: 崩溃报告
**目标**: 崩溃收集与报告

```
收集:
- 堆栈跟踪
- 系统信息
- 用户操作记录
- 上传到分析服务 (可选)
```

---

### Phase 3: 测试与 CI/CD (Step 17-23)

#### Step 17: 单元测试框架
**目标**: Jest + testing-library

```bash
# 测试覆盖目标:
- WindowManager: 90%
- MenuManager: 85%
- IPCClient: 90%
- TrayManager: 80%
```

#### Step 18: E2E 测试
**目标**: Playwright 集成测试

```
测试场景:
- 应用启动流程
- 窗口操作
- 菜单功能
- IPC 通信
- 模拟运行
```

#### Step 19: CI 配置
**目标**: GitHub Actions

```yaml
# 工作流:
- Lint (ESLint)
- Type check (tsc)
- Unit tests
- E2E tests
- Build
- Release
```

#### Step 20: 构建优化
**目标**: 优化构建速度

```
优化:
- 增量编译
- 缓存依赖
- 并行构建
- 产物压缩
```

#### Step 21: 多平台构建
**目标**: Windows + macOS + Linux

```bash
# 构建目标:
Windows: .exe (NSIS), .msi
macOS:   .dmg, .pkg
Linux:   .AppImage, .deb, .rpm
```

#### Step 22: Code Signing
**目标**: 应用签名

```
Windows: 代码签名证书
macOS:   Apple Developer ID + Notarization
```

#### Step 23: 发布配置
**目标**: GitHub Releases 集成

```
- 自动生成 Release Notes
- 上传构建产物
- 生成校验和
- 预发布标签
```

---

### Phase 4: 文档与完善 (Step 24-30)

#### Step 24: API 文档
**目标**: 完整的 IPC API 文档

```
文档内容:
- 每个通道的请求/响应格式
- 错误代码说明
- 示例代码
```

#### Step 25: 开发者文档
**目标**: 开发指南

```
内容:
- 环境搭建
- 调试技巧
- 常见问题
- 贡献指南
```

#### Step 26: 用户手册
**目标**: 用户使用指南

```
内容:
- 功能介绍
- 操作教程
- 配置说明
- 快捷键列表
```

#### Step 27: 架构图更新
**目标**: 更新架构文档

```
更新:
- 模块关系图
- 数据流图
- 序列图
```

#### Step 28: 性能优化
**目标**: 优化内存与启动速度

```
优化点:
- 懒加载模块
- 内存泄漏修复
- 启动画面
- 预加载关键资源
```

#### Step 29: 安全审计
**目标**: 安全检查

```
检查:
- contextIsolation
- nodeIntegration
- Preload 沙箱
- CSP 配置
```

#### Step 30: 集成测试
**目标**: 端到端验证

```
验证:
- 完整启动流程
- Go Gateway 集成
- Python 子进程
- Web 前端通信
```

---

## 三、关键里程碑

```
Week 1 (Step 1-8)   │████████████████████│ Phase 1 完成
Week 2 (Step 9-16)   │████████████████████│ Phase 2 完成
Week 3 (Step 17-23)  │████████████████████│ Phase 3 完成
Week 4 (Step 24-30)  │████████████████████│ Phase 4 完成
                     │                     │
                     └─────────────────────┘
                          4 周完成
```

---

## 四、优先级矩阵

```
        Impact
          │
High      │  [Auto-updater]  [Crash Report]
          │  [Data Persist]  [CI/CD]
          │
Medium    │  [Deep Links]    [Multi-platform]
          │  [Shortcuts]     [Code Signing]
          │
Low       │  [File Assoc]   [Notifications]
          │  [Drag & Drop]   [Documentation]
          │
          └─────────────────────────────
                      Effort
```

---

## 五、技术债务

| 债务项 | 优先级 | 预估时间 | 说明 |
|--------|--------|----------|------|
| IPC 通道缺失 | P0 | 2h | 阻塞所有 Python 通信 |
| Python 进程管理 | P0 | 4h | 核心功能 |
| 数据持久化 | P1 | 2h | 用户体验 |
| Auto-updater | P1 | 3h | 生产必需 |
| 测试覆盖 | P2 | 8h | 长期质量 |
| 文档完善 | P2 | 4h | 易用性 |

---

## 六、成功标准

### 6.1 功能标准

- [ ] Python 子进程可以正常启动/停止/通信
- [ ] 所有 preload API 正常工作
- [ ] 数据可以正确持久化
- [ ] 全局快捷键响应
- [ ] Deep links 可以打开应用

### 6.2 质量标准

- [ ] 单元测试覆盖率 >= 80%
- [ ] E2E 测试覆盖核心流程
- [ ] CI/CD 全部通过
- [ ] 多平台构建成功

### 6.3 体验标准

- [ ] 启动时间 < 5s
- [ ] 内存占用 < 300MB
- [ ] 无崩溃报告 (48h)
- [ ] 文档完整

---

## 七、快速开始

### Step 1: 验证当前状态

```bash
cd electron
npm install
npm run typecheck
```

### Step 2: 添加 IPC 通道

编辑 `electron/src/main.ts`，添加:

```typescript
// Python handlers (Step 1)
ipcMain.handle('python:execute', async (_, command, args) => {
  return ipcClient.executePython(command, args);
});

ipcMain.handle('python:getStatus', async () => {
  return ipcClient.getPythonStatus();
});
```

### Step 3: 运行测试

```bash
npm run dev:electron
```

---

**文档版本**: v1.0
**创建日期**: 2026-05-04
**维护者**: NEMT Lab
