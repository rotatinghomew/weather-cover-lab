"""发布冻结资料并处理独立业务询价。"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import base64
import hashlib
import json
from . import domain

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()

class Source:
    def __init__(self, path):
        self.data = json.loads(Path(path).read_text())
        self.version = self.data['version']
        self.digest = hashlib.sha256(canonical(self.data)).hexdigest()

    def cursor(self, offset):
        return base64.urlsafe_b64encode(canonical({'release': self.version, 'offset': offset})).decode()

    def read_page(self, cursor):
        offset = 0
        if cursor:
            try:
                decoded = json.loads(base64.b64decode(cursor, altchars=b'-_', validate=True))
                if decoded['release'] != self.version:
                    raise ValueError('游标不属于当前资料版本')
                offset = decoded['offset']
            except (KeyError, TypeError, json.JSONDecodeError, ValueError) as error:
                raise ValueError('游标无效或跨版本') from error
        if isinstance(offset, bool) or not isinstance(offset, int) or not 0 <= offset <= len(self.data['rows']):
            raise ValueError('页偏移非法')
        stop = offset + self.data['page_size']
        return {'release': self.version, 'rows': self.data['rows'][offset:stop],
                'next': self.cursor(stop) if stop < len(self.data['rows']) else None}

def make_server(path, host='127.0.0.1', port=0):
    source = Source(path)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def respond(self, status, value):
            body = canonical(value)
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('ETag', source.version)
            self.end_headers()
            self.wfile.write(body)

        def require_release(self):
            if self.headers.get('If-Match') != source.version:
                self.respond(412, {'error': '资料版本已变化，请重新确认'})
                return False
            return True

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == '/manifest':
                metadata = {key: value for key, value in source.data.items() if key != 'rows'}
                self.respond(200, {'release': source.version, 'digest': source.digest,
                                   'row_count': len(source.data['rows']), 'metadata': metadata})
            elif parsed.path == '/records':
                if not self.require_release():
                    return
                try:
                    cursor = parse_qs(parsed.query).get('cursor', [''])[0]
                    self.respond(200, source.read_page(cursor))
                except ValueError as error:
                    self.respond(400, {'error': str(error)})
            else:
                self.respond(404, {'error': '地址不存在'})

        def do_POST(self):
            if not self.require_release():
                return
            routes = {'/quote': domain.quote, '/detail': domain.detail}
            if self.path not in routes:
                self.respond(404, {'error': '业务接口不存在'})
                return
            try:
                length = int(self.headers.get('Content-Length', 0))
                if length > 100000:
                    raise ValueError('请求过大')
                request = json.loads(self.rfile.read(length))
                result = routes[self.path](source.data, request)
                self.respond(200, {'release': source.version, 'request': request, 'result': result})
            except (ValueError, TypeError, KeyError) as error:
                self.respond(422, {'error': str(error)})
    server = ThreadingHTTPServer((host, port), Handler)
    server.source = source
    return server
