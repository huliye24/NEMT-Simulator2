# NEMT Simulator Web

非平衡市场理论模拟器 Web 界面

## 技术栈

- React 18
- TypeScript
- Vite
- Chart.js

## 本地开发

```bash
cd web
npm install
npm run dev
```

## 构建

```bash
npm run build
```

## Cloudflare Pages 部署

本项目配置了 GitHub Actions 自动部署到 Cloudflare Pages。

### 首次设置

1. Fork 本仓库到你的 GitHub 账号
2. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)
3. 进入 Workers & Pages → 创建应用程序 → Pages
4. 选择"连接到 GitHub"
5. 选择仓库 `nemt-simulator`
6. 构建命令: `npm run build`
7. 输出目录: `web/dist`
8. 点击"保存并部署"

### 自动部署

每次推送到 `main` 分支时，会自动触发构建和部署。

### 手动部署

```bash
# 本地构建
npm run build

# 使用 wrangler 部署到 Cloudflare Pages
npx wrangler pages deploy web/dist --project-name=nemt-simulator
```

## 项目结构

```
web/
├── src/
│   ├── App.tsx          # 主应用组件
│   ├── main.tsx        # 入口文件
│   ├── components/      # UI 组件
│   ├── utils/          # 工具函数 (NEMT核心算法)
│   └── types/          # TypeScript 类型定义
├── index.html
├── vite.config.ts
└── package.json
```

## 许可证

MIT
