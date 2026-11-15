"""来源协议客户端，统一记录请求所用资料版本。"""
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import hashlib
import json
from .provider import canonical

class Client:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')

    def request(self, path, release=None, value=None):
        headers = {'Accept': 'application/json'}
        if release:
            headers['If-Match'] = release
        body = None if value is None else canonical(value)
        if body is not None:
            headers['Content-Type'] = 'application/json'
        request = Request(self.base_url + path, data=body, headers=headers)
        with urlopen(request, timeout=5) as response:
            return json.load(response)

    def bundle(self):
        manifest = self.request('/manifest')
        release, rows, cursor = manifest['release'], [], None
        while True:
            page = self.request('/records' + ('?' + urlencode({'cursor': cursor}) if cursor else ''), release)
            if page['release'] != release:
                raise ValueError('页版本与清单不一致')
            rows.extend(page['rows'])
            cursor = page['next']
            if cursor is None:
                break
        data = {**manifest['metadata'], 'rows': rows}
        if len(rows) != manifest['row_count'] or hashlib.sha256(canonical(data)).hexdigest() != manifest['digest']:
            raise ValueError('资料完整性核验失败')
        return {'manifest': manifest, 'data': data}

    def quote(self, release, request):
        return self.request('/quote', release, request)

    def detail(self, release, request):
        return self.request('/detail', release, request)
