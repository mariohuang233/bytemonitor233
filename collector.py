"""招聘职位结构化采集器，浏览器实例可在多次任务之间复用。"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from playwright.async_api import Browser, Playwright, async_playwright


TASKS: list[dict[str, Any]] = [
    {
        "source_type": "intern",
        "name": "实习招聘",
        "url": "https://jobs.bytedance.com/campus/position?keywords=&category=6704215864629004552%2C6704215864591255820%2C6704216224387041544%2C6704215924712409352&location=&project=7481474995534301447%2C7468181472685164808%2C7194661644654577981%2C7194661126919358757&type=&job_hot_flag=&current=1&limit=200&functionCategory=&tag=",
        "extra_fields": [],
    },
    {
        "source_type": "campus",
        "name": "校园招聘",
        "url": "https://jobs.bytedance.com/campus/position?keywords=&category=6704215864629004552%2C6704215864591255820%2C6704216224387041544%2C6704215924712409352&location=&project=7649336829398468869%2C7624064258157889845%2C7621018151002507573&type=&job_hot_flag=&current=1&limit=200&functionCategory=&tag=",
        "extra_fields": ["location", "department"],
    },
    {
        "source_type": "experienced",
        "name": "社会招聘",
        "url": "https://jobs.bytedance.com/experienced/position?keywords=&category=6704215864629004552%2C6704215864591255820%2C6704215924712409352%2C6704216224387041544&location=&project=&type=&job_hot_flag=&current=1&limit=200&functionCategory=&tag=",
        "extra_fields": ["location", "department"],
    },
]


def city_names(value: Any) -> list[str]:
    """返回独立城市名，兼容 API 城市对象及历史逗号分隔字段。"""
    if isinstance(value, str):
        values = re.split(r"[,，]", value)
    elif isinstance(value, dict):
        values = [value.get("name") or value.get("i18n_name")]
    elif isinstance(value, list):
        values = [name for item in value for name in city_names(item)]
    else:
        values = []
    return list(dict.fromkeys(str(item).strip() for item in values if item and str(item).strip()))


def job_cities(record: dict[str, Any]) -> list[str]:
    return city_names(record.get("city_list") or record.get("location") or record.get("city_info"))


def normalize_job(job: dict[str, Any], extra_fields: list[str]) -> dict[str, Any]:
    publish_value = job.get("publish_time")
    publish_time = None
    if publish_value:
        publish_time = datetime.fromtimestamp(
            publish_value / 1000, tz=timezone(timedelta(hours=8))
        ).strftime("%Y-%m-%d %H:%M:%S")
    result = {
        "title": job.get("title"),
        "sub_title": job.get("sub_title"),
        "description": job.get("description"),
        "requirement": job.get("requirement"),
        "publish_time": publish_time,
        "code": job.get("code"),
        "job_id": job.get("id"),
        "job_type": job.get("job_type"),
        "job_category": _name(job.get("job_category")),
        "job_function": _name(job.get("job_function")),
        "department_id": job.get("department_id"),
        "job_process_id": job.get("job_process_id"),
        "recruit_type_name": _name(job.get("recruit_type")),
        "recruit_type_parent": _name((job.get("recruit_type") or {}).get("parent"))
        if isinstance(job.get("recruit_type"), dict)
        else None,
        "job_subject_name": _subject_name(job.get("job_subject")),
        "city_list": ", ".join(job_cities(job)) or None,
        "city_codes": ", ".join(
            city.get("code", "") for city in job.get("city_list", []) if isinstance(city, dict)
        )
        or None,
        "address": job.get("address"),
        "degree": job.get("degree"),
        "experience": job.get("experience"),
        "min_salary": job.get("min_salary"),
        "max_salary": job.get("max_salary"),
        "currency": job.get("currency"),
        "head_count": job.get("head_count"),
        "job_hot_flag": job.get("job_hot_flag"),
        "is_urgent": job.get("is_urgent"),
        "job_active_status": job.get("job_active_status"),
        "recommend_id": job.get("recommend_id"),
        "team_name": job.get("team_name"),
        "brand_name": job.get("brand_name"),
        "ats_online_apply": job.get("ats_online_apply"),
        "pc_job_url": job.get("pc_job_url"),
        "wap_job_url": job.get("wap_job_url"),
        "storefront_mode": job.get("storefront_mode"),
        "process_type": job.get("process_type"),
    }
    for field in extra_fields:
        result[field] = _name(job.get(field))
    return {key: value for key, value in result.items() if value not in (None, "")}


def _name(value: Any) -> Any:
    return value.get("name") if isinstance(value, dict) else value


def _subject_name(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    name = value.get("name")
    return name.get("zh_cn") if isinstance(name, dict) else name


def page_url(url: str, current: int) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update(location="", current=str(current), limit="200")
    return urlunsplit(parts._replace(query=urlencode(query)))


def is_page_response(response: Any, offset: int) -> bool:
    if "api/v1/search/job/posts" not in response.url or response.request.method != "POST":
        return False
    try:
        return (response.request.post_data_json or {}).get("offset") == offset
    except (ValueError, TypeError):
        return False


class PersistentCollector:
    def __init__(self, artifact_dir: Path, retries: int = 3) -> None:
        self.artifact_dir = artifact_dir
        self.retries = retries
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None

    async def start(self) -> None:
        if self.browser and self.browser.is_connected():
            return
        await self.close()
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        logging.info("常驻采集浏览器已启动")

    async def close(self) -> None:
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                pass
        self.browser = None
        self.playwright = None

    async def collect_all(self) -> dict[str, Any]:
        await self.start()
        results = await asyncio.gather(*(self._collect_with_retry(task) for task in TASKS))
        return {item["source_type"]: item for item in results}

    async def _collect_with_retry(self, task: dict[str, Any]) -> dict[str, Any]:
        errors: list[str] = []
        for attempt in range(1, self.retries + 1):
            try:
                jobs = await self._collect_one(task, attempt)
                if not jobs:
                    raise RuntimeError("接口返回 0 条，已按异常空结果处理并保留历史数据")
                return {
                    "source_type": task["source_type"],
                    "name": task["name"],
                    "status": "success",
                    "jobs": jobs,
                    "attempts": attempt,
                    "error": None,
                }
            except Exception as exc:
                errors.append(str(exc))
                logging.warning("%s 第 %s 次采集失败：%s", task["name"], attempt, exc)
                if self.browser is None or not self.browser.is_connected():
                    await self.start()
                if attempt < self.retries:
                    await asyncio.sleep(min(2**attempt, 8))
        return {
            "source_type": task["source_type"],
            "name": task["name"],
            "status": "failed",
            "jobs": [],
            "attempts": self.retries,
            "error": errors[-1] if errors else "未知错误",
        }

    async def _collect_one(self, task: dict[str, Any], attempt: int) -> list[dict[str, Any]]:
        assert self.browser is not None
        context = await self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/108.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()
        try:
            jobs: dict[str, dict[str, Any]] = {}
            expected_total = 0
            for current in range(1, 501):
                async with page.expect_response(
                    lambda response: is_page_response(response, (current - 1) * 200),
                    timeout=45000,
                ) as info:
                    await page.goto(
                        page_url(task["url"], current),
                        wait_until="domcontentloaded", timeout=45000,
                    )
                response = await info.value
                if response.status != 200:
                    raise RuntimeError(f"第 {current} 页接口返回 HTTP {response.status}")
                request = response.request.post_data_json or {}
                if request.get("location_code_list"):
                    raise RuntimeError("接口仍带城市限制，本次结果不作为全量数据写入")
                if request.get("offset") != (current - 1) * 200:
                    raise RuntimeError(f"第 {current} 页分页偏移异常，已停止同步")
                data = (await response.json()).get("data") or {}
                raw_jobs = data.get("job_post_list")
                if not isinstance(raw_jobs, list):
                    raise RuntimeError(f"第 {current} 页缺少岗位列表")
                total = data.get("count")
                if not isinstance(total, int) or total < 0:
                    raise RuntimeError("接口未返回有效总数，无法确认完整性")
                expected_total = max(expected_total, total)
                previous_count = len(jobs)
                for raw_job in raw_jobs:
                    record = normalize_job(raw_job, task["extra_fields"])
                    key = str(record.get("code") or record.get("job_id") or "")
                    if not key:
                        raise RuntimeError("接口岗位缺少唯一标识，已停止同步")
                    jobs[key] = record
                logging.info(
                    "%s 全城市第 %s 页：已采集 %s / %s 条",
                    task["name"], current, len(jobs), expected_total,
                )
                if len(jobs) >= expected_total:
                    return list(jobs.values())
                if not raw_jobs or len(jobs) == previous_count:
                    raise RuntimeError(
                        f"分页结果不完整（{len(jobs)}/{expected_total}），保留历史数据"
                    )
                await asyncio.sleep(0.2)
            raise RuntimeError("分页超过安全上限，保留历史数据")
        except Exception:
            self.artifact_dir.mkdir(parents=True, exist_ok=True)
            screenshot = self.artifact_dir / (
                f"{datetime.now():%Y%m%d-%H%M%S}-{task['source_type']}-attempt{attempt}.png"
            )
            try:
                await page.screenshot(path=str(screenshot), full_page=True)
            except Exception:
                pass
            raise
        finally:
            await context.close()
