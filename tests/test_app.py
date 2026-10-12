"""Basic tests. Run with:  python -m unittest discover -s tests -v
(also works with pytest). These are what a CI pipeline will run later."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app, level_for  # noqa: E402


class HealthMonitorTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_dashboard_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"DevOps Health Monitor", response.data)

    def test_dashboard_has_project_sections(self):
        html = self.client.get("/").get_data(as_text=True)
        for text in ("About this project", "How it was built", "Workflow", "Endpoints"):
            self.assertIn(text, html)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_api_status_structure(self):
        data = self.client.get("/api/status").get_json()
        for key in ("app", "system", "metrics", "checks", "status"):
            self.assertIn(key, data)
        self.assertIn(data["status"], ("healthy", "degraded"))
        self.assertGreaterEqual(data["metrics"]["cpu_percent"], 0)

    def test_ready_endpoint_returns_known_status(self):
        response = self.client.get("/ready")
        self.assertIn(response.status_code, (200, 503))

    def test_metrics_format(self):
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"app_cpu_percent", response.data)
        self.assertIn(b"# TYPE app_memory_percent gauge", response.data)

    def test_level_for(self):
        self.assertEqual(level_for(50, 80), "ok")
        self.assertEqual(level_for(80, 80), "warning")
        self.assertEqual(level_for(99, 80), "warning")


if __name__ == "__main__":
    unittest.main()
