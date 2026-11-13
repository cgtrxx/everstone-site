from common import page_name
import json
import sys
from common import CONFIG, pages, text, jsonld, route, document, norm, finish

errors, shared, count = [], {}, 0
files = pages()
required = CONFIG['jsonld_required']
if not required or not set(required) <= {page_name(p) for p in files}:
    errors.append('jsonld_required must identify existing pages')
for path in files:
    try:
        nodes = jsonld(text(path))
    except (ValueError, TypeError) as error:
        errors.append(f'{page_name(path)}: {error}')
        continue
    doc = document(text(path))
    descriptions = [n.attrs.get('content', '') for n in doc.find('meta') if n.attrs.get('name') == 'description']
    description = norm(descriptions[0]) if len(descriptions) == 1 else ''
    count += len(nodes)
    ids = [n['@id'] for n in nodes if '@id' in n]
    if len(ids) != len(set(ids)):
        errors.append(f'{page_name(path)}: duplicate JSON-LD @id')
    by_id = {n['@id']: n for n in nodes if '@id' in n}
    canonical = CONFIG['domain'].rstrip('/') + route(page_name(path))
    for node in nodes:
        kind = node.get('@type')
        if kind in ('WebPage', 'Service') and norm(node.get('description', '')) != description:
            errors.append(f'{page_name(path)}: {kind} description must match page metadata')
        if kind in ('WebPage', 'Service') and node.get('url') != canonical:
            errors.append(f'{page_name(path)}: {kind} URL must match canonical')
        if kind == 'Service':
            provider = by_id.get(node.get('provider', {}).get('@id'), {})
            page = by_id.get(node.get('mainEntityOfPage', {}).get('@id'), {})
            if provider.get('@type') != 'InsuranceAgency':
                errors.append(f'{page_name(path)}: Service must link to the InsuranceAgency provider')
            if page.get('@type') != 'WebPage' or page.get('mainEntity', {}).get('@id') != node.get('@id'):
                errors.append(f'{page_name(path)}: Service and WebPage must link to each other')
        if kind == 'BreadcrumbList':
            items = node.get('itemListElement', [])
            expected = [CONFIG['domain'].rstrip('/') + '/', canonical]
            if [item.get('position') for item in items] != [1, 2] or [item.get('item') for item in items] != expected:
                errors.append(f'{page_name(path)}: breadcrumb must run from home to canonical page')
    types = [n.get('@type') for n in nodes]
    for required_type in required.get(page_name(path), []):
        if types.count(required_type) != 1:
            errors.append(f'{page_name(path)}: expected exactly one {required_type} node')
    for node in nodes:
        if node.get('@type') in CONFIG['shared_jsonld_types']:
            shared.setdefault(node['@type'], {})[page_name(path)] = json.dumps(node, sort_keys=True)
for kind, values in shared.items():
    reference = values.get(CONFIG['reference_page'])
    if reference is None or any(v != reference for v in values.values()):
        errors.append(f'{kind}: semantic content differs from reference page')
sys.exit(finish('check_jsonld', errors, f'{len(files)} pages; {count} nodes; required types enforced'))
