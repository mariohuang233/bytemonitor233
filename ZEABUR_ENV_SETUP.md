# Zeabur 环境变量设置指南

## 🐛 问题总结

### 错误信息
```
pymongo.errors.InvalidURI: Invalid URI scheme: URI must begin with 'mongodb://' or 'mongodb+srv://'
```

### 根本原因
从日志看到：
```
连接MongoDB:    mongodb+srv://...
                ↑↑↑↑ URI前面有多个空格
```

**Zeabur环境变量设置时，不小心在值的前面或后面添加了空格！**

---

## ✅ 解决方案

### 1. 代码层面修复（已完成）

在 `backend/config.py` 中，对所有环境变量添加 `.strip()` 清理：

```python
# ✅ 修复后
MONGO_URI = os.getenv('MONGO_URI', 'default').strip()
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'paquzijie_sponge').strip()
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key').strip()
DEBUG = os.getenv('DEBUG', 'True').strip() == 'True'
CORS_ORIGINS = [origin.strip() for origin in os.getenv('CORS_ORIGINS', '*').split(',')]
```

在 `backend/app.py` 中，添加URI验证：

```python
# 验证MongoDB URI格式
if not MONGO_URI or not MONGO_URI.startswith(('mongodb://', 'mongodb+srv://')):
    logger.error(f"❌ 无效的MongoDB URI: '{MONGO_URI}'")
    logger.error("请检查环境变量 MONGO_URI 是否正确设置")
    raise ValueError(f"Invalid MongoDB URI: '{MONGO_URI}'")
```

---

### 2. Zeabur环境变量设置（⚠️ 重要！）

#### 正确的设置方式 ✅

在Zeabur控制台 → 你的服务 → Variables（变量）页面：

**MONGO_URI**（必须）
```
mongodb+srv://byte123:fXb39P2JDuJA6U8S@yierbubu.aha67vc.mongodb.net/?retryWrites=true&w=majority&appName=yierbubu
```
⚠️ 注意：
- 不要在URI前后添加空格
- 不要添加引号（Zeabur会自动处理）
- 直接粘贴完整的URI

**SECRET_KEY**（必须）
```
生成一个随机密钥
```

生成方法：
```bash
# 本地运行
python3 -c "import secrets; print(secrets.token_hex(32))"
```

输出示例：
```
a1b2c3d4e5f6...（64个字符）
```

**其他变量**（可选，使用默认值）

| 变量名 | 值 | 说明 |
|--------|-----|------|
| MONGO_DB_NAME | `paquzijie_sponge` | 数据库名（已有默认值） |
| DEBUG | `False` | 生产环境（已有默认值） |
| CORS_ORIGINS | `*` | 允许所有来源（已有默认值） |
| CRAWLER_SCRIPT_PATH | `/app/1.py` | 爬虫脚本路径（已有默认值） |

---

#### 错误的设置方式 ❌

**不要这样做**：

1. ❌ 在URI前后添加空格
   ```
   " mongodb+srv://..."  或  "mongodb+srv://... "
   ```

2. ❌ 添加引号
   ```
   "mongodb+srv://..."
   ```

3. ❌ 换行
   ```
   mongodb+srv://
   user:pass@cluster...
   ```

4. ❌ 添加注释
   ```
   mongodb+srv://...  # 这是MongoDB URI
   ```

---

## 🎯 Zeabur 设置步骤

### 第1步：进入变量设置页面

1. 登录 Zeabur 控制台
2. 选择你的项目
3. 选择服务（bytemonitor233）
4. 点击 **Variables**（变量）标签页

---

### 第2步：设置 MONGO_URI

1. 点击 **Add Variable**（添加变量）
2. Key（键）输入：`MONGO_URI`
3. Value（值）粘贴：
   ```
   mongodb+srv://byte123:fXb39P2JDuJA6U8S@yierbubu.aha67vc.mongodb.net/?retryWrites=true&w=majority&appName=yierbubu
   ```
