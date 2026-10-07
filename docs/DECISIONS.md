# Architectural & Design Decisions (Stage 10 Frontend)

## 1. Metaphor & Identity
- **Field Notebook / Hike Retracing**: Built around the core metaphor that scientific verification is like retracing a backcountry route to verify if you reach the exact same destination. Every visual object is an artifact from this notebook: torn paper pages, postmarked postcards, polaroid stacks with washi tape, trail flags, and luggage tags.
- **Brand Palette**:
  - Neutrals (60%): `--cream` (#F1ECE0), `--paper` (#F4F1E8), `--kraft-light` (#D9D4C6), `--kraft` (#CDC8BA), `--night-deep` (#0F172A).
  - Landscape Atmosphere (30%): Dusk sky gradients, Dawn gradients, Ember sky, Mountain strata (`--mtn-far`, `--mtn-clay`, `--mtn-tan`, `--mtn-rust`).
  - Brand Accent (10%): Pure **Rust** (`--rust` #B8572F, `--rust-ink` #8F3F20). Default teal/cyan SaaS gradients are strictly banned on the landing page. Teal is reserved solely for the Solver role chip.

## 2. Tear Engine Architecture
- **Sticky Stage**: All scenes (1 through 7) are layered inside a single `position: sticky; top: 0; height: 100svh` stage.
- **Dual-Sheet Mechanics**:
  - Upper sheet: Contains scene content with a ragged bottom edge generated deterministically via seeded Mulberry32 algorithm. Rises and rotates by 0.4° during scrolling.
  - Lower teaser band: Sits in the next scene's paper/sky color with a torn top edge; drops downward faster during tear.
  - Under-scene: Pinned beneath with z-index ordering, rising with scale from behind.
- **Scroll Performance**: Driven by a single passive `window` scroll listener coupled with a `requestAnimationFrame` render loop writing directly to DOM node style transforms. No React state is updated per scroll frame.

## 3. Calibrated Data Integrity
- **No Invented Numbers**:
  - Metric outcomes in the sample run card and Case B4 walkthrough strictly reflect real calibrations documented in `benchmarks/MEASURED.md`.
  - Bad learning rate (0.01) produces observed accuracy **0.8733** (silent divergence).
  - Config fix (0.5) produces observed accuracy **0.9556 ± 0.0018** (matches target 0.9560 ± 0.01 within tolerance).

## 4. Accessibility & Fallbacks
- **Static Fallback**: Responsive breakpoint below 768px, or users with `prefers-reduced-motion: reduce`, or toggling "Skip Scroll Animations" switches immediately to `<StaticScenes />` with static `<TearEdge />` dividers and standard linear flow.
- **Contrast Compliance**:
  - Cream on Dusk Mid: 5.1:1 (WCAG AA pass)
  - Ink on Paper: 12.6:1 (WCAG AAA pass)
  - Ink on Kraft Light: 9.6:1 (WCAG AAA pass)
  - Rust Ink on Paper: 6.4:1 (WCAG AA pass)
