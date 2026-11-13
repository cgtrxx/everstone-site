"""Publication boundaries fail closed before artifact mutation."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('artifact_builder', ROOT/'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class BuildPathTests(unittest.TestCase):
    def test_unsafe_config_paths_fail_before_output_changes(self):
        manifest = ROOT/'dist/deployment.json'
        before = manifest.read_bytes()
        for name in ('../secret.txt', '/secret.txt', 'C:/secret.txt', 'assets/../secret',
                     'assets\\secret', 'assets//secret', 'assets/file:stream', '.'):
            with self.subTest(name=name), patch.dict(builder.CONFIG, public_files=[name]):
                with self.assertRaises(ValueError):
                    builder.build()
                self.assertEqual(manifest.read_bytes(), before)

    def test_untracked_asset_excluded_and_stale_output_removed(self):
        stray = ROOT/'assets/pipeline-untracked-fixture.txt'
        stale = ROOT/'dist/stale-fixture.txt'
        self.assertFalse(stray.exists())
        try:
            stray.write_text('not published')
            stale.write_text('stale')
            result = builder.build()
            self.assertNotIn('assets/pipeline-untracked-fixture.txt', result['files'])
            self.assertFalse((ROOT/'dist/assets/pipeline-untracked-fixture.txt').exists())
            self.assertFalse(stale.exists())
        finally:
            stray.unlink(missing_ok=True)
