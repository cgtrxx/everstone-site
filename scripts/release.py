"""Shared fail-fast release checks for local work, GitHub CI, and Cloudflare."""
import shutil
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    npx = shutil.which('npx')
    pnpm = shutil.which('pnpm')
    if npx:
        validator = [npx, '--yes', 'html-validate@8.29.0']
    elif pnpm:
        store = os.environ.get('PNPM_STORE_DIR')
        validator = [pnpm] + ([f'--config.store-dir={store}'] if store else []) + ['dlx', 'html-validate@8.29.0']
    else:
        raise RuntimeError('Install Node.js with npx, or pnpm, to run the pinned HTML validator')
    validator += json.loads((ROOT / 'site.config.json').read_text())['pages']
    steps = [
        [sys.executable, 'scripts/checks/run_all.py'],
        validator,
        ['node', '--check', 'assets/main.js'],
        ['node', '--test', 'scripts/tests/test_contact_form.mjs'],
        [sys.executable, 'scripts/build.py'],
        [sys.executable, '-m', 'unittest', 'discover', '-s', 'scripts/tests', '-v'],
    ]
    for command in steps:
        print('Release step: ' + ' '.join(command), flush=True)
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return result.returncode
    print('Release checks and artifact build passed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
