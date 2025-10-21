#!/bin/bash
# 启动后端服务

echo "🚀 启动丝瓜清单后端服务..."
cd "$(dirname "$0")/backend"
python3 app.py

