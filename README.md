# NEMT — Non-Equilibrium Market Theory
非平衡市场理论 · 市场研究与交易策略知识库

> **Research only. No executable trading software.**  
> 本仓库用于提出、修订与检验市场理论及交易策略假设，不提供交易程序、交易所接口、回测服务、自动下单或可执行的软件产品。

## 研究定位

NEMT 的研究核心是：市场是否呈现可定义、可观测、可重复验证的非平衡状态？如果可以，这些状态是否具有独立于朴素基准的可检验预测或风险管理价值？

本项目区分三个层次：
1. **理论（Theory）**：定义概念、变量、方程、适用边界与反证条件。
2. **假设与证据（Evidence）**：事先登记可证伪命题，记录数据来源与实验结论；接受 FAIL / INCONCLUSIVE / BLOCKED。
3. **策略规范（Strategy Specifications）**：以自然语言和数学表达式描述策略、风险、适用市场、成本假设、样本外验证标准；不发布可执行的策略代码。

## 目录

- [theory/book/](theory/book/)：NEMT《非平衡市场与宏观趋势调度理论》原书稿（研究资产，保留章节顺序）
- [theory/principles/](theory/principles/)：风险优先、策略生命周期等研究思想
- [theory/notes/](theory/notes/)：术语和建模备忘
- [experiments/preregistration/](experiments/preregistration/)：已制定的数学及样本外实验方案（不含运行程序）
- [experiments/reports/](experiments/reports/)：已有研究报告文本，须独立核对原始证据
- [strategies/](strategies/)：假设性的策略候选与填写模板
- [archive/legacy/](archive/legacy/)：历史研究记录，**不代表当前已验证结论**
- [governance/](governance/)：可证伪性、证据分类、出版审查与仓库边界

## 策略与理论的边界

* 文档中的指标、参数、信号和阶段划分均为研究对象，不应被解读为已获证实。
* 回测收益、示例仓位或历史策略清单不构成投资建议，也不代表可复制的未来表现。
* 研究者可以引用 Emergenzix 的试验报告，但必须明确版本、数据集、时间范围、手续费/滑点、样本外划分及审阅状态。
* **NEMT 无权部署策略，更不能直接连接交易账户。**

## 与 Emergenzix 的关系

- **NEMT**（本文档）：提出理论、定义策略、评价证据。
- **[Emergenzix](https://github.com/huliye24/emergenzix)**：承担代码实现、实验执行、回测、模拟交易、风控和产品部署。
- 由理论流向产品的是**经版本化评审的策略规范与证据引用**，不是仓库内可直接运行的交易程序。

## 来源与整理

本文档快照基于 [NEMT-Simulator2](https://github.com/huliye24/NEMT-Simulator2) 于 2026-10-26 的公开默认分支材料筛选。历史文本原作者、日期、内部参考以及不同阶段状态应予保留。详细见 [MIGRATION.md](MIGRATION.md)。

**本分支是独立研究仓库的可审核导出快照，不是新 GitHub 仓库，也不是对原仓库 main 的清理。创建新的 NEMT-Theory 仓库时仅导入文件快照，不复制源仓库 Git 历史。**

## License

保留原项目已有的 GPL-3.0-only 许可证文本及历史 Apache-2.0 许可证说明。历史贡献及第三方内容仍受其原有授权约束，仓库迁移本身不改变版权归属。