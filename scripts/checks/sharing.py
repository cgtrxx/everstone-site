from common import page_name
"""Static Open Graph/X Card contract. Standard library only."""
import hashlib
import struct
from pathlib import PurePosixPath
from common import CONFIG, ROOT, norm

def validate_sharing(path, doc, errors):
    sharing = CONFIG.get('sharing', {})
    card = sharing.get('pages', {}).get(page_name(path), sharing.get('default', {}))
    relative = card.get('image', '')
    image = CONFIG['domain'].rstrip('/') + '/' + relative
    titles, descriptions = doc.find('title'), [n for n in doc.find('meta') if n.attrs.get('name') == 'description']
    title = norm(titles[0].content()) if len(titles) == 1 else ''
    description = norm(descriptions[0].attrs.get('content', '')) if len(descriptions) == 1 else ''
    expected = {
        'og:title': title, 'og:description': description, 'og:type': 'website',
        'og:site_name': CONFIG['site_name'], 'og:locale': 'en_CA',
        'og:image': image, 'og:image:secure_url': image, 'og:image:type': 'image/png',
        'og:image:width': str(sharing.get('width', '')),
        'og:image:height': str(sharing.get('height', '')),
        'og:image:alt': card.get('alt', ''),
        'twitter:card': 'summary_large_image', 'twitter:title': title,
        'twitter:description': description, 'twitter:image': image,
        'twitter:image:alt': card.get('alt', '')
    }
    for key, value in expected.items():
        attr = 'property' if key.startswith('og:') else 'name'
        found = [norm(n.attrs.get('content', '')) for n in doc.find('meta') if n.attrs.get(attr) == key]
        if not value or found != [norm(value)]:
            errors.append(f'{page_name(path)}: expected one matching {key}')
    file = PurePosixPath(relative)
    if not relative.startswith('assets/social/') or file.is_absolute() or '..' in file.parts:
        errors.append(f'{page_name(path)}: sharing image must be inside assets/social')
        return
    try:
        data = (ROOT / relative).read_bytes()
        if data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR':
            raise ValueError('expected PNG IHDR')
        dimensions = struct.unpack('>II', data[16:24])
        if dimensions != (sharing.get('width'), sharing.get('height')):
            errors.append(f'{page_name(path)}: sharing image dimensions differ from configured source')
        if len(data) > sharing.get('max_bytes', 300000):
            errors.append(f'{page_name(path)}: sharing image exceeds byte budget')
        if file.stem.rsplit('.', 1)[-1] != hashlib.sha256(data).hexdigest()[:12]:
            errors.append(f'{page_name(path)}: sharing image fingerprint differs from bytes')
    except (OSError, ValueError, struct.error) as error:
        errors.append(f'{page_name(path)}: sharing image invalid: {error}')
