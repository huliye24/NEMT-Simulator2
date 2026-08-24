# NEMT Simulator - Complete Electron App Docker Image
# 本地构建: docker build -t nemt-simulator .
# 保存镜像: docker save nemt-simulator -o nemt-simulator.tar
# 上传到云: scp nemt-simulator.tar root@42.51.42.123:/
# 云端加载: docker load -i nemt-simulator.tar
# 云端运行: docker run -p 3000:3000 -p 9222:9222 nemt-simulator

FROM node:20-slim as builder

# 安装依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制 package.json
COPY electron/package.json ./
COPY web/package.json ./web/ 2>/dev/null || true

# 安装 Node 依赖
RUN npm install -g npm@latest && \
    npm install

# 安装 Python 依赖
RUN pip3 install --no-cache-dir \
    fastapi \
    uvicorn \
    websockets \
    aiohttp \
    pandas \
    numpy

# 复制前端源码
COPY electron/ ./

# 复制后端源码
COPY nemt_os/ ./nemt_os/
COPY web/ ./web/ 2>/dev/null || mkdir -p web
COPY backtest/ ./backtest/ 2>/dev/null || mkdir -p backtest

# 构建 Electron (no bundling, just verify setup)
RUN if [ -f "package.json" ]; then \
    npm run build:web 2>/dev/null || echo "Skipping build"; \
    fi

# =============================================================================
# 运行阶段
# =============================================================================
FROM node:20-slim

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libgtk-3-0 \
    libnotify4 \
    libnss3 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    libatspi2.0-0 \
    libdrm2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# 从构建阶段复制
COPY --from=builder /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# Python 依赖
RUN pip3 install --no-cache-dir \
    fastapi \
    uvicorn \
    websockets \
    aiohttp \
    pandas \
    numpy

# 环境变量
ENV DISPLAY=:99
ENV NODE_ENV=production
ENV NEMT_HOME=/app

# 端口
EXPOSE 3000 9222 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# 启动方式选择
# 1. Electron 图形界面 (需要 X11/VNC)
# ENTRYPOINT ["npm", "run", "start:electron"]
# 
# 2. Web 模式 (推荐，无头运行)
CMD ["python3", "-m", "uvicorn", "nemt_os.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
