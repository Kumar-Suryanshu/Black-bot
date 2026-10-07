# Frontend Sources & Attributions

## 1. Bundled Typography
All fonts are installed locally via `@fontsource` npm packages. No external CDN or remote web requests:
- `@fontsource/libre-caslon-text`: Display headings, serif accents, and editorial letterforms.
- `@fontsource/jetbrains-mono`: Monospace labels, execution traces, code diffs, and hints.
- `Inter`: UI labels across application pages (`/new`, `/p/:id`, `/p/:id/report`).

## 2. Original Inline Artwork
All illustrations are crafted as bespoke inline SVG components without external stock icon bloat:
- `MountainRidgesSvg`: Multi-layer geological strata with rim lighting and structural hatch lines.
- `EagleSvg`: Soaring backcountry eagle in dusk sky.
- `PineBranchSvg`: Evergreen pine needles with pine cone clusters.
- `SquirrelSvg`: Perched woodland squirrel holding an acorn.
- `PenSketchPeakSvg`: Hand-drawn cross-hatched summit illustration.
- `BadgeLogo`: Signature mountain-in-loop seal for Rerun & InnoHacks 4.0.

## 3. Seeded Noise & Procedural Shaders
- `Mulberry32`: High-speed, 32-bit seeded pseudo-random number generator used in `tear.ts` to ensure mathematically identical ragged edge curves across all reloads.
- Static SVG Filter `#paper-fibre`: `feTurbulence` (baseFrequency 0.9, numOctaves 2) displaced onto stroke outlines for authentic paper fibre jaggedness.
- Static SVG Filter `#paper-grain`: Microscopic paper grain overlay with `mix-blend-mode: multiply` at 9% opacity.

## 4. Verification Proofs & Laptop Ergonomics
- `docs/screens/proof-chrome-cover.png`: 1201x899 viewport verification proving 2-line hero headline, zero right-edge clipping, and navbar `[ ↺ TEAR ]` and `[ OPEN THE APP → ]` CTA.
- `docs/screens/proof-chrome-problem.png`: Problem scene verification proving dark ink (`#1F2A44`) navbar contrast over Kraft paper.
- `docs/screens/proof-chrome-new.png`: `/new` page reskinned into Field Notebook Deep Night & Rust palette.
