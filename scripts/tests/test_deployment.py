"""HTTP contract fixtures; no browser or live production requests."""
import hashlib
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'scripts/deploy').mkdir(parents=True)
        shutil.copyfile(ROOT / 'scripts/deploy/verify_hashed_assets.py', self.root / 'scripts/deploy/verify_hashed_assets.py')
        dist = self.root / 'dist'
        dist.mkdir()
        self.payloads = {'index.html': b'<html><body>Release</body></html>', 'assets/styles.123.css': b'body {}', 'assets/main.456.js': b'void 0;'}
        self.payloads['assets/social/home.test.png'] = b'sharing image fixture'
        (self.root / 'site.config.json').write_text(json.dumps({'sharing': {'pages': {'index.html': {'image': 'assets/social/home.test.png'}}}}))
        self.manifest = {'revision': 'a' * 40, 'assets': {'assets/styles.css':'assets/styles.123.css', 'assets/main.js':'assets/main.456.js'},
                         'files': {name:hashlib.sha256(data).hexdigest() for name,data in self.payloads.items()}}
        (dist / 'deployment.json').write_text(json.dumps(self.manifest))
        self.live_manifest = dict(self.manifest)
        self.cache_ok = True
        self.preload_ok = True
        fixture = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                name = self.path.split('?')[0].lstrip('/')
                if name == 'deployment.json':
                    data = json.dumps(fixture.live_manifest).encode()
                else:
                    data = fixture.payloads[name]
                self.send_response(200)
                if name.startswith('assets/'):
                    self.send_header('Cache-Control', 'public, max-age=31536000, immutable' if fixture.cache_ok else 'no-cache')
                if name.endswith('.html') and fixture.preload_ok:
                    self.send_header('Link', '</assets/styles.123.css>; rel=preload; as=style')
                self.end_headers()
                self.wfile.write(data)

        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def verify(self, success):
        env = dict(os.environ, BASE_URL=f'http://127.0.0.1:{self.server.server_port}', DEPLOY_WAIT_SECONDS='0')
        result = subprocess.run([sys.executable, str(self.root / 'scripts/deploy/verify_hashed_assets.py')], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)

    def test_matching_release_passes(self):
        self.verify(True)

    def test_stale_html_only_revision_fails(self):
        self.live_manifest['revision'] = 'b' * 40
        self.verify(False)

    def test_corrupt_html_bytes_fail(self):
        self.payloads['index.html'] = b'Previous HTML with unchanged CSS'
        self.verify(False)

    def test_corrupt_asset_bytes_fail(self):
        self.payloads['assets/styles.123.css'] = b'Previous CSS'
        self.verify(False)

    def test_corrupt_sharing_image_fails(self):
        self.payloads['assets/social/home.test.png'] = b'wrong sharing image'
        self.verify(False)

    def test_mutable_cache_policy_fails(self):
        self.cache_ok = False
        self.verify(False)

    def test_missing_preload_header_fails(self):
        self.preload_ok = False
        self.verify(False)


if __name__ == '__main__':
    unittest.main()

