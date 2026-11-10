# Frontend, Brand System and Accessibility Implementation

## Experience objective

Build a calm, evidence-first workspace for grant administrators and reviewers. Users must understand what was checked, what could not be checked, why a finding appeared and what action is available. Avoid generic AI chat UI or dashboards that hide evidence behind scores.

## Current brand source of truth

Use the supplied ShakaHive brand asset pack as the current visual source of truth. Use exact supplied logo exports, icon, app icon, favicon and social variants. Do not redraw, stretch, recolour or approximate the mark. Preserve transparent backgrounds and use the correct light/dark lockup.

### Supplied palette

| Token | Hex | Use |
|---|---|---|
| Deep Teal | #046975 | Primary brand / navigation |
| Hive Teal | #1A8E85 | Interactive/supporting brand |
| Honey Gold | #FBAA10 | Accent/highlights |
| Comb Yellow | #F7DC8A | Soft accent surface |
| Night Hive | #05343B | Dark surfaces |
| Wax Cream | #FFF8E6 | Warm light background |

### Typography
- Fredoka SemiBold: headings.
- Nunito Regular/Bold: body and interface.

Use licensed font files or a permitted font delivery method. Define fallbacks and avoid layout shift.

### Asset rules
- Preserve supplied originals unchanged under assets/brand/.
- Maintain a manifest with filename, use, dimensions, transparency, version and approval status.
- Use horizontal lockup in suitable headers, symbol-only in compact contexts and supplied favicon sizes for browsers.
- Do not use social banners/avatars as product logos.
- Do not substitute the older palette in earlier draft notes.
- The supplied pack establishes the selected visual direction, not trademark clearance.

## Design tokens

Create a single token source consumed by web components: brand and semantic colours separately; text/background/border/focus/disabled states; spacing/radius/elevation/type/breakpoints; light/dark mappings; accessible data visualization colours. Test actual contrast pairs. Adjust UI semantic tokens where necessary without altering logo artwork.

## Core screens

Sign-in/account recovery; organization workspace; grant-call list/detail; RFP upload/version history/requirement extraction; requirement verification; application upload/association/processing queue; application detail/screening status; evidence workspace; finding detail; review queue/decision history; reports/export; administration/users/roles/audit.

## Evidence workspace

Show finding type and origin (rule or AI signal); state; exact supporting passage and document/page; method and rule/model version; score meaning; source coverage and missing/unavailable sources; reviewer action and rationale history. Keep the source document directly inspectable. Colour must not be the only status cue.

## Interaction and accessibility

Implement loading, empty, success, partial, error, permission-denied and offline states. Show progress for asynchronous processing. Provide safe retry and explain manual intervention. Confirm destructive actions and preview bulk actions.

Target WCAG 2.2 AA: semantic headings/landmarks/labels; keyboard navigation and visible focus; screen-reader announcements; sufficient contrast and non-colour cues; accessible tables/dialogs/menus/errors; reduced motion; zoom/reflow; responsive layouts; accessible fallback for document preview. Run automated checks and manual keyboard/screen-reader review.

## Frontend engineering acceptance

Shared tokens/components; presentation/data/domain separation; client and server validation; consistent API errors; no client-side authorization trust; critical journey tests; server as source of truth; privacy-aware error monitoring. All product surfaces use supplied brand assets and typography, critical journeys are keyboard-operable, evidence is inspectable, and every async operation has progress and terminal states.
