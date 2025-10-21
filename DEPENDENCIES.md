# 项目依赖说明

## 📦 Python 依赖

### 完整依赖列表 (`backend/requirements.txt`)

```txt
# Flask Web框架
flask==3.0.0
flask-cors==4.0.0

# 数据库
pymongo==4.6.0

# 工具
python-dotenv==1.0.0
APScheduler==3.10.4
pytz==2024.1

# 爬虫脚本依赖
openpyxl==3.1.2
pandas==2.1.4
playwright==1.40.0
```

### 依赖分类

#### 1. Web框架层

| 包名 | 版本 | 用途 |
|------|------|------|
| flask | 3.0.0 | Web框架，提供API服务 |
| flask-cors | 4.0.0 | 跨域请求支持 |

#### 2. 数据库层

| 包名 | 版本 | 用途 |
|------|------|------|
| pymongo | 4.6.0 | MongoDB数据库驱动 |

#### 3. 工具层

| 包名 | 版本 | 用途 |
|------|------|------|
| python-dotenv | 1.0.0 | 环境变量管理 |
| APScheduler | 3.10.4 | 定时任务调度（30分钟爬取） |
| pytz | 2024.1 | 时区处理（北京时间） |

#### 4. 爬虫层

| 包名 | 版本 | 用途 |
|------|------|------|
| openpyxl | 3.1.2 | Excel文件读写 |
| pandas | 2.1.4 | 数据处理和分析 |
| playwright | 1.40.0 | 浏览器自动化（爬取动态页面） |

## 🎭 Playwright 特殊说明

### 为什么需要Playwright？

字节跳动招聘网站是动态JavaScript渲染的，使用Playwright可以：
1. 模拟真实浏览器访问
2. 等待JavaScript加载完成
3. 拦截API请求获取数据
4. 绕过反爬虫机制

### Playwright 安装要求

#### Python包
```bash
pip install playwright==1.40.0
```

#### 浏览器二进制文件
```bash
playwright install chromium
```

#### 系统依赖（Linux）
```bash
# Debian/Ubuntu
apt-get install -y \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils
```

### Docker中的Playwright

在Dockerfile中，我们：

1. **安装系统依赖**（第17-42行）
   ```dockerfile
   RUN apt-get update && apt-get install -y \
       gcc \
       wget \
       gnupg \
       ... # 各种库
   ```

2. **安装Python包**（第45-46行）
   ```dockerfile
   RUN pip install --no-cache-dir -r requirements.txt
   ```

3. **安装浏览器**（第49行）
   ```dockerfile
   RUN playwright install chromium --with-deps
   ```

### 镜像大小影响

| 组件 | 大小 |
|------|------|
| Python基础镜像 | ~150MB |
| 系统依赖 | ~50MB |
| Python包 | ~100MB |
| Chromium浏览器 | ~300MB |
| **总计** | **~600MB** |

虽然镜像较大，但对于运行浏览器自动化是必需的。

## 🔧 本地开发环境

### 1. 安装Python依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 安装Playwright浏览器

```bash
playwright install chromium
```

### 3. 验证安装

```bash
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
python -c "import pandas; print('Pandas OK')"
python -c "import openpyxl; print('Openpyxl OK')"
```

## 🐳 Docker环境

### 构建镜像

```bash
docker build -t paquzijie .
```

构建时间：约5-10分钟（首次）

### 运行容器

```bash
docker run -p 5001:5001 \
  -e MONGO_URI="mongodb+srv://..." \
  -e CRAWLER_SCRIPT_PATH="/app/1.py" \
  paquzijie
```

### 验证依赖

```bash
docker run --rm paquzijie python -c "
import flask
import pymongo
import playwright
import pandas
import openpyxl
print('All dependencies OK!')
"
```

## ☁️ Zeabur部署

### 自动处理

Zeabur会自动：
1. 读取 `Dockerfile`
2. 构建镜像
3. 安装所有依赖
4. 部署应用

### 部署时间

首次部署：约10-15分钟
- 前端构建：2-3分钟
- 后端依赖：3-5分钟
- Playwright安装：5-7分钟

### 环境变量

