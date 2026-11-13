"""The inherited publication contract, exercised against Everstone's configured routes."""
import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = ROOT / 'dist'
        cls.manifest = json.loads((cls.output / 'deployment.json').read_text())
        cls.config = json.loads((ROOT / 'site.config.json').read_text())

    def test_only_physical_hashed_shared_assets(self):
        for bare, hashed in self.manifest['assets'].items():
            self.assertFalse((self.output / bare).exists())
            data = (self.output / hashed).read_bytes()
            self.assertEqual(Path(hashed).stem.rsplit('.',1)[1],hashlib.sha256(data).hexdigest()[:12])
            self.assertEqual(data,(ROOT / bare).read_bytes().replace(b'\r\n',b'\n'))
        for name in self.config['pages']:
            source = (self.output / name).read_text()
            for bare, hashed in self.manifest['assets'].items():
                self.assertNotRegex(source,rf'(?:src|href)=["\']/{re.escape(bare)}(?:["\'?])')
                self.assertEqual(source.count('/'+hashed),1)

    def test_manifest_matches_all_published_bytes(self):
        actual = {p.relative_to(self.output).as_posix() for p in self.output.rglob('*') if p.is_file()}
        self.assertEqual(actual,set(self.manifest['files'])|{'deployment.json'})
        for name, expected in self.manifest['files'].items():
            self.assertEqual(hashlib.sha256((self.output/name).read_bytes()).hexdigest(),expected,name)

    def test_source_and_internal_files_never_published(self):
        for name in self.manifest['files']:
            self.assertNotEqual(Path(name).suffix,'.md')
            self.assertNotIn(name.split('/')[0],{'scripts','tools','docs','.github','.git','site.config.json','build.sh','.htmlvalidate.json'})

    def test_security_cache_and_preload_headers(self):
        headers = (self.output/'_headers').read_text()
        for name in self.manifest['assets'].values():
            self.assertIn('/'+name+'\n  Cache-Control: public, max-age=31536000, immutable',headers)
        for name in self.config['routes'].values():
            self.assertIn(name+'\n  Cache-Control: public, max-age=0, must-revalidate',headers)
        self.assertIn("connect-src 'none'",headers)
        self.assertIn('X-Content-Type-Options: nosniff',headers)
        image=self.config['sharing']['default']['image']
        self.assertEqual((self.output/image).read_bytes(),(ROOT/image).read_bytes())

    def test_repeat_build_is_deterministic(self):
        subprocess.run([sys.executable,'scripts/build.py'],cwd=ROOT,check=True,capture_output=True)
        self.assertEqual(json.loads((self.output/'deployment.json').read_text()),self.manifest)


if __name__ == '__main__':
    unittest.main()
