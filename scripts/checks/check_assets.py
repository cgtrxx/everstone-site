from common import page_name
import sys
from common import ROOT, CONFIG, pages, text, document, finish

errors = []
files = pages()
assets = CONFIG['shared_assets']
if not assets or len(set(assets)) != len(assets):
    errors.append('shared_assets must be nonempty and unique')
for asset in assets:
    if not (ROOT / asset).is_file() or (ROOT / asset).stat().st_size == 0:
        errors.append(f'{asset}: missing or empty')
for path in files:
    doc = document(text(path))
    css = [n.attrs.get('href') for n in doc.find('link') if n.attrs.get('rel') == 'stylesheet']
    js = [n.attrs.get('src') for n in doc.find('script') if n.attrs.get('src', '').startswith(CONFIG.get('asset_url_prefix', '') + 'assets/')]
    expected_css = [CONFIG.get('asset_url_prefix', '') + a for a in assets if a.endswith('.css')]
    expected_js = [CONFIG.get('asset_url_prefix', '') + a for a in assets if a.endswith('.js')]
    if css != expected_css or js != expected_js:
        errors.append(f'{page_name(path)}: expected bare shared references {assets}, found {css + js}')
for name in CONFIG['public_files']:
    if not (ROOT / name).is_file():
        errors.append(f'required public file missing: {name}')
sys.exit(finish('check_assets', errors, f'{len(files)} pages; {len(assets)} shared assets'))
