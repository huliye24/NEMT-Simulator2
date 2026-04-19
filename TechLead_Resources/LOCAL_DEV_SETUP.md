# 本地开发环境
> 新成员或 Agent 搭建本地开发环境的步骤

## 一、环境要求

### 1.1 必需软件

| 软件 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 后端开发 |
| Node.js | 18+ | 前端开发 |
| Git | 2.30+ | 版本控制 |
| Docker | 24+ | 容器化 |

### 1.2 可选软件

| 软件 | 版本 | 用途 |
|------|------|------|
| VS Code | Latest | IDE |
| PyCharm | Latest | Python IDE |
| Cursor | Latest | AI 辅助编程 |
| Obsidian | Latest | 知识管理 |

## 二、环境搭建

### 2.1 克隆代码

```bash
# SSH
git clone git@github.com:huliye24/NEMT-Simulator2.git

# HTTPS
git clone https://github.com/huliye24/NEMT-Simulator2.git

cd NEMT-Simulator2
```

### 2.2 Python 环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活 (Windows)
.\venv\Scripts\activate

# 激活 (Linux/Mac)
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt  # 如果存在
```

### 2.3 Node.js 环境

```bash
cd web

# 安装依赖
npm install

# 复制环境变量
cp .env.example .env
```

### 2.4 配置环境变量

创建 `quant-sync-server/.env`:

```bash
# Notion API
NOTION_TOKEN=your_notion_token

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Go Server
GOSERVER_HOST=localhost
GOSERVER_PORT=8080
```

## 三、运行服务

### 3.1 Python API Server

```bash
cd quant-sync-server

# 开发模式
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --port 8080
```

### 3.2 Web 前端

```bash
cd web

# 开发模式
npm run dev

# 构建生产版本
npm run build
```

### 3.3 Electron (可选)

```bash
cd web

# 启动 Electron
npm run electron:dev
```

### 3.4 Docker (推荐)

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

## 四、运行测试

### 4.1 Python 测试

```bash
cd quant-sync-server

# 运行所有测试
python -m pytest

# 运行单个文件
python -m pytest services/test_capital_node.py

# 带覆盖率
python -m pytest --cov=services --cov-report=html

# Watch 模式
python -m pytest --watch
```

### 4.2 TypeScript 测试

```bash
cd web

# 运行测试
npm test

# 覆盖率
npm test -- --coverage

# Watch 模式
npm test -- --watch
```

## 五、代码质量

### 5.1 Lint

```bash
# Python
cd quant-sync-server
black .
pylint services/

# TypeScript
cd web
npm run lint
npm run lint:fix
```

### 5.2 类型检查

```bash
# Python
cd quant-sync-server
mypy services/

# TypeScript
cd web
npx tsc --noEmit
```

### 5.3 格式化

```bash
# Python
cd quant-sync-server
black .
isort .

# TypeScript
cd web
npm run format
```

## 六、调试

### 6.1 Python 调试

VS Code 配置 `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal"
        }
    ]
}
```

### 6.2 Node.js 调试

```bash
# 使用 Chrome DevTools
node --inspect-brk index.js

# 或在 VS Code 中
npm run debug
```

### 6.3 日志

```python
# 在代码中添加日志
import logging

logger = logging.getLogger(__name__)
logger.info("Debug info")
logger.error("Error occurred")
```

## 七、常见问题

### Q: pip install 失败？

```bash
# 升级 pip
python -m pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: npm install 失败？

```bash
# 清理缓存
npm cache clean --force

# 重新安装
rm -rf node_modules package-lock.json
npm install
```

### Q: 端口被占用？

```bash
# Windows
netstat -ano | findstr :8080
taskkill /PID <pid> /F

# Linux
lsof -i :8080
kill -9 <pid>
```

## 八、更新环境

### 8.1 拉取最新代码

```bash
git checkout main
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade
npm install
```

### 8.2 数据库迁移

```bash
# 运行迁移
python manage.py migrate

# 或
alembic upgrade head
```

## 九、IDE 推荐配置

### 9.1 VS Code 扩展

```
Python
Pylance
ESLint
Prettier
GitLens
```

### 9.2 保存时自动格式化

```json
// .vscode/settings.json
{
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter"
    }
}
```

---

*创建时间: 2026-04-19*
*最后更新: 2026-04-19*
