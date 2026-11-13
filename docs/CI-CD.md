# Shared static-site CI/CD process

Based on cgtrxx/boyd-wp commit 9ea51a436b6ad85b9bb31a14aff28c662394dc88. Release entry point, pinned validator policy, CI workflows and deployment verifier are inherited. General process refinement belongs in a separate task.

## Local release

1. Work on a scoped branch.
2. Run bash build.sh or python scripts/release.py.
3. Preview dist with python scripts/preview.py and inspect affected pages.
4. Review diff, status and checks; obtain explicit push authorization and open a PR. Owner merges.

Python 3.12 and Node 24 are CI runtimes. Python uses the standard library. HTML validation is pinned to 8.29.0; a verified existing cache of that exact version may be used locally.

Six source gates cover doctype/BOM, CSS debt, bare source assets, JSON-LD, SEO/sharing/shared markup and FAQ parity. Release also checks JavaScript syntax, local form behavior and artifact regression fixtures. Build normalizes text LF, physically hashes CSS/JS, emits security/cache/preload headers and records full SHA-256 hashes and revision. Only explicit public files and tracked assets enter disposable dist. Unsafe paths, symlinks and junctions fail closed. Preview verifies the complete artifact before serving it.

## Hosting and CI

Use Cloudflare Pages Git integration: repository root, build command bash build.sh, output directory dist, PYTHON_VERSION=3.12 and NODE_VERSION=24. Workers Wrangler defaults are a different deployment flow. Never deploy the repository root.

CI / site-gates runs the same release command for PRs and main pushes and retains artifacts seven days. Pages owns deployment and branch previews and independently rebuilds the checked-out commit. GitHub Actions has no deploy job and needs no Cloudflare deployment secret.

Post-deploy verification polls for the triggering revision and checks deployed HTML/assets against full hashes, immutable caching and stylesheet Link preload headers. Failure is reported without automatic rollback. PRODUCTION_BASE_URL overrides the configured domain. Revision comes from BUILD_REVISION, CF_PAGES_COMMIT_SHA or local Git HEAD.

External setup remains unverified: connect Pages, configure actual hostname, set URL variable if needed, require PRs and site-gates on main, and verify previews/live deployment.

## Everstone adapters

- Nested directory-index routes, native details/summary FAQs and existing local-only form. No Boyd identity or form credentials copied.
- Approved stylesheet preserved. Reviewed initial baseline: 86 existing override occurrences across 64 signatures. Never automatically regenerate it.
- Sharing image reuses the 1320x1191 logo with configured dimensions/hash; dedicated social artwork is future work.
- Domain remains reserved https://everstone.example with prototype noindex and disallowing robots policy. Replace hostname and review indexing before launch.
- Same-origin security policy blocks external subresources and connections. A real form backend requires policy review and delivery tests.
