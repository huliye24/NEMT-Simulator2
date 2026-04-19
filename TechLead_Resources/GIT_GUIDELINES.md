# Git 规范
> 分支管理、Commit 规范、合并策略

## 一、分支模型

```
                    ┌─────────────┐
                    │    main     │ ← 生产环境
                    └──────┬──────┘
                           │ 合并
                    ┌──────┴──────┐
                    │ develop      │ ← 开发分支
                    └──────┬──────┘
                           │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────┴───────┐ ┌───────┴───────┐ ┌───────┴───────┐
│ feature/xxx  │ │ feature/yyy  │ │  bugfix/zzz  │
└──────────────┘ └──────────────┘ └───────────────┘
```

### 分支说明

| 分支 | 用途 | 保护状态 |
|------|------|----------|
| `main` | 生产环境代码 | 强制保护 |
| `develop` | 开发集成分支 | 建议保护 |
| `feature/*` | 新功能开发 | 无保护 |
| `bugfix/*` | Bug 修复 | 无保护 |
| `hotfix/*` | 紧急修复 | 无保护 |

## 二、分支命名

### 2.1 命名格式

```
<type>/<issue-id>-<short-description>
```

### 2.2 类型前缀

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feature/` | 新功能 | `feature/123-capital-allocation` |
| `bugfix/` | Bug 修复 | `bugfix/456-order-execution` |
| `hotfix/` | 紧急修复 | `hotfix/789-security-patch` |
| `refactor/` | 重构 | `refactor/101-risk-module` |
| `docs/` | 文档更新 | `docs/102-api-documentation` |
| `test/` | 测试编写 | `test/103-add-unit-tests` |
| `chore/` | 维护任务 | `chore/104-update-deps` |

### 2.3 示例

```bash
# Good
feature/123-add-capital-allocation
bugfix/456-fix-order-execution
hotfix/789-security-patch
refactor/101-improve-risk-module

# Bad
new-feature
fix-bug
123-feature
feature
```

## 三、Commit 规范

### 3.1 格式

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### 3.2 类型

| 类型 | 描述 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(capital): add phase allocation` |
| `fix` | Bug 修复 | `fix(risk): correct ATR calc` |
| `docs` | 文档更新 | `docs: update API docs` |
| `style` | 代码格式 | `style: format with black` |
| `refactor` | 重构 | `refactor: split large function` |
| `perf` | 性能优化 | `perf: cache results` |
| `test` | 测试 | `test: add unit tests` |
| `build` | 构建 | `build: update docker` |
| `ci` | CI/CD | `ci: add github actions` |
| `chore` | 维护 | `chore: update deps` |
| `revert` | 回退 | `revert: undo last change` |

### 3.3 作用域

| 作用域 | 描述 |
|--------|------|
| `capital` | 资金管理层 |
| `risk` | 风控模块 |
| `signal` | 信号模块 |
| `market` | 市场层 |
| `model` | 模型层 |
| `strategy` | 策略层 |
| `web` | Web 前端 |
| `api` | API 服务 |
| `docs` | 文档 |

### 3.4 示例

```bash
# Good commits
feat(capital): add PhaseDrivenCapitalManager
fix(risk): correct ATR calculation
docs(api): update endpoint documentation
refactor(signal): extract signal generator
test(capital): add allocation tests

# Bad commits
fix bug
update
WIP
asdf
123
```

### 3.5 Commit 模板

```bash
# ~/.gitmessage
# <type>(<scope>): <subject>
# 
# [optional body]
# 
# [optional footer: Closes #<issue>]
```

## 四、Commit Message 规范

### 4.1 Subject 规则

1. 使用祈使语气: "add" 而非 "added" / "adds"
2. 不以句号结尾
3. 长度 ≤ 50 字符
4. 描述做了什么，而非怎么做的

### 4.2 Body 规则

1. 解释**为什么**，而非**是什么**
2. 每行 ≤ 72 字符
3. 使用 bullet points 时用 `-`

### 4.3 Footer 规则

用于引用 Issue:
```
Closes #123
Fixes #456
Related to #789
```

## 五、合并策略

### 5.1 Feature 分支

```bash
# Squash Merge (推荐)
git checkout develop
git merge --squash feature/123-name
git commit -m "feat(scope): add feature"
```

### 5.2 Hotfix 分支

```bash
# Merge Commit
git checkout main
git merge --no-ff hotfix/789-name
git tag -a v1.2.1 -m "fix: urgent patch"
```

### 5.3 Rebase vs Merge

| 场景 | 推荐 |
|------|------|
| 整理 local commits | Rebase |
| 合并 feature 到 develop | Squash Merge |
| 同步 main 到 feature | Rebase |
| 紧急修复 | Merge Commit |

## 六、Tag 规范

### 6.1 版本格式

```
v<major>.<minor>.<patch>

示例:
v1.0.0  - 首次发布
v1.1.0  - 新功能 (向后兼容)
v1.1.1  - Bug 修复 (向后兼容)
v2.0.0  - 破坏性变更
```

### 6.2 Tag 命名

```bash
# Annotated Tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# Signed Tag
git tag -s v1.0.0 -m "Release version 1.0.0"
```

## 七、保护规则

### 7.1 main 分支

- 必须通过 CI
- 必须有人 review
- 禁止 force push
- 禁止删除

### 7.2 develop 分支

- 建议通过 CI
- 建议有人 review
- 禁止 force push

## 八、常见问题

### Q: 提交信息写错了怎么办？

```bash
# 最后一次提交
git commit --amend -m "correct message"

# 多次提交
git rebase -i HEAD~3
# 修改 pick 为 reword
```

### Q: 如何撤销已推送的 commit？

```bash
# 创建新 commit 撤销
git revert <commit-hash>

# 如果必须删除
git reset --hard <commit-hash>
git push --force-with-lease
```

---

*创建时间: 2026-04-19*
*最后更新: 2026-04-19*
