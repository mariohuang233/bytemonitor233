# 字节跳动招聘监测

在线浏览：https://mariohuang233.github.io/bytemonitor233/

采集实习、校园和社会招聘的全部城市岗位，展示城市、团队、岗位详情和原始职位链接，支持城市筛选、关键词搜索和字段排序，并记录新增、字段修改、重新上线与下架。信息更新时间仅在岗位内容或状态发生变化时改变。

## 云端自动采集

GitHub Actions 工作流 `.github/workflows/monitor.yml` 每天运行三次，计划时间为北京时间每天 10:00、16:00、22:00（UTC 02:00、08:00、14:00），GitHub 的实际启动时间可能延迟。也可在 Actions 页选择 **Collect jobs and publish Pages → Run workflow** 手动触发。

采集器按每页 200 条抓取并检查总数，每类最多重试三次。失败或分页不完整时保留该类历史数据。每次结果写入 `state/monitor.json.gz` 并提交到仓库，随后构建并发布 GitHub Pages。该文件包含招聘岗位、最近 3,000 条变化及最近 90 次云端运行记录，不包含本机 Windows 调度配置、用户目录或通知设置。Git 提交历史可用于恢复旧快照。

Pages 是静态网页，浏览器负责搜索、城市筛选、排序和分页；网页上的“采集记录”按钮打开 GitHub Actions。云端通知由 GitHub Actions 的工作流通知设置管理，本地 Windows 提醒仍由本地管理台提供。在线版导出支持 CSV 和 JSON。

仓库 Settings → Pages 的 **Source** 应设为 **GitHub Actions**，Actions 需要 `contents: write`、`pages: write` 和 `id-token: write` 权限，工作流已声明。仓库公开，因此岗位数据也公开。按 GitHub 平台规则，长期无仓库活动的定时工作流可能被停用，可在 Actions 中重新启用。

## 本地使用

安装 Python 3.12 后运行 `pip install -r requirements-cloud.txt` 与 `python -m playwright install chromium`，再执行 `python job_dashboard.py`，浏览器打开 `http://127.0.0.1:8765`。如需 Excel 导出，另外安装 `pandas openpyxl`。Windows 用户也可以使用 `启动管理台.bat`。本地完整使用说明见 `使用说明.md`。

从本地数据库生成云端基线：`python cloud_pipeline.py seed --database data/jobs.db`；仅重新构建静态网站：`python cloud_pipeline.py build`。`public/` 是生成目录，可用 `python -m http.server 8000 --directory public` 预览。

仓库原有 `backend/`、`frontend/` 与旧部署说明作为历史实现保留，当前 Pages 发布使用根目录采集器与 `web/` 页面。
