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

The Boyd pipeline now supplies CI workflows, verified dist, physical asset hashing, security headers and prototype metadata. The reserved everstone.example domain must be replaced before launch. Hosting and live verification remain external setup. See CI-CD.md.

No analytics, tracking, service worker, remote font/image fetch, or package runtime is required by the site. The JSON-LD schema.org identifiers are metadata, not external browser resources.

## Repository preparation

The approved stylesheet is preserved. Integration adds metadata, a shared 404 and HTML syntax corrections. Temporary files, caches and machine-specific launchers are excluded. Python uses the standard library; release checks also require Node and the pinned validator.

