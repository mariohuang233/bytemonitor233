# 🥒 丝瓜清单管理系统

一个简洁、现代、视觉高级的Web应用，用于管理和查看从各个渠道采集的丝瓜清单数据。

## ✨ 功能特性

- 📊 **数据展示**：三个分类标签（新丝瓜/生丝瓜/熟丝瓜），卡片式精美展示
- 🔍 **智能搜索**：支持标题、描述、要求关键词实时搜索
- 📈 **统计仪表盘**：可视化数据统计，趋势图表展示
- 🔄 **一键同步**：触发Python爬虫脚本，自动更新数据
- 💾 **MongoDB存储**：数据持久化，高性能查询
- 📱 **响应式设计**：完美支持桌面、平板、移动端

## 🏗️ 技术栈

### 后端
- **Flask** - Python Web框架
- **MongoDB** - NoSQL数据库
- **PyMongo** - MongoDB驱动

### 前端
- **React 18** - UI框架
- **TypeScript** - 类型安全
- **Ant Design** - UI组件库
- **Recharts** - 数据可视化
- **Vite** - 构建工具

## 📦 安装部署

### 前置要求

- Python 3.8+
- Node.js 18+
- MongoDB 4.4+

### 步骤1: 安装MongoDB

**macOS:**
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Linux/Windows**: 参考 [MongoDB官方文档](https://www.mongodb.com/docs/manual/installation/)

### 步骤2: 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 步骤3: 初始化数据库

```bash
cd backend
python3 init_db.py
```

按提示选择是否清空现有数据。首次运行建议选择 `y`（清空并导入）。

### 步骤4: 启动后端服务

```bash
cd backend
python3 app.py
```

后端将运行在 `http://localhost:5000`

### 步骤5: 安装前端依赖

```bash
cd frontend
npm install
```

### 步骤6: 启动前端服务

```bash
cd frontend
npm run dev
```

前端将运行在 `http://localhost:5173`

## 🚀 使用指南

### 1. 访问应用

打开浏览器访问 `http://localhost:5173`

### 2. 查看数据

- 点击顶部标签切换不同类型（新丝瓜/生丝瓜/熟丝瓜）
- 使用搜索框进行关键词搜索
- 点击卡片查看详细信息

### 3. 查看统计

点击右上角"统计视图"按钮，查看：
- 总数、今日新增、本周新增
- 每日采摘趋势图
- 类型分布饼图和柱状图

### 4. 同步数据

点击右上角"同步数据"按钮：
1. 系统会自动运行Python爬虫脚本
2. 显示同步进度
3. 完成后自动刷新列表

## 📁 项目结构

```
paquzijie/
├── 1.py                    # 原爬虫脚本
├── PRD.md                  # 产品需求文档
├── README.md               # 本文档
│
├── backend/                # 后端代码
│   ├── app.py             # Flask主程序
│   ├── config.py          # 配置文件
│   ├── init_db.py         # 数据库初始化脚本
│   ├── requirements.txt   # Python依赖
│   ├── routes/            # API路由
│   │   ├── items.py       # 清单API
│   │   ├── stats.py       # 统计API
│   │   └── sync.py        # 同步API
│   └── services/          # 业务逻辑
│       ├── db.py          # 数据库服务
│       └── importer.py    # 数据导入
│
└── frontend/              # 前端代码
    ├── index.html         # HTML入口
    ├── package.json       # NPM依赖
    ├── vite.config.ts     # Vite配置
    ├── tsconfig.json      # TypeScript配置
    └── src/
        ├── App.tsx        # 应用主组件
        ├── main.tsx       # 入口文件
        ├── components/    # UI组件
        │   ├── ItemCard.tsx      # 条目卡片
        │   ├── ItemDetail.tsx    # 详情模态框
        │   └── Dashboard.tsx     # 统计仪表盘
        ├── pages/         # 页面
        │   └── Home.tsx   # 主页
        ├── services/      # API服务
        │   └── api.ts     # API封装
        └── styles/        # 样式
            └── index.css
```

## 🔌 API接口

### 基础信息
- **Base URL**: `http://localhost:5000/api`

### 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/items` | 获取清单列表 |
| GET | `/items/:id` | 获取单个详情 |
| GET | `/stats` | 获取统计数据 |
| POST | `/sync` | 触发同步 |
| GET | `/sync/status` | 获取同步状态 |
| GET | `/sync-logs` | 获取同步日志 |

详细API文档见 [PRD.md](./PRD.md#-api接口设计)

## 🎨 界面预览

- **列表页**: 卡片式展示，新条目黄色徽章标识
- **详情页**: 模态框展示完整信息，支持复制和跳转
- **统计页**: 精美图表，数据一目了然

## 🛠️ 开发命令

### 后端
```bash
# 开发模式运行
python3 backend/app.py

# 初始化数据库
python3 backend/init_db.py

# 运行爬虫
python3 1.py
```

### 前端
```bash
# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

## 🐛 常见问题

### 1. MongoDB连接失败

确保MongoDB服务已启动：
```bash
brew services list  # 查看服务状态
brew services start mongodb-community  # 启动服务
```

### 2. 前端无法连接后端

检查后端是否运行在 `http://localhost:5000`，查看控制台错误信息。

### 3. 同步失败

检查：
- 爬虫脚本 `1.py` 是否可以正常运行
- Playwright浏览器是否已安装（`playwright install`）
- JSON缓存文件是否存在

## 📝 配置说明

### 后端配置 (backend/config.py)

```python
MONGO_URI = 'mongodb://localhost:27017/'  # MongoDB连接
MONGO_DB_NAME = 'sponge_tracker'          # 数据库名称
```

### 前端代理配置 (frontend/vite.config.ts)

```typescript
proxy: {
  '/api': {
    target: 'http://localhost:5000',  # 后端地址
    changeOrigin: true
  }
}
```

## 🚢 生产部署

### 后端部署

```bash
# 使用gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

### 前端部署

```bash
# 构建
cd frontend
npm run build

# 部署dist目录到静态服务器（Nginx/Apache等）
```

## 📄 许可证

MIT License

## 👨‍💻 作者

AI Assistant

---

**最后更新**: 2025-10-21

