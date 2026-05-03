# Dockerfile - Python 计算模块
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV REDIS_HOST=redis

# 默认启动订阅器
CMD ["python", "subscriber.py"]