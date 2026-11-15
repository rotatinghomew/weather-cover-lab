"""按内容寻址保存咨询材料，历史档案只读。"""
import hashlib
import json
from pathlib import Path
import sqlite3
from .provider import canonical

class Ledger:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute('CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def save(self, payload):
        encoded = canonical(payload)
        identifier = hashlib.sha256(encoded).hexdigest()
        with self.connect() as connection:
            connection.execute('INSERT OR IGNORE INTO reports(id,payload) VALUES (?,?)', (identifier, encoded.decode()))
        return identifier

    def read(self, identifier):
        with self.connect() as connection:
            row = connection.execute('SELECT payload FROM reports WHERE id=?', (identifier,)).fetchone()
        return None if row is None else json.loads(row[0])
