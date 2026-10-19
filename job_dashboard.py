"""招聘职位本地管理台：调度爬虫、持久化数据并提供浏览 API。"""

from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import logging
import re
import os
import sqlite3
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from collector import PersistentCollector, job_cities

if sys.platform == "win32":
    import msvcrt


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "jobs.db"
STATIC_DIR = ROOT / "web"
ARTIFACT_DIR = DATA_DIR / "artifacts"
EXPORT_DIR = ROOT / "exports"
DEFAULT_CACHE = Path.home() / "Documents" / "bytedance_jobs_cache.json"
if not DEFAULT_CACHE.parent.exists():
    DEFAULT_CACHE = Path.home() / "文档" / "bytedance_jobs_cache.json"
if not DEFAULT_CACHE.exists() and (ROOT / "bytedance_jobs_cache.json").exists():
    DEFAULT_CACHE = ROOT / "bytedance_jobs_cache.json"

JOB_TYPES = {"intern": "实习招聘", "campus": "校园招聘", "experienced": "社会招聘"}
DEFAULT_SCHEDULE = {
    "enabled": False,
    "mode": "daily",
    "time": "09:00",
    "interval_minutes": 60,
    "weekdays": [0, 1, 2, 3, 4],
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def now_text() -> str:
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init_db() -> None:
    with connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_key TEXT NOT NULL UNIQUE,
                source_type TEXT NOT NULL,
                title TEXT,
                city TEXT,
                department TEXT,
                category TEXT,
                publish_time TEXT,
                picked_at TEXT,
                dropped_at TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                content_hash TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_jobs_type_active
                ON jobs(source_type, is_active);
            CREATE INDEX IF NOT EXISTS idx_jobs_publish
                ON jobs(publish_time DESC);
            CREATE TABLE IF NOT EXISTS changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_key TEXT NOT NULL,
                source_type TEXT NOT NULL,
                change_type TEXT NOT NULL,
                title TEXT,
                detail TEXT,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_changes_created
                ON changes(created_at DESC);
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                new_count INTEGER NOT NULL DEFAULT 0,
                updated_count INTEGER NOT NULL DEFAULT 0,
                dropped_count INTEGER NOT NULL DEFAULT 0,
                message TEXT
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        db.execute(
            "INSERT OR IGNORE INTO settings(key, value) VALUES('schedule', ?)",
            (json.dumps(DEFAULT_SCHEDULE, ensure_ascii=False),),
        )
        migrate_parsed_fields(db)
        migrate_operational_fields(db)
        migrate_city_index(db)


def canonical_payload(record: dict[str, Any]) -> str:
    ignored = {"is_new", "采摘时间", "掉落时间"}
    clean = {k: v for k, v in record.items() if k not in ignored}
    return json.dumps(clean, ensure_ascii=False, sort_keys=True, default=str)


def parse_job_fields(source_type: str, record: dict[str, Any]) -> dict[str, str | None]:
    """解析岗位名、团队名、团队介绍和官方网站详情链接。"""
    raw_title = str(record.get("title") or "").strip()
    job_name, team_name = raw_title, None
    title_parts = re.split(r"\s+-\s+", raw_title)
    if len(title_parts) >= 2:
        job_name = " - ".join(title_parts[:-1]).strip()
        team_name = title_parts[-1].strip() or None
    elif "-" in raw_title:
        left, right = raw_title.rsplit("-", 1)
        if left.strip() and right.strip():
            job_name, team_name = left.strip(), right.strip()

    description = str(record.get("description") or "").strip()
    intro_match = re.search(
        r"(?:^|\n)\s*团队介绍\s*[：:]\s*(.+?)(?=\n\s*\n|\n\s*(?:职位描述|岗位职责|工作职责|职位职责|任职要求|岗位要求)\s*[：:]|$)",
        description,
        flags=re.S,
    )
    team_intro = intro_match.group(1).strip() if intro_match else None
    job_id = record.get("job_id") or record.get("id")
    section = "experienced" if source_type == "experienced" else "campus"
    detail_url = (
        f"https://jobs.bytedance.com/{section}/position/{job_id}/detail"
        if job_id
        else record.get("pc_job_url")
    )
    return {
        "job_name": job_name or raw_title or None,
        "team_name": team_name,
        "team_intro": team_intro,
        "detail_url": detail_url,
    }


def migrate_parsed_fields(db: sqlite3.Connection) -> None:
    columns = {row["name"] for row in db.execute("PRAGMA table_info(jobs)")}
    for name in ("job_name", "team_name", "team_intro", "detail_url"):
        if name not in columns:
            db.execute(f"ALTER TABLE jobs ADD COLUMN {name} TEXT")
    rows = db.execute("SELECT job_key, source_type, payload FROM jobs").fetchall()
    for row in rows:
        parsed = parse_job_fields(row["source_type"], json.loads(row["payload"]))
        db.execute(
            """UPDATE jobs SET job_name=?, team_name=?, team_intro=?, detail_url=?
               WHERE job_key=?""",
            (
                parsed["job_name"],
                parsed["team_name"],
                parsed["team_intro"],
                parsed["detail_url"],
                row["job_key"],
            ),
        )


def migrate_operational_fields(db: sqlite3.Connection) -> None:
    job_columns = {row["name"] for row in db.execute("PRAGMA table_info(jobs)")}
    if "info_updated_at" not in job_columns:
        db.execute("ALTER TABLE jobs ADD COLUMN info_updated_at TEXT")
    db.execute(
        """UPDATE jobs
           SET info_updated_at=COALESCE(
               (SELECT MAX(changes.created_at) FROM changes
                WHERE changes.job_key=jobs.job_key),
               created_at,
               picked_at
           )
           WHERE info_updated_at IS NULL"""
    )
    change_columns = {row["name"] for row in db.execute("PRAGMA table_info(changes)")}
    for name in ("changed_fields", "before_json", "after_json"):
        if name not in change_columns:
            db.execute(f"ALTER TABLE changes ADD COLUMN {name} TEXT")
    run_columns = {row["name"] for row in db.execute("PRAGMA table_info(runs)")}
    for name in ("heartbeat_at", "details_json"):
        if name not in run_columns:
            db.execute(f"ALTER TABLE runs ADD COLUMN {name} TEXT")
    db.execute(
        "INSERT OR IGNORE INTO settings(key,value) VALUES('notifications', ?)",
        (json.dumps({"changes": True, "failures": True, "success_without_changes": False}),),
    )


def replace_city_index(db: sqlite3.Connection, job_key: str, cities: list[str]) -> None:
    db.execute("DELETE FROM job_cities WHERE job_key=?", (job_key,))
    db.executemany(
        "INSERT INTO job_cities(job_key,city) VALUES(?,?)",
        [(job_key, city) for city in cities],
    )


def migrate_city_index(db: sqlite3.Connection) -> None:
    db.executescript(
        """CREATE TABLE IF NOT EXISTS job_cities(
            job_key TEXT NOT NULL REFERENCES jobs(job_key) ON DELETE CASCADE,
            city TEXT NOT NULL,
            PRIMARY KEY(job_key,city)
        );
        CREATE INDEX IF NOT EXISTS idx_job_cities_city ON job_cities(city,job_key);"""
    )
    if db.execute("SELECT 1 FROM settings WHERE key='city_index_version'").fetchone():
        return
    for row in db.execute("SELECT job_key,city FROM jobs").fetchall():
        replace_city_index(db, row["job_key"], job_cities({"city_list": row["city"]}))
    db.execute("INSERT INTO settings(key,value) VALUES('city_index_version','1')")


def import_cache(cache_path: Path = DEFAULT_CACHE, record_changes: bool = True) -> dict[str, int]:
    """将爬虫缓存增量同步到 SQLite，并记录新增、更新和下架事件。"""
    if not cache_path.exists():
        raise FileNotFoundError(f"未找到爬虫缓存：{cache_path}")
    raw = json.loads(cache_path.read_text(encoding="utf-8"))
    stats = {"new": 0, "updated": 0, "dropped": 0, "total": 0}
    seen_by_type: dict[str, set[str]] = {}
    timestamp = now_text()

    with connect() as db:
        for source_type, records in raw.items():
            seen: set[str] = set()
            seen_by_type[source_type] = seen
            for record in records:
                code = str(record.get("code") or record.get("job_id") or "")
                if not code:
                    continue
                job_key = f"{source_type}:{code}"
                seen.add(job_key)
                payload = canonical_payload(record)
                content_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
                parsed = parse_job_fields(source_type, record)
                existing = db.execute(
                    "SELECT content_hash, is_active FROM jobs WHERE job_key=?", (job_key,)
                ).fetchone()
                dropped_at = record.get("掉落时间")
                active = 0 if dropped_at else 1
                fields = (
                    source_type,
                    record.get("title"),
                    record.get("city_list") or record.get("location"),
                    record.get("department") or record.get("team_name"),
                    record.get("job_category"),
                    record.get("publish_time"),
                    record.get("采摘时间"),
                    dropped_at,
                    active,
                    content_hash,
                    json.dumps(record, ensure_ascii=False, default=str),
                    parsed["job_name"],
                    parsed["team_name"],
                    parsed["team_intro"],
                    parsed["detail_url"],
                    timestamp,
                )
                if existing is None:
                    db.execute(
                        """INSERT INTO jobs(
                            job_key, source_type, title, city, department, category,
                            publish_time, picked_at, dropped_at, is_active, content_hash,
                            payload, job_name, team_name, team_intro, detail_url,
                            created_at, updated_at
                        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (job_key, *fields, timestamp),
                    )
                    if record_changes:
                        db.execute(
                            """INSERT INTO changes(job_key, source_type, change_type, title, detail, created_at)
                               VALUES(?,?,?,?,?,?)""",
                            (job_key, source_type, "new", record.get("title"), "首次采集", timestamp),
                        )
                        stats["new"] += 1
                else:
                    change_type = None
                    detail = None
                    if existing["content_hash"] != content_hash:
                        change_type, detail = "updated", "职位内容发生变化"
                        stats["updated"] += 1
                    if existing["is_active"] and not active:
                        change_type, detail = "dropped", "职位已下架"
                        stats["dropped"] += 1
                    elif not existing["is_active"] and active:
                        change_type, detail = "restored", "职位重新上线"
                        stats["updated"] += 1
                    db.execute(
                        """UPDATE jobs SET source_type=?, title=?, city=?, department=?,
                           category=?, publish_time=?, picked_at=?, dropped_at=?, is_active=?,
                           content_hash=?, payload=?, job_name=?, team_name=?, team_intro=?,
                           detail_url=?, updated_at=? WHERE job_key=?""",
                        (*fields, job_key),
                    )
                    if change_type:
                        db.execute(
                            """INSERT INTO changes(job_key, source_type, change_type, title, detail, created_at)
                               VALUES(?,?,?,?,?,?)""",
                            (job_key, source_type, change_type, record.get("title"), detail, timestamp),
                        )
                replace_city_index(db, job_key, job_cities(record))
                stats["total"] += 1
    return stats


def _payload_diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, dict[str, Any]]:
    ignored = {"is_new", "采摘时间", "掉落时间"}
    changes: dict[str, dict[str, Any]] = {}
    for field in sorted((set(before) | set(after)) - ignored):
        old, new = before.get(field), after.get(field)
        if old != new:
            changes[field] = {"before": old, "after": new}
    return changes


def sync_collection(results: dict[str, Any]) -> dict[str, int]:
    """将本次成功分类的采集结果直接写入 SQLite，并保留字段级差异。"""
    stats = {"new": 0, "updated": 0, "dropped": 0, "total": 0}
    timestamp = now_text()
    with connect() as db:
        for source_type, result in results.items():
            if result["status"] != "success":
                continue
            seen: set[str] = set()
            for record in result["jobs"]:
                code = str(record.get("code") or record.get("job_id") or "")
                if not code:
                    continue
                job_key = f"{source_type}:{code}"
                seen.add(job_key)
                parsed = parse_job_fields(source_type, record)
                payload_json = json.dumps(record, ensure_ascii=False, default=str)
                content_hash = hashlib.sha256(canonical_payload(record).encode("utf-8")).hexdigest()
                existing = db.execute(
                    "SELECT * FROM jobs WHERE job_key=?", (job_key,)
                ).fetchone()
                values = (
                    source_type,
                    record.get("title"),
                    record.get("city_list") or record.get("location"),
                    record.get("department"),
                    record.get("job_category"),
                    record.get("publish_time"),
                    1,
                    content_hash,
                    payload_json,
                    parsed["job_name"],
                    parsed["team_name"],
                    parsed["team_intro"],
                    parsed["detail_url"],
                    timestamp,
                )
                if existing is None:
                    db.execute(
                        """INSERT INTO jobs(
                            job_key,source_type,title,city,department,category,publish_time,
                            picked_at,dropped_at,is_active,content_hash,payload,job_name,
                            team_name,team_intro,detail_url,created_at,updated_at,info_updated_at
                        ) VALUES(?,?,?,?,?,?,?, ?,NULL,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            job_key, source_type, record.get("title"),
                            record.get("city_list") or record.get("location"),
                            record.get("department"), record.get("job_category"),
                            record.get("publish_time"), timestamp, 1, content_hash,
                            payload_json, parsed["job_name"], parsed["team_name"],
                            parsed["team_intro"], parsed["detail_url"], timestamp, timestamp,
                            timestamp,
                        ),
                    )
                    db.execute(
                        """INSERT INTO changes(
                            job_key,source_type,change_type,title,detail,created_at,
                            changed_fields,before_json,after_json
                        ) VALUES(?,?,?,?,?,?,?,?,?)""",
                        (
                            job_key, source_type, "new", parsed["job_name"],
                            "首次发现该职位", timestamp,
                            json.dumps(list(record.keys()), ensure_ascii=False),
                            None, payload_json,
                        ),
                    )
                    stats["new"] += 1
                else:
                    before = json.loads(existing["payload"])
                    differences = _payload_diff(before, record)
                    change_type = None
                    detail = None
                    if not existing["is_active"]:
                        change_type, detail = "restored", "职位重新上线"
                    elif differences:
                        change_type = "updated"
                        detail = "、".join(differences.keys()) + "发生变化"
                    info_updated_at = timestamp if change_type else existing["info_updated_at"]
                    db.execute(
                        """UPDATE jobs SET source_type=?,title=?,city=?,department=?,category=?,
                           publish_time=?,is_active=?,content_hash=?,payload=?,job_name=?,
                           team_name=?,team_intro=?,detail_url=?,updated_at=?,dropped_at=NULL,
                           info_updated_at=?
                           WHERE job_key=?""",
                        (*values, info_updated_at, job_key),
                    )
                    if change_type:
                        db.execute(
                            """INSERT INTO changes(
                                job_key,source_type,change_type,title,detail,created_at,
                                changed_fields,before_json,after_json
                            ) VALUES(?,?,?,?,?,?,?,?,?)""",
                            (
                                job_key, source_type, change_type, parsed["job_name"],
                                detail, timestamp,
                                json.dumps(list(differences.keys()), ensure_ascii=False),
                                json.dumps(before, ensure_ascii=False, default=str),
                                payload_json,
                            ),
                        )
                        stats["updated"] += 1
                replace_city_index(db, job_key, job_cities(record))
                stats["total"] += 1

            active_rows = db.execute(
                "SELECT job_key,title,payload FROM jobs WHERE source_type=? AND is_active=1",
                (source_type,),
            ).fetchall()
            for old in active_rows:
                if old["job_key"] in seen:
                    continue
                db.execute(
                    """UPDATE jobs SET is_active=0,dropped_at=?,updated_at=?,
                       info_updated_at=? WHERE job_key=?""",
                    (timestamp, timestamp, timestamp, old["job_key"]),
                )
                db.execute(
                    """INSERT INTO changes(
                        job_key,source_type,change_type,title,detail,created_at,
                        changed_fields,before_json,after_json
                    ) VALUES(?,?,?,?,?,?,?,?,?)""",
                    (
                        old["job_key"], source_type, "dropped", old["title"],
                        "本次完整采集中未再出现", timestamp,
                        json.dumps(["is_active"], ensure_ascii=False),
                        old["payload"], None,
                    ),
                )
                stats["dropped"] += 1
    return stats


class BrowserService:
    """在专用事件循环中维护可复用的 Playwright 浏览器。"""

    def __init__(self) -> None:
        self.loop = asyncio.new_event_loop()
        self.collector = PersistentCollector(ARTIFACT_DIR)
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def collect_all(self) -> dict[str, Any]:
        future = asyncio.run_coroutine_threadsafe(self.collector.collect_all(), self.loop)
        return future.result(timeout=600)

    def close(self) -> None:
        try:
            future = asyncio.run_coroutine_threadsafe(self.collector.close(), self.loop)
            future.result(timeout=20)
        finally:
            self.loop.call_soon_threadsafe(self.loop.stop)


class CrawlerRunner:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.running = False

    def start(self, reason: str = "manual") -> bool:
        with self.lock:
            if self.running:
                return False
            self.running = True
        threading.Thread(target=self._run, args=(reason,), daemon=True).start()
        return True

    def _run(self, reason: str) -> None:
        lock_path = DATA_DIR / "crawler.lock"
        DATA_DIR.mkdir(exist_ok=True)
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(descriptor, f"{os.getpid()} {now_text()}".encode("utf-8"))
            os.close(descriptor)
        except FileExistsError:
            if time.time() - lock_path.stat().st_mtime > 1800:
                lock_path.unlink(missing_ok=True)
                return self._run(reason)
            logging.warning("另一个采集任务正在运行，本次触发已跳过")
            with self.lock:
                self.running = False
            return
        started = now_text()
        with connect() as db:
            cursor = db.execute(
                """INSERT INTO runs(started_at,status,message,heartbeat_at)
                   VALUES(?,?,?,?)""",
                (started, "running", f"{reason} trigger", started),
            )
            run_id = cursor.lastrowid
        try:
            results = BROWSER_SERVICE.collect_all()
            with connect() as db:
                db.execute(
                    "UPDATE runs SET heartbeat_at=? WHERE id=?", (now_text(), run_id)
                )
            stats = sync_collection(results)
            failed = [item for item in results.values() if item["status"] == "failed"]
            run_details = {
                key: {
                    "name": item["name"],
                    "status": item["status"],
                    "count": len(item["jobs"]),
                    "attempts": item["attempts"],
                    "error": item["error"],
                }
                for key, item in results.items()
            }
            status = "partial" if failed else "success"
            message = (
                f"同步完成，共 {stats['total']} 条"
                if not failed
                else "部分成功；" + "；".join(f"{x['name']}：{x['error']}" for x in failed)
            )
            with connect() as db:
                db.execute(
                    """UPDATE runs SET finished_at=?, status=?, new_count=?,
                       updated_count=?, dropped_count=?, message=?,heartbeat_at=?,
                       details_json=? WHERE id=?""",
                    (
                        now_text(),
                        status,
                        stats["new"],
                        stats["updated"],
                        stats["dropped"],
                        message,
                        now_text(),
                        json.dumps(run_details, ensure_ascii=False, default=str),
                        run_id,
                    ),
                )
            notification_settings = get_notification_settings()
            if failed and notification_settings["failures"]:
                send_windows_notification("招聘职位采集部分失败", message, "runs")
            elif (
                stats["new"] or stats["updated"] or stats["dropped"]
            ) and notification_settings["changes"]:
                send_change_notification(stats)
            elif notification_settings["success_without_changes"]:
                send_windows_notification("招聘职位采集完成", message, "runs")
        except Exception as exc:
            logging.exception("爬虫运行失败")
            with connect() as db:
                db.execute(
                    """UPDATE runs SET finished_at=?,status='failed',message=?,
                       heartbeat_at=? WHERE id=?""",
                    (now_text(), str(exc)[-2000:], now_text(), run_id),
                )
            if get_notification_settings()["failures"]:
                send_windows_notification("招聘职位采集失败", str(exc)[-600:], "runs")
        finally:
            lock_path.unlink(missing_ok=True)
            with self.lock:
                self.running = False


def send_windows_notification(title: str, message: str, view: str = "changes") -> bool:
    if sys.platform != "win32":
        logging.info("%s：%s", title, message)
        return True
    fallback_title = title.replace("'", "''")
    fallback_message = message.replace("'", "''")
    url = f"http://127.0.0.1:8765/?view={view}"
    script = f"""
    try {{
      $shell = New-Object -ComObject WScript.Shell
      [System.Media.SystemSounds]::Asterisk.Play()
      $choice = $shell.Popup('{fallback_message}', 45, '{fallback_title}', 1 + 64)
      if ($choice -eq 1) {{
        Start-Process '{url}'
      }}
    }} catch {{
      Add-Type -AssemblyName PresentationFramework
      [System.Windows.MessageBox]::Show('{fallback_message}','{fallback_title}') | Out-Null
    }}
    """
    subprocess.Popen(
        ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    with connect() as db:
        db.execute(
            """INSERT INTO settings(key,value) VALUES('last_notification',?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
            (
                json.dumps(
                    {"title": title, "message": message, "view": view, "started_at": now_text()},
                    ensure_ascii=False,
                ),
            ),
        )
    logging.info("Windows 桌面提醒进程已启动：%s", title)
    return True


def send_change_notification(stats: dict[str, int]) -> None:
    send_windows_notification(
        "招聘职位有更新",
        f"新增 {stats['new']} 条，更新 {stats['updated']} 条，"
        f"下架 {stats['dropped']} 条。打开本地管理台查看详情。",
        "changes",
    )


def get_notification_settings() -> dict[str, bool]:
    with connect() as db:
        row = db.execute("SELECT value FROM settings WHERE key='notifications'").fetchone()
    defaults = {"changes": True, "failures": True, "success_without_changes": False}
    if row:
        defaults.update(json.loads(row["value"]))
    return defaults


def save_notification_settings(value: dict[str, Any]) -> dict[str, bool]:
    settings = {
        "changes": bool(value.get("changes", True)),
        "failures": bool(value.get("failures", True)),
        "success_without_changes": bool(value.get("success_without_changes", False)),
    }
    with connect() as db:
        db.execute(
            "INSERT OR REPLACE INTO settings(key,value) VALUES('notifications',?)",
            (json.dumps(settings, ensure_ascii=False),),
        )
    return settings


def get_schedule() -> dict[str, Any]:
    with connect() as db:
        row = db.execute("SELECT value FROM settings WHERE key='schedule'").fetchone()
    return json.loads(row["value"]) if row else dict(DEFAULT_SCHEDULE)


def save_schedule(value: dict[str, Any]) -> dict[str, Any]:
    schedule = {
        "enabled": bool(value.get("enabled")),
        "mode": value.get("mode") if value.get("mode") in {"interval", "daily", "weekly"} else "daily",
        "time": str(value.get("time", "09:00"))[:5],
        "interval_minutes": max(5, min(int(value.get("interval_minutes", 60)), 10080)),
        "weekdays": [int(x) for x in value.get("weekdays", [0, 1, 2, 3, 4]) if 0 <= int(x) <= 6],
    }
    schedule["system_task"] = sync_windows_task(schedule)
    with connect() as db:
        db.execute(
            "INSERT OR REPLACE INTO settings(key, value) VALUES('schedule', ?)",
            (json.dumps(schedule, ensure_ascii=False),),
        )
    return schedule


def sync_windows_task(schedule: dict[str, Any]) -> dict[str, Any]:
    if sys.platform != "win32":
        return {"active": False, "message": "当前平台不支持 Windows 任务计划"}
    command = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(ROOT / "configure_scheduled_task.ps1"),
        "-PythonPath", sys.executable,
        "-ScriptPath", str(ROOT / "job_dashboard.py"),
        "-Mode", schedule["mode"],
        "-RunTime", schedule["time"],
        "-IntervalMinutes", str(schedule["interval_minutes"]),
        "-Weekdays", ",".join(str(x) for x in schedule["weekdays"]),
        "-Enabled", "true" if schedule["enabled"] else "false",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    output = (result.stdout or result.stderr).strip()
    active = result.returncode == 0 and schedule["enabled"] and "ACTIVE|" in output
    return {
        "active": active,
        "message": (
            "Windows 系统任务已验证并启用"
            if active
            else ("系统任务已停用" if result.returncode == 0 and not schedule["enabled"] else output)
        ),
    }


def export_jobs(format_name: str) -> Path:
    EXPORT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    with connect() as db:
        rows = db.execute(
            """SELECT source_type,job_name,team_name,team_intro,city,department,
               category,publish_time,info_updated_at AS information_updated_at,
               picked_at,dropped_at,is_active,detail_url,payload
               FROM jobs ORDER BY is_active DESC,publish_time DESC"""
        ).fetchall()
    records = []
    for row in rows:
        record = dict(row)
        record["招聘类型"] = JOB_TYPES.get(record.pop("source_type"), "")
        record["状态"] = "有效" if record.pop("is_active") else "已下架"
        record["原始数据"] = json.loads(record.pop("payload"))
        records.append(record)
    if format_name == "json":
        path = EXPORT_DIR / f"jobs-{stamp}.json"
        path.write_text(json.dumps(records, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return path
    if format_name == "xlsx":
        import pandas as pd
        flat = [{k: v for k, v in row.items() if k != "原始数据"} for row in records]
        path = EXPORT_DIR / f"jobs-{stamp}.xlsx"
        pd.DataFrame(flat).to_excel(path, index=False)
        return path
    raise ValueError("仅支持 json 或 xlsx")


class Scheduler:
    def __init__(self, runner: CrawlerRunner) -> None:
        self.runner = runner
        self.last_key: str | None = None

    def serve(self) -> None:
        while True:
            try:
                schedule = get_schedule()
                system_active = schedule.get("system_task", {}).get("active", False)
                if schedule["enabled"] and not system_active:
                    now = datetime.now()
                    due, key = self._is_due(schedule, now)
                    if due and key != self.last_key:
                        if self.runner.start("schedule"):
                            self.last_key = key
                time.sleep(20)
            except Exception:
                logging.exception("调度检查失败")
                time.sleep(20)

    @staticmethod
    def _is_due(schedule: dict[str, Any], now: datetime) -> tuple[bool, str]:
        if schedule["mode"] == "interval":
            minutes = schedule["interval_minutes"]
            bucket = int(now.timestamp() // (minutes * 60))
            return True, f"interval:{bucket}"
        target_h, target_m = map(int, schedule["time"].split(":"))
        passed = (now.hour, now.minute) >= (target_h, target_m)
        if schedule["mode"] == "weekly" and now.weekday() not in schedule["weekdays"]:
            return False, ""
        return passed, f"{schedule['mode']}:{now.date().isoformat()}"


BROWSER_SERVICE = BrowserService()
RUNNER = CrawlerRunner()


class ApiHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def log_message(self, fmt: str, *args: Any) -> None:
        logging.info("Web %s", fmt % args)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def json_response(self, data: Any, status: int = 200) -> None:
        encoded = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/"):
            if parsed.path == "/":
                self.path = "/index.html"
            return super().do_GET()
        try:
            query = parse_qs(parsed.query)
            if parsed.path == "/api/summary":
                return self.json_response(self.summary())
            if parsed.path == "/api/jobs":
                return self.json_response(self.jobs(query))
            if parsed.path == "/api/cities":
                return self.json_response(self.cities(query))
            if parsed.path == "/api/changes":
                return self.json_response(self.changes(query))
            if parsed.path == "/api/runs":
                return self.json_response(self.runs())
            if parsed.path == "/api/schedule":
                return self.json_response(get_schedule())
            if parsed.path == "/api/notifications":
                return self.json_response(get_notification_settings())
            if parsed.path == "/api/status":
                return self.json_response(
                    {"running": RUNNER.running, "browser_service": BROWSER_SERVICE.thread.is_alive()}
                )
            self.json_response({"error": "接口不存在"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            logging.exception("API 请求失败")
            self.json_response({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        try:
            if self.path == "/api/run":
                started = RUNNER.start("manual")
                return self.json_response({"started": started}, 202 if started else 409)
            if self.path == "/api/schedule":
                return self.json_response(save_schedule(self.read_json()))
            if self.path == "/api/notifications":
                return self.json_response(save_notification_settings(self.read_json()))
            if self.path == "/api/export":
                body = self.read_json()
                path = export_jobs(body.get("format", "xlsx"))
                return self.json_response({"path": str(path), "name": path.name})
            if self.path == "/api/notification/test":
                sent = send_windows_notification(
                    "招聘职位通知测试",
                    "通知功能工作正常。今后检测到新增、更新或下架时会自动提醒。",
                    "changes",
                )
                return self.json_response({"sent": sent})
            self.json_response({"error": "接口不存在"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self.json_response({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    @staticmethod
    def summary() -> dict[str, Any]:
        with connect() as db:
            counts = {
                row["source_type"]: row["count"]
                for row in db.execute(
                    "SELECT source_type, COUNT(*) count FROM jobs WHERE is_active=1 GROUP BY source_type"
                )
            }
            total = db.execute("SELECT COUNT(*) count FROM jobs WHERE is_active=1").fetchone()["count"]
            changed = db.execute(
                "SELECT COUNT(*) count FROM changes WHERE created_at >= ?",
                ((datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"),),
            ).fetchone()["count"]
            last_run = db.execute(
                "SELECT * FROM runs ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return {
            "total": total,
            "changed7d": changed,
            "types": {key: counts.get(key, 0) for key in JOB_TYPES},
            "labels": JOB_TYPES,
            "last_run": dict(last_run) if last_run else None,
            "running": RUNNER.running,
        }

    @staticmethod
    def jobs(query: dict[str, list[str]]) -> dict[str, Any]:
        search = query.get("q", [""])[0].strip()
        source_type = query.get("type", ["all"])[0]
        status = query.get("status", ["active"])[0]
        city = query.get("city", [""])[0].strip()
        page = max(1, int(query.get("page", ["1"])[0]))
        limit = min(100, max(10, int(query.get("limit", ["30"])[0])))
        sort_key = query.get("sort", ["updated_at"])[0]
        sort_direction = query.get("direction", ["desc"])[0].lower()
        sort_columns = {
            "job_name": "job_name",
            "team_name": "team_name",
            "source_type": "source_type",
            "city": "city",
            "publish_time": "publish_time",
            "updated_at": "info_updated_at",
            "is_active": "is_active",
        }
        sort_column = sort_columns.get(sort_key, "info_updated_at")
        direction = "ASC" if sort_direction == "asc" else "DESC"
        where, params = [], []
        if source_type in JOB_TYPES:
            where.append("source_type=?")
            params.append(source_type)
        if status == "active":
            where.append("is_active=1")
        elif status == "dropped":
            where.append("is_active=0")
        if city == "__unknown__":
            where.append("NOT EXISTS (SELECT 1 FROM job_cities jc WHERE jc.job_key=jobs.job_key)")
        elif city:
            where.append(
                "EXISTS (SELECT 1 FROM job_cities jc WHERE jc.job_key=jobs.job_key AND jc.city=?)"
            )
            params.append(city)
        if search:
            where.append(
                "(title LIKE ? OR job_name LIKE ? OR team_name LIKE ? OR team_intro LIKE ? "
                "OR city LIKE ? OR department LIKE ? OR category LIKE ?)"
            )
            params.extend([f"%{search}%"] * 7)
        clause = " WHERE " + " AND ".join(where) if where else ""
        with connect() as db:
            total = db.execute(f"SELECT COUNT(*) count FROM jobs{clause}", params).fetchone()["count"]
            rows = db.execute(
                f"""SELECT job_key, source_type, title, job_name, team_name, team_intro,
                    detail_url, city, department, category, publish_time, picked_at,
                    dropped_at, is_active, payload, info_updated_at AS updated_at
                    FROM jobs{clause}
                    ORDER BY {sort_column} {direction}, job_name ASC, job_key ASC
                    LIMIT ? OFFSET ?""",
                (*params, limit, (page - 1) * limit),
            ).fetchall()
            city_map: dict[str, list[str]] = {}
            if rows:
                placeholders = ",".join("?" for _ in rows)
                for city_row in db.execute(
                    f"SELECT job_key,city FROM job_cities WHERE job_key IN ({placeholders}) ORDER BY city",
                    [row["job_key"] for row in rows],
                ):
                    city_map.setdefault(city_row["job_key"], []).append(city_row["city"])
        items = []
        for row in rows:
            item = dict(row)
            item["payload"] = json.loads(item["payload"])
            item["cities"] = city_map.get(item["job_key"], [])
            items.append(item)
        return {"items": items, "total": total, "page": page, "limit": limit}

    @staticmethod
    def cities(query: dict[str, list[str]]) -> dict[str, Any]:
        source_type = query.get("type", ["all"])[0]
        status = query.get("status", ["active"])[0]
        where, params = [], []
        if source_type in JOB_TYPES:
            where.append("j.source_type=?")
            params.append(source_type)
        if status in {"active", "dropped"}:
            where.append("j.is_active=?")
            params.append(1 if status == "active" else 0)
        clause = " WHERE " + " AND ".join(where) if where else ""
        with connect() as db:
            rows = db.execute(
                f"""SELECT jc.city,COUNT(*) count FROM job_cities jc
                    JOIN jobs j ON j.job_key=jc.job_key{clause}
                    GROUP BY jc.city ORDER BY jc.city""", params,
            ).fetchall()
            missing_clause = " AND " if where else " WHERE "
            missing = db.execute(
                f"SELECT COUNT(*) FROM jobs j{clause}{missing_clause}"
                "NOT EXISTS (SELECT 1 FROM job_cities jc WHERE jc.job_key=j.job_key)", params,
            ).fetchone()[0]
        return {"items": [dict(row) for row in rows], "unknown_count": missing}

    @staticmethod
    def changes(query: dict[str, list[str]]) -> dict[str, Any]:
        limit = min(100, int(query.get("limit", ["40"])[0]))
        with connect() as db:
            rows = db.execute(
                """SELECT changes.*,jobs.detail_url,jobs.job_name,jobs.team_name
                   FROM changes LEFT JOIN jobs ON jobs.job_key=changes.job_key
                   ORDER BY changes.id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            if not item.get("detail_url"):
                snapshot = item.get("after_json") or item.get("before_json")
                try:
                    payload = json.loads(snapshot) if snapshot else {}
                except (TypeError, json.JSONDecodeError):
                    payload = {}
                job_id = payload.get("job_id") or payload.get("id")
                section = "experienced" if item["source_type"] == "experienced" else "campus"
                if job_id:
                    item["detail_url"] = (
                        f"https://jobs.bytedance.com/{section}/position/{job_id}/detail"
                    )
            items.append(item)
        return {"items": items}

    @staticmethod
    def runs() -> dict[str, Any]:
        with connect() as db:
            rows = db.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 30").fetchall()
        return {"items": [dict(row) for row in rows]}


def acquire_dashboard_lock():
    """持有进程级文件锁，防止 Windows 将多个服务绑定到同一端口。"""
    DATA_DIR.mkdir(exist_ok=True)
    lock_file = open(DATA_DIR / "dashboard.lock", "a+b")
    lock_file.seek(0)
    if lock_file.read(1) == b"":
        lock_file.seek(0)
        lock_file.write(b"0")
        lock_file.flush()
    lock_file.seek(0)
    try:
        if sys.platform == "win32":
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock_file.close()
        return None
    return lock_file


def main() -> None:
    init_db()
    try:
        with connect() as db:
            empty = db.execute("SELECT COUNT(*) count FROM jobs").fetchone()["count"] == 0
        if empty and DEFAULT_CACHE.exists():
            stats = import_cache(record_changes=False)
            logging.info("已导入现有缓存：%s", stats)
    except Exception:
        logging.exception("初始数据导入失败")
    if "--run-once" in sys.argv:
        RUNNER.running = True
        RUNNER._run("windows-task")
        BROWSER_SERVICE.close()
        return
    instance_lock = acquire_dashboard_lock()
    if instance_lock is None:
        logging.warning("管理台已经在运行，本次重复启动已取消")
        if "--no-browser" not in sys.argv:
            webbrowser.open("http://127.0.0.1:8765")
        BROWSER_SERVICE.close()
        return
    threading.Thread(target=Scheduler(RUNNER).serve, daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", 8765), ApiHandler)
    url = "http://127.0.0.1:8765"
    logging.info("本地管理台已启动：%s", url)
    if "--no-browser" not in sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("管理台已停止")
    finally:
        BROWSER_SERVICE.close()
        instance_lock.close()


if __name__ == "__main__":
    main()
