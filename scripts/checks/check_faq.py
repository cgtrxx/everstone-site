from common import page_name
import sys
from common import CONFIG, pages, text, document, jsonld, norm, finish


def visible(source):
    result = []
    for article in document(source).find('details'):
        summaries, answers = article.find('summary'), article.find('p')
        if len(summaries) != 1 or not answers:
            raise ValueError('FAQ item must have one summary and a nonempty answer')
        result.append((norm(summaries[0].content()), norm(' '.join(p.content() for p in answers))))
    return result


def main():
    errors, checked = [], 0
    expected = set(CONFIG['faq_pages'])
    files = pages()
    if not expected or not expected <= {page_name(p) for p in files}:
        errors.append('faq_pages must identify at least one existing page')
    for path in files:
        try:
            source = text(path)
            vis = visible(source)
            nodes = [n for n in jsonld(source) if n.get('@type') == 'FAQPage']
            if page_name(path) not in expected and (vis or nodes):
                errors.append(f'{page_name(path)}: FAQ found outside configured inventory')
            if page_name(path) not in expected:
                continue
            checked += 1
            if not vis or len(nodes) != 1:
                errors.append(f'{page_name(path)}: expected nonempty visible FAQ and one FAQPage')
                continue
            ld = [(norm(q['name']), norm(q['acceptedAnswer']['text'])) for q in nodes[0]['mainEntity']]
            if ld != vis:
                errors.append(f'{page_name(path)}: visible FAQ and schema must match in order after whitespace normalization')
        except (ValueError, KeyError, TypeError) as error:
            errors.append(f'{page_name(path)}: {error}')
    return finish('check_faq', errors, f'{checked} FAQ pages')


if __name__ == '__main__':
    sys.exit(main())
