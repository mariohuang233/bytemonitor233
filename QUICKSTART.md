# 🚀 快速启动指南

## 当前状态

✅ 后端代码已完成  
✅ 前端代码已完成  
✅ Python依赖已安装  
✅ Node.js依赖已安装  
⚠️ **需要您更新MongoDB连接信息**

---

## 第一步：更新MongoDB连接（重要！）

您的MongoDB连接认证失败，可能原因：
1. **密码不正确** - 请确认密码是否正确
2. **IP白名单限制** - 需要在MongoDB Atlas添加您的IP到白名单
3. **用户权限问题** - 确保数据库用户有读写权限

### 解决方法：

#### 方案1：更新密码（如果密码变了）

编辑 `backend/config.py` 第6行，更新您的MongoDB连接字符串：

```python
MONGO_URI = os.getenv('MONGO_URI', '您正确的MongoDB连接字符串')
```

#### 方案2：添加IP白名单（推荐）

1. 登录 [MongoDB Atlas](https://cloud.mongodb.com/)
2. 进入您的集群
3. 点击 "Network Access"
4. 点击 "Add IP Address"
5. 选择 "Allow Access from Anywhere" (0.0.0.0/0)  
   或添加您当前的IP地址

#### 方案3：验证连接字符串

运行以下命令测试连接：

```bash
python3 -c "from pymongo import MongoClient; client = MongoClient('您的连接字符串', serverSelectionTimeoutMS=5000); print('✅ 连接成功'); print('数据库:', client.list_database_names())"
```

---

## 第二步：初始化数据库

连接成功后，运行初始化脚本导入数据：

```bash
cd backend
python3 init_db.py
```

选择 `y` 清空并导入（首次运行推荐）

---

## 第三步：启动服务

### 启动后端（终端1）

```bash
cd backend
python3 app.py
```

后端将运行在：`http://localhost:5000`

### 启动前端（终端2）

```bash
cd frontend
npm run dev
```

前端将运行在：`http://localhost:5173`

---

## 第四步：访问应用

打开浏览器访问：**http://localhost:5173**

---

## 🎯 核心功能

### 数据展示
- 🌱 新丝瓜（实习招聘）
- 🌿 生丝瓜（校园招聘）  
- 🥒 熟丝瓜（社会招聘）

### 主要功能
- ✅ 搜索和筛选
- ✅ 详情查看
- ✅ 统计仪表盘
- ✅ 一键同步数据

---

## 🔧 数据库信息

**数据库名称**: `paquzijie_sponge`  
**Collections**:
- `sponge_items` - 清单数据
- `sync_logs` - 同步日志

**特别说明**: 使用独立数据库名 `paquzijie_sponge`，**不会与您MongoDB中的其他项目冲突**！

---

## 📝 常用命令

### 查看后端健康状态
```bash
curl http://localhost:5000/health
```

### 手动触发同步
```bash
curl -X POST http://localhost:5000/api/sync
```

### 查看统计数据
```bash
curl http://localhost:5000/api/stats
```

---

## ⚠️ 故障排查

### MongoDB连接失败
1. 检查连接字符串是否正确
2. 检查IP白名单设置
3. 检查用户名密码

### 前端无法访问后端
- 确保后端运行在 `http://localhost:5000`
- 检查浏览器控制台是否有CORS错误

### 同步失败
- 确保 `1.py` 爬虫脚本可以正常运行
- 确保 Playwright已安装：`playwright install`

---

## 🎉 完成！

修复MongoDB连接后，您就可以完整使用系统了！

有任何问题请参考 `README.md` 或检查控制台日志。

