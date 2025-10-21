#!/bin/bash
# 启动前端服务

echo "🚀 启动丝瓜清单前端服务..."
cd "$(dirname "$0")/frontend"
npm run dev

