"""GitHub Actions 采集与 Pages 构建，只导出招聘数据，不上传本机设置。"""

from __future__ import annotations

import argparse
import asyncio
import gzip
import json
import os
import shutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path

if hasattr(time, "tzset"):
    os.environ["TZ"] = "Asia/Shanghai"
    time.tzset()

import job_dashboard as dashboard
from collector import PersistentCollector, job_cities

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state" / "monitor.json.gz"
PUBLIC = ROOT / "public"
REPOSITORY = "mariohuang233/bytemonitor233"


def read_state() -> dict:
    if not STATE.exists():
        raise RuntimeError("缺少 state/monitor.json.gz 数据基线，请先导入历史数据")
    with gzip.open(STATE, "rt", encoding="utf-8") as file:
        return json.load(file)


def write_state(state: dict) -> None:
    STATE.parent.mkdir(exist_ok=True)
    payload = json.dumps(state, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    STATE.write_bytes(gzip.compress(payload, compresslevel=9, mtime=0))


def snapshot(db_path: Path, runs: list | None = None) -> dict:
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        jobs = [dict(row) for row in db.execute("SELECT * FROM jobs ORDER BY job_key")]
        changes = [dict(row) for row in db.execute("SELECT * FROM changes ORDER BY id DESC LIMIT 3000")]
    return {
        "schema_version": 1,
        "generated_at": dashboard.now_text(),
        "jobs": jobs,
        "changes": changes,
        "runs": (runs or [])[:90],
    }


def restore(state: dict) -> None:
    dashboard.init_db()
    with dashboard.connect() as db:
        if db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]:
            raise RuntimeError("云端临时数据库应为空，请为每次运行使用新的临时目录")
        for table in ("jobs", "changes"):
            allowed = {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}
            for record in state[table]:
                fields = [key for key in record if key in allowed]
                names = ",".join(fields)
                placeholders = ",".join("?" for _ in fields)
                db.execute(f"INSERT INTO {table}({names}) VALUES({placeholders})", [record[key] for key in fields])
        for job in state["jobs"]:
            dashboard.replace_city_index(db, job["job_key"], job_cities({"city_list": job.get("city")}))


async def collect() -> dict:
    engine = PersistentCollector(ROOT / "data" / "artifacts")
    try:
        return await engine.collect_all()
    finally:
        await engine.close()


def run_collection(state: dict, db_path: Path) -> tuple[dict, bool]:
    dashboard.DB_PATH = db_path
    restore(state)
    started = dashboard.now_text()
    result_details = {}
    stats = {"new": 0, "updated": 0, "dropped": 0}
    try:
        results = asyncio.run(collect())
        stats = dashboard.sync_collection(results)
        successes = sum(item["status"] == "success" for item in results.values())
        status = "success" if successes == 3 else ("partial" if successes else "failed")
        result_details = {
            key: {"name": item["name"], "status": item["status"], "count": len(item["jobs"]), "attempts": item["attempts"], "error": item["error"]}
            for key, item in results.items()
        }
        message = "；".join(f"{item['name']}：{len(item['jobs'])} 条" if item["status"] == "success" else f"{item['name']}：采集失败，保留历史数据" for item in results.values())
    except Exception as error:
        status = "failed"
        message = f"采集失败，保留历史数据：{type(error).__name__}"
        print(f"::error::{error}")
    run = {
        "id": max((item["id"] for item in state.get("runs", [])), default=0) + 1,
        "started_at": started,
        "finished_at": dashboard.now_text(),
        "status": status,
        "new_count": stats["new"], "updated_count": stats["updated"], "dropped_count": stats["dropped"],
        "message": message, "details_json": json.dumps(result_details, ensure_ascii=False),
    }
    next_state = snapshot(db_path, [run, *state.get("runs", [])])
    print(json.dumps(run, ensure_ascii=False))
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as file:
            file.write(f"all_failed={'true' if status == 'failed' else 'false'}\n")
    return next_state, status == "failed"


def build_site(state: dict) -> None:
    PUBLIC.mkdir(exist_ok=True)
    for name in ("styles.css", "app.js", "static_api.js"):
        shutil.copy2(ROOT / "web" / name, PUBLIC / name)
    index = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    index = index.replace('href="/styles.css', 'href="./styles.css').replace('src="/app.js', 'src="./app.js')
    config = json.dumps({"repository": REPOSITORY, "schedule": "每天 10:00、16:00、22:00（北京时间）"}, ensure_ascii=False)
    index = index.replace("</head>", f"<script>window.BYTE_MONITOR_STATIC={config};</script>\n<script src=\"./static_api.js\"></script>\n</head>")
    (PUBLIC / "index.html").write_text(index, encoding="utf-8")
    (PUBLIC / ".nojekyll").touch()
    public_jobs = []
    fields = ("job_key", "source_type", "title", "job_name", "team_name", "team_intro", "detail_url", "city", "department", "category", "publish_time", "picked_at", "dropped_at", "is_active")
    for row in state["jobs"]:
        job = {key: row.get(key) for key in fields}
        job["updated_at"] = row.get("info_updated_at") or row.get("created_at")
        job["payload"] = json.loads(row["payload"])
        job["cities"] = job_cities({"city_list": job["city"]})
        public_jobs.append(job)
    public_data = {"generated_at": state["generated_at"], "jobs": public_jobs, "changes": state["changes"], "runs": state["runs"]}
    compressed = gzip.compress(json.dumps(public_data, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), mtime=0)
    (PUBLIC / "data").mkdir(exist_ok=True)
    (PUBLIC / "data" / "monitor.json.gz").write_bytes(compressed)
    print(f"Pages 构建完成：{len(public_jobs)} 条历史岗位，快照 {len(compressed):,} bytes")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["seed", "run", "build"])
    parser.add_argument("--database", type=Path, default=ROOT / "data" / "jobs.db")
    args = parser.parse_args()
    if args.mode == "seed":
        state = snapshot(args.database)
        write_state(state)
    else:
        state = read_state()
    if args.mode == "run":
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            state, _failed = run_collection(state, Path(folder) / "cloud.db")
            write_state(state)
            # sqlite3 的事务上下文不会主动关闭连接，回收临时连接后再移除临时文件。
            import gc
            gc.collect()
    build_site(state)


if __name__ == "__main__":
    main()
