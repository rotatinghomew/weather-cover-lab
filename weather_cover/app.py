"""资料概览、业务报价和咨询档案接口。"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from urllib.error import HTTPError, URLError
from .client import Client
from .ledger import Ledger
from .overview import summarize
from .provider import canonical

def make_server(source_url, archive_path, host='127.0.0.1', port=0):
    client, ledger = Client(source_url), Ledger(archive_path)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def respond(self, status, value):
            body = canonical(value)
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == '/overview':
                bundle = client.bundle()
                result = summarize(bundle['data'])
                self.respond(200, {'release': bundle['manifest']['release'], 'digest': bundle['manifest']['digest'], 'overview': result})
            elif self.path.startswith('/reports/'):
                identifier = self.path.rsplit('/', 1)[-1]
                result = ledger.read(identifier)
                self.respond(200 if result is not None else 404, {'id': identifier, 'payload': result})
            elif self.path == '/health':
                self.respond(200, {'status': 'ok'})
            else:
                self.respond(404, {'error': '地址不存在'})

        def do_POST(self):
            try:
                length = int(self.headers.get('Content-Length', 0))
                if length > 1000000:
                    raise ValueError('请求过大')
                request = json.loads(self.rfile.read(length))
                if self.path == '/quotes':
                    self.respond(200, client.quote(request['release'], request['request']))
                elif self.path == '/reports':
                    required = {'release', 'source_digest', 'kind', 'result', 'receipts'}
                    if not required <= request.keys() or not isinstance(request['receipts'], list):
                        raise ValueError('咨询材料缺少来源或回执')
                    identifier = ledger.save(request)
                    self.respond(201, {'id': identifier})
                else:
                    self.respond(404, {'error': '地址不存在'})
            except HTTPError as error:
                try:
                    value = json.load(error)
                finally:
                    error.close()
                self.respond(error.code, value)
            except URLError:
                self.respond(503, {'error': '来源服务暂不可用'})
            except (ValueError, KeyError, TypeError) as error:
                self.respond(422, {'error': str(error)})
    return ThreadingHTTPServer((host, port), Handler)
