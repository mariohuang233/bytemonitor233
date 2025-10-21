# 时间与调度更新说明

## 📅 更新时间
2025-10-21

## 🎯 更新内容

### 1. 爬取频率调整为30分钟

**实现方式**：
- 在 `backend/app.py` 中集成 APScheduler
- 使用 `BackgroundScheduler` 在后台运行定时任务
- 设置 `IntervalTrigger(minutes=30)` 每30分钟执行一次

**调度器特性**：
- ✅ 自动运行爬虫脚本（使用 `--auto` 参数静默模式）
- ✅ 自动导入数据到MongoDB
- ✅ 记录同步日志（类型标记为 `scheduled`）
- ✅ 支持优雅关闭（程序退出时自动停止调度器）
- ✅ 使用北京时区（Asia/Shanghai）

**日志输出示例**：
```
2025-10-21 14:30:00 - INFO - ✅ 定时调度器已启动，每30分钟执行一次爬取任务
2025-10-21 15:00:00 - INFO - [定时任务] 开始执行爬取任务 - 2025-10-21 15:00:00
2025-10-21 15:02:30 - INFO - [定时任务] 任务完成 - 2025-10-21 15:02:30 (耗时: 150.23秒)
```

### 2. 所有时间统一为北京时间（UTC+8）

**修改的文件**：

#### `1.py` - 爬虫脚本
- ✅ 导入 `pytz` 并定义 `BEIJING_TZ = pytz.timezone('Asia/Shanghai')`
- ✅ `publish_time`: `datetime.fromtimestamp(..., tz=BEIJING_TZ)`
- ✅ `采摘时间`: `datetime.now(BEIJING_TZ)`
- ✅ 通知时间：使用北京时间
- ✅ 日志时间：使用北京时间

#### `backend/services/db.py` - 数据库服务
- ✅ `created_at`: `datetime.now(BEIJING_TZ)`
- ✅ `updated_at`: `datetime.now(BEIJING_TZ)`
- ✅ `sync_time`: `datetime.now(BEIJING_TZ)`
- ✅ 统计数据（今日/本周）：基于北京时间计算

#### `backend/services/importer.py` - 数据导入
- ✅ 时间解析：自动识别并转换为北京时间
- ✅ 支持字符串、datetime对象、无时区datetime的转换
- ✅ 智能处理UTC时间和其他时区

#### `backend/routes/sync.py` - 同步路由
- ✅ 同步日志时间：使用北京时间
- ✅ 耗时计算：基于北京时间

#### `backend/app.py` - Flask应用
- ✅ 定时任务时间：使用北京时间
- ✅ 调度器时区：设置为北京时区

#### `backend/requirements.txt`
- ✅ 添加依赖：`pytz==2024.1`

### 3. 数据迁移工具

**新增文件**：`backend/migrate_timezone.py`

**功能**：
- 将MongoDB中现有数据的时间字段转换为北京时间
- 支持的集合：
  - `sponge_items`（职位数据）
  - `sync_logs`（同步日志）
- 支持的时间字段：
  - `采摘时间`
  - `publish_time`
  - `created_at`
  - `updated_at`
  - `sync_time`

**使用方法**：
```bash
cd backend
python migrate_timezone.py
```

**运行时提示**：
```
⚠️  警告：此脚本将修改数据库中的所有时间字段
数据库: paquzijie_sponge
连接: mongodb+srv://byte123:fXb39P2JDuJA6U8S@yierbu...

确定要继续吗？(yes/no): yes
```

**执行结果**：
- 自动扫描所有时间字段
- 智能识别时区并转换
- 详细的迁移日志
- 最终汇总报告

## 📊 时间处理逻辑

### 时区转换规则

1. **字符串时间** (`'2025-10-21 14:30:00'`)
   - 假设为北京时间
   - 添加时区信息：`BEIJING_TZ.localize(dt)`

2. **无时区的datetime对象**
   - 假设为北京时间
   - 添加时区信息：`BEIJING_TZ.localize(dt)`

3. **UTC时间**
   - 转换为北京时间
   - `dt.astimezone(BEIJING_TZ)`

4. **其他时区**
   - 转换为北京时间
   - `dt.astimezone(BEIJING_TZ)`

### MongoDB存储说明

- MongoDB内部以UTC时间存储datetime对象
- 读取时pytz会自动处理时区转换
- 显示时确保时区信息正确

## 🚀 部署更新

### 本地开发

1. **安装新依赖**：
```bash
cd backend
pip install -r requirements.txt
```

2. **运行数据迁移**（可选，如有历史数据）：
```bash
python migrate_timezone.py
```

3. **启动后端**：
```bash
python app.py
```

4. **验证定时任务**：
查看日志确认调度器启动：
```
✅ 定时调度器已启动，每30分钟执行一次爬取任务
```

### Zeabur部署

**无需额外配置**，Zeabur会自动：
1. 读取 `requirements.txt` 安装 `pytz`
2. 运行 `backend/app.py` 启动调度器
3. 调度器会在后台每30分钟执行一次爬取

**注意**：
- Zeabur服务器时区可能不同，但代码中强制使用北京时区
- 所有时间显示都会是北京时间
- 数据迁移建议在本地完成后再部署

## 📝 验证方法

### 1. 验证定时任务
查看后端日志，应该看到：
```
[定时任务] 开始执行爬取任务 - 2025-10-21 HH:MM:SS
[定时任务] 任务完成 - 2025-10-21 HH:MM:SS (耗时: XX秒)
```

### 2. 验证时间显示
- 检查Excel文件中的 `采摘时间` 列
- 查看MongoDB中的时间字段
- 前端页面显示的时间

### 3. 验证时区
```python
from datetime import datetime
import pytz

BEIJING_TZ = pytz.timezone('Asia/Shanghai')
now = datetime.now(BEIJING_TZ)
print(now)  # 应显示类似：2025-10-21 14:30:00+08:00
```

## ⚠️ 注意事项

1. **首次运行**：
   - 如果有历史数据，建议运行迁移脚本
   - 迁移会修改数据库，建议先备份

2. **定时任务冲突**：
   - 避免同时运行多个后端实例
   - 调度器使用 `replace_existing=True` 防止重复任务

3. **时区一致性**：
   - 所有代码统一使用 `BEIJING_TZ`
   - 避免使用 `datetime.now()` 无时区版本
   - MongoDB查询时注意时区匹配

4. **Zeabur环境**：
   - 服务器可能在其他时区
   - 但代码强制使用北京时间
   - 日志时间会显示为北京时间

## 🔗 相关文件

- `1.py` - 爬虫脚本（30分钟执行一次）
- `backend/app.py` - Flask应用 + 调度器
- `backend/services/db.py` - 数据库服务
- `backend/services/importer.py` - 数据导入
- `backend/routes/sync.py` - 同步路由
- `backend/migrate_timezone.py` - 数据迁移工具
- `backend/requirements.txt` - Python依赖

## 📦 Git提交

**提交信息**：
```
feat: 调整爬取频率为30分钟并统一使用北京时间
```

**已推送到GitHub**：
```
To https://github.com/mariohuang233/bytemonitor233.git
   6f5ce80..22e9477  main -> main
```

---

**更新完成时间**：2025-10-21  
**版本**：v1.1.0

