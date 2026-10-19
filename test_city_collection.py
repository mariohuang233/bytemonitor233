"""全城市分页完整性和多城市精确筛选的回归检查（仅使用临时数据库）。"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlsplit

import collector
import job_dashboard as dashboard


class FakeResponse:
    status = 200

    def __init__(self, offset, jobs, total):
        self.request = type("Request", (), {
            "post_data_json": {"offset": offset, "location_code_list": []},
        })()
        self.data = {"data": {"job_post_list": jobs, "count": total}}

    async def json(self):
        return self.data


class ResponseContext:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    @property
    def value(self):
        async def result():
            return self.response
        return result()


class FakePage:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.urls = []
        self.screenshot = AsyncMock()

    def expect_response(self, *_args, **_kwargs):
        return ResponseContext(next(self.responses))

    async def goto(self, url, **_kwargs):
        self.urls.append(url)


class PaginationTests(unittest.IsolatedAsyncioTestCase):
    async def collect(self, responses):
        self.page = FakePage(responses)
        context = type("Context", (), {
            "new_page": AsyncMock(return_value=self.page), "close": AsyncMock(),
        })()
        engine = collector.PersistentCollector(Path("data/artifacts"))
        engine.browser = type("Browser", (), {
            "new_context": AsyncMock(return_value=context),
        })()
        # 失败截图路径放入临时目录，避免测试污染项目。
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            engine.artifact_dir = Path(tmp)
            return await engine._collect_one(collector.TASKS[0], 1)

    async def test_full_second_page_and_city_scope(self):
        first = [{"id": str(i), "code": f"A{i}", "title": "Role"} for i in range(200)]
        last = [{"id": "200", "code": "A200", "title": "Role"}]
        jobs = await self.collect([
            FakeResponse(0, first, 201), FakeResponse(200, last, 201),
        ])
        self.assertEqual(len(jobs), 201)
        for index, url in enumerate(self.page.urls, 1):
            query = parse_qs(urlsplit(url).query, keep_blank_values=True)
            self.assertEqual(query["location"], [""])
            self.assertEqual(query["current"], [str(index)])

    async def test_incomplete_page_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "不完整"):
            await self.collect([
                FakeResponse(0, [{"id": "1", "code": "A1"}], 201),
                FakeResponse(200, [], 201),
            ])

    async def test_repeated_first_page_is_rejected(self):
        row = {"id": "1", "code": "A1"}
        with self.assertRaisesRegex(RuntimeError, "偏移异常"):
            await self.collect([FakeResponse(0, [row], 201), FakeResponse(0, [row], 201)])


class CityFilterTests(unittest.TestCase):
    def test_delayed_response_from_previous_page_is_ignored(self):
        response = FakeResponse(1600, [], 1858)
        response.url = "https://jobs.bytedance.com/api/v1/search/job/posts"
        response.request.method = "POST"
        self.assertFalse(collector.is_page_response(response, 1800))
        self.assertTrue(collector.is_page_response(response, 1600))

    def test_exact_multi_city_filter_and_unchanged_timestamp(self):
        original_db = dashboard.DB_PATH
        original_connect = dashboard.connect
        connections = []
        def tracked_connect():
            connection = original_connect()
            connections.append(connection)
            return connection
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            dashboard.DB_PATH = Path(tmp) / "test.db"
            dashboard.connect = tracked_connect
            try:
                dashboard.init_db()
                jobs = [
                    {"code": "A1", "job_id": "1", "title": "Role", "city_list": "上海, 北京"},
                    {"code": "A2", "job_id": "2", "title": "Role", "city_list": "北京"},
                    {"code": "A3", "job_id": "3", "title": "Role", "city_list": "上海市"},
                    {"code": "A4", "job_id": "4", "title": "Role"},
                ]
                results = {"intern": {"status": "success", "jobs": jobs}}
                dashboard.sync_collection(results)
                with dashboard.connect() as db:
                    db.execute("UPDATE jobs SET info_updated_at='2020-01-01 00:00:00'")
                db.close()
                dashboard.sync_collection(results)
                for city, expected in [("上海", 1), ("北京", 2), ("上海市", 1), ("__unknown__", 1)]:
                    data = dashboard.ApiHandler.jobs({"city": [city]})
                    self.assertEqual(data["total"], expected)
                    self.assertTrue(all(row["updated_at"] == "2020-01-01 00:00:00" for row in data["items"]))
                cities = dashboard.ApiHandler.cities({})
                self.assertEqual({row["city"]: row["count"] for row in cities["items"]}, {"上海": 1, "北京": 2, "上海市": 1})
                self.assertEqual(cities["unknown_count"], 1)
            finally:
                for connection in connections:
                    connection.close()
                dashboard.connect = original_connect
                dashboard.DB_PATH = original_db


if __name__ == "__main__":
    unittest.main()