4. **检查**：确保Value输入框中：
   - ✅ 没有前导空格
   - ✅ 没有尾随空格
   - ✅ 没有引号
   - ✅ 完整的URI

5. 点击 **Save**（保存）

---

### 第3步：设置 SECRET_KEY

1. 在本地终端生成密钥：
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

2. 复制输出的密钥（64个字符）

3. 在Zeabur：
   - Key：`SECRET_KEY`
   - Value：粘贴刚才生成的密钥

4. 点击 **Save**

---

### 第4步：验证设置（重要！）

在保存后，Zeabur会显示已设置的变量列表。

**检查清单**：

```
✅ MONGO_URI
   - 开头是 mongodb+srv://
   - 没有多余的空格
   - 完整的连接字符串

✅ SECRET_KEY
   - 64个字符
   - 随机生成
   - 没有空格

✅ 其他变量（可选）
   - MONGO_DB_NAME: paquzijie_sponge
   - DEBUG: False
   - CORS_ORIGINS: *
```

---

### 第5步：重新部署

设置环境变量后，Zeabur会自动触发重新部署。

如果没有自动部署：
1. 点击 **Redeploy**（重新部署）按钮
2. 等待构建完成（10-15分钟）

---

## 🔍 验证部署成功

### 查看日志

在 Zeabur 控制台 → Logs（日志）页面：

**成功的日志**：
```
✅ 连接MongoDB: mongodb+srv://byte123:fXb39P2JDuJA6U8S@yierbubu...
✅ MongoDB连接成功
✅ 定时调度器已启动，每30分钟执行一次爬取任务
Flask应用初始化完成
启动Flask服务器...
 * Running on all addresses (0.0.0.0)
 * Running on http://0.0.0.0:5001
```

**失败的日志**：
```
❌ 无效的MongoDB URI: '    mongodb+srv://...'
    ↑↑↑↑ 如果看到这个，说明URI前面有空格

❌ pymongo.errors.InvalidURI: Invalid URI scheme
```

如果看到失败日志，重新检查环境变量设置！

---

## 📊 MongoDB Atlas 配置

### 1. IP 白名单

确保MongoDB Atlas允许Zeabur的服务器访问：

