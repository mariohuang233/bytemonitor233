"""验证云端基线恢复、失败保护以及 Pages 子路径资源。"""

import gc
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cloud_pipeline as cloud
import job_dashboard as dashboard


class CloudPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.original_db = dashboard.DB_PATH
        self.connections = []
        original_connect = dashboard.connect
        def connect():
            connection = original_connect()
            self.connections.append(connection)
            return connection
        self.mock_connect = patch.object(dashboard, "connect", connect)
        self.mock_connect.start()
        dashboard.DB_PATH = Path(self.temp.name) / "seed.db"
        dashboard.init_db()
        dashboard.sync_collection({"intern": {"status": "success", "jobs": [{
            "code": "A1", "job_id": "123", "title": "产品实习生 - 团队",
            "city_list": "上海, 北京", "description": "团队介绍：测试团队。",
        }]}})
        with dashboard.connect() as db:
            db.execute("INSERT INTO settings(key,value) VALUES('private_test','not-for-upload')")
        self.state = cloud.snapshot(dashboard.DB_PATH)

    def tearDown(self):
        for connection in self.connections:
            connection.close()
        self.mock_connect.stop()
        dashboard.DB_PATH = self.original_db
        gc.collect()
        self.temp.cleanup()

    def test_snapshot_excludes_settings_and_restore_keeps_city_index(self):
        self.assertNotIn("private_test", json.dumps(self.state))
        dashboard.DB_PATH = Path(self.temp.name) / "restored.db"
        cloud.restore(self.state)
        self.assertEqual(dashboard.ApiHandler.jobs({"city": ["北京"]})["total"], 1)
        self.assertEqual(dashboard.ApiHandler.jobs({"city": ["上海"]})["total"], 1)

    def test_all_sources_failed_preserves_jobs_and_records_failure(self):
        async def failed_collection():
            return {"intern": {"name": "实习招聘", "status": "failed", "jobs": [], "attempts": 3, "error": "网络不可用"}}
        target = Path(self.temp.name) / "failed.db"
        with patch.object(cloud, "collect", failed_collection):
            state, failed = cloud.run_collection(self.state, target)
        self.assertTrue(failed)
        self.assertEqual(state["runs"][0]["status"], "failed")
        self.assertEqual(len(state["jobs"]), 1)
        self.assertEqual(state["jobs"][0]["is_active"], 1)

    def test_pages_uses_relative_paths_and_new_schedule(self):
        public = Path(self.temp.name) / "public"
        with patch.object(cloud, "PUBLIC", public):
            cloud.build_site(self.state)
        index = (public / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="./styles.css', index)
        self.assertIn('src="./app.js', index)
        self.assertIn("10:00、16:00、22:00", index)
        self.assertTrue((public / "data" / "monitor.json.gz").exists())


if __name__ == "__main__":
    unittest.main()
