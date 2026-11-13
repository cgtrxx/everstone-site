# Everstone Home Renovations

Static website with 14 content pages, a 404 page, local images/fonts and vanilla JavaScript.

## Build and preview

Use Python 3.12+ and Node 24; prefer existing Codex bundled runtimes locally. HTML validation uses pinned html-validate 8.29.0 via npx or pnpm.

```sh
bash build.sh
# Windows equivalent:
python scripts/release.py
python scripts/preview.py --port 8777
```

Open http://127.0.0.1:8777/. Restart after rebuilding; Ctrl+C stops preview. Preview serves a verified startup snapshot of dist only, binds IPv4 loopback, permits GET/HEAD, validates Host/origin and expires after two hours.

Release runs six source gates, pinned HTML validation, JavaScript syntax/form fixtures, an allowlisted build and Python regression tests. Only configured public files and Git-tracked assets are published. CSS/JS get physical content-hashed filenames; deployment.json records full SHA-256 hashes and revision. Never commit dist or serve the repository root.

Follow docs/CI-CD.md for Cloudflare Pages setup and provenance. The domain is the reserved https://everstone.example placeholder and indexing is disabled. The form validates locally and does not transmit inquiries. Business details, privacy copy and image rights need owner review; photographs are inspiration rather than documented Everstone projects.

Assets and route directories contain the site; scripts contains the pipeline. Asset provenance is in docs/asset-sources.json and font licenses in licenses. No reuse license is granted for original code, brand or artwork; third-party licenses apply separately.
