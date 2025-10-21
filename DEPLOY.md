# 🚀 部署指南

## GitHub上传

1. **初始化Git仓库**
```bash
git init
git add .
git commit -m "feat: 初始化丝瓜清单管理系统

- 完整的Flask后端API (6个接口)
- React + TypeScript前端
- MongoDB数据存储
- 精美的UI设计与数据可视化
- 一键同步功能
- 申请按钮功能"
```

2. **连接到GitHub**
```bash
git remote add origin https://github.com/mariohuang233/bytemonitor233.git
git branch -M main
git push -u origin main
```

## Zeabur部署

### 方法1：通过Zeabur Dashboard

1. 登录 [Zeabur Dashboard](https://dash.zeabur.com/)
2. 点击 "Create Project"
3. 选择 "Deploy from GitHub"
4. 选择仓库：`mariohuang233/bytemonitor233`
5. 设置环境变量：
   - `MONGO_URI`: `mongodb+srv://byte123:fXb39P2JDuJA6U8S@yierbubu.aha67vc.mongodb.net/?retryWrites=true&w=majority&appName=yierbubu`
   - `SECRET_KEY`: `your-secret-key-here`
6. 点击 "Deploy"

### 方法2：通过CLI

```bash
# 安装Zeabur CLI
npm i -g @zeabur/cli

# 登录
zeabur auth login

# 部署
zeabur deploy
```

## 环境变量说明

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `MONGO_URI` | MongoDB连接字符串 | `mongodb+srv://...` |
| `MONGO_DB_NAME` | 数据库名称 | `paquzijie_sponge` |
| `SECRET_KEY` | Flask密钥 | `your-secret-key` |
| `DEBUG` | 调试模式 | `False` |
| `CORS_ORIGINS` | 允许的CORS来源 | `*` |

## 部署后访问

- **生产地址**: `https://your-app.zeabur.app`
- **健康检查**: `https://your-app.zeabur.app/health`
- **API文档**: `https://your-app.zeabur.app/api/stats`

## 功能验证

部署完成后，访问以下功能：

1. ✅ **主页面** - 查看三种类型的丝瓜清单
2. ✅ **搜索功能** - 测试关键词搜索
3. ✅ **详情查看** - 点击卡片查看详情
4. ✅ **申请按钮** - 点击申请按钮跳转到招聘页面
5. ✅ **统计页面** - 查看数据可视化图表
6. ✅ **同步功能** - 测试一键同步数据

## 故障排除

### 1. 部署失败
- 检查Dockerfile语法
- 确认依赖文件完整
- 查看构建日志

### 2. 数据库连接失败
- 确认MongoDB连接字符串正确
- 检查IP白名单设置
- 验证数据库用户权限

### 3. 前端资源404
- 确认构建产物正确生成
- 检查静态文件路径配置

## 技术栈

- **后端**: Python + Flask + PyMongo
- **前端**: React + TypeScript + Ant Design
- **数据库**: MongoDB Atlas
- **部署**: Zeabur + Docker
- **可视化**: Recharts

## 数据库结构

- **数据库**: `paquzijie_sponge`（独立数据库，不冲突）
- **集合**: 
  - `sponge_items` - 职位数据（903条）
  - `sync_logs` - 同步日志

## 已实现功能

### 核心功能
- ✅ 数据展示（三种类型分类）
- ✅ 实时搜索和筛选
- ✅ 详情查看模态框
- ✅ **申请按钮（直达招聘页面）**
- ✅ 统计仪表盘
- ✅ 一键数据同步

### UI特性
- ✅ 现代渐变设计
- ✅ 响应式布局
- ✅ 流畅动画效果
- ✅ 专业数据可视化

### 技术特性
- ✅ RESTful API设计
- ✅ TypeScript类型安全
- ✅ MongoDB索引优化
- ✅ Docker容器化部署

---

**部署完成后记得测试所有功能！** 🎉
