from common import page_name
import sys
from common import pages, finish

files = pages()
errors = [f'{page_name(p)}: must begin with <!doctype html>, without BOM or leading whitespace'
          for p in files if not p.read_bytes().lower().startswith(b'<!doctype html>')]
sys.exit(finish('check_doctype', errors, f'{len(files)} pages'))
