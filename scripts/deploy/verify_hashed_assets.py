"""Verify a specific deployed revision, public manifest, asset bytes, and headers."""
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
expected = json.loads((ROOT / 'dist/deployment.json').read_text())
config = json.loads((ROOT / 'site.config.json').read_text()) if (ROOT / 'site.config.json').exists() else {}
base = (os.environ.get('BASE_URL') or config.get('domain', '')).rstrip('/')
if not base.startswith(('https://', 'http://127.0.0.1:')):
    raise ValueError('BASE_URL must be an explicit HTTPS deployment URL (or loopback for tests)')
sharing = config.get('sharing', {})
social_images = {card['image'] for card in sharing.get('pages', {}).values()}
if sharing.get('default'):
    social_images.add(sharing['default']['image'])

deadline = time.monotonic() + int(os.environ.get('DEPLOY_WAIT_SECONDS', '600'))


def fetch(name):
    request = urllib.request.Request(base + '/' + name, headers={'Cache-Control':'no-cache', 'Accept-Encoding':'identity'})
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise ValueError(f'{name}: HTTP {response.status}')
        return response.read(), response.headers


while True:
    try:
        data, _ = fetch('deployment.json?verify=' + str(time.time_ns()))
        live = json.loads(data)
        if live != expected:
            raise ValueError('Deployment manifest/revision differs from expected build')
        for name in [n for n in expected['files'] if n.endswith('.html')] + list(expected['assets'].values()) + sorted(social_images):
            data, headers = fetch(name)
            if hashlib.sha256(data).hexdigest() != expected['files'][name]:
                raise ValueError(f'{name}: response bytes differ from artifact')
            if name in expected['assets'].values() or name in social_images:
                policy = headers.get('Cache-Control', '').lower()
                if 'max-age=31536000' not in policy or 'immutable' not in policy:
                    raise ValueError(f'{name}: missing immutable cache policy')
            else:
                link = headers.get('Link', '')
                for css in [a for a in expected['assets'].values() if a.endswith('.css')]:
                    if f'</{css}>' not in link or 'rel=preload' not in link or 'as=style' not in link:
                        raise ValueError(f'{name}: missing stylesheet Link preload header')
        break
    except (urllib.error.URLError, ValueError, TimeoutError) as error:
        if time.monotonic() >= deadline:
            print('Verification FAILED: ' + str(error))
            sys.exit(1)
        print('Waiting for expected deployment: ' + str(error), flush=True)
        time.sleep(15)
print('Production verified: exact revision, HTML, shared-asset and sharing-image bytes, immutable cache policy, Link preload headers.')

