from common import page_name
import collections
import re
import sys
import xml.etree.ElementTree as ET
from common import ROOT, CONFIG, pages, text, document, norm, route, finish

from urllib.parse import urlsplit
from sharing import validate_sharing

errors = []
files = pages()
domain = CONFIG['domain'].rstrip('/')
reference = text(ROOT / CONFIG['reference_page'])
values = {key: collections.defaultdict(list) for key in ('title', 'description', 'h1')}
mode = CONFIG['mode']
if mode not in ('prototype', 'production'):
    errors.append('mode must be prototype or production')
for path in files:
    source = text(path)
    doc = document(source)
    validate_sharing(path, doc, errors)
    for link in doc.find('a'):
        href = urlsplit(link.attrs.get('href', ''))
        if not href.netloc or href.netloc == urlsplit(domain).netloc:
            if href.path.lstrip('/') in CONFIG['pages']:
                errors.append(f'{page_name(path)}: internal link must use canonical route: {href.path}')
    for label in values:
        nodes = ([n for n in doc.find('meta') if n.attrs.get('name') == 'description']
                 if label == 'description' else doc.find(label))
        value = norm(nodes[0].attrs.get('content', '') if label == 'description' else nodes[0].content()) if len(nodes) == 1 else ''
        if not value:
            errors.append(f'{page_name(path)}: expected one nonempty {label}')
        values[label][value.casefold()].append(page_name(path))
    robots = [n.attrs.get('content', '') for n in doc.find('meta') if n.attrs.get('name') == 'robots']
    if len(robots) != 1 or ((mode == 'prototype' or page_name(path) == '404.html') != ('noindex' in robots[0].lower())):
        errors.append(f'{page_name(path)}: robots policy differs from configured {mode} mode')
    if page_name(path) != '404.html':
        expected = domain + route(page_name(path))
        canonical = [n.attrs.get('href') for n in doc.find('link') if n.attrs.get('rel') == 'canonical']
        og = [n.attrs.get('content') for n in doc.find('meta') if n.attrs.get('property') == 'og:url']
        if canonical != [expected] or og != [expected]:
            errors.append(f'{page_name(path)}: canonical and og:url must equal {expected}')
    for tag, cls in CONFIG['shared_blocks'].items():
        pattern = rf'<{tag}\b[^>]*class="{re.escape(cls)}"[^>]*>[\s\S]*?</{tag}>'
        found, ref = re.findall(pattern, source), re.findall(pattern, reference)
        def shared_markup(value):
            for allowed_class in CONFIG.get('shared_block_presentation_classes', []):
                value = value.replace(f' class="{allowed_class}"', '')
            return value
        if len(found) != 1 or len(ref) != 1 or shared_markup(found[0]) != shared_markup(ref[0]):
            errors.append(f'{page_name(path)}: shared {tag} differs from reference')
for label, grouped in values.items():
    for value, names in grouped.items():
        if value and len(names) > 1:
            errors.append(f'duplicate {label}: {names}')
locs = [n.text for n in ET.parse(ROOT / 'sitemap.xml').getroot().iter() if n.tag.endswith('}loc')]
expected_locs = {domain + route(page_name(p)) for p in files if page_name(p) not in CONFIG['sitemap_exclude']}
if len(locs) != len(set(locs)) or set(locs) != expected_locs:
    errors.append('sitemap URLs must match configured canonical pages without duplicates')
robots_source = text(ROOT / 'robots.txt')
blocked = bool(re.search(r'^Disallow:\s*/\s*$', robots_source, re.M))
if (mode == 'prototype') != blocked:
    errors.append('robots.txt crawl policy differs from configured mode')
if mode == 'production' and f'Sitemap: {domain}/sitemap.xml' not in robots_source:
    errors.append('production robots.txt must declare sitemap')
sys.exit(finish('check_seo', errors, f'{len(files)} pages; {len(locs)} sitemap URLs; {mode} mode'))
