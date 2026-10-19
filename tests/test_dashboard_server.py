import http.client
import json
from pathlib import Path
import sys
import threading
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from bench_dashboard import DashboardHandler
from http.server import ThreadingHTTPServer


class DashboardServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), DashboardHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, body=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        headers = {"Content-Type": "application/json"} if body is not None else {}
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        content = response.read()
        connection.close()
        return response.status, content

    def test_dashboard_and_default_fixture_load(self):
        status, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Depth Bench Inspector", body)
        status, body = self.request("GET", "/api/default")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["summary"]["total"], 10)

    def test_invalid_recording_returns_clear_error(self):
        request = json.dumps({"name": "broken.jsonl", "content": "{not json}"})
        status, body = self.request("POST", "/api/replay", request)
        self.assertEqual(status, 400)
        self.assertIn("malformed JSON", json.loads(body)["error"])


if __name__ == "__main__":
    unittest.main()
