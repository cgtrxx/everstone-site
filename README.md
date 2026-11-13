# Everstone Home Renovations

A responsive, 14-page static renovation-business website using HTML, CSS and vanilla JavaScript. Images and fonts are served locally. No package installation or build step is required.

## Preview and validate

Use Python 3.12 or newer, including Codex's existing bundled Python when available. The runtime is not included in this repository.

```sh
python -I -B tools/validate.py
python -I -B tools/preview.py --port 8777
```

Open http://127.0.0.1:8777/ and leave the terminal running. Ctrl+C stops the preview; it also expires automatically after two hours. Choose another port if needed. Use the numeric loopback address: the preview deliberately rejects alternate Host headers.

The preview serves an explicit in-memory file allowlist on IPv4 loopback, accepts only GET/HEAD, blocks cross-origin browser access and external subresources, and reads the site only at startup. Restart after editing. It is a development tool, not a production server or an OS sandbox. Other local processes can access the published site files.

## Structure

- HTML at the root and in route directories.
- `assets/style.css`, `assets/main.js`, logo, favicon and architectural watermark.
- `assets/local/`: eight inspiration photographs and nine font files.
- `licenses/`: DM Sans and Manrope SIL Open Font License texts.
- `docs/asset-sources.json`: original asset URLs, download URLs, sizes and SHA-256 hashes.
- `docs/RELEASE-NOTES.md`: current implementation and remaining launch work.
- `tools/`: dependency-free preview and validation tools.

Serve this directory as the origin root. Navigation and asset URLs start with `/`; deploying beneath a URL subdirectory requires path changes. The existing source package targeted Cloudflare Pages, but no hosting account, domain, deployment or GitHub workflow is configured here. The local preview's response headers must be configured separately on the eventual host.

## Current behavior

The estimate form validates entries locally and displays a review message. **It does not transmit inquiries.** Project photographs are design inspiration rather than verified Everstone projects. Contact details and some business/legal information remain placeholders.

The repository preserves the approved desktop layout and mobile refinements, logo treatment, typography, related-services watermark bands, and widened service-page heroes and calls to action.

## Before public launch

Connect and test the inquiry backend; verify business details and claims; review privacy copy and image rights; configure the production domain, canonical/social URLs and hosting security headers; then verify the deployed pages. See release notes and third-party notices.

No license is granted here for the site's original brand, artwork or code. Third-party font licenses apply to the font files separately.
