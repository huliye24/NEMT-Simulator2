# 常用命令
> Tech Lead Agent 常用脚本和命令

## 一、任务管理

### 1.1 创建新任务

```bash
# 创建新任务 (使用模板)
python TechLead_Resources/SCRIPTS/create_task.py --type feature --name "新功能"

# 手动创建
# 编辑 TechLead_Resources/TASKS.md
```

### 1.2 扫描停滞任务

```bash
python TechLead_Resources/SCRIPTS/scan_tasks.py
```

输出示例:
```
📋 扫描任务: TASKS.md
   找到 12 个任务

⚠️ 停滞任务 (2 个):

- TASK-003: 3 天未更新
- TASK-007: 5 天未更新
```

### 1.3 查看任务状态

```bash
# 使用 grep
grep -E "^\| TASK-" TASKS.md

# 或查看表格
cat TASKS.md | grep "| 状态"
```

## 二、代码审查

### 2.1 获取待审查 PR

```bash
# 需要设置 GITHUB_TOKEN
export GITHUB_TOKEN=your_token
python TechLead_Resources/SCRIPTS/fetch_prs.py
```

### 2.2 审查检查清单

参见 `CODE_REVIEW_GUIDELINES.md`

## 三、报告生成

### 3.1 生成周报

```bash
python TechLead_Resources/SCRIPTS/generate_weekly_report.py
```

### 3.2 查看覆盖率

```bash
# Python 覆盖率
cd quant-sync-server
pytest --cov=services --cov-report=html

# 打开报告
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

## 四、Git 操作

### 4.1 创建功能分支

```bash
# 创建并切换
git checkout -b feature/TASK-123-name

# 推送
git push -u origin HEAD
```

### 4.2 查看分支

```bash
# 列出所有分支
git branch -a

# 查看当前分支
git branch --show-current

# 查看最新提交
git log --oneline -5
```

### 4.3 整理提交历史

```bash
# 交互式 rebase
git rebase -i HEAD~3

# Squash merge 到 main
git checkout main
git merge --squash feature/branch-name
```

## 五、测试

### 5.1 运行测试

```bash
# Python
cd quant-sync-server
pytest

# 带覆盖率
pytest --cov=services --cov-report=term-missing

# 单个文件
pytest services/test_capital_node.py

# Watch 模式
pytest --watch

# TypeScript
cd web
npm test
```

### 5.2 测试模板

```bash
# 运行特定测试类
pytest -k TestCapitalNode

# 运行特定测试
pytest -k "test_allocate"
```

## 六、代码质量

### 6.1 Lint 检查

```bash
# Python
cd quant-sync-server
black --check .
pylint services/

# TypeScript
cd web
npm run lint
npm run lint:fix
```

### 6.2 类型检查

```bash
# Python
mypy services/

# TypeScript
npx tsc --noEmit
```

## 七、开发服务

### 7.1 启动服务

```bash
# Python API Server
cd quant-sync-server
python main.py

# Web 前端
cd web
npm run dev

# Electron
cd web
npm run electron:dev
```

### 7.2 Docker

```bash
# 启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down

# 重启特定服务
docker-compose restart api
```

## 八、环境管理

### 8.1 Python 虚拟环境

```bash
# 创建
python -m venv venv

# 激活 (Windows)
.\venv\Scripts\activate

# 激活 (Linux/Mac)
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 8.2 更新依赖

```bash
# Python
pip install -r requirements.txt --upgrade

# Node.js
cd web
npm update
```

## 九、快捷脚本

### 9.1 tl 命令 (Bash)

添加以下别名到 `.bashrc` 或 `.zshrc`:

```bash
alias tl-scan='python TechLead_Resources/SCRIPTS/scan_tasks.py'
alias tl-prs='python TechLead_Resources/SCRIPTS/fetch_prs.py'
alias tl-report='python TechLead_Resources/SCRIPTS/generate_weekly_report.py'
alias tl-test='cd quant-sync-server && pytest --cov=services'
```

使用:
```bash
tl-scan    # 扫描停滞任务
tl-prs     # 查看待审查 PR
tl-report  # 生成周报
tl-test    # 运行测试
```

## 十、常见操作

### 10.1 提交代码

```bash
git add .
git commit -m "feat(scope): description"
git push
```

### 10.2 更新 main 分支

```bash
git checkout main
git pull origin main
git checkout -
git rebase main
```

### 10.3 查看状态

```bash
# Git 状态
git status

# 工作目录
ls -la
```

---

*创建时间: 2026-04-19*
*最后更新: 2026-04-19*
