# Copyright 2026 NEMT Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

# NEMT Core - Python 主程序镜像
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖 (matplotlib 需要)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY *.py .

# 创建输出目录
RUN mkdir -p /app/output

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

# 默认启动命令 (演示模式)
CMD ["python", "main.py", "--demo"]

# 可选命令:
#   python main.py --demo          # 演示模式
#   python main.py --fetch         # 仅获取数据
#   python main.py --interval 5m   # 使用5分钟K线