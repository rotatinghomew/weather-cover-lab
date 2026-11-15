"""来源分页、版本和消费档案的实际 HTTP 回归。"""
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from weather_cover.provider import make_server as source_server
from weather_cover.app import make_server as application_server
from weather_cover.client import Client

class TransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parent.parent
        cls.directory = tempfile.TemporaryDirectory()
        cls.source = source_server(root / 'data/release.json')
        cls.source_thread = threading.Thread(target=cls.source.serve_forever, daemon=True)
        cls.source_thread.start()
        cls.url = f'http://127.0.0.1:{cls.source.server_port}'
        cls.client = Client(cls.url)
        cls.application = application_server(cls.url, Path(cls.directory.name) / 'reports.db')
        cls.app_thread = threading.Thread(target=cls.application.serve_forever, daemon=True)
        cls.app_thread.start()
        cls.base = f'http://127.0.0.1:{cls.application.server_port}'
        cls.query = json.loads((root / 'data/request.json').read_text())

    @classmethod
    def tearDownClass(cls):
        cls.application.shutdown()
        cls.source.shutdown()
        cls.application.server_close()
        cls.source.server_close()
        cls.directory.cleanup()

    def test_complete_bundle(self):
        bundle = self.client.bundle()
        self.assertEqual(len(bundle['data']['rows']), bundle['manifest']['row_count'])
        self.assertGreater(bundle['manifest']['row_count'], 13)

    def test_stale_release(self):
        with self.assertRaises(HTTPError) as error:
            self.client.request('/records', 'old-release')
        self.assertEqual(error.exception.code, 412)
        error.exception.close()

    def test_cross_version_cursor(self):
        import base64
        cursor = base64.urlsafe_b64encode(json.dumps({'release': 'old', 'offset': 13}).encode()).decode()
        release = self.client.request('/manifest')['release']
        with self.assertRaises(HTTPError) as error:
            self.client.request('/records?cursor=' + cursor, release)
        self.assertEqual(error.exception.code, 400)
        error.exception.close()

    def test_archive_and_quote(self):
        bundle = self.client.bundle()
        receipt = self.client.quote(bundle['manifest']['release'], self.query)
        self.assertEqual(receipt['request'], self.query)
        with urlopen(self.base + '/overview') as response:
            overview = json.load(response)
        payload = {'release': overview['release'], 'source_digest': overview['digest'], 'kind': 'source-consultation', 'result': overview['overview'], 'receipts': [receipt]}
        request = Request(self.base + '/reports', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
        with urlopen(request) as response:
            identifier = json.load(response)['id']
        with urlopen(self.base + '/reports/' + identifier) as response:
            self.assertEqual(json.load(response)['payload'], payload)

    def test_consumer_keeps_stale_release_status(self):
        request = Request(self.base + '/quotes', data=json.dumps({'release': 'old', 'request': self.query}).encode(), headers={'Content-Type': 'application/json'})
        with self.assertRaises(HTTPError) as error:
            urlopen(request)
        self.assertEqual(error.exception.code, 412)
        error.exception.close()

    def test_unknown_archive(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(self.base + '/reports/not-present')
        self.assertEqual(error.exception.code, 404)
        error.exception.close()
