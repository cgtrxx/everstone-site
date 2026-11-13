"""Actual HTTP requests must expose only the verified artifact."""
import http.client
import json
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from preview import Server, handler


class PreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads((ROOT/'site.config.json').read_text())
        cls.server=Server(('127.0.0.1',0),handler(ROOT/'dist'))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()

    def request(self,path,method='GET',headers=None):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        c.request(method,path,headers=headers or {})
        r=c.getresponse();result=(r.status,r.read(),dict(r.getheaders()));c.close()
        return result

    def test_every_canonical_route_and_physical_redirect(self):
        for name,route in self.config['routes'].items():
            status,body,headers=self.request(route)
            self.assertEqual(status,200,route)
            self.assertEqual(body,(ROOT/'dist'/name).read_bytes())
            self.assertIn('rel=preload',headers['Link'])
            self.assertIn('noindex',headers['X-Robots-Tag'])
            status,body,headers=self.request('/'+name+'?ref=test')
            self.assertEqual(status,301)
            self.assertEqual(headers['Location'],route+'?ref=test')

    def test_all_manifest_assets_and_cache_policy(self):
        manifest=json.loads((ROOT/'dist/deployment.json').read_text())
        for name in manifest['assets'].values():
            status,body,headers=self.request('/'+name)
            self.assertEqual(body,(ROOT/'dist'/name).read_bytes())
            self.assertIn('immutable',headers['Cache-Control'])

    def test_unpublished_files_traversal_and_source_paths_fail(self):
        for path in ('/.git/config','/site.config.json','/scripts/build.py','/README.md','/_headers','/assets/style.css','/../README.md','/%2e%2e/README.md','/not-a-page'):
            self.assertEqual(self.request(path)[0],404,path)

    def test_host_origin_methods_and_head(self):
        for headers in ({'Host':'evil.example'},{'Origin':'https://evil.example'},{'Sec-Fetch-Site':'cross-site'}):
            self.assertEqual(self.request('/',headers=headers)[0],403)
        self.assertEqual(self.request('/',method='POST')[0],501)
        self.assertEqual(self.request('/',method='HEAD')[1],b'')

    def test_source_directory_is_not_a_preview_target(self):
        with self.assertRaises(FileNotFoundError):handler(ROOT)

    def test_tampered_artifact_is_rejected_before_serving(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'dist';shutil.copytree(ROOT/'dist',target)
            (target/'index.html').write_text('tampered')
            with self.assertRaisesRegex(ValueError,'integrity'):handler(target)


if __name__=='__main__':unittest.main()
