# Dockerfile - BTC 数据采集器
# 构建: docker build -t btc-collector .

FROM golang:1.22-alpine AS builder

WORKDIR /app

# 安装依赖
RUN apk add --no-cache git

# 复制代码
COPY main.go go.mod go.sum ./

# 下载依赖
RUN go mod download

# 构建
RUN CGO_ENABLED=0 GOOS=linux go build -o collector .

# 最终镜像
FROM alpine:latest

WORKDIR /app

# 安装 CA 证书 (用于 HTTPS)
RUN apk add --no-cache ca-certificates tzdata

# 复制二进制
COPY --from=builder /app/collector .

# 环境变量
ENV REDIS_ADDR=redis:6379
ENV GIN_MODE=release

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# 启动命令
CMD ["./collector"]