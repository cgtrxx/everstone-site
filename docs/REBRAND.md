# Paramount Renovations rebrand

## Scope

All 15 HTML pages: replace current business identity with Paramount Renovations, standalone Everstone with Paramount, and the uppercase header/footer wordmark with PARAMOUNT. Keep HOME RENOVATIONS as the existing descriptor. Includes visible text, accessible names, copyright, titles/descriptions, existing social tags and structured data; no new metadata fields or business claims are added.

Rename assets/everstone-logo.png to assets/paramount-logo.png and assets/everstone-watermark.svg to assets/paramount-watermark.svg, updating HTML/CSS references. Their image bytes and the favicon are unchanged. The header references the full PNG but crops it to the architectural symbol; this does not create a new Paramount logo. Future brand-board artwork remains separate.

Replace the old full-logo social image with assets/social/paramount.0559d5e570a6.png: a deterministic 1200x630 navy/blue text-only Paramount Renovations card using an existing local font. Update all page image URLs, dimensions, alternative text and sharing configuration; remove the superseded social file.

Replace the reserved everstone.example placeholder with paramount.example in page metadata, JSON-LD, sitemap, config, documentation and the existing negative fixture. This changes no real domain, DNS, Cloudflare project or hostname. Prototype noindex and crawling restrictions remain.

Update current brand references in README, release notes, CI/CD documentation, third-party notices and the artifact-test description. The social-width negative fixture follows the new width. No tooling rewrites or gate weakening. The one CSS change is the watermark filename reference; all layout/typography declarations stay the same.

## Deliberate exceptions and boundaries

The original Everstone name remains only in this provenance documentation and third-party artwork notices. Historical Git commits are not rewritten. Original logo artwork may still contain that name in its pixels, intentionally pending separate artwork review.

Retained artwork SHA-256:

- paramount-logo.png: 52fbe4aab42b0e6c2d3da8d7250494dff741daf4017edb77159e8ada83ec11f4
- paramount-watermark.svg: 65b2e1f2db49095830d1ea9b6fa10eeb29d365e396daba1904e50c168e18ff34
- favicon.svg: 36cc995f1ee6d4f077b54c189c0ad288c4a3f87152893bbfff2ab455f2839708

No repository rename, hosting migration, runtime upgrade, contact-detail invention, form backend, indexing change, route change, redesign or new business promises. Branch/PR is based on the existing pipeline merge, not a repeat of that work. Generated dist stays uncommitted. The later repository rename and possible new Cloudflare Pages project are separate steps.

## Verification

Run the unchanged full release process; audit residual old-brand text and filenames; verify preserved artwork hashes and CSS reference-only diff; inspect the new social image and desktop/mobile verified-dist layouts. Record actual results in the PR. Approval of this rebrand does not approve new logo artwork or deployment migration.

Completed locally: all six source gates, pinned HTML validation, JavaScript syntax, four JavaScript tests and 37 Python tests passed. The actual dist HTTP verifier passed for revision, page/shared/social bytes, caching and preload headers. Old-brand text audit found only the documented provenance exceptions. The three artwork hashes match the originals; Git detects the logo and watermark as exact renames. The CSS diff changes only the watermark URL. Homepage desktop (1440px) and mobile (390px), including mobile footer, were inspected: the new wordmark fits without layout changes, no horizontal overflow, and no failed loaded images. This is focused visual inspection, not exhaustive browser testing of every page; source/shared-markup gates cover all 15 pages. The social image was visually inspected. No live deployment verification or hosting changes performed.
