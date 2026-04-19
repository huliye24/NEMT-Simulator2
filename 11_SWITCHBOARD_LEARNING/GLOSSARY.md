# Switchboard 术语表

## 核心概念

### Oracle (预言机)
- 定义: 将链下数据引入链上的中间件服务
- 作用: 打破区块链无法访问外部数据的限制
- 类型: 价格预言机、随机数预言机、天气预言机等

### Feed (数据源)
- 定义: 提供特定数据的聚合器
- 组成: Job + Data Source + Aggregator
- 示例: BTC/USD 价格 Feed

### Job (任务)
- 定义: 定义数据获取方式的指令
- 类型: HTTP Job、JSON Parse Job、Python Job
- 示例: 从CoinGecko获取BTC价格

### Data Source (数据源)
- 定义: 实际提供数据的来源
- 示例: CoinGecko API, Binance API
- 要求: 可靠性和稳定性

### Aggregator (聚合器)
- 定义: 聚合多个数据源的结果
- 作用: 提高数据的准确性和抗篡改性
- 机制: 取中位数、加权平均等

### Crank (曲柄)
- 定义: 执行排程机制，触发数据更新
- 作用: 定期唤醒 Oracle 更新数据
- 费用: 每次触发需要支付 SOL

### Queue (队列)
- 定义: Oracle 节点的工作队列
- 作用: 组织和管理 Oracle 任务分发
- 组件: Oracle Keys, 验证者集合

### Oracle Node (���言机节点)
- 定义: 运行预言机软件的服务器
- 作用: 执行 Jobs、提交数据
- 要求: 技术能力 + 质押保证金

---

## NCN 相关

### NCN (Node Consensus Network)
- 全称: Node Consensus Network
- 合作方: Switchboard + Jito
- 作用: 去中心化的节点验证网络

### svSWTCH (staked-vote SWTCH)
- 定义: 已质押的 SWTCH 代币
- 作用: 用于 NCN 投票和治理
- 收益: 参与网络运营的奖励

---

## 技术术语

### SPL Token
- 定义: Solana Program Library Token Standard
- 作用: Solana 上的代币标准
- 类似: Ethereum 的 ERC-20

### Solana RPC
- 定义: Remote Procedure Call 节点
- 作用: 提供链上数据的读取接口
- 类型: 公共 RPC、私有 RPC

### TEE (Trusted Execution Environment)
- 定义: 可信执行环境
- 作用: 硬件级别的安全隔离
- 示例: Intel SGX

### Heartbeat (心跳)
- 定义: Oracle 节点定期发送的存活信号
- 作用: 证明节点在线
- 周期: 通常几分钟一次

### Slashing (罚没)
- 定义: 对作恶节点的代币惩罚
- 作用: 经济激励确保诚实行为
- 后果: 质押代币被扣除

---

## 经济术语

### SWTCH
- 定义: Switchboard 的原生代币
- 作用: 治理 + 质押 + 奖励
- 供应: 总量 10 亿枚

### Epoch
- 定义: Solana 的时间周期
- 长度: 约 2-3 天
- 作用: 奖励发放周期

### 年化收益率 (APY)
- 定义: 年化收益率
- 计算: (收益/本金) × 100%
- 预期: 6-12%

### Delegation (委托)
- 定义: 将代币委托给 Oracle 节点
- 作用: 小额用户也能参与质押
- 收益: 分享节点运营奖励

---

## 操作术语

### Stake (质押)
- 定义: 将代币锁入协议
- 作用: 获得收益 + 参与治理

### Unstake (解除质押)
- 定义: 从协议中取出代币
- 时限: 需要等待解锁期

### Delegate (委托)
- 定义: 将质押权委托给其他人
- 作用: 专业化运营

### Revoke (撤销)
- 定义: 取消委托或权限
- 时限: 即时或等待期

---

## 项目特定

### Surge
- 定义: Switchboard 的极速数据流
- 特点: 毫秒级更新
- 用途: 高频交易场景

### Crossbar
- 定义: Switchboard 的高级工具
- 作用: 快速数据查询
- 适用: 开发者/专业用户

### Pythnet
- 定义: Pyth Network 的专用链
- 作用: 高速数据传输
- 注意: 与 Solana 主网分离

### pyth-agent
- 定义: Pyth 的数据发布代理软件
- 作用: 简化数据发布流程
- 要求: 需要第一方数据

---

## 相关项目

### Pyth Network
- 定位: 机构级价格预言机
- 特点: 高精度、低延迟
- 门槛: 机构专属

### Chainlink
- 定位: 多链预言机
- 特点: 去中心化、高安全性
- 生态: 最大预言机网络

### Band Protocol
- 定位: 跨链预言机
- 特点: 支持多链数据
- 代币: BAND

---

## 学习资源

### 官方文档
- 官网: https://switchboard.xyz
- 文档: https://docs.switchboard.xyz
- GitHub: https://github.com/switchboard-xyz

### 浏览器
- Explorer: https://explorer.switchboardlabs.xyz
- 用途: 查看 Feeds、节点、队列

### 社交媒体
- Twitter: @switchboardxyz
- Discord: Switchboard Community
- 用途: 获取最新动态

---

## 更新记录

- 2026-04-12: 初始创建
