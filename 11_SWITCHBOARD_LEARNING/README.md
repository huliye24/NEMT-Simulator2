# Switchboard 学习目录

## 目录说明

这个目录用于记录 Switchboard 预言机网络的学习过程和实践。

## 核心资源

### 官方文档
- 官网: https://switchboard.xyz
- 文档: https://docs.switchboard.xyz
- Explorer: https://explorer.switchboardlabs.xyz

### 代币信息
- 代币: SWTCH
- 合约地址: (待补充)
- 质押平台: stake.switchboard.xyz

## 学习路线图

### 阶段1: 了解基础
- [ ] 阅读官方文档
- [ ] 了解预言机工作原理
- [ ] 探索现有数据 feeds
- [ ] 了解 SWTCH 代币经济模型

### 阶段2: 质押体验
- [ ] 购买 SWTCH
- [ ] 在 Switchboard 质押
- [ ] 观察收益发放

### 阶段3: 技术深度
- [ ] 学习构建自定义 Feed
- [ ] 部署测试网 Feed
- [ ] 理解 Crank/Queue 机制
- [ ] 学习 Oracle Node 运营

### 阶段4: 差异化方向
- [ ] 创建波动率数据 Feed
- [ ] 整合 NEMT 分析能力
- [ ] 部署到主网

## 关键概念

### Oracle (预言机)
将链下数据引入链上的中间件服务。

### Feed (数据源)
提供特定数据 (如价格) 的数据源。

### Crank (曲柄)
执行排程机制，触发数据更新。

### Queue (队列)
Oracle 节点的工作队列。

### NCN (Node Consensus Network)
Switchboard 与 Jito 合作的节点共识网络。

## 收入模式

| 模式 | 要求 | 收益 |
|:---|:---|:---|
| 质押 | 购买 SWTCH | 年化 6-12% |
| Oracle Node | 运行节点 + 质押 | 每次响应奖励 |
| 自定义 Feed | 构建并部署 | 使用费分成 |

## 相关项目链接

- NEMT 分析: ../results/docs/
- 数据目录: ../data/
- 实验代码: ../experiments.py

## 更新日志

- 2026-04-12: 创建目录
