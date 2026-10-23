# NEMT 云端开发状态

更新时间：2026-10-23

## 总目标

先建立一个稳定、可测试、可扩展的量化交易框架，再持续增加交易策略。系统复杂度应主要随策略数量、策略组合和计算规模增长，而不是在早期堆叠无必要的代码与基础设施。

## 核心路线

1. 本地 Codex 是控制面和代码事实源。
2. AWS 宁夏 CPU 节点是受控计算节点，用于测试、批量回测、参数优化、Walk-forward、蒙特卡洛和 MATLAB 实验。
3. Git 管理版本和合并；Mutagen 将经过过滤的运行代码单向投送到隔离目录；大型数据和结果后续交给 rclone/S3。
4. DeepSeek 只作为可选分析助手，不直接控制主代码、凭据或实盘交易。
5. 开发顺序为：框架可运行 → 环境基线 → 离线测试 → 性能基准 → 策略插件化 → 增加策略 → 模拟盘 → 风控验证 → 实盘。

## 安全边界

- 云端同步目标：`/home/ubuntu/nemt-runs/current`
- 云端原项目：`/home/ubuntu/nemt-studio`，禁止覆盖。
- Mutagen 使用 `one-way-safe`，默认暂停，检查后才恢复。
- 不同步 `.git`、环境变量、密钥、Token、数据库、虚拟环境、缓存、构建产物和大型数据。
- 环境配置不得连接交易所、下单、执行数据库迁移或启动实盘服务。

## 当前状态

- SSH 已连接到当前 AWS 节点。
- `/home/ubuntu/nemt-studio` 已制作完整 Git bundle 并在本地验证。
- 首次受控同步已完成：475 个文件，约 4.8 MB。
- 初始 SHA-256 清单：`/home/ubuntu/nemt-runs/baselines/initial-sync-20261023.sha256`。
- Mutagen 会话 `nemt-aws-worktree` 当前暂停。
- 云端硬件：8 vCPU、30 GiB 内存、约 204 GB 可用磁盘。
- Python 3.12.3 项目隔离环境已建立：`/home/ubuntu/nemt-runs/.venv`。
- Python 依赖已通过本地 wheelhouse 离线安装，`pip check` 无破损依赖。
- 可复用 wheelhouse 位于本地 `E:\亚马逊云\宁夏CPU节点\wheelhouse\py312-linux-x86_64-20261023`，云端副本位于 `/home/ubuntu/nemt-runs/wheelhouse/py312-linux-x86_64-20261023`。
- wheelhouse 归档 SHA-256：`6829951b19191c3314bfd935127ec1900915440ea9e50b09bf3aed51b3aea593`。
- Node.js 24.14.0 已作为 NEMT 任务级运行时验证；系统默认 Node.js 18 不用于本项目。
- Web 依赖已通过本地 npm cache 离线安装：402 个包，Linux x64 SWC 已验证。
- 可复用 npm cache 位于本地 `E:\亚马逊云\宁夏CPU节点\npm-offline\cache-20261023`，归档 SHA-256 为 `28a3cd1309d43e63683031485f022e0bcce76436ce6734e4560dc7310346a282`。
- MATLAB R2023b Update 11 已安装，当前无活动会话。
- Mihomo VPN/TUN 已验证无法建立可用外网 TLS 连接，保持关闭；SSH bypass 有效。云端依赖应优先由本地下载、校验后上传。

## 当前阶段

配置并验证云端隔离开发环境：

1. 保存完整环境版本清单。
2. 执行纯离线、无交易、无数据库迁移的测试。
3. 处理测试暴露的真实代码问题，保持环境问题与代码问题分离。

## 首轮环境验证结果

- Python 核心依赖导入：通过。
- `nemt_os` pytest 收集：53 项，通过。
- `backend` pytest 收集：65 项，通过。
- TypeScript `tsc --noEmit`：通过。
- ESLint：未通过，4 个错误、19 个警告。
- ESLint 的 4 个错误均为现有 React 代码规则问题：3 处 effect 内同步状态更新、1 处 render 初始化调用 `Date.now()`；不是云端环境故障。
- npm 报告 3 个既有弃用警告；暂不擅自升级锁文件。

## 首轮离线测试基线

- 研究/策略测试：31/31 通过，约 3.4 秒。
- 后端测试：65/65 通过，约 51.9 秒。
- 旧 NEMT 测试：12/22 通过，10 项失败。
- 总计：108/118 通过。
- FastAPI 0.109 / Starlette 0.35 与 httpx 0.28 不兼容；云端隔离环境已固定为 httpx 0.27.2，`pip check` 通过。根依赖声明后续应在方向锁允许时正式增加 `<0.28` 约束。
- 旧 NEMT 测试需使用 `pytest -s`，因为 `tests/test_nemt.py` 在导入阶段直接调用 `sys.stdout.reconfigure()`，与 pytest 输出捕获冲突。
- 10 项 NEMT 失败来自两个跨平台路径问题，而非云端环境故障：
  - `nemt/emt_core/__init__.py` 导入不存在的 `emt_pipeline`，实际文件名为 `nemt_pipeline.py`。
  - 测试导入 `nemt.nemt_core`，实际目录名为 `nEMT_core`；Windows 大小写不敏感会掩盖此问题，Linux 会正确失败。
- 上述 NEMT 核心路径不在当前方向锁允许修改范围内，本阶段只记录，不越权修复。

## 后续策略路线

环境和框架通过后，优先验证统一策略接口、数据输入、回测、指标、风控和结果输出，再增加海龟交易法等策略。只有批量策略和参数搜索形成稳定负载后，才扩展服务器和算力。

## 香港公网入口

- 香港节点 SSH 别名：`moodify-global-engine`，公网 IP：`103.144.246.242`。
- `sonviaf.service` 已在 `127.0.0.1:4173` 正常提供站点，Nginx、80/443 端口和防火墙规则正常。
- 已新增独立 Nginx 虚拟主机 `/etc/nginx/sites-available/sonviaf.com`，代理 `sonviaf.com` 与 `www.sonviaf.com` 到 `127.0.0.1:4173`。
- Nginx 配置检测通过，本机 Host 路由和公网强制解析测试均返回 HTTP 200。
- DNSPod 权威解析已验证：根域名和 `www` 均指向 `103.144.246.242`。本机查询曾出现的 `198.18.0.138/139` 是本地代理的 Fake-IP 映射，不是 DNSPod 真实记录。
- 已用 Certbot 为 `sonviaf.com` 和 `www.sonviaf.com` 签发并部署 Let's Encrypt 证书，有效期至 2027-01-21。
- HTTP 已自动 301 跳转到 HTTPS；两个 HTTPS 地址均返回 HTTP 200。
- `certbot.timer` 已启用并处于运行状态，负责证书自动续期。
