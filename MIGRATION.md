# NEMT Theory Migration / 研究仓库迁移说明

## 目标
将 NEMT-Simulator2 中的研究思想、论文、可证伪数学假设、实验预注册方案与纯文本策略规范整理为独立的 NEMT-Theory 仓库，与 Emergenzix 的软件实现解耦。

## 来源
源仓库：https://github.com/huliye24/NEMT-Simulator2
源分支：main
源提交：8582b66f3bff4b2aa6d2433399c6d3c4452761c9
整理日期：2026-10-26

## 迁移映射
- `docs/NEMT_Theory_EPUB/manuscript/chapters/` → `theory/book/chapters/`
- `NEMT_Vision/Principles/Risk_Above_Return.md` → `theory/principles/Risk_Above_Return.md`
- `docs/NEMT_CORE_MATH_EXPERIMENTS_20261017/` → `experiments/preregistration/core-math-20261017/`
- `docs/NEMT_NEXT_EXPERIMENTS_20261017/` 中的研究设计 → `experiments/preregistration/follow-up-20261017/`
- `docs/NEMT_MATLAB_Conclusions_EPUB/manuscript/chapters/01-conclusions.md` → `experiments/reports/matlab-conclusions.md`
- `docs/NEMT_NEXT_RESULTS_EPUB/manuscript/chapters/01-report.md` → `experiments/reports/follow-up-results.md`
- `results/docs/` 选定的旧研究文字 → `archive/legacy/`
- 新增的 `strategies/` 为待验证策略规范，而非运行代码。

## 明确不导入
- `electron/`, `web/`, `backend/`, `src/`, `services/`, `nemt_os/`, `quant-mvp/`
- `node_modules/`, 依赖安装产物、构建缓存、二进制包
- `*.py`, `*.m`, `*.go`, `*.ts`, `*.tsx`, `*.js`, Dockerfile, Compose, 交易凭据和账户配置
- 云端运行脚本、执行日志、数据库、原始大文件和其他软件工程资产

## 安全与历史
原仓库存在历史凭据清理风险；删除当前文件并不会从 Git 历史抹去秘密。**不得通过 GitHub fork / mirror / 保留提交历史的方式直接创建新研究库**。应以整理后的文件快照建立全新仓库和首次提交。核查并轮换曾泄露的凭据；如需清理旧历史，应由维护者另行执行专门流程。

## 建议步骤
1. 对本快照中的研究文件进行术语/版权/证据状态审核；
2. 在 `huliye24` 下建立空仓库 `NEMT-Theory`（不从旧库 fork）；
3. 将本快照作为**不含旧 .git 目录**的初始内容导入新库；
4. 为旧仓库添加迁移提示，后续可归档旧工程；
5. 在 Emergenzix 中维护到 NEMT-Theory 策略版本的引用，代码仅存在 Emergenzix。
