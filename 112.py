import asyncio
import hashlib
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Any

import openpyxl
import pandas as pd
from openpyxl.styles import PatternFill
from playwright.async_api import async_playwright, Browser
from collector import TASKS, PersistentCollector

# --- 1. 配置区 ---

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

# 数据文件与程序放在同一目录，确保管理台和独立采集进程使用同一份缓存。
DOCUMENTS_PATH = Path(__file__).resolve().parent
OUTPUT_FILENAME = DOCUMENTS_PATH / "bytedance_jobs_tracker.xlsx"
JSON_CACHE_FILENAME = DOCUMENTS_PATH / "bytedance_jobs_cache.json"

# 与管理台共用全城市分页采集配置。
TASK_CONFIGS: List[Dict[str, Any]] = [
    {
        'id': 1,
        'name': '实习招聘',
        'sheet_name': 'intern',
        'url': TASKS[0]['url'],
        'api_url_mark': "api/v1/search/job/posts",
        'extra_fields': []
    },
    {
        'id': 2,
        'name': '校园招聘',
        'sheet_name': 'campus',
        'url': TASKS[1]['url'],
        'api_url_mark': "api/v1/search/job/posts",
        'extra_fields': ['location', 'department']
    },
    {
        'id': 3,
        'name': '社会招聘',
        'sheet_name': 'experienced',
        'url': TASKS[2]['url'],
        'api_url_mark': "api/v1/search/job/posts",
        'extra_fields': ['location', 'department']
    }
]

# --- 2. 核心逻辑区 ---

