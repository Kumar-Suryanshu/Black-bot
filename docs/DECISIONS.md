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

## 5. Report System & Verification Engine (Stage 11 / Step 2)
- **Deterministic Verifier (Rules V1–V7)**:
  - Solver LLM generated statements cannot be trusted blindly. Plain Python verifier code enforces rules V1–V7 before any statement reaches the user or final report:
    - **V1 (Placeholder Resolution)**: Catches any unresolved `{{...}}` tokens.
    - **V2 (Numerical Fidelity)**: Numbers cited in claims must strictly match observed execution metrics or paper target values within tolerance.
    - **V3 (Accusatory Prevention)**: Accusatory words (e.g., *hallucinated*, *fraud*, *fabricated*) are strictly stripped.
    - **V4 (Status Consistency)**: Cannot assert reproduction succeeded if status is `FAILED` or outside tolerance.
    - **V5 (Evidence Grounding)**: Findings must cite recorded evidence IDs (`E-xxx`) existing in the project run ledger.
    - **V6 (Hypothesis Provenance)**: Causes must correspond to verified hypotheses.
    - **V7 (Confirmed Causality)**: A cause statement cannot claim `confirmed` status without backing confirmed hypotheses.
  - Invalid statements are moved to `statements_removed` with recorded violation rationale, preserving full audit transparency.
- **Unpatched vs. Patched Headline Metric Contract**:
  - `generate_report` automatically packages both Run 1 (unpatched baseline) and final patched Run N metrics, enabling the frontend `ReportChart` and Recharts comparison to render headline comparison bars without separate calculations.
- **Multi-Format Exports**:
  - Direct REST endpoint `/api/projects/{id}/report` provides the full JSON payload.
  - Download endpoint `/api/projects/{id}/report.md` provides clean GitHub-compatible Markdown.
  - Download endpoint `/api/projects/{id}/report.html` provides a self-contained, printable, styled HTML document with embedded CSS.

## 6. API Key Rotation Policy & Quota Compliance (Stage 12 / Step 3)
- **Compliance Analysis**: Google Generative AI / Gemini API terms prohibit creating multiple accounts or rotating credentials to evade free-tier rate limits or usage quotas.
- **Decision & Default Stance**:
  - Multi-key rotation is **disabled by default in standard configuration**. `.env.example` ships with a single `SOLVER_API_KEY` and empty `GEMINI_API_KEYS=`.
  - Production deployments should use a single paid quota tier or documented organization quota.
  - For continuous integration and local regression suites, Rerun utilizes **Cassette Record/Replay** (`LLM_MODE=replay`), derived exclusively from real runs, avoiding unnecessary live calls and eliminating quota exhaustion.
  - The rotation engine in `agent/key_rotator.py` is maintained for legitimate multi-project organizational credential pools with task-boundary awareness and soft request ceilings, but is not configured by default.

## 7. Self-Contained Reproduction Kit Architecture (Stage 10 / R7)
- **Decision**: Rather than forcing subsequent researchers to re-run the full AI agent from scratch, Rerun packages a deterministic reproduction kit (`rerun_kit.zip`) containing:
  - `reproduce.md`: Complete terminal walkthrough with pinned git commit SHA, Python version, dependencies, exact command, random seeds, and expected vs observed tolerances.
  - `patches/*.diff`: Standard unified diffs applicable directly via `git apply`.
  - `results/` & `logs/`: Original attempt execution outputs and raw logs.
  - `report.md` / `report.html`: Verifier-certified reports.
  - `evidence_index.json`: Full structured evidence ledger.
- This decoupling allows third-party auditors to verify reproductions in clean Docker containers without AI dependency or agent installation.



## 8. Critic Scope: Packet Review, Not Independent Fetching (defect remediation)
- **Designed behaviour**: `agent/critic/schemas.py` describes a Critic that can take up to three
  read-only fetches of its own (`CriticPatchReviewOutput.action`), re-deriving facts from
  artifacts it chooses rather than only those the Solver cited.
- **Actual behaviour**: that loop was never implemented. `review_patch` makes a single call and
  judges only `build_review_packet`'s contents: the patch, its diff, the cited evidence slices,
  the paper settings and the config diff. The `fetches_left = 3` local was dead code and has
  been removed.
- **Decision**: keep the single-call review for now and record the gap here rather than leaving
  the schema imply a capability that does not exist. Implementing independent Critic tool use is
  a feature, not a defect fix, and was explicitly left out of the remediation branch.
- **Consequence to be aware of**: the Critic cannot discover evidence the Solver chose not to
  cite. Its independence is therefore limited to re-judging the cited material against policy
  and the paper settings. The deterministic quote check in `review_patch` and the code-enforced
  verdict override in `agent/critic/review.py` remain the real guarantees.
- **Related hardening applied**: the review call now returns a judgment-only schema
  (`CriticJudgement`). `id`, `patch_id`, `round` and `model` are set by code, because `model`
  carrying the value `"unavailable"` is the Arbiter's signal that no independent review
  happened (`agent/arbiter.py`), and a reviewer must not be able to assert that about itself.

## 9. Simulation Provenance (defect remediation)
- **Decision**: `state.simulated` is set during `INGEST` whenever the resolved sandbox is not
  `DockerSandbox`. It was previously declared and read, but never written, so the report's
  "SIMULATED RUN" banner and the dashboard indicator were unreachable and a fake-sandbox run
  produced a report indistinguishable from a real containerised one.
- **Consequence**: any run under `SANDBOX_TYPE=fake` now carries the banner in `report.md`,
  `report.html` and the UI. `benchmarks/run_bench.py` stamps the LLM mode and sandbox type into
  `benchmarks/MEASURED.md` for the same reason: its Rerun rows are produced with scripted LLM
  replies by default and measure the orchestrator, not a model.
