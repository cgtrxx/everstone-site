"""Negative fixtures prove the configured source gates reject real regressions."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        config=json.loads((ROOT/'site.config.json').read_text())
        shutil.copytree(ROOT/'scripts/checks',self.root/'scripts/checks',ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(ROOT/'assets',self.root/'assets')
        for name in ['site.config.json',*config['pages'],*config['public_files']]:
            target=self.root/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,target)

    def change(self,name,before,after):
        p=self.root/name;text=p.read_text();self.assertIn(before,text)
        p.write_text(text.replace(before,after,1),encoding='utf-8')

    def gate(self,name,success=False):
        r=subprocess.run([sys.executable,str(self.root/'scripts/checks'/f'check_{name}.py')],capture_output=True,text=True)
        self.assertEqual(r.returncode==0,success,r.stdout+r.stderr)

    def test_well_formed_fixture_passes_all_six_gates(self):
        for gate in ('doctype','css','assets','jsonld','seo','faq'):
            with self.subTest(gate=gate):self.gate(gate,True)

    def test_missing_page_rejected(self):
        (self.root/'about/index.html').unlink();self.gate('doctype')

    def test_unconfigured_nested_html_rejected(self):
        (self.root/'about/private.html').write_text('<!doctype html>');self.gate('doctype')

    def test_bom_rejected(self):
        self.change('index.html','<!doctype html>','\ufeff<!doctype html>');self.gate('doctype')

    def test_query_asset_versioning_rejected(self):
        self.change('index.html','/assets/style.css','/assets/style.css?v=1');self.gate('assets')

    def test_invalid_jsonld_rejected(self):
        self.change('index.html','"@context":','BROKEN "@context":');self.gate('jsonld')

    def test_wrong_page_url_rejected(self):
        self.change('index.html','"url": "https://everstone.example/"','"url": "https://everstone.example/wrong"');self.gate('jsonld')

    def test_prototype_indexing_regression_rejected(self):
        self.change('index.html','content="noindex,nofollow"','content="index,follow"');self.gate('seo')

    def test_missing_canonical_rejected(self):
        self.change('about/index.html','rel="canonical"','rel="alternate"');self.gate('seo')

    def test_shared_footer_drift_rejected(self):
        self.change('about/index.html','Thoughtful renovations.','Different footer.');self.gate('seo')

    def test_faq_drift_rejected(self):
        self.change('bathroom-renovations/index.html','<summary>What kinds of projects can you help with?</summary>','<summary>Changed question?</summary>');self.gate('faq')

    def test_social_image_corruption_rejected(self):
        config=json.loads((self.root/'site.config.json').read_text())
        (self.root/config['sharing']['default']['image']).write_bytes(b'broken');self.gate('seo')

    def test_wrong_social_dimensions_rejected(self):
        self.change('index.html','property="og:image:width" content="1320"','property="og:image:width" content="600"');self.gate('seo')

    def test_undefined_variable_rejected(self):
        p=self.root/'assets/style.css';p.write_text(p.read_text()+'\nbody{color:var(--undefined-ci)}');self.gate('css')

    def test_unbalanced_css_rejected(self):
        p=self.root/'assets/style.css';p.write_text(p.read_text()+'\nbody{color:red;');self.gate('css')

    def test_new_cascade_debt_rejected(self):
        p=self.root/'assets/style.css';p.write_text(p.read_text()+'\nbody{opacity:1}body{opacity:.9}');self.gate('css')

    def test_variable_fallback_allowed(self):
        p=self.root/'assets/style.css';p.write_text(p.read_text()+'\nbody{outline-color:var(--optional-ci,red)}');self.gate('css',True)

if __name__=='__main__':unittest.main()