class JobMonitor:
    """招聘职位管理器（异步版），封装采集、数据处理、保存和通知逻辑"""

    def __init__(self, tasks: List[Dict[str, Any]], filename: Path, headless: bool = True):
        self.tasks = tasks
        self.filename = filename
        self.json_cache_filename = JSON_CACHE_FILENAME
        self.headless = headless
        self.results: List[tuple[str, str, List[Dict[str, Any]]]] = []
        # 招聘类型展示名称
        self.job_to_sponge = {
            '实习招聘': '实习招聘',
            '校园招聘': '校园招聘',
            '社会招聘': '社会招聘'
        }

    @staticmethod
    def _generate_job_hash(job_data: Dict[str, Any]) -> str:
        """仅使用岗位 code 字段生成唯一标识"""
        code_val = str(job_data.get('code', ''))
        return hashlib.md5(code_val.encode('utf-8')).hexdigest()
    
    def _save_json_cache(self, data_frames: Dict[str, pd.DataFrame]) -> None:
        """将数据保存为JSON缓存文件"""
        try:
            cache_data = {}
            for sheet_name, df in data_frames.items():
                records = df.to_dict('records')
                for record in records:
                    # 处理JSON不可序列化的值
                    for key, value in record.items():
                        if pd.isna(value):
                            record[key] = None
                        elif isinstance(value, (pd.Timestamp, datetime)):
                            record[key] = str(value)
                cache_data[sheet_name] = records
            
            with open(self.json_cache_filename, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"💾 招聘职位数据已存档")
        except Exception as e:
            logging.error(f"⚠️ 存档时遇到问题: {e}")
    
    def _load_json_cache(self) -> Dict[str, pd.DataFrame]:
        """从JSON缓存文件加载数据"""
        cache_dataframes: Dict[str, pd.DataFrame] = {}
        
        if not self.json_cache_filename.exists():
            logging.info(f"暂无存档记录。")
            return cache_dataframes
        
        try:
            with open(self.json_cache_filename, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            for sheet_name, records in cache_data.items():
                if records:
                    df = pd.DataFrame(records)
                    # 兼容旧字段名，将highlight_time迁移到采摘时间
                    if 'highlight_time' in df.columns and '采摘时间' not in df.columns:
                        df['采摘时间'] = df['highlight_time']
                        df = df.drop(columns=['highlight_time'], errors='ignore')
                    elif 'highlight_time' in df.columns:
                        # 如果两个字段都存在，优先用采摘时间，然后删除旧字段
                        df = df.drop(columns=['highlight_time'], errors='ignore')
                    
                    # 确保有必要的时间列
                    if '掉落时间' not in df.columns:
                        df['掉落时间'] = None
                    
                    # 将掉落后的职位的is_new重置为False
                    if 'is_new' in df.columns:
                        df.loc[df['掉落时间'].notna(), 'is_new'] = False
                    
                    cache_dataframes[sheet_name] = df
                    logging.info(f"已从存档加载 {self._get_sponge_by_sheet(sheet_name)} 的 {len(records)} 条。")
            
        except Exception as e:
            logging.warning(f"读取存档时遇到问题: {e}。将重新整理。")
        
        return cache_dataframes
    
    def _get_sponge_by_sheet(self, sheet_name: str) -> str:
        """通过工作表名获取对应的招聘类型。"""
        sheet_to_sponge = {'intern': '实习招聘', 'campus': '校园招聘', 'experienced': '社会招聘'}
        return sheet_to_sponge.get(sheet_name, sheet_name)
    
    @staticmethod
    def _sort_jobs_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """统一排序：掉落的放最下面，其他按采摘时间-publish time排序"""
        # 创建排序键列
        df = df.copy()
        
        # 1. 标记是否已掉落（有掉落时间）
        df['_is_dropped'] = False
        if '掉落时间' in df.columns:
            df['_is_dropped'] = df['掉落时间'].notna()
        
        # 2. 创建排序用的时间列
        df['_sort_time'] = None
        
        # 优先级：采摘时间 > publish_time
        if '采摘时间' in df.columns:
            # 使用采摘时间
            df['_sort_time'] = pd.to_datetime(df['采摘时间'], errors='coerce')
        elif 'publish_time' in df.columns:
            # 既没有采摘时间也没有掉落时间，使用publish_time
            df['_sort_time'] = pd.to_datetime(df['publish_time'], errors='coerce')
        
        # 排序：将掉落的放最后（_is_dropped为True的排后）
        # True=1, False=0，ascending=True时，0在前1在后
        df['_sort_priority'] = df['_is_dropped'].astype(int)
        
        # 按优先级和时间排序
        df = df.sort_values(
            by=['_sort_priority', '_sort_time'], 
            ascending=[True, False],  # 优先级升序(False=0在前, True=1在后)，时间降序(新的在前)
            na_position='last'
        )
        
        # 清理临时列
        df = df.drop(columns=['_is_dropped', '_sort_time', '_sort_priority'], errors='ignore')
        
        return df

    def _load_existing_hashes(self) -> tuple[Dict[str, Set[str]], Dict[str, pd.DataFrame]]:
        """从缓存或 Excel 加载各招聘类型的哈希值和数据。"""
        existing_hashes: Dict[str, Set[str]] = {}
        existing_dataframes: Dict[str, pd.DataFrame] = {}
        
        # 优先从存档加载
        cache_dataframes = self._load_json_cache()
        if cache_dataframes:
            logging.info("已使用存档数据。")
            existing_dataframes = cache_dataframes
        elif self.filename.exists():
            logging.info("从清单文件加载数据。")
            try:
                with pd.ExcelFile(self.filename, engine='openpyxl') as xls:
                    for sheet_name in xls.sheet_names:
                        df = pd.read_excel(xls, sheet_name=sheet_name)
                        
                        # 兼容旧字段名，将highlight_time迁移到采摘时间
                        if 'highlight_time' in df.columns and '采摘时间' not in df.columns:
                            df['采摘时间'] = df['highlight_time']
                            df = df.drop(columns=['highlight_time'], errors='ignore')
                        elif 'highlight_time' in df.columns:
                            # 如果两个字段都存在，优先用采摘时间，然后删除旧字段
                            df = df.drop(columns=['highlight_time'], errors='ignore')
                        
                        # 确保有必要的时间列
                        if '掉落时间' not in df.columns:
                            df['掉落时间'] = None
                        
                        existing_dataframes[sheet_name] = df
                        sponge_type = self._get_sponge_by_sheet(sheet_name)
                        logging.info(f"已加载 {sponge_type} 的 {len(df)} 条。")
            except Exception as e:
                logging.warning(f"读取清单文件时遇到问题: {e}。将重新整理。")
        else:
            logging.info(f"首次整理，将创建新清单。")
        
        # 生成各招聘类型的标识
        for sheet_name, df in existing_dataframes.items():
            hashes = {self._generate_job_hash(row.to_dict()) for _, row in df.iterrows()}
            existing_hashes[sheet_name] = hashes
            sponge_type = self._get_sponge_by_sheet(sheet_name)
            logging.info(f"已整理 {sponge_type} {len(hashes)} 条标识。")
        
        return existing_hashes, existing_dataframes

    async def _run_single_task_async(self, task_config: Dict[str, Any], browser: Browser) -> None:
        """异步执行单个招聘职位采集任务。"""
        task_name = task_config['name']
        sponge_type = self.job_to_sponge.get(task_name, task_name)
        sheet_name = task_config['sheet_name']
        scraped_jobs: List[Dict[str, Any]] = []
        collector = PersistentCollector(DOCUMENTS_PATH / 'data' / 'artifacts')
        collector.browser = browser
        task = {**task_config, 'source_type': sheet_name}
        result = await collector._collect_with_retry(task)
        if result['status'] == 'success':
            scraped_jobs = result['jobs']
            logging.info(f"{sponge_type} 全城市采集完成，共 {len(scraped_jobs)} 条。")
        else:
            logging.error(f"{sponge_type} 采集失败，保留原数据：{result['error']}")
        self.results.append((sheet_name, task_name, scraped_jobs))

    def _process_results(self, existing_hashes: Dict[str, Set[str]], existing_dataframes: Dict[str, pd.DataFrame]) -> Dict:
        """整理结果：删除‘重新出现’逻辑，掉落后再次出现视为新岗位"""
        final_data_frames: Dict[str, pd.DataFrame] = {}
        summary_info: List[Dict[str, Any]] = []
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for sheet_name, task_name, new_jobs_data in self.results:
            sponge_type = self.job_to_sponge.get(task_name, task_name)
            previous_hashes = existing_hashes.get(sheet_name, set())
            existing_df = existing_dataframes.get(sheet_name, pd.DataFrame())

            if not new_jobs_data:
                if not existing_df.empty:
                    final_data_frames[sheet_name] = self._sort_jobs_dataframe(existing_df)
                summary_info.append({'task_name': task_name, 'new_count': 0, 'total_count': len(existing_df)})
                logging.info(f"ℹ️ {sponge_type} 无新增，保留原有 {len(existing_df)} 条。")
                continue

            # 标记新条目并添加采摘时间
            for job in new_jobs_data:
                job_hash = self._generate_job_hash(job)
                is_new = job_hash not in previous_hashes
                job['is_new'] = is_new
                job['job_hash'] = job_hash
                job['采摘时间'] = current_time if is_new else None
                # 删除对重新出现的判定
                # job['重新出现时间'] = None  # 移除初始化

            new_df = pd.DataFrame(new_jobs_data)

            # 合并新旧清单
            if not existing_df.empty:
                if 'is_new' not in existing_df.columns:
                    existing_df['is_new'] = False
                if '采摘时间' not in existing_df.columns:
                    existing_df['采摘时间'] = None
                if '掉落时间' not in existing_df.columns:
                    existing_df['掉落时间'] = None

                existing_df['job_hash'] = existing_df.apply(lambda row: self._generate_job_hash(row.to_dict()), axis=1)

                new_hashes = set(new_df['job_hash'])
                disappeared_count = 0
                for idx, row in existing_df.iterrows():
                    if row['job_hash'] not in new_hashes and pd.isna(row['掉落时间']):
                        existing_df.at[idx, '掉落时间'] = current_time
                        # 掉落后重置is_new为False
                        existing_df.at[idx, 'is_new'] = False
                        disappeared_count += 1
                if disappeared_count > 0:
                    logging.info(f"📉 {sponge_type} 检测到 {disappeared_count} 条已掉落，已记录掉落时间。")
                # 不再恢复采摘时间、掉落时间以外的任何时间
                old_hash_to_pick_time = dict(zip(existing_df['job_hash'], existing_df['采摘时间']))
                old_hash_to_drop_time = dict(zip(existing_df['job_hash'], existing_df['掉落时间']))
                for idx, row in new_df.iterrows():
                    if not row['is_new'] and row['job_hash'] in old_hash_to_pick_time:
                        new_df.at[idx, '采摘时间'] = old_hash_to_pick_time[row['job_hash']]
                    if not row['is_new'] and row['job_hash'] in old_hash_to_drop_time:
                        new_df.at[idx, '掉落时间'] = old_hash_to_drop_time[row['job_hash']]
                # 合并、去重
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=['job_hash'], keep='last')
                combined_df = combined_df.drop(columns=['job_hash'])
                final_df = combined_df
            else:
                final_df = new_df.drop(columns=['job_hash'], errors='ignore')
                if '掉落时间' not in final_df.columns:
                    final_df['掉落时间'] = None
            final_df = self._sort_jobs_dataframe(final_df)
            final_data_frames[sheet_name] = final_df

            new_count = final_df['is_new'].sum() if 'is_new' in final_df.columns else 0
            has_pick_time_count = final_df['采摘时间'].notna().sum() if '采摘时间' in final_df.columns else 0
            has_drop_time_count = final_df['掉落时间'].notna().sum() if '掉落时间' in final_df.columns else 0
            summary_info.append({
                'task_name': task_name,
                'new_count': new_count,
                'total_count': len(final_df)
            })
            logging.info(f"ℹ️ {sponge_type} 新增 {new_count} 条，当前共 {len(final_df)} 条（采摘时间:{has_pick_time_count}条，掉落时间:{has_drop_time_count}条）。")
        return {"data_frames": final_data_frames, "summary": summary_info}

    def _save_and_highlight(self, data_frames: Dict[str, pd.DataFrame]) -> None:
        """保存清单到Excel并高亮新条目"""
        if not data_frames:
            logging.info("暂无数据需要保存。")
            return
            
        try:
            # 保存Excel文件
            with pd.ExcelWriter(self.filename, engine='openpyxl') as writer:
                for sheet_name, df in data_frames.items():
                    # 隐藏is_new字段，保留采摘时间等展示字段
                    display_df = df.drop(columns=['is_new'], errors='ignore')
                    
                    # 调试：确认时间列是否存在
                    sponge_type = self._get_sponge_by_sheet(sheet_name)
                    has_pick_time = '采摘时间' in display_df.columns
                    has_drop_time = '掉落时间' in display_df.columns
                    # has_reappear_time = '重新出现时间' in display_df.columns # 移除
                    
                    if has_pick_time:
                        pick_time_count = display_df['采摘时间'].notna().sum()
                        logging.info(f"📝 准备保存 {sponge_type}：包含采摘时间列，{pick_time_count}条有时间记录")
                    else:
                        logging.warning(f"⚠️ {sponge_type} 数据中缺少采摘时间列！")
                    
                    if has_drop_time:
                        drop_time_count = display_df['掉落时间'].notna().sum()
                        logging.info(f"📉 {sponge_type} 包含掉落时间列，{drop_time_count}条有掉落记录")
                    else:
                        logging.warning(f"⚠️ {sponge_type} 数据中缺少掉落时间列！")
                    
                    # if has_reappear_time: # 移除
                    #     reappear_time_count = display_df['重新出现时间'].notna().sum()
                    #     logging.info(f"🔄 {sponge_type} 包含重新出现时间列，{reappear_time_count}条有重新出现记录")
                    # else:
                    #     logging.warning(f"⚠️ {sponge_type} 数据中缺少重新出现时间列！")
                    
                    # 确保时间列在靠前位置（方便查看）
                    if has_pick_time or has_drop_time: # 移除has_reappear_time
                        time_cols = []
                        if has_pick_time:
                            time_cols.append('采摘时间')
                        if has_drop_time:
                            time_cols.append('掉落时间')
                        # if has_reappear_time: # 移除
                        #     time_cols.append('重新出现时间')
                        other_cols = [col for col in display_df.columns if col not in time_cols]
                        display_df = display_df[time_cols + other_cols]
                    
                    display_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # 为新条目添加黄色高亮，重新出现橙色，已掉落红色
            workbook = openpyxl.load_workbook(self.filename)
            highlight_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")  # 黄：新
            # reappear_fill  = PatternFill(start_color="FFA500", end_color="FFA500", fill_type="solid")  # 橙：重新出现 # 移除
            drop_fill     = PatternFill(start_color="FF3333", end_color="FF3333", fill_type="solid")  # 红：掉落

            for sheet_name, df in data_frames.items():
                if sheet_name in workbook.sheetnames and 'is_new' in df.columns:
                    worksheet = workbook[sheet_name]
                    for row_idx, (is_new, drop_time) in enumerate(
                        zip(df['is_new'],
                            df['掉落时间'] if '掉落时间' in df.columns else [None]*len(df)),
                        start=2):  # 跳过表头
                        # ① 已掉落(掉落时间有): 红色
                        if drop_time is not None and pd.notna(drop_time):
                            for col_idx in range(1, worksheet.max_column + 1):
                                worksheet.cell(row=row_idx, column=col_idx).fill = drop_fill
                        # ② 新增: 黄色（保持原状）
                        elif is_new:
                            for col_idx in range(1, worksheet.max_column + 1):
                                worksheet.cell(row=row_idx, column=col_idx).fill = highlight_fill
            workbook.save(self.filename)
            logging.info(f"💾 清单已保存。")
            
            # 保存JSON缓存
            self._save_json_cache(data_frames)
            
        except Exception as e:
            logging.error(f"⚠️ 保存清单时遇到问题: {e}")
            # 即使Excel保存失败，仍尝试保存缓存
            try:
                self._save_json_cache(data_frames)
            except Exception as cache_error:
                logging.error(f"⚠️ 存档时遇到问题: {cache_error}")

    @staticmethod
    def _send_notification(summary: List[Dict[str, Any]]) -> None:
        """发送招聘职位变化桌面通知。"""
        job_to_sponge = {'实习招聘': '实习招聘', '校园招聘': '校园招聘', '社会招聘': '社会招聘'}
        # 统计各招聘类型数据
        type_stats = {}
        total_new = 0
        total_count = 0
        for info in summary:
            job_type = info['task_name']
            sponge_type = job_to_sponge.get(job_type, job_type)
            new_cnt = info.get('new_count', 0)
            total_cnt = info.get('total_count', 0)
            type_stats[sponge_type] = {
                'new': new_cnt, 
                'total': total_cnt
            }
            total_new += new_cnt
            total_count += total_cnt
        current_time = datetime.now().strftime("%H:%M")

        # 有变化时的通知内容
        if total_new > 0:
            title = "招聘职位有变化"
            
            # 构建详细信息
            details_parts = []
            for sponge_type, stats in type_stats.items():
                if stats['new'] > 0:
                    detail_parts = []
                    if stats['new'] > 0:
                        detail_parts.append(f"新增{stats['new']}个")
                    details_parts.append(f"   • {sponge_type}: {', '.join(detail_parts)}，共{stats['total']}个")
            
            details = "\\n".join(details_parts)
            
            # 构建变化摘要
            change_summary = []
            if total_new > 0:
                change_summary.append(f"新增{total_new}个")
            
            message = f"本次变化: {', '.join(change_summary)}\\n当前共有 {total_count} 个职位\\n时间: {current_time}\\n\\n分类情况:\\n{details}"
        # 无变化时的通知内容
        else:
            title = "招聘职位采集完成"
            details = "\\n".join(
                f"   • {sponge_type}: 共{stats['total']}个"
                for sponge_type, stats in type_stats.items()
            )
            message = f"本次没有变化\\n当前共有 {total_count} 个职位\\n时间: {current_time}\\n\\n存量情况:\\n{details}"

        # macOS 通知（AppleScript）
        if sys.platform == "darwin":
            buttons = '{"稍后整理", "现在看看"}'
            default_button = '"现在看看"'
            action_script = f'do shell script "open \\"{OUTPUT_FILENAME}\\""'
            script = f'''
            try
                set response to display dialog "{message}" with title "{title}" buttons {buttons} default button {default_button} with icon note
                if button returned of response is "现在看看" then
                    {action_script}
                end if
            on error errMsg number errNum
                -- 静默处理用户取消等异常
            end try
            '''
            try:
                result = subprocess.run(
                    ['osascript', '-e', script], 
                    capture_output=True, text=True, timeout=120, check=False
                )
                if result.returncode != 0:
                    logging.error("⚠️ 招聘职位通知发送失败，脚本执行出错。")
                    logging.error(f"   - 返回码: {result.returncode}")
                    logging.error(f"   - 错误输出: {result.stderr.strip()}")
                else:
                    logging.info("🔔 招聘职位通知已发送。")
            except subprocess.TimeoutExpired:
                logging.warning("⚠️ 招聘职位通知超时，用户可能未及时响应。")
            except Exception as e:
                logging.error(f"⚠️ 发送招聘职位通知时发生错误: {e}")
        # Windows 通知（PowerShell）
        elif sys.platform == "win32":
            try:
                # 转换消息格式，将\\n替换为实际换行
                message_formatted = message.replace("\\n", "\n").replace('"', '""')
                title_formatted = title.replace('"', '""')
                
                # 使用PowerShell发送Windows MessageBox通知（最明显的方式）
                ps_script = f'''
                try {{
                    # 方法1: 使用MessageBox（最明显，模态对话框）
                    Add-Type -AssemblyName PresentationFramework
                    [System.Windows.MessageBox]::Show("{message_formatted}", "{title_formatted}", "OK", "Information")
                }} catch {{
                    # 方法2: 使用WScript Popup（也很明显）
                    try {{
                        $wshell = New-Object -ComObject WScript.Shell
                        $wshell.Popup("{message_formatted}", 0, "{title_formatted}", 0 + 64)
                    }} catch {{
                        # 方法3: 使用Toast通知（作为最后备选）
                        try {{
                            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
                            
                            $template = @"
                            <toast duration="long">
                                <visual>
                                    <binding template="ToastGeneric">
                                        <text>{title_formatted}</text>
                                        <text>{message_formatted}</text>
                                    </binding>
                                </visual>
                                <audio src="ms-winsoundevent:Notification.Default" />
                            </toast>
                            "@
                            
                            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
                            $xml.LoadXml($template)
                            $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
                            $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("招聘职位管理台")
                            $notifier.Show($toast)
                        }} catch {{
                            # 方法4: 使用气球通知（最后的备选）
                            Add-Type -AssemblyName System.Windows.Forms
                            Add-Type -AssemblyName System.Drawing
                            
                            $balloon = New-Object System.Windows.Forms.NotifyIcon
                            $balloon.Icon = [System.Drawing.SystemIcons]::Information
                            $balloon.BalloonTipIcon = "Info"
                            $balloon.BalloonTipTitle = "{title_formatted}"
                            $balloon.BalloonTipText = "{message_formatted}"
                            $balloon.Visible = $true
                            $balloon.ShowBalloonTip(30000)
                            [System.Media.SystemSounds]::Asterisk.Play()
                            Start-Sleep -Seconds 30
                            $balloon.Dispose()
                        }}
                    }}
                }}
                '''
                
                result = subprocess.run(
                    ['powershell', '-NoProfile', '-Command', ps_script],
                    capture_output=True, text=True, timeout=120, check=False,
                    shell=True
                )
                
                if result.returncode == 0:
                    logging.info("🔔 招聘职位通知已发送。")
                else:
                    logging.warning(f"⚠️ 招聘职位通知发送失败: {result.stderr.strip()}")
            except subprocess.TimeoutExpired:
                logging.warning("⚠️ 招聘职位通知超时。")
            except Exception as e:
                logging.error(f"⚠️ 发送招聘职位通知时发生错误: {e}")
        # 其他平台 日志通知
        else:
            logging.info("--- 招聘职位采集通知 ---")
            logging.info(f"标题: {title}")
            logging.info(message.replace("\\n", "\n"))
            logging.info("---------------------")

    async def run_async(self, silent_mode: bool = False, send_notification: bool = True):
        """执行完整的清单整理流程（异步）"""
        start_time = datetime.now()
        logging.info(f"--- 开始整理 {start_time.strftime('%Y-%m-%d %H:%M:%S')} ---")
        
        # 确保输出目录存在
        DOCUMENTS_PATH.mkdir(exist_ok=True)
        
        # 加载历史清单
        existing_hashes, existing_dataframes = self._load_existing_hashes()
        
        # 异步抓取各招聘类型
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            tasks_to_run = [self._run_single_task_async(task, browser) for task in self.tasks]
            await asyncio.gather(*tasks_to_run)
            await browser.close()

        # 处理整理结果
        results = self._process_results(existing_hashes, existing_dataframes)
        data_frames = results["data_frames"]
        summary = results["summary"]
        
        # 保存并高亮新条目
        self._save_and_highlight(data_frames)
        
        # 输出整理结果日志
        total_new = sum(info.get('new_count', 0) for info in summary)
        total_count = sum(info.get('total_count', 0) for info in summary)
        
        if not silent_mode or total_new > 0:
            logging.info("--- 整理结果 ---")
            for info in summary:
                sponge_type = self.job_to_sponge.get(info['task_name'], info['task_name'])
                changes = []
                if info.get('new_count', 0) > 0:
                    changes.append(f"新增{info['new_count']}条")
                
                if changes:
                    logging.info(f"  - {sponge_type}: {', '.join(changes)}，共{info.get('total_count', 0)}条")
                else:
                    logging.info(f"  - {sponge_type}: 无变化，共{info.get('total_count', 0)}条")
            
            summary_changes = []
            if total_new > 0:
                summary_changes.append(f"新增{total_new}条")
            
            if summary_changes:
                logging.info(f"总计变化: {', '.join(summary_changes)}")
            else:
                logging.info("总计无变化")
        
        # 发送通知；由本地管理台调度时统一根据数据库变更发送通知
        if send_notification and "--no-notification" not in sys.argv:
            self._send_notification(summary)
        
        # 流程结束
        end_time = datetime.now()
        logging.info(f"--- 整理完成, 耗时: {(end_time - start_time).total_seconds():.2f} 秒 ---")

# --- 3. 主程序入口 ---
if __name__ == "__main__":
    try:
        # 支持--auto参数开启静默模式（无新增时不输出详细日志）
        is_silent = "--auto" in sys.argv
        monitor = JobMonitor(tasks=TASK_CONFIGS, filename=OUTPUT_FILENAME, headless=True)
        asyncio.run(
            monitor.run_async(
                silent_mode=is_silent,
                send_notification="--no-notification" not in sys.argv,
            )
        )
        
    except KeyboardInterrupt:
        logging.info("\n⚠️ 整理已中断。")
        sys.exit(0)
    except Exception as e:
        if "Executable doesn't exist" in str(e):
            logging.critical("❌ 依赖未安装! 请先运行 'playwright install' 命令。")
        else:
            logging.critical(f"\n❌ 整理遇到严重问题: {e}", exc_info=True)
        sys.exit(1)
