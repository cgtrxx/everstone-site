"""Shared, project-configured helpers. No third-party Python dependencies."""
import json
import re
import html
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((ROOT / 'site.config.json').read_text(encoding='utf-8'))


def page_name(path):
    return path.relative_to(ROOT).as_posix()


def pages():
    expected = set(CONFIG['pages'])
    if not expected or len(expected) != len(CONFIG['pages']):
        raise ValueError('pages must be nonempty and unique')
    excluded = {'.git', 'dist', 'node_modules', '.build', '.venv'}
    actual = {page_name(p) for p in ROOT.rglob('*.html')
              if not excluded.intersection(p.relative_to(ROOT).parts)}
    if actual != expected:
        raise ValueError(f'page inventory mismatch: missing={expected-actual}, unconfigured={actual-expected}')
    if set(CONFIG['routes']) != expected or len(set(CONFIG['routes'].values())) != len(expected):
        raise ValueError('Every page needs a unique configured route')
    for name in expected:
        path = ROOT / name
        if (path.resolve() != path.absolute() or not path.is_file() or
                any(p.is_symlink() or p.is_junction() for p in (path, *path.parents))):
            raise ValueError('Unsafe configured page path')
    return [ROOT / name for name in sorted(expected)]


def text(path):
    return path.read_text(encoding='utf-8')


class Element:
    def __init__(self, tag='', attrs=(), parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children = []

    def find(self, tag=None, cls=None):
        result = []
        for child in self.children:
            if isinstance(child, Element):
                if (tag is None or child.tag == tag) and (cls is None or cls in child.attrs.get('class', '').split()):
                    result.append(child)
                result.extend(child.find(tag, cls))
        return result

    def content(self):
        return ''.join(c.content() if isinstance(c, Element) else c for c in self.children)


class Document(HTMLParser):
    VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}

    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = Element()
        self.current = self.root
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        node = Element(tag, attrs, self.current)
        self.current.children.append(node)
        if tag not in self.VOID:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        node = self.current
        while node.parent:
            if node.tag == tag:
                self.current = node.parent
                return
            node = node.parent

    def handle_data(self, data):
        self.current.children.append(data)


def document(source):
    return Document(source).root


def norm(value):
    return re.sub(r'\s+', ' ', html.unescape(value)).strip()


def jsonld(source):
    result = []
    for script in document(source).find('script'):
        if script.attrs.get('type') != 'application/ld+json':
            continue
        data = json.loads(script.content())
        values = data if isinstance(data, list) else [data]
        for value in values:
            if not isinstance(value, dict):
                raise ValueError('JSON-LD node must be an object')
            result.extend(value.get('@graph', [value]))
    return result


def route(name):
    return CONFIG['routes'][name]


def finish(name, errors, coverage):
    for error in errors:
        print('  FAIL ' + error)
    print(f'{name}: {"FAILED" if errors else "OK"} ({coverage})')
    return int(bool(errors))
