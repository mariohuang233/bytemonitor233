# 多阶段构建：前端构建 + 后端运行
FROM node:18-alpine as frontend-builder

# 构建前端
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install --production=false
COPY frontend/ ./
RUN npm run build

# Python后端镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装Python依赖
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./

# 从前端构建阶段复制构建产物
COPY --from=frontend-builder /app/frontend/dist ./static

# 复制爬虫脚本
COPY 1.py ./

# 设置环境变量
ENV PYTHONPATH=/app
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV CRAWLER_SCRIPT_PATH=/app/1.py

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "app.py"]
