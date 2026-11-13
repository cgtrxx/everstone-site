# Implementation and launch notes

## Included

- All 14 reviewed pages and the final approved stylesheet, copied without rewriting the UI.
- Local versions of the existing photographs and fonts, plus font license texts and asset provenance.
- Corrected header-logo crop, aligned navigation chevron, centered header subtitle with the approved desktop offset.
- Shared slate-navy service bands with a decorative architectural SVG watermark.
- 1340px desktop service-page hero, related-service and closing CTA content widths; matching homepage bands.
- Mobile-only trust-banner and section-spacing refinements. The final desktop process-to-local gap reduction is included separately.
- Scoped footer-brand spacing refinements.

## Behavior requiring launch work

The contact form is a local review flow, without a sending endpoint. Phone/email and legal business details need owner verification. Draft privacy copy must match the actual production services. Inspiration photographs are not claims of completed Everstone work.

The site currently has no production hostname, canonical URL configuration, deployment workflow, production sitemap or robots policy. Those depend on the chosen hosting and domain. Preview response headers are implemented by the local preview tool, not by the HTML; configure equivalent rules on the eventual host.

No analytics, tracking, service worker, remote font/image fetch, or package runtime is required by the site. The JSON-LD schema.org identifiers are metadata, not external browser resources.

## Repository preparation

The website files match the reviewed localized preview byte for byte at packaging time. Temporary editing scripts, screenshot artifacts, local drive paths, cached runtimes, and machine-specific launchers are excluded. The generic tools in this repository require only Python's standard library.
