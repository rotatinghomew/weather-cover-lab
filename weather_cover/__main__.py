"""命令行启动与本地材料浏览。"""
import argparse
import json
from pathlib import Path
import tempfile
import threading
from urllib.request import Request, urlopen
from .app import make_server as application_server
from .provider import make_server as source_server
from .client import Client

def main():
    parser = argparse.ArgumentParser(description='经营资料与咨询服务')
    parser.add_argument('action', choices=['source', 'serve', 'demo'])
    parser.add_argument('--port', type=int, default=8760)
    parser.add_argument('--source-url', default='http://127.0.0.1:8760')
    parser.add_argument('--archive', default='var/reports.sqlite3')
    options = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    if options.action == 'source':
        server = source_server(root / 'data/release.json', port=options.port)
    elif options.action == 'serve':
        server = application_server(options.source_url, options.archive, port=options.port)
    else:
        with tempfile.TemporaryDirectory() as directory:
            source = source_server(root / 'data/release.json')
            source_thread = threading.Thread(target=source.serve_forever, daemon=True)
            source_thread.start()
            application = application_server(f'http://127.0.0.1:{source.server_port}', Path(directory) / 'reports.db')
            app_thread = threading.Thread(target=application.serve_forever, daemon=True)
            app_thread.start()
            try:
                client = Client(f'http://127.0.0.1:{source.server_port}')
                bundle = client.bundle()
                example = json.loads((root / 'data/request.json').read_text())
                receipt = client.quote(bundle['manifest']['release'], example)
                base = f'http://127.0.0.1:{application.server_port}'
                with urlopen(base + '/overview') as response:
                    overview = json.load(response)
                payload = {'release': bundle['manifest']['release'], 'source_digest': bundle['manifest']['digest'], 'kind': 'source-consultation', 'result': overview['overview'], 'receipts': [receipt]}
                request = Request(base + '/reports', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
                with urlopen(request) as response:
                    identifier = json.load(response)['id']
                with urlopen(base + '/reports/' + identifier) as response:
                    stored = json.load(response)
                print(json.dumps({'资料概览': overview, '业务回执': receipt, '存档编号': identifier, '重读一致': stored['payload'] == payload}, ensure_ascii=False, indent=2))
            finally:
                application.shutdown()
                source.shutdown()
                application.server_close()
                source.server_close()
        return
    print(f'服务已启动：127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
