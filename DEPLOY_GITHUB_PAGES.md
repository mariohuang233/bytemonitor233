# 部署到 mariohuang233/bytemonitor233

此版本已准备好以下流程：每天北京时间 10:00、16:00、22:00 由 GitHub Actions 抓取全部城市岗位，将历史数据与变化记录提交到仓库，再发布 GitHub Pages。

部署包中的文件应放到仓库根目录，保留原仓库其他文件。工作流文件位于 `.github/workflows/monitor.yml`，数据基线位于 `state/monitor.json.gz`。这份基线已从现有本地数据库导出，不包含本机通知设置、Windows 任务设置或本机运行日志。

在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。在 **Actions** 中打开 **Collect jobs and publish Pages** 并选择 **Run workflow**，即可立即执行第一次采集和发布。

部署后的网址为 https://mariohuang233.github.io/bytemonitor233/ 。GitHub 的定时任务可能出现排队延迟；精确配置为 UTC 02:00、08:00、14:00（北京时间 10:00、16:00、22:00）。

如果 GitHub 应用报告 `403 Resource not accessible by integration`，需在 GitHub 应用授权中允许该仓库的 Contents 写入和 Workflows 写入；使用其他上传方式时，同样需要相应权限。Pages 设置只需配置一次。

本地验证：`pip install -r requirements-cloud.txt`，然后运行 `python -m unittest test_city_collection test_cloud_pipeline -v`。重新生成静态网页运行 `python cloud_pipeline.py build`，预览运行 `python -m http.server 8000 --directory public`。
