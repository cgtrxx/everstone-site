from common import page_name
"""Run all enabled source gates and report every failed gate."""
import subprocess
import sys
from pathlib import Path

CHECKS = ['doctype', 'css', 'assets', 'jsonld', 'seo', 'faq']
HERE = Path(__file__).resolve().parent
failed = []
for name in CHECKS:
    result = subprocess.run([sys.executable, str(HERE / f'check_{name}.py')])
    if result.returncode:
        failed.append(name)
print('run_all: ' + ('FAILED: ' + ', '.join(failed) if failed else 'all 6 gates passed'))
sys.exit(int(bool(failed)))
