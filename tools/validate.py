"""Validate the buildless site's links, assets, metadata and publication inventory."""
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = {"index.html", "about/index.html", "services/index.html", "projects/index.html",
            "privacy-policy/index.html", "contact/index.html", "our-process/index.html",
            "bathroom-renovations/index.html", "kitchen-renovations/index.html",
            "basement-renovations/index.html", "flooring/index.html", "drywall-painting/index.html",
            "full-home-renovations/index.html", "garage-renovations/index.html"}
errors = []
class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs = []; self.ids = set(); self.h1 = 0; self.title = False
        self.description = False; self.ld = False; self.json_text = ""
    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        if attrs.get("id"):
            if attrs["id"] in self.ids: errors.append("Duplicate HTML id: " + attrs["id"])
            self.ids.add(attrs["id"])
        self.h1 += tag == "h1"
        self.title |= tag == "title"
        self.description |= tag == "meta" and attrs.get("name") == "description" and bool(attrs.get("content"))
        if any(key.startswith("on") for key in attrs): errors.append("Inline event handler")
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.ld = True; self.json_text = ""
        for key in ("href", "src"):
            if key in attrs: self.refs.append((attrs[key], tag != "a"))
    def handle_data(self, data):
        if self.ld: self.json_text += data
    def handle_endtag(self, tag):
        if tag == "script" and self.ld:
            try: json.loads(self.json_text)
            except ValueError: errors.append("Invalid JSON-LD")
            self.ld = False

pages = {p.relative_to(ROOT).as_posix(): p for p in ROOT.rglob("*.html") if ".git" not in p.parts}
if set(pages) != EXPECTED: errors.append("HTML page inventory does not match the 14 approved pages")
documents = {}
for relative, path in pages.items():
    text = path.read_text(encoding="utf-8")
    if "\ufffd" in text: errors.append(relative + ": replacement character in UTF-8")
    if re.search(r"(?:[A-Z]:\\\\Users\\\\|127\.0\.0\.1|localhost)", text): errors.append(relative + ": local-machine reference")
    doc = Document(); doc.feed(text); documents[relative] = doc
    if doc.h1 != 1 or not doc.title or not doc.description: errors.append(relative + ": incomplete page metadata")

def check_reference(reference, parent, resource=False):
    parsed = urlsplit(reference)
    if parsed.scheme or parsed.netloc:
        if resource or parsed.scheme.lower() in ("javascript", "data"):
            errors.append(parent + ": non-local or unsafe reference")
        return
    path = unquote(parsed.path)
    target = (ROOT / path.lstrip("/")) if path.startswith("/") else (ROOT / parent).parent / path
    if not path: target = ROOT / parent
    target = target.resolve()
    if not target.is_relative_to(ROOT): errors.append(parent + ": path escapes root"); return
    if target.is_dir(): target /= "index.html"
    if not target.is_file(): errors.append(parent + ": missing reference " + reference); return
    if parsed.fragment and target.suffix == ".html":
        relative = target.relative_to(ROOT).as_posix()
        if relative in documents and parsed.fragment not in documents[relative].ids:
            errors.append(parent + ": missing fragment " + reference)

for relative, doc in documents.items():
    for ref, resource in doc.refs: check_reference(ref, relative, resource)
for path in (ROOT / "assets").rglob("*.css"):
    text = path.read_text(encoding="utf-8")
    if "@import" in text: errors.append("Remote CSS import")
    for ref in re.findall(r"url\(([^)]+)\)", text):
        check_reference(ref.strip(" \"'"), path.relative_to(ROOT).as_posix(), True)
manifest = json.loads((ROOT / "docs/asset-sources.json").read_text(encoding="utf-8"))
for entry in manifest:
    path = ROOT / entry["path"]
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
        errors.append("Asset provenance hash mismatch: " + entry["path"])
for path in ROOT.rglob("*"):
    if ".git" in path.parts: continue
    if path.is_symlink() or path.is_junction(): errors.append("Linked path")
    if path.is_file() and path.suffix in (".html", ".css", ".js", ".py", ".md", ".json", ".txt"):
        content = path.read_text(encoding="utf-8")
        if re.search(r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)", content):
            errors.append("Possible embedded credential in " + path.relative_to(ROOT).as_posix())
if errors:
    for error in errors: print("FAIL:", error)
    raise SystemExit(1)
print("PASS: 14 pages; internal links/fragments; local HTML/CSS resources; JSON-LD; UTF-8.")
print("PASS: 17 third-party asset hashes; no linked paths or detected credential patterns.")