在Zeabur控制台或`zeabur.json`中设置：
```json
{
  "environment": {
    "MONGO_URI": "${MONGO_URI}",
    "CRAWLER_SCRIPT_PATH": "/app/1.py"
  }
}
```

## 📊 依赖关系图

```
┌─────────────────────────────────────────┐
│          Flask Application              │
│         (backend/app.py)                │
└──────────┬──────────────────────────────┘
           │
           ├─────► Flask (Web框架)
           │       └─► flask-cors (CORS支持)
           │
           ├─────► PyMongo (数据库)
           │       └─► MongoDB Atlas
           │
           ├─────► APScheduler (定时任务)
           │       └─► 每30分钟执行爬虫
           │
           └─────► 爬虫脚本 (1.py)
                   ├─► Playwright (浏览器)
                   │   └─► Chromium
                   ├─► Pandas (数据处理)
                   ├─► Openpyxl (Excel)
                   └─► Pytz (时区)
```

## 🔄 依赖更新策略

### 主要依赖固定版本

为了稳定性，我们固定了关键依赖的版本：
- Flask 3.0.0
- Playwright 1.40.0
- Pandas 2.1.4

### 更新建议

#### 安全更新（立即）
```bash
pip install --upgrade pymongo  # 安全补丁
```

#### 功能更新（测试后）
```bash
# 1. 更新到最新版本
pip install --upgrade playwright

# 2. 测试爬虫功能
python 1.py

# 3. 更新requirements.txt
pip freeze | grep playwright >> requirements.txt
```

#### 主要版本（谨慎）
```bash
# Flask 3.x → 4.x
# 需要全面测试
```

## 🐛 常见问题

### 1. ModuleNotFoundError

**问题**：`ModuleNotFoundError: No module named 'openpyxl'`

**原因**：依赖未安装

**解决**：
```bash
pip install -r backend/requirements.txt
```

### 2. Playwright浏览器未安装

**问题**：`playwright._impl._api_types.Error: Executable doesn't exist`

**原因**：浏览器二进制文件未安装

**解决**：
```bash
playwright install chromium
```

### 3. Docker构建失败

**问题**：`playwright install` 超时

**原因**：网络问题或资源不足

**解决**：
```bash
# 增加Docker内存限制
docker build --memory=4g -t paquzijie .

# 或使用代理
docker build --build-arg HTTP_PROXY=http://proxy:port -t paquzijie .
```

### 4. 系统依赖缺失

**问题**：`ImportError: libgtk-3.so.0`

**原因**：系统库未安装

**解决**：
```bash
# Ubuntu/Debian
sudo apt-get install libgtk-3-0

# 或重新安装Playwright
playwright install-deps chromium
```

## 📝 依赖检查清单

部署前检查：

- [ ] `backend/requirements.txt` 包含所有依赖
- [ ] Dockerfile 安装系统依赖
- [ ] Dockerfile 安装Playwright浏览器
- [ ] 环境变量 `CRAWLER_SCRIPT_PATH` 正确设置
- [ ] MongoDB连接字符串正确
- [ ] 本地测试爬虫功能正常
- [ ] Docker镜像构建成功
- [ ] Docker容器运行正常

## 🎯 优化建议

### 减少镜像大小

1. **使用多阶段构建**（已实现）
   - 前端构建阶段：node:18-alpine
   - 后端运行阶段：python:3.11-slim

2. **清理不必要的文件**
   ```dockerfile
   RUN apt-get clean && rm -rf /var/lib/apt/lists/*
   ```

3. **使用 `.dockerignore`**
   ```
   node_modules
   .git
   *.pyc
   __pycache__
   ```

### 加速构建

1. **缓存依赖层**
   - 先复制 requirements.txt
   - 再安装依赖
   - 最后复制代码

2. **使用国内镜像**
   ```dockerfile
   RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
   ```

## 📚 相关文档

- [Flask文档](https://flask.palletsprojects.com/)
- [Playwright文档](https://playwright.dev/python/)
- [Pandas文档](https://pandas.pydata.org/)
- [APScheduler文档](https://apscheduler.readthedocs.io/)
- [MongoDB Python驱动](https://pymongo.readthedocs.io/)

---

**最后更新**：2025-10-21  
**Python版本**：3.11  
**总依赖数**：10个包 + 1个浏览器

