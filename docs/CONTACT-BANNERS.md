# Shared contact banners

## Requested scope

Adapt the owner's https://foundationsasphaltconcrete.ca/ implementation to Paramount: a sticky desktop quick-quote strip above the header and a fixed mobile Call Now / Free Quote bar. Both are included on all 15 configured pages, including 404. Use Paramount's existing navy/blue colors and typography, not Foundations' yellow palette or business claims.

Like the reference, switch at 850px: hide the top strip and show the bottom bar on smaller screens. The bottom bar includes 48px minimum touch targets, keyboard focus inherited from the site, safe-area padding, document-bottom clearance and scroll padding to keep the final footer links reachable. The existing navigation remains unchanged.

The owner explicitly approved using Foundations' contact information: (905) 517-6765 and bryan.larocque@hotmail.com. Both call links use tel:+19055176765. Free Quote links to /contact/#estimate-form. Replace the shared footer's unverified-contact placeholder with these phone/email links, and replace the equivalent contact-page placeholder. No claim about Paramount form delivery is added: the existing local-only form still does not send inquiries.

## Files and boundaries

- All 15 configured HTML pages: identical top strip, identical mobile contact navigation and shared footer phone/email. Contact page additionally shows phone/email in its contact-details panel.
- assets/style.css: only banner styles, responsive visibility/clearance and wrapping for the new email links.
- docs/CONTACT-BANNERS.md: full scope and validation notes.

No JavaScript dependency, form/backend change, metadata/schema change, artwork change, runtime/pipeline change, hostname migration or repository rename. The reference code was inspected for behavior; its forms, tracking and business copy are not copied.

## Validation performed

Full local release passed: six source gates, pinned HTML validation, JavaScript syntax, four JavaScript tests and 37 Python tests. No CSS baseline changes. Verified-dist browser checks: desktop 1440px strip stays at top while scrolling; mobile 390px bar stays fixed with 48px buttons; Free Quote navigates to the existing contact form; footer privacy link remains reachable above the bar. No horizontal overflow at 320, 390, 850, 851 or 1440px. At 850px the top strip is hidden and bottom bar shown; at 851px the reverse applies. Phone link destinations were inspected without placing calls. Contact page and shared footer display the approved phone/email. Safe-area behavior is implemented with CSS env() and was not tested on a physical notched device. No production deployment performed.
