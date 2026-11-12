# ShakaHive brand assets

This directory is the source of truth for ShakaHive's official brand assets.
The tagline is **Many hands, one hive.**

## Official colour palette

| Colour | Hex |
|---|---|
| Deep Teal | `#046975` |
| Hive Teal | `#1A8E85` |
| Honey Gold | `#FBAA10` |
| Comb Yellow | `#F7DC8A` |
| Night Hive | `#05343B` |
| Wax Cream | `#FFF8E6` |

The existing `design-tokens.css` provides these colours and separate interface
tokens. Test actual foreground and background combinations: all interface
elements must meet applicable WCAG 2.2 AA contrast requirements. Do not rely on
colour alone to communicate meaning.

## Typography

- **Headings:** Fredoka SemiBold.
- **Body and interfaces:** Nunito Regular and Bold.

Use a permitted font distribution method, record the font source and licensing,
and provide fallback font stacks.

## Directory contents

- `source/`: founder-supplied original `logo-horizontal.png`,
  `logo-on-dark.png`, `logo-stacked.png`, and `favicon-64.png`.
- `reference/`: founder-supplied `colour-palette.png` reference sheet.
- `exports/`: optimized copies for application use, derived from approved
  originals.

The original logo variants and favicon are present in `source/`; the palette
reference is present in `reference/`.

## Logo and artwork usage

Use only the approved, supplied artwork. Use `source/logo-on-dark.png` on Night
Hive (`#05343B`) surfaces, and select other logo variants only where their
background and contrast are appropriate. The horizontal and stacked logos are
intended for layouts with suitable space; use the supplied favicon for its
intended browser context. Do not substitute social assets for product UI logos.

Keep original files unchanged. Never redraw, distort, stretch, skew, crop,
recolour, or approximate the logo or wordmark; preserve proportions and any
transparency. Do not overwrite originals with derivatives.

The web application uses an unchanged copy of `source/logo-on-dark.png`
(3333 × 1060) at `apps/web/public/brand/logo-on-dark.png` for its Night Hive
headers, and `source/favicon-64.png` (64 × 64) at `apps/web/app/icon.png`. The
teal-background `logo-horizontal.png` remains unchanged and is not used on
these dark headers. No optimized derivatives are currently used.

See `../../company/brand/brand-guidelines.md` for broader identity guidance and
`../../docs/implementation/brand-asset-manifest.md` for the supplied pack
inventory. The inventory does not imply that its files are present here.
