"""已有领域规则的边界回归。"""
import json
from pathlib import Path
import unittest
from weather_cover import domain
from weather_cover.overview import summarize

class DomainTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parent.parent
        self.data = json.loads((root / 'data/release.json').read_text())
        self.request = json.loads((root / 'data/request.json').read_text())

    def test_business_rules(self):
        result = domain.quote(self.data, self.request)
        self.assertEqual(result['premium_yuan'], 85.32)
        self.assertEqual(domain.detail(self.data, {**self.request, 'rain_mm': 20})['payout_yuan'], 192)
        self.assertIsNone(domain.detail(self.data, {**self.request, 'rain_mm': None})['payout_yuan'])

    def test_overview_counts(self):
        self.assertTrue(summarize(self.data))
        self.assertTrue(self.data['synthetic'])
        self.assertEqual(len({row['id'] for row in self.data['rows']}), len(self.data['rows']))

    def test_invalid_request(self):
        with self.assertRaises((ValueError, KeyError)):
            domain.quote(self.data, {})
