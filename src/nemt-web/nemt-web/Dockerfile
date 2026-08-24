# Copyright 2026 NEMT Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

# NEMT Web - 前端镜像 (Vite + React)
FROM node:18-alpine AS builder

WORKDIR /app

# 复制 package 文件
COPY web/package.json web/package-lock.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY web/ .

# 构建
RUN npm run build

# 生产镜像
FROM nginx:alpine

# 复制 nginx 配置
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]