# 丝瓜清单管理系统 PRD

## 📋 项目概述

**项目名称：** 丝瓜清单管理系统（Sponge Gourd Tracker）

**版本：** v1.0

**目标：** 构建一个简洁、现代、视觉高级的Web应用，用于管理和查看从各个渠道采集的丝瓜清单数据。

---

## 🎯 核心功能需求

### 1. 数据展示功能

#### 1.1 清单列表页
- **多标签视图**：支持三个分类标签
  - 🌱 新丝瓜（实习招聘）
  - 🌿 生丝瓜（校园招聘）
  - 🥒 熟丝瓜（社会招聘）
  
- **卡片式展示**
  - 每条数据以精美卡片形式展示
  - 新采摘的条目带有特殊标识（黄色徽章或闪光效果）
  - 卡片悬浮时有微动效果

- **关键信息展示**
  - 标题（title）
  - 副标题（sub_title）
  - 采摘时间（高亮显示）
  - 发布时间（publish_time）
  - 分类标签

#### 1.2 详情页
- 点击卡片展开/弹窗显示完整信息
- 展示所有字段（description, requirement, location, department等）
- 提供快速操作按钮（复制、标记、外部链接）

#### 1.3 搜索与筛选
- **实时搜索**：支持标题、描述、要求关键词搜索
- **时间筛选**：按采摘时间、发布时间范围筛选
- **状态筛选**：新采摘/已查看

### 2. 数据统计功能

#### 2.1 仪表盘
- **总览卡片**
  - 总条目数
  - 今日新增
  - 本周新增
  - 各类型占比（饼图）

- **趋势图表**
  - 每日采摘数量趋势（折线图）
  - 分类对比柱状图

### 3. 数据同步功能

#### 3.1 手动同步
- 触发Python爬虫脚本运行
- 显示同步进度和状态
- 同步完成后自动刷新列表

#### 3.2 自动同步（可选）
- 支持定时任务配置
- 可设置同步频率（每小时/每天等）

---

## 🎨 视觉设计要求

### 设计风格
- **现代简约**：扁平化设计，去繁就简
- **高级感**：使用渐变、毛玻璃、阴影等现代元素
- **舒适配色**：
  - 主色调：深蓝/紫罗兰渐变 `#667eea → #764ba2`
  - 辅助色：翠绿色 `#48c774`（代表新鲜丝瓜）
  - 背景：浅灰渐变 `#f5f7fa`
  - 文字：深灰 `#2c3e50`

### UI组件
- **Material Design** 或 **Ant Design** 风格
- 圆角卡片（border-radius: 12px）
- 柔和阴影（box-shadow: 0 4px 20px rgba(0,0,0,0.08)）
- 流畅动画（hover效果、页面切换）

### 响应式设计
- 支持桌面端（1920px+）
- 支持平板（768px-1024px）
- 支持移动端（320px+）

---

## 🏗️ 技术架构

### 前端技术栈
- **框架**：React 18 + TypeScript
- **UI库**：Ant Design 5.x / Tailwind CSS
- **状态管理**：Zustand / React Query
- **图表**：Chart.js / Recharts
- **HTTP请求**：Axios

### 后端技术栈
- **框架**：Flask / FastAPI (Python)
- **数据库**：MongoDB
- **ORM/ODM**：PyMongo / Motor (异步)
- **任务调度**：APScheduler（定时任务）

### 数据库设计

#### Collection: `sponge_items`

```javascript
{
  _id: ObjectId,
  sheet_name: String,        // 'intern' | 'campus' | 'experienced'
  type_name: String,         // '新丝瓜' | '生丝瓜' | '熟丝瓜'
  
  // 核心信息
  title: String,
  sub_title: String,
  description: String,
  requirement: String,
  
  // 时间信息
  采摘时间: Date,             // 检测到的时间
  publish_time: Date,        // 发布时间
  
  // 标识信息
  code: String,
  job_id: String,
  job_hash: String,          // 用于去重
  
  // 分类信息
  job_category: String,
  job_function: String,
  recruit_type_name: String,
  
  // 地点信息
  city_list: String,
  address: String,
  location: Object,
  
  // 其他信息
  department: Object,
  min_salary: Number,
  max_salary: Number,
  degree: String,
  experience: String,
  
  // 链接
  pc_job_url: String,
  wap_job_url: String,
  
  // 状态
  is_new: Boolean,           // 是否为新采摘
  is_viewed: Boolean,        // 是否已查看
  
  // 元数据
  created_at: Date,
  updated_at: Date
}
```

#### Collection: `sync_logs`

```javascript
{
  _id: ObjectId,
  sync_time: Date,           // 同步时间
  type: String,              // 'auto' | 'manual'
  status: String,            // 'success' | 'failed'
  new_count: Number,         // 新增数量
  total_count: Number,       // 总数量
  duration: Number,          // 耗时（秒）
  error_message: String      // 错误信息（如有）
}
```

---

## 🚀 功能优先级

### P0 (必须有)
- [x] 数据库连接与数据导入
- [x] 列表页展示（三个分类）
- [x] 基础搜索功能
- [x] 详情查看
- [x] 响应式布局

### P1 (重要)
- [ ] 数据统计仪表盘
- [ ] 高级筛选
- [ ] 手动同步功能
- [ ] 美观的UI设计

### P2 (锦上添花)
- [ ] 自动同步任务
- [ ] 数据导出（Excel/CSV）
- [ ] 个人收藏功能
- [ ] 深色模式

---

## 📁 项目结构

```
paquzijie/
├── backend/                 # 后端代码
│   ├── app.py              # Flask主程序
│   ├── config.py           # 配置文件
│   ├── models.py           # 数据模型
│   ├── routes/             # API路由
│   │   ├── items.py        # 清单相关API
│   │   ├── stats.py        # 统计相关API
│   │   └── sync.py         # 同步相关API
│   ├── services/           # 业务逻辑
│   │   ├── db.py           # 数据库操作
│   │   └── sync.py         # 同步服务
│   └── requirements.txt    # Python依赖
│
├── frontend/               # 前端代码
│   ├── public/
│   ├── src/
│   │   ├── components/     # 组件
│   │   │   ├── ItemCard.tsx
│   │   │   ├── ItemDetail.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   └── Dashboard.tsx
│   │   ├── pages/          # 页面
│   │   │   ├── Home.tsx
│   │   │   └── Stats.tsx
│   │   ├── services/       # API调用
│   │   ├── store/          # 状态管理
│   │   ├── styles/         # 样式
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── 1.py                    # 原爬虫脚本
├── PRD.md                  # 本文档
└── README.md               # 项目说明
```

---

## 🔌 API接口设计

### 基础信息
- **Base URL**: `http://localhost:5000/api`
- **认证方式**: 暂不需要（可后续添加）

### 接口列表

#### 1. 获取清单列表
```http
GET /api/items?type={type}&page={page}&limit={limit}&search={keyword}

Response:
{
  "success": true,
  "data": {
    "items": [...],
    "total": 895,
    "page": 1,
    "limit": 20
  }
}
```

#### 2. 获取单个详情
```http
GET /api/items/{id}

Response:
{
  "success": true,
  "data": { ... }
}
```

#### 3. 获取统计数据
```http
GET /api/stats

Response:
{
  "success": true,
  "data": {
    "total": 895,
    "today_new": 15,
    "week_new": 80,
    "type_distribution": {
      "新丝瓜": 180,
      "生丝瓜": 115,
      "熟丝瓜": 600
    },
    "daily_trend": [...]
  }
}
```

#### 4. 触发同步
```http
POST /api/sync

Response:
{
  "success": true,
  "message": "同步已启动",
  "task_id": "xxx"
}
```

#### 5. 获取同步状态
```http
GET /api/sync/status/{task_id}

Response:
{
  "success": true,
  "data": {
    "status": "running" | "completed" | "failed",
    "progress": 75,
    "message": "正在整理新丝瓜..."
  }
}
```

---

## 🎬 实施步骤

### Phase 1: 后端搭建（1-2天）
1. ✅ 安装MongoDB并配置
2. ✅ 创建Flask项目结构
3. ✅ 实现数据库连接和模型
4. ✅ 开发核心API接口
5. ✅ 编写数据导入脚本（从Excel/JSON到MongoDB）

### Phase 2: 前端开发（2-3天）
1. ✅ 初始化React + Vite项目
2. ✅ 设计并实现UI组件
3. ✅ 实现列表页和详情页
4. ✅ 接入后端API
5. ✅ 优化视觉效果和动画

### Phase 3: 功能完善（1天）
1. ✅ 实现搜索和筛选
2. ✅ 添加统计仪表盘
3. ✅ 实现同步功能
4. ✅ 测试和Bug修复

### Phase 4: 部署上线（半天）
1. ✅ 配置生产环境
2. ✅ 编写部署文档
3. ✅ 启动服务

---

## 📊 成功指标

- ✅ 页面加载时间 < 2秒
- ✅ 支持1000+条数据流畅展示
- ✅ 移动端适配完整
- ✅ UI设计获得用户好评
- ✅ 同步功能稳定可靠

---

## 🔮 未来扩展

- 用户登录和权限管理
- 多人协作和数据共享
- 智能推荐系统
- 数据分析和洞察
- 通知提醒功能

---

**文档创建时间**: 2025-10-21  
**最后更新**: 2025-10-21  
**负责人**: AI Assistant

