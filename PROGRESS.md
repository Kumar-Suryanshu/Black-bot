# Rerun Implementation Progress

> **Team Plan:** See [`TEAM_PLAN.md`](file:///c:/Users/LENOVO/OneDrive/Desktop/Black-bot/TEAM_PLAN.md) for phase breakdown, track assignments, and collaboration guide.
> **Build Spec:** [`rerun_antigravity_build_prompt.md`](file:///c:/Users/LENOVO/OneDrive/Desktop/Black-bot/rerun_antigravity_build_prompt.md) · **Guide:** [`rerun_project_guide.md`](file:///c:/Users/LENOVO/OneDrive/Desktop/Black-bot/rerun_project_guide.md)

---

## Stage Gates and Deliverables

- [x] **Stage 0**: Bootstrap & machine readiness
  - *Owner:* —
  - *Gate Run Results:* PASS (setup ok, images built `rerun-base:py311`, hardened-smoke printed PASS)
- [x] **Stage 1**: Contracts
  - *Owner:* —
  - *Gate Run Results:* PASS (`pytest tests/unit/test_contracts.py` passed, SQLite roundtrip verified)
- [x] **Stage 2**: Deterministic core
  - *Owner:* —
  - *Gate Run Results:* PASS (All unit tests for compare, status, errors, results, config_audit, policy, evidence passed)
- [x] **Stage 3**: Sandbox — *Owner: Track B*
  - *Gate Run Results:* PASS (wheelhouse built, security selftest verified network/root/PID limits, unit tests passed)
- [x] **Stage 4**: Benchmark — *Owner: Track C*
  - *Gate Run Results:* PASS (`build-benchmarks` runs successfully; template, calibrate, seed-faults, papers, registry, and gold files generated and verified)
- [x] **Stage 5**: Baselines & harness — *Owner: Member 3 (Track C)*
  - *Gate Run Results:* PASS (`B-0` baseline script, `B-2` baseline stub, and `run_bench.py` harness built and wired to `dev.py bench`. `B-0` sweep executing successfully against 5 seeded cases.)
- [x] **Stage 6**: LLM layer — *Owner: Member 1 (Track A)*
  - *Gate Run Results:* PASS (`pytest tests/agent/test_llm.py` passed; `agent/llm.py` with `call()`, providers `gemini`, `replay`; cassette record/replay verified; secret scrubbing verified; fallback on primary failure verified; schema validation with 1 re-prompt verified)
- [x] **Stage 7**: Solver loop — *Owner: Member 1 (Track A)*
  - *Gate Run Results:* PASS (`pytest tests/agent/test_loop.py` passed; `tools/policy.py` completed with P1–P10, hard limits MAX_FILES=5, MAX_CHANGED_LINES=200, guarded sensitive keys; `agent/loop.py` orchestrator verified end-to-end on B1 control, B2 dependency with approval, and budget exhaustion; safety-net nudge verified)
- [x] **Stage 8**: Critic + Arbiter — *Owner: Member 1 (Track A)*
  - *Gate Run Results:* PASS (`pytest tests/unit/test_arbiter.py tests/agent/test_critic.py` passed; `python scripts/dev.py adversarial` passed; all adversarial fixtures X1–X9 blocked by Policy or Critic; gold patch false-block count = 0 verified)
- [x] **Stage 9**: Backend — *Owner: TBD (Track B+D)*
  - *Gate Run Results:* PASS (`pytest tests/e2e/test_b4_api.py` passed; B4 driven end-to-end via HTTP: create → start → claims-confirm → approve ×2 → DONE; `status == "REPRODUCED"` verified; SSE stream, worker thread, SQLite WAL, Last-Event-ID resume, and all 13 §14.1 endpoints implemented)
- [x] **Stage 10**: Frontend — *Owner: Track B+D*
  - *Gate Run Results:* PASS (`npm run build` passed in 600ms with 0 errors; all routes `/`, `/new`, `/p/:id`, `/p/:id/report`, `/dev/tear`, `*` implemented per `Rerun_Frontend_Spec (1).md`; "Field Desk & Torn Postcard" visual styling S1–S7 with SVG torn paper dividers, Mulberry32 deterministic ragged edge algorithm, Postcard claim confirmation, Live Console with SSE stream, terminal logs, diff view, Critic review card, human approval modal with 9 checks and banners, and certified report with unpatched vs patched chart).
  - *Polishing & Audit Updates:*
    - Fixed 3-column desk overflow constraints (`TracePanel`, `Terminal`, `DiffView`) with `min-h-0` and internal scroll containers, resolving overlap with `BudgetBar` ("Step Budget / Patch Budget") and `AttemptsTable` ("Execution Runs & Metric Verification").
    - Unified the operational console (`/p/:id`), report page (`/p/:id/report`), and project launcher (`/new`) into an archival Kraft paper & ink palette (`#EDE7DB`, `#FAF7F0`, `#CDC5B4`).
    - Fixed root body background in `index.html` and `index.css` to prevent dark background peeking during scroll.
- [x] **Stage 11**: Report — *Owner: Track A (generation) + Track B+D (rendering)*
  - *Gate Run Results:* PASS (`pytest tests/unit/test_report_verifier.py` passed; `tools/report.py` implemented with placeholder resolution, deterministic verifier V1–V7, unpatched vs final runs comparison for frontend `ReportChart`, Markdown & HTML exports, and `/api/projects/{id}/report[.md|.html]` endpoints; certified reproduction report interactive rendering at `/p/:id/report` with baseline comparison charts, patch provenance with Critic checklist, config audits, and limitation disclosures).
- [ ] **Stage 12**: Evaluation sweep — *Owner: TBD (Track C)*
- [ ] **Stage 13**: Hardening & fallbacks — *Owner: TBD (Track B+D)*
- [ ] **Stage 14**: Docs & demo kit — *Owner: All*

## Checkpoint Reports
*(Updated after Stages 3, 7, 10, 11, and 13)*

### After Stage 11 (Report Generation & Verification Engine Complete)
- **What works:**
  - **Deterministic Verification Engine (`tools/report.py`)**: Enforces verifier rules V1–V7 on all solver-generated statements:
    - Resolves template placeholders `{{claim...}}`, `{{result...}}`, `{{status}}`.
    - Bounds numerical citations against measured results and target claims.
    - Strips accusatory / hostile language (*hallucinated*, *fraud*, *fabricated*).
    - Checks status consistency against final reproduction verdict.
    - Validates evidence references against recorded project evidence ledger.
    - Isolates non-compliant statements into `statements_removed` with explicit violation reasons.
  - **Dual-Run Comparison & Reporting Contract**: Computes unpatched (Run 1) vs. final patched (Run N) metrics directly in `runs_summary` and `attempts` payload, powering the frontend Recharts `ReportChart` tolerance band display.
  - **Multi-Format Export Routes**:
    - JSON: `/api/projects/{id}/report`
    - Markdown: `/api/projects/{id}/report.md`
    - Self-contained HTML: `/api/projects/{id}/report.html`
  - **Interactive Frontend Report Viewer (`/p/:id/report`)**: Archival Field Desk styling, dynamic `Stamp` verdict badge, metric comparison chart, provenance tables, Critic checklist review flags, and one-click Markdown clipboard copy / PDF print export.
  - **Test Suite**: 65 passed, 3 skipped (Docker), 0 failed across unit, agent, e2e API, and report verifier test suites.
- **What's next:** Stage 12 Evaluation sweep (sweep across benchmark cases B1–B5) and Stage 14 documentation release kit.

### After Stage 10 (Frontend & UI Polish Complete)
- **What works:**
  - **Landing Page & Torn Paper Engine**: 7-scene narrative journey with Mulberry32 procedural tear seams, sticky viewport stage, rAF animation loop, responsive static fallback, and `/dev/tear` interactive tuner.
  - **Operational Console (`/p/:id`)**: Real-time SSE event stream, live terminal container streaming with autoscroll and download, unified diff inspector, step/patch budget gauges, execution attempts table, and 9-point Critic review approval modal.
  - **Postcard Claim Confirmation (`/new`)**: Interactive benchmark selector with paper claim cards, preflight checks, editable target metrics, and run command preview.
  - **Certified Reproduction Report (`/p/:id/report`)**: Stamp verdict badge, baseline vs observed delta bar chart, applied patch audit, and honest limits disclosure.
  - **Archival Field Desk Design System**: Consistent warm Kraft paper (`#EDE7DB` / `#FAF7F0`), ink typography (`Libre Caslon Text` & `JetBrains Mono`), rust accents (`#B8572F`), and responsive ergonomics across desktop and laptop screens.
  - **Test Suite**: 59 passed in 11s across unit, agent, arbiter, loop, and API suites. Frontend TypeScript compilation and production bundle build clean.
- **What's next:** Stage 11 Report generation and Stage 12 Evaluation sweep.

### After Stage 7 & Stage 8 (Checkpoint IC-2 Ready)
- **What works:**
  - **LLM Layer**: Unified `call()` interface supporting Gemini models, and Cassette Replay. Automated fallback and secret scrubbing active.
  - **Deterministic Policy**: Full P1–P10 enforcement including hard limits (≤ 5 files, ≤ 200 lines), soft thresholds with human confirmation flags, and guarded sensitive keys (seeds, epochs, etc. locked to paper-stated values only).
  - **Solver Loop Orchestrator**: 20-phase state machine managing end-to-end execution, FakeSandbox and Docker sandboxes, hypothesis tracking, safety-net nudges for silent divergence, and budget guards (40 steps, 3 patches).
  - **Critic & Arbiter**: Independent review packet construction, quote verification against raw evidence artifacts, code-enforced verdict overrides on critical checks, and authority hierarchy (`Human > Policy > Critic > Solver`).
  - **Adversarial Hardening**: Suite of 9 attack fixtures (X1–X9) blocked by Policy/Critic, with zero false blocks on valid gold patches.
  - **Audit & Invariant Hardening**:
    - `tools/patch.py`: File backups pre-cached on apply and reliably restored on disk during `revert_patch()` or smoke test failure.
    - `tools/policy.py`: Rule P6 requires stored traceback error provenance for non-paper parameters, flagging `no_provenance` violation otherwise.
    - `agent/critic/review.py`: Full set of 9 fixed checklist keys (§9.3) enforced and returned as `False` in unavailable fallback.
    - `agent/llm.py`: Cassettes recorded only after JSON schema validation succeeds.
    - `agent/loop.py`: Hypothesis evidence IDs strictly validated against ledger in `handle_diagnose()`; investigation tools executed and evidence recorded; solver `write_report` invoked in `handle_report()`.
    - `tools/status.py`: Fixed `INCONCLUSIVE` bug to properly enforce mismatch checks against `config_diff` instead of failing on empty list.
    - `agent/loop.py`: Enforced §7.3 constraint requiring a confirmed hypothesis with valid evidence before `PATCH_PROPOSE`.
    - `agent/loop.py`: Wired missing investigation tools (`read_logs`, `inspect_error`, `run_command`) into `handle_diagnose` with proper sandbox isolation.
    - `agent/loop.py`: Added patch regeneration budgets to `handle_patch_propose` and `handle_policy_check` to strictly allow max 2 retries before escalating to `failed_fixes` per §7.1.
- **What is incomplete:** Frontend React dashboard (Stage 10), Report generator/verifier (Stage 11).
- **What's next:** Phase 4 UI: Stage 10 (Frontend Dashboard) then Stage 11 (Report).

### After Stage 9 (Checkpoint IC-3 Ready)
- **What works:**
  - **FastAPI Backend**: Full REST API with all 13 §14.1 endpoints. CORS enabled for Vite dev server.
  - **SQLite Persistence**: `projects` and `events` tables in WAL mode; `state_json` stores full `ProjectState` round-tripped through Pydantic.
  - **Worker Thread**: Synchronous orchestrator per project in a daemon thread; pauses when `state.pending` is set; resumed by the human-action API endpoints.
  - **SSE Streaming**: Thread-safe event bus via `loop.call_soon_threadsafe`; events persisted to DB before push; `Last-Event-ID` header replay for reconnect.
  - **E2E Gate**: `test_b4_api.py` drives B4 (create → start → claims-confirm → approve ×2 → DONE) via HTTP using Cassette Replay (Replay fully implemented); asserts `status == "REPRODUCED"` and report fetch.
  - **Test Suite**: 56 passed, 3 skipped (Docker), 0 failures across all 59 test items (now running strictly on replay/mocks).
- **What is incomplete:** Frontend React dashboard (Stage 10), report generator (Stage 11), `/report.md` and `/report.html` download routes (deferred to Stage 11).
- **What's next:** Stage 10 (Frontend: React 18 + Vite + TS + Tailwind Dashboard).

## Blockers (STOP-AND-ASK)
*(None currently)*

## Decision Log
*(Append new decisions below. Full log in `docs/DECISIONS.md`)*

---

*Last updated: 2026-10-07*