1. 登录 [MongoDB Atlas](https://cloud.mongodb.com/)
2. 选择你的集群
3. 点击 **Network Access**（网络访问）
4. 点击 **Add IP Address**（添加IP地址）
5. 选择 **Allow Access from Anywhere**（允许任何地方访问）
   - 或者输入：`0.0.0.0/0`
6. 点击 **Confirm**（确认）

⚠️ 注意：生产环境建议只允许特定IP，但Zeabur的IP是动态的，所以需要允许所有。

---

### 2. 数据库用户权限

确保数据库用户有正确的权限：

1. 在MongoDB Atlas，点击 **Database Access**（数据库访问）
2. 找到用户 `byte123`
3. 确认权限包含：
   - ✅ Read and write to any database（读写任何数据库）
   - 或者至少：Read and write to `paquzijie_sponge` 数据库

---

### 3. 连接字符串格式

标准的MongoDB Atlas连接字符串格式：

```
mongodb+srv://<username>:<password>@<cluster-url>/<database>?retryWrites=true&w=majority
```

我们的连接字符串：
```
mongodb+srv://byte123:fXb39P2JDuJA6U8S@yierbubu.aha67vc.mongodb.net/?retryWrites=true&w=majority&appName=yierbubu
```

分解：
- 协议：`mongodb+srv://`
- 用户名：`byte123`
- 密码：`fXb39P2JDuJA6U8S`
- 集群：`yierbubu.aha67vc.mongodb.net`
- 参数：`?retryWrites=true&w=majority&appName=yierbubu`

---

## 🧪 本地测试

在推送到Zeabur前，可以本地测试环境变量：

### 方法1：使用 .env 文件

创建 `backend/.env`：
```env
MONGO_URI=mongodb+srv://byte123:fXb39P2JDuJA6U8S@yierbubu.aha67vc.mongodb.net/?retryWrites=true&w=majority&appName=yierbubu
MONGO_DB_NAME=paquzijie_sponge
SECRET_KEY=your-secret-key-here
DEBUG=False
CORS_ORIGINS=*
```

运行：
```bash
cd backend
python app.py
```

---

### 方法2：直接导出环境变量

```bash
export MONGO_URI="mongodb+srv://byte123:fXb39P2JDuJA6U8S@yierbubu.aha67vc.mongodb.net/?retryWrites=true&w=majority&appName=yierbubu"
export SECRET_KEY="your-secret-key"
cd backend
python app.py
```

---

### 验证连接

```python
from pymongo import MongoClient

uri = "mongodb+srv://byte123:fXb39P2JDuJA6U8S@yierbubu.aha67vc.mongodb.net/?retryWrites=true&w=majority&appName=yierbubu"
client = MongoClient(uri)

# 测试连接
print(client.server_info())  # 如果成功，会打印服务器信息
print("✅ MongoDB连接成功！")
```

---

## 🆘 常见问题

### Q1: 为什么URI前面会有空格？

**A**: 通常是复制粘贴时不小心带入的。建议：
1. 先粘贴到文本编辑器
2. 检查并删除前后空格
3. 再复制到Zeabur

---

### Q2: 设置环境变量后，为什么还是失败？

**A**: 可能原因：
1. ❌ 环境变量没有保存
2. ❌ 没有触发重新部署
3. ❌ 缓存问题

**解决方案**：
1. 确认环境变量已保存（在Variables页面能看到）
2. 手动点击 **Redeploy**
3. 清除Zeabur缓存（Advanced → Clear Cache）

---

### Q3: 如何查看当前使用的环境变量？

**A**: 在应用日志中，我们添加了验证和打印：

```
连接MongoDB: mongodb+srv://byte123:fXb39P2JDuJA6U8S@yi...
                        ↑ 前50个字符（安全考虑）
```

如果这行日志显示URI有问题，说明环境变量设置错误。

---

### Q4: SECRET_KEY是什么？需要多长？

**A**: 
- Flask的密钥，用于session加密
- 推荐长度：64个字符（32字节的hex）
- 生成方法：`python3 -c "import secrets; print(secrets.token_hex(32))"`

---

### Q5: 为什么建议使用 0.0.0.0/0 的IP白名单？

**A**: 
- Zeabur的服务器IP是动态的
- 无法提前知道具体IP
- 使用 `0.0.0.0/0` 允许所有IP访问

**安全建议**：
- MongoDB已经有用户名密码保护
- URI不应该泄露
- 生产环境考虑使用VPN或专用网络

---

## ✅ 最终检查清单

在Zeabur部署前：

### 代码层面
- [x] `backend/config.py` 所有环境变量都添加了 `.strip()`
- [x] `backend/app.py` 添加了URI验证
- [x] 代码已推送到GitHub

### Zeabur设置
- [ ] MONGO_URI 已设置（无空格）
- [ ] SECRET_KEY 已设置（64字符）
- [ ] 其他变量已设置（可选）
- [ ] 保存后触发重新部署

### MongoDB Atlas
- [ ] IP白名单设置为 `0.0.0.0/0`
- [ ] 用户 `byte123` 有读写权限
- [ ] 数据库 `paquzijie_sponge` 已创建

### 部署验证
- [ ] 构建成功（无错误）
- [ ] 应用运行中（状态：Running）
- [ ] 日志显示 MongoDB 连接成功
- [ ] 访问首页正常
- [ ] 同步数据功能正常

---

**文档更新时间**：2025-10-21 18:25  
**问题状态**：✅ 已修复（代码层面）  
**待做事项**：在Zeabur正确设置环境变量

