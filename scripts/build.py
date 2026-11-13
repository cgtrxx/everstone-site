"""Create and verify the same explicit public artifact on Windows and Linux."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts' / 'checks'))
from common import CONFIG, pages, route, page_name


def digest(data):
    return hashlib.sha256(data).hexdigest()


def revision():
    value = os.environ.get('BUILD_REVISION') or os.environ.get('CF_PAGES_COMMIT_SHA') or subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if not re.fullmatch(r'[0-9a-f]{40}', value):
        raise ValueError('BUILD_REVISION must be a full Git commit SHA')
    return value


def public_path(name):
    if (not isinstance(name, str) or not name or '\\' in name
            or PureWindowsPath(name).drive or name.startswith('/')
            or any(part in ('', '.', '..') for part in name.split('/'))
            or ':' in name):
        raise ValueError(f'Unsafe public path: {name!r}')
    candidate = ROOT / PurePosixPath(name)
    if not candidate.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError(f'Public path escapes repository: {name}')
    if any(p.is_symlink() or p.is_junction() for p in (candidate, *candidate.parents)):
        raise ValueError(f'Symlinked public path: {name}')
    return candidate


def build():
    # Validate configuration before deleting or writing any artifact.
    for key in ('public_files', 'public_directories', 'shared_assets', 'pages'):
        for name in CONFIG[key]:
            public_path(name)
    files = pages()
    output = ROOT / 'dist'
    if output.is_symlink() or output.is_junction() or output.resolve().parent != ROOT.resolve():
        raise ValueError('Unsafe output directory')
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    allowed = set(CONFIG['public_files']) | {page_name(p) for p in files}
    extensions = set(CONFIG['public_extensions'])
    tracked = set(subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines())
    # Only committed public assets are eligible; local backup/untracked files cannot leak.
    for directory in CONFIG['public_directories']:
        folder = ROOT / directory
        if not folder.is_dir():
            raise ValueError(f'Missing public directory: {directory}')
        allowed.update(p for p in tracked if p.startswith(directory + '/') and Path(p).suffix.lower() in extensions)
    for name in sorted(allowed):
        source = public_path(name)
        if not source.is_file() or any(p.is_symlink() or p.is_junction() for p in (source, *source.parents)):
            raise ValueError(f'Missing or symlinked public file: {name}')
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = source.read_bytes()
        if source.suffix in ('.html', '.css', '.js', '.xml', '.txt', '.svg'):
            data = data.replace(b'\r\n', b'\n')
        destination.write_bytes(data)
    assets = {}
    for name in CONFIG['shared_assets']:
        asset = output / name
        data = asset.read_bytes()
        hashed = asset.with_name(f'{asset.stem}.{digest(data)[:12]}{asset.suffix}')
        hashed.write_bytes(data)
        assets[name] = hashed.relative_to(output).as_posix()
        asset.unlink()
        allowed.discard(name)
    for source in files:
        page = output / page_name(source)
        content = page.read_text(encoding='utf-8')
        for bare, hashed in assets.items():
            attr = 'href' if bare.endswith('.css') else 'src'
            pattern = rf'({attr}\s*=\s*["\']){re.escape(CONFIG.get('asset_url_prefix', '') + bare)}(["\'])'
            content, count = re.subn(pattern, lambda m: m[1] + CONFIG.get('asset_url_prefix', '') + hashed + m[2], content)
            if count != 1:
                raise ValueError(f'{source.name}: expected one {bare}, rewrote {count}')
        page.write_bytes(content.encode('utf-8'))
    headers = ['# Generated; only physical hashed assets are immutable.', '/*']
    headers += ['  ' + k + ': ' + v for k, v in CONFIG.get('response_headers', {}).items()]
    for bare, hashed in assets.items():
        headers += [f'/{hashed}', '  Cache-Control: public, max-age=31536000, immutable']
    cards = CONFIG.get('sharing', {})
    social_images = {card['image'] for card in cards.get('pages', {}).values()}
    if cards.get('default'):
        social_images.add(cards['default']['image'])
    for image in sorted(social_images):
        if image not in allowed:
            raise ValueError(f'Sharing image missing from tracked public assets: {image}')
        headers += ['/' + image, '  Cache-Control: public, max-age=31536000, immutable']
    css_assets = [a for a in assets.values() if a.endswith('.css')]
    for source in files:
        headers += [route(page_name(source)), '  Cache-Control: public, max-age=0, must-revalidate']
        headers += [f'  Link: </{asset}>; rel=preload; as=style' for asset in css_assets]
    headers += ['/deployment.json', '  Cache-Control: no-store']
    (output / '_headers').write_bytes(('\n'.join(headers) + '\n').encode())
    public = {p.relative_to(output).as_posix(): digest(p.read_bytes()) for p in output.rglob('*') if p.is_file()}
    manifest = {'revision': revision(), 'assets': assets, 'files': public}
    (output / 'deployment.json').write_bytes((json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode())
    permitted = allowed | set(assets.values()) | {'_headers', 'deployment.json'}
    actual = {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}
    if actual != permitted:
        raise ValueError(f'Artifact allowlist mismatch: {actual ^ permitted}')
    for hashed in assets.values():
        if Path(hashed).stem.rsplit('.', 1)[1] != digest((output / hashed).read_bytes())[:12]:
            raise ValueError('Hash does not match deployed bytes')
    print(f'build: OK ({len(files)} pages, {len(assets)} hashed assets, {len(actual)} public files; revision {manifest["revision"]})')
    return manifest


if __name__ == '__main__':
    build()
