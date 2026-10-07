# 🌲 Rerun Design System: The Field Notebook

> **One Metaphor:** A field notebook of a hike that retraces a route. (Rerun = run the route again and check you reach the same headline numbers.) Everything on the page is an object from that notebook: torn pages, postcards, polaroids, trail flags, luggage tags, rubber stamps, a cairn.

---

## 1. Authorship Rules ("Made by us, not a template")

1. **Every sheet is torn, never straight.** No rounded-corner cards with soft glows on the landing page.
2. **Tilt and overlap.** Paper objects sit at −3° to +3° and overlap their neighbours (tape, polaroids over frames, envelope over a peak).
3. **Real labels, not decoration:** Folio line on each scene (`No. 03 · FIELD NOTES`), hint lines (`NEXT · THE FIELD CREW`), rubber-stamp status badges, postmarks. They carry product meaning.
4. **Our own illustration set:** Drawn as inline SVG in one consistent style: flat shapes, fine crack/hatch lines, no outlines on landscape, 1.5 px rim light on ridges.
5. **Voice:** Short, calm, concrete. Say what Rerun does, not what it "empowers". No exclamation marks.
6. **Two typefaces on the landing page:**
   - Display: **Libre Caslon Text** (regular weight, uppercase, letter-spaced).
   - Labels/Body/Code: **JetBrains Mono** (uppercase for navigation/labels, clean monospace for body/code).
7. **One accent colour (Rust `#B8572F`):** Everything else is neutral paper/night or landscape colour.
8. **Signature mark:** The Loop-in-Mountain badge on the navbar, footer, postmark, and favicon.

### Banned on Landing
- Teal, cyan, neon green, purple gradients, or arbitrary Tailwind gradients between two brand colours.
- Glow effects (`shadow-teal-*`, colored drop shadows, blurred colored blobs).
- Pill badges with sparkles, "v1.0" chips, emoji, gradient text, shimmer buttons.
- Three-icons-in-a-row strips or three-equal-cards generic SaaS containers.
- Pure black (`#000000`) and pure white (`#FFFFFF`).

---

## 2. 60 / 30 / 10 Colour Distribution

- **60% Neutrals:** Paper (`--cream` `#F1ECE0`, `--paper` `#F4F1E8`, `--kraft-light` `#D9D4C6`, `--kraft` `#CDC8BA`) on light scenes, Night (`--night-deep` `#0F172A`, `--night-top` `#34476F`) on dark scenes.
- **30% Landscape:** Mountains (`--mtn-far`, `--mtn-tan`, `--mtn-clay`, `--mtn-rust`), Sky (`--dusk-*`, `--dawn-*`, `--ember-*`), Pines (`--pine`, `--cone`, `--bark`).
- **10% Accents:** Rust (`--rust` `#B8572F`, `--rust-ink` `#8F3F20`), Ink Blue (`--ink-blue` `#2F4F93`), and semantic role colors (Solver teal, Critic purple, Human amber) only on chips/stamps.

---

## 3. Review Tests

- **Squint Test:** Blur the screen; you should see sky, mountains, paper, and one cream button. If you see "dark box with teal button", it fails.
- **Strip Test:** Disable artwork; layout retains asymmetric rhythm, varied section heights, and tilted paper objects.

---

## 4. Application Desk Pages (`/new`, `/p/:id`, `/p/:id/report`)

The application console translates the outdoor Field Notebook into the investigator's indoor **Field Desk & Archival Ledger**:
1. **Background**: Warm Kraft paper `#EDE7DB` across `html`, `body`, and outer desk layout. No dark blue backgrounds outside terminal cards.
2. **Cards & Containers**: `#FAF7F0` (light parchment) with fine `#CDC5B4` structural borders and `#F4F1E8` card headers.
3. **Typography**: Monospace data tables (`JetBrains Mono`) with editorial serif accents (`Libre Caslon Text`) for report stamps and headings.
4. **Three-Column Operational Desk**:
   - Column 1: Execution Trace Ledger (events stream).
   - Column 2: Sandbox Container Console (terminal output with autoscroll & download).
   - Column 3: Proposed Patch Diff & Critic review.
   - Height constrained to `h-[500px]` with `min-h-0` internal flex scrollbars so panels never overflow into sibling components.
5. **Budget Counters & Verification Runs**:
   - `BudgetBar`: Step budget and patch budget gauges housed in an archival card beneath the 3-column desk.
   - `AttemptsTable`: Verification runs table showing exit codes, error classifications, observed metrics, and tolerance checks.
6. **Persistent Kraft Footer**: Signature footer present on all pages, including `/p/:id` and `/p/:id/report`.
