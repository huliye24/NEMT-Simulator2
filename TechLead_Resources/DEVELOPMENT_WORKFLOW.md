# 开发流程
> 从任务领取到代码合并的完整流程

## 一、任务领取

### 1.1 获取任务

1. **查看 TASKS.md**: 从任务清单中选取优先级最高且无依赖的任务
2. **确认理解**: 确保理解任务目标和验收标准
3. **评估工作量**: 如有疑问，与 Tech Lead 确认

### 1.2 任务状态更新

```
状态流转: 待办 → 进行中
```

在任务卡片中添加:
- 负责人
- 预计完成时间
- 开始时间

## 二、分支创建

### 2.1 分支命名规范

```
<type>/<issue-id>-<short-description>

示例:
feature/123-capital-allocation
fix/456-order-execution
chore/update-deps
refactor/789-risk-module
```

### 2.2 分支类型

| 类型 | 用途 | 生命周期 |
|------|------|----------|
| `feature/` | 新功能开发 | 1-2 周 |
| `fix/` | Bug 修复 | 1-3 天 |
| `refactor/` | 重构 | 1-2 周 |
| `chore/` | 维护任务 | 1 天 |
| `hotfix/` | 紧急修复 | 1 天 |

### 2.3 创建分支

```bash
# 从最新 main 分支创建
git checkout main
git pull origin main
git checkout -b feature/123-task-name
```

## 三、编码

### 3.1 编码规范

遵循 `CODE_STANDARDS.md` 中的规范:
- 代码格式化 (Black / Prettier)
- 命名规范 (Python: snake_case, TS: camelCase)
- 类型注解 (TypeScript: interface, Python: type hints)
- 错误处理 (具体异常 + 上下文)
- 日志记录 (结构化日志)

### 3.2 开发自测

编码过程中:
- 编写单元测试
- 本地运行测试 `pytest` / `npm test`
- 确保 Lint 通过

### 3.3 提交代码

```bash
# 添加修改的文件
git add path/to/changed/file.py

# 提交 (遵循 Conventional Commits)
git commit -m "feat(module): add new feature

- 添加 xxx 功能
- 修复 yyy 问题

Closes #123"
```

### 3.4 Commit 规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档
- `style`: 格式（不影响功能）
- `refactor`: 重构
- `test`: 测试
- `chore`: 维护

## 四、提交 PR

### 4.1 PR 创建

1. **推送分支**: `git push -u origin feature/123-name`
2. **创建 PR**: 使用 GitHub UI 或 CLI
3. **填写模板**:

```markdown
## PR 描述

### 做了什么
-

### 为什么做
-

### 如何测试
-

### 影响范围
-

## 审查清单
- [ ] CI 通过
- [ ] 测试通过
- [ ] 文档已更新
```

### 4.2 PR 标题规范

```
<type>(<scope>): <简短描述>

示例:
feat(capital-node): add phase-driven allocation
fix(risk): correct ATR calculation
```

## 五、代码审查

### 5.1 审查流程

1. **Tech Lead 收到通知**: GitHub 自动通知
2. **执行审查**: 按照 `CODE_REVIEW_GUIDELINES.md` 检查
3. **给出结论**:
   - ✅ **批准** (Approved)
   - ⚠️ **需要修改** (Changes Requested)
   - ❌ **拒绝** (Rejected)

### 5.2 审查时间要求

| 场景 | 时间要求 |
|------|----------|
| 普通 PR | < 4 小时 |
| 紧急修复 | < 1 小时 |
| 大型重构 | < 24 小时 |

### 5.3 常见审查意见

参见 `COMMON_CR_ISSUES.md`

## 六、合并

### 6.1 合并条件

- ✅ 所有 CI 检查通过
- ✅ 至少 1 人批准
- ✅ 无未解决的审查意见
- ✅ 测试覆盖率达标

### 6.2 合并策略

**Squash Merge** (推荐):
- 将多个 commit 合并为一个
- 保持历史整洁

**Merge Commit**:
- 保留完整历史
- 用于大型功能分支

### 6.3 合并后

1. 删除源分支
2. 更新相关任务状态
3. 如需要，部署到测试环境

## 七、Hotfix 流程

### 7.1 紧急修复

```
1. 从 main 创建 hotfix/xxx 分支
2. 快速修复
3. 提交 PR (标注 hotfix)
4. Tech Lead 优先审查
5. 合并后部署
```

### 7.2 同步修复

将修复同步到其他活跃分支 (cherry-pick)

## 八、工具和脚本

### 8.1 常用命令

```bash
# 创建任务分支
git checkout -b feature/TASK-123-name

# 查看状态
git status

# 交互式 rebase (整理 commit)
git rebase -i HEAD~3

# 更新 main
git fetch origin
git rebase origin/main
```

### 8.2 CI 检查

每次 push 自动运行:
- 单元测试
- Lint 检查
- 类型检查
- 构建验证

## 九、流程图

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  领取任务 │───→│ 创建分支 │───→│   编码   │───→│  提交   │
└─────────┘    └─────────┘    └─────────┘    └────┬────┘
                                                  │
                                                  ▼
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│   合并   │◀───│  审查通过 │◀──│  审查   │◀───│  创建PR │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

---

*创建时间: 2026-04-19*
*最后更新: 2026-04-19*
