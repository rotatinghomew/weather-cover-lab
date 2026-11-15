"""内容档案的幂等、重开和未知编号。"""
from pathlib import Path
import tempfile
import unittest
from weather_cover.ledger import Ledger

class LedgerTests(unittest.TestCase):
    def test_content_address_and_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'nested/reports.db'
            ledger = Ledger(path)
            payload = {'金额': 10, 'release': 'r1'}
            identifier = ledger.save(payload)
            self.assertEqual(identifier, ledger.save({'release': 'r1', '金额': 10}))
            self.assertEqual(Ledger(path).read(identifier), payload)
            self.assertIsNone(ledger.read('unknown'))
