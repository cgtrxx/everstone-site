from common import page_name
#!/usr/bin/env python3
"""CI gate: shared CSS stays resolved, referenced, and free of cascade duplicates."""
import re
import sys
from collections import defaultdict
from pathlib import Path

from common import ROOT, CONFIG, pages
import json
STYLE = ROOT / next(a for a in CONFIG["shared_assets"] if a.endswith(".css"))
COMMENT = re.compile(r"/\*[\s\S]*?\*/")
VARIABLE_DEFINITION = re.compile(r"(?<![\w-])(--[a-z0-9_-]+)\s*:", re.IGNORECASE)
VARIABLE_USE = re.compile(r"var\(\s*(--[a-z0-9_-]+)", re.IGNORECASE)
CLASS_SELECTOR = re.compile(r"\.(-?[_a-zA-Z]+[_a-zA-Z0-9-]*)")
HTML_CLASS = re.compile(r"""\bclass\s*=\s*(["'])(.*?)\1""", re.IGNORECASE | re.DOTALL)
QUOTED_TOKEN = re.compile(r"""["'`]([a-zA-Z_][a-zA-Z0-9_-]*)["'`]""")
IGNORED_SOURCE_PARTS = {".git", "dist"}
DECLARATION = re.compile(r"(?:^|;)\s*([a-z-]+)\s*:\s*([^;]*)", re.IGNORECASE)
NESTED_AT_RULES = ("@media", "@supports", "@container", "@layer")


def blank_comments(text):
    return COMMENT.sub(lambda match: re.sub(r"[^\n]", " ", match.group(0)), text)


def closing_brace(text, opening):
    depth = 1
    quote = None
    index = opening + 1

    while index < len(text):
        char = text[index]
        if quote:
            if char == "\\":
                index += 2
                continue
            if char == quote:
                quote = None
        elif char in ('"', "'"):
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1

    return -1


def declarations(body):
    return [(match.group(1).lower(), match.group(2).strip()) for match in DECLARATION.finditer(body)]


def rules(text, start=0, end=None, context=()):
    end = len(text) if end is None else end
    position = start
    found = []

    while position < end:
        while position < end and (text[position].isspace() or text[position] == ";"):
            position += 1
        if position >= end:
            break

        opening = text.find("{", position, end)
        if opening == -1:
            break

        semicolon = text.find(";", position, opening)
        if semicolon != -1:
            position = semicolon + 1
            continue

        prelude = " ".join(text[position:opening].split())
        closing = closing_brace(text, opening)
        if closing == -1 or closing > end:
            raise ValueError("Unbalanced CSS block")

        body = text[opening + 1:closing]
        lowered = prelude.lower()
        if lowered.startswith(NESTED_AT_RULES):
            found.extend(rules(text, opening + 1, closing, context + (prelude,)))
        elif not prelude.startswith("@"):
            line = text.count("\n", 0, position) + 1
            found.append((context, prelude, line, declarations(body)))

        position = closing + 1

    return found


def referenced_classes():
    found = set()
    for path in [*pages(), *(ROOT / asset for asset in CONFIG['shared_assets'] if asset.endswith('.js'))]:
        source = path.read_text(encoding='utf-8')
        if path.suffix == '.html':
            for match in HTML_CLASS.finditer(source):
                found.update(match.group(2).split())
        else:
            found.update(QUOTED_TOKEN.findall(source))
    return found


def main():
    source = STYLE.read_text(encoding="utf-8")
    clean = blank_comments(source)
    failures = []

    defined = set(VARIABLE_DEFINITION.findall(clean))
    # Variables with fallbacks are valid without a global definition.
    used = set(re.findall(r"var\(\s*(--[a-z0-9_-]+)\s*\)", clean, re.IGNORECASE))
    scripts = '\n'.join((ROOT / a).read_text(encoding='utf-8') for a in CONFIG['shared_assets'] if a.endswith('.js'))
    defined.update(re.findall(r"setProperty\(\s*['\"](--[a-z0-9_-]+)['\"]", scripts))
    for name in sorted(used - defined):
        failures.append(f"undefined CSS variable {name}")

    depth = 0
    quote = None
    escaped = False
    for char in clean:
        if escaped:
            escaped = False
            continue
        if char == '\\':
            escaped = True
            continue
        if quote:
            if char == quote:
                quote = None
            continue
        if char in ('"', "'"):
            quote = char
        elif char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth < 0:
                raise ValueError('Unexpected CSS closing brace')
    if depth or quote:
        raise ValueError('Unbalanced CSS syntax')
    parsed = rules(clean)
    grouped = defaultdict(list)
    referenced = referenced_classes()
    selector_lines = defaultdict(set)

    for context, selector, line, items in parsed:
        for class_name in CLASS_SELECTOR.findall(selector):
            selector_lines[class_name].add(line)
        properties = [name for name, _ in items]
        duplicates = sorted({name for name in properties if properties.count(name) > 1})
        for name in duplicates:
            failures.append(f"style.css:{line}: {selector} repeats {name} in one rule")
        grouped[(context, selector)].append((line, dict(items)))

    for name, lines in sorted(selector_lines.items()):
        if name not in referenced:
            locations = ",".join(str(line) for line in sorted(lines))
            failures.append(f"style.css:{locations}: .{name} has no source reference")

    for (_, selector), occurrences in grouped.items():
        for earlier_index, (earlier_line, earlier) in enumerate(occurrences[:-1]):
            for later_line, later in occurrences[earlier_index + 1:]:
                for name in sorted(set(earlier) & set(later)):
                    failures.append(
                        f"style.css:{earlier_line}/{later_line}: {selector} redeclares {name} "
                        "in the same cascade context"
                    )

    baseline_file = ROOT / 'scripts/checks/css-baseline.json'
    baseline = json.loads(baseline_file.read_text(encoding='utf-8')) if baseline_file.exists() else {}
    def signature(message):
        return re.sub(r'style\.css:[0-9, /]+:', 'CSS:', message)
    counts = defaultdict(int)
    for message in failures:
        counts[signature(message)] += 1
    if '--initial-baseline' in sys.argv:
        fatal = [m for m in failures if m.startswith('undefined CSS variable')]
        if fatal:
            raise ValueError('Cannot baseline undefined variables: ' + str(fatal))
        baseline_file.write_text(json.dumps(dict(sorted(counts.items())), indent=2) + '\n', encoding='utf-8')
        print(f'Initial CSS baseline: {len(counts)} findings')
        return 0
    failures = [f'{message} (count {count}, allowed {baseline.get(message, 0)})'
                for message, count in counts.items() if count > baseline.get(message, 0)]
    print(f'check_css: {sum(counts.values())} existing baseline findings; new findings are blocked')
    if failures:
        print(f"\ncheck_css: {len(failures)} failure(s)")
        for message in failures:
            print(f"  FAIL {message}")
        return 1

    print(
        f"check_css: OK ({len(defined)} resolved variables; CSS debt ratchet passed)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
