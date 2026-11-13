"""Preview only a verified dist artifact; retain the local-only security controls."""
import argparse
import fnmatch
import hashlib
import http.server
import json
from pathlib import Path
import socket
import threading
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
TYPES = {'.html':'text/html; charset=utf-8', '.css':'text/css; charset=utf-8',
         '.js':'text/javascript; charset=utf-8', '.svg':'image/svg+xml',
         '.png':'image/png', '.jpg':'image/jpeg', '.jpeg':'image/jpeg',
         '.ttf':'font/ttf', '.woff':'font/woff', '.woff2':'font/woff2',
         '.json':'application/json', '.xml':'application/xml', '.txt':'text/plain; charset=utf-8'}


def handler(directory):
    directory = Path(directory).absolute()
    if any(p.is_symlink() or p.is_junction() for p in (directory, *directory.parents)):
        raise ValueError('Linked artifact directory')
    manifest_path = directory / 'deployment.json'
    if manifest_path.is_symlink() or manifest_path.is_junction():
        raise ValueError('Linked deployment manifest')
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    allowed = set(manifest['files']) | {'deployment.json'}
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}
    if actual != allowed or len(allowed) > 256:
        raise ValueError('Artifact differs from its publication manifest')
    snapshot = {}
    total = 0
    for name in allowed:
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts or '\\' in name:
            raise ValueError('Unsafe manifest path')
        path = directory / relative
        if any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
            raise ValueError('Linked artifact file')
        if path.stat().st_size > 10 * 1024 * 1024:
            raise ValueError('Oversized artifact file')
        data = path.read_bytes()
        total += len(data)
        if total > 25 * 1024 * 1024:
            raise ValueError('Oversized artifact')
        if name != 'deployment.json' and hashlib.sha256(data).hexdigest() != manifest['files'][name]:
            raise ValueError('Artifact integrity failure: ' + name)
        snapshot[name] = data
    # _headers is hosting configuration, not a publicly downloadable document.
    header_rules = []
    pattern = None
    for line in snapshot['_headers'].decode('utf-8').splitlines():
        if not line or line.startswith('#'):
            continue
        if not line[0].isspace():
            pattern = line
            header_rules.append((pattern, {}))
        elif pattern:
            key, value = line.strip().split(':', 1)
            header_rules[-1][1][key] = value.strip()
    snapshot.pop('_headers')
    routes, redirects = {}, {}
    for name in snapshot:
        if not name.endswith('.html'):
            continue
        canonical = '/' if name == 'index.html' else '/' + name.removesuffix('index.html') if name.endswith('/index.html') else '/' + name[:-5]
        routes[canonical] = name
        redirects['/' + name] = canonical
        if canonical.endswith('/') and canonical != '/':
            redirects[canonical.rstrip('/')] = canonical

    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.0'

        def setup(self):
            self.request.settimeout(2)
            super().setup()

        def log_message(self, *args):
            pass

        def reply(self, status, data=b'', name='', location=None):
            self.send_response_only(status)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Content-Type', TYPES.get(Path(name).suffix, 'text/plain'))
            headers = {'Connection':'close', 'Cache-Control':'no-store'}
            route = self.path.split('?', 1)[0]
            for pattern, values in header_rules:
                if fnmatch.fnmatchcase(route, pattern):
                    headers.update(values)
            if status == 404:
                headers['X-Robots-Tag'] = 'noindex'
            if location:
                headers['Location'] = location
            for key, value in headers.items():
                self.send_header(key, value)
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(data)
            self.close_connection = True

        def send_error(self, code, message=None, explain=None):
            self.reply(code)

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            origin = f'http://127.0.0.1:{self.server.server_port}'
            if self.headers.get_all('Host') != [f'127.0.0.1:{self.server.server_port}']:
                return self.reply(403)
            for key in ('Origin', 'Sec-Fetch-Site', 'Content-Length', 'Transfer-Encoding'):
                if len(self.headers.get_all(key, [])) > 1:
                    return self.reply(400)
            if self.headers.get('Origin', origin) != origin or self.headers.get('Sec-Fetch-Site', 'none') not in ('none','same-origin'):
                return self.reply(403)
            if self.headers.get('Transfer-Encoding') or self.headers.get('Content-Length', '0') != '0':
                return self.reply(400)
            parsed = urllib.parse.urlsplit(self.path)
            path = parsed.path
            if path in redirects and path != redirects[path]:
                return self.reply(301, location=redirects[path] + ('?' + parsed.query if parsed.query else ''))
            name = routes.get(path, path.lstrip('/'))
            if name not in snapshot:
                return self.reply(404, snapshot['404.html'], '404.html')
            return self.reply(200, snapshot[name], name)

    return Handler


class Server(http.server.HTTPServer):
    allow_reuse_address = False
    request_queue_size = 8

    def server_bind(self):
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

    def handle_error(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT / 'dist')
    parser.add_argument('--port', type=int, default=8777)
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('Invalid port')
    with Server(('127.0.0.1', args.port), handler(args.directory)) as server:
        timer = threading.Timer(7200, server.shutdown)
        timer.daemon = True
        timer.start()
        print(f'Preview: http://127.0.0.1:{server.server_port}/ (verified dist only)', flush=True)
        try:
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            pass
        finally:
            timer.cancel()


if __name__ == '__main__':
    main()
