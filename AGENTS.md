# Repository workflow

- Follow the shared Boyd static-site pipeline. General process refinement is a separate task; avoid an individual deployment architecture.
- Use a scoped branch and PR. Run bash build.sh or python scripts/release.py. Preview only verified dist through scripts/preview.py.
- Show the diff, status, and check results before pushing. Push only with explicit authorization for that push. The owner reviews and merges PRs; agents do not merge.
- Preserve all six gates, pinned validator and regression checks. Never regenerate the CSS baseline automatically or weaken gates to pass.
- Never commit dist, secrets, caches or machine-specific launchers. Configure publication in site.config.json.
- Prefer bundled runtimes without global PATH changes. Preserve loopback-only, read-only, temporary, manifest-verified preview.
