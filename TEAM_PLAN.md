# 🏗️ RERUN — Team Build Plan & Collaboration Guide

> **Event:** InnoHacks 4.0, Agentic AI & GenAI track (10–11 Oct 2026)
> **Team Size:** 3 members
> **Primary Tool:** Google Antigravity (each member runs their own session)
> **Source of Truth:** [`rerun_antigravity_build_prompt.md`](file:///c:/Users/shivt/Documents/Programs/Rerun/Black-bot/rerun_antigravity_build_prompt.md) (technical spec) and [`rerun_project_guide.md`](file:///c:/Users/shivt/Documents/Programs/Rerun/Black-bot/rerun_project_guide.md) (human guide)

---

## 📋 Table of Contents

1. [Current Status](#-current-status)
2. [Team Roles & Track Assignments](#-team-roles--track-assignments)
3. [Phase-by-Phase Breakdown](#-phase-by-phase-breakdown)
4. [Dependency Graph](#-dependency-graph)
5. [Antigravity Session Guide](#-antigravity-session-guide)
6. [Integration Checkpoints](#-integration-checkpoints)
7. [File Ownership Rules](#-file-ownership-rules)
8. [Cut List (If Time Runs Out)](#-cut-list-if-time-runs-out)
9. [Communication Protocol](#-communication-protocol)
10. [Quick Reference: Key Commands](#-quick-reference-key-commands)

---

## 🔵 Current Status

| Stage | Status | Owner | Notes |
|-------|--------|-------|-------|
| **Stage 0** — Bootstrap | ✅ Done | — | Setup ok, images built, hardened-smoke PASS |
| **Stage 1** — Contracts | ✅ Done | — | SQLite roundtrip verified, all models frozen |
| **Stage 2** — Deterministic Core | ✅ Done | — | All unit tests green (compare, status, errors, results, config_audit, policy, evidence) |
| **Stage 3** — Sandbox | ✅ Done | **Member 2** | `dev.py wheelhouse` and `dev.py selftest` pass |
| **Stage 4** — Benchmark | ✅ Done | **Member 3** | Templates, cases, papers, and calibration sweep pass |
| **Stage 5** — Baselines | ✅ Done | **Member 3** | B-0 fixed script, B-2 stub, and harness built. Sweep running. |
| **Stage 6** — LLM Layer | ✅ Done | **Member 1** | `agent/llm.py`, providers, cassettes, fallback, test_llm pass, Replay fully implemented |
| **Stage 7** — Solver Loop | ✅ Done | **Member 1** | `agent/loop.py`, full P1–P10 policy, budget guards, test_loop pass |
| **Stage 8** — Critic + Arbiter | ✅ Done | **Member 1** | `agent/critic/review.py`, `agent/arbiter.py`, X1–X9 adversarial tests pass |
| **Stage 9** — Backend API | ✅ Done | **Member 2** | Endpoints and E2E API tests pass |
| **Stage 10** — Frontend UI | 🔲 Not started | **Member 2** | — |
| **Stage 11** — Report | 🔲 Not started | **Member 1 & 2** | — |
| **Stage 12** — Evaluation Sweep | 🔲 Not started | **Member 3** | — |
| **Stage 13** — Hardening | 🔲 Not started | **Member 2** | — |
| **Stage 14** — Docs & Demo Kit | 🔲 Not started | **All** | — |

> **Next milestone:** IC-3 ready. Stage 9 (Backend API) is complete — all 13 §14.1 endpoints implemented, E2E test passes (B4 create→start→confirm→approve×2→DONE via HTTP), 56 tests passing. Next: Stage 10 (Frontend React Dashboard) to complete IC-3.

---

## 👥 Team Roles & Track Assignments

The build prompt (§1.11 and project guide §12) defines four work packages. With 3 people, we merge Track D into the lightest load. Here's the recommended split:

### Recommended Assignment

| Person | Track | Owns | Stages | Why This Fits |
|--------|-------|------|--------|---------------|
| **Member 1** | **A: Agent Core** | Orchestrator, LLM layer, Solver, Critic, Arbiter, Report generation | **6, 7, 8, 11** (generation part) | Heaviest AI/logic work; needs deep understanding of the prompt spec |
| **Member 2** | **B: Sandbox + Security** + **D: Backend + UI** | Docker sandbox, wheelhouse, security, Backend API, Frontend dashboard, Report page | **3, 9, 10, 11** (page part), **13, 14** | Infrastructure + user-facing; combines well because both are "plumbing" |
| **Member 3** | **C: Benchmark + Evaluation** | Template repo, calibration, 5 test cases, mini-papers, baselines, adversarial fixtures, evaluation harness | **4, 5, 12** | Self-contained testing world; can work mostly independently |

> [!IMPORTANT]
> **Stage 1 (Contracts) is already done.** All data models in [`agent/state.py`](file:///c:/Users/shivt/Documents/Programs/Rerun/Black-bot/src/core/models.py) and the schemas from §6 of the build prompt are frozen. **Do not change a contract** without updating every user and recording it in `docs/DECISIONS.md`.

### Assign Names Now

| Role | Name | GitHub Handle |
|------|------|---------------|
| Member 1 (Agent Core) | __________ | __________ |
| Member 2 (Sandbox + UI) | __________ | __________ |
| Member 3 (Benchmark) | __________ | __________ |

---

## 📦 Phase-by-Phase Breakdown

### 🔧 Phase 1: The Foundation (Stages 0–2) — ✅ COMPLETE

All three stages are done. The scaffolding, data contracts, and core deterministic logic (math, comparisons, evidence, policy, error classification) are built and tested.

**What exists:**
- Repo skeleton with all `__init__.py` files
- Docker environment with hardened sandbox (`rerun-base:py311`)
- All Pydantic v2 data models (Claim, Evidence, Hypothesis, PatchProposal, CriticReview, etc.)
- SQLite layer with WAL mode
- `tools/compare.py` — tolerance math (abs/rel, boundary, NaN handling)
- `tools/status.py` — `compute_status()` deterministic verdict
- `tools/evidence.py` — immutable evidence ledger with sha256
- `tools/errors.py` — error signature library (Appendix A patterns)
- `tools/policy.py` — all 10 policy rules (P1–P10) including guarded keys
- `tools/config_audit.py` — config mismatch detection with alias map

---

### 🧪 Phase 2: Testing Grounds (Stages 3–5)

#### Stage 3 — Sandbox (👤 Member 2)

**What to build:**
- `sandbox/manager.py` — full Docker container lifecycle (create, run, harvest, cleanup)
- `sandbox/limits.py` — resource limits enforcement
- `sandbox/cleanup.py` — orphan container/volume cleanup
- `sandbox/images/Dockerfile.base` — the `rerun-base:py311` image (exists but needs the full spec from §11.1)
- `scripts/make_wheelhouse.py` — builds wheelhouse INSIDE a container (arch-matched)
- `FakeSandbox` — canned `RunResult`s for testing without Docker
- Security self-test (`tests/security/escape_repo/attempt.py`)
- Optional GPU mode (mocked unit test only — can be cut)

**Key spec sections:** §11 (entire), §11.1–§11.5

**Container spec (critical — from §11.2):**
```python
common = dict(
    image="rerun-base:py311", detach=True, user="1000:1000",
    network_mode="none", read_only=True,
    cap_drop=["ALL"], security_opt=["no-new-privileges"],
    pids_limit=256, mem_limit="2g", memswap_limit="2g",
    tmpfs={"/tmp": "rw,size=256m"},
    working_dir="/workspace",
    environment={"HOME": "/tmp", "PYTHONPATH": "/workspace/.site",
                 "PYTHONHASHSEED": "0", "OMP_NUM_THREADS": "1"},
)
```

**Gate:**
```
python scripts/dev.py wheelhouse          # ok
python scripts/dev.py selftest            # all items PASS
# Hand-run: unfixed b2-like repo fails with ModuleNotFoundError, succeeds after install
tests/unit/test_gpu_mode.py               # green
```

**Deliverables checklist:**
- [ ] `sandbox/manager.py` with `run_container()` returning `RunResult`
- [ ] `sandbox/limits.py` with configurable CPU/mem/PID/time limits
- [ ] `sandbox/cleanup.py` with labeled container cleanup
- [ ] `scripts/make_wheelhouse.py` building offline wheel cache
- [ ] `FakeSandbox` protocol implementation for testing
- [ ] Security self-test passing all 8 checks (network, write, env, socket, uid, PID, OOM, timeout)
- [ ] `docs/security_selftest_output.json` saved
- [ ] `tests/unit/test_gpu_mode.py` (mocked, no real GPU needed)

---

#### Stage 4 — Benchmark (👤 Member 3)

**What to build:**
- `benchmarks/template/` — clean digits softmax regression repo (§15.1)
  - `data/digits.csv` (1,797 rows × 65 cols, exported once from sklearn)
  - `data.py`, `model.py`, `evaluate.py`, `train.py`
  - `configs/default.yaml`, `requirements.txt`, `README.md`, `tests/smoke.py`
- `scripts/calibrate_benchmark.py` — sweep learning rates, find good/bad pair (§15.3)
- `scripts/seed_faults.py` — generate 5 cases from template (§15.2)
- `scripts/make_papers.py` — generate synthetic PDF from measured numbers (§15.4)
- `benchmarks/registry.json` — allow-list (§15.5)
- `benchmarks/gold/*.json` — gold labels (never exposed to agent)

**Key spec sections:** §15 (entire)

**The 5 benchmark cases (§15.2):**

| Case | Fault | Expected Result |
|------|-------|-----------------|
| `b1_control` | Nothing wrong | `REPRODUCED`, 0 patches |
| `b2_dependency` | PyYAML missing from requirements.txt | `REPRODUCED` after 1 patch |
| `b3_silent_config` | Config learning_rate ≠ paper; run exits 0 with wrong number | `REPRODUCED` after 1 patch |
| `b4_combined` | Both b2 + b3 (THE DEMO CASE) | `REPRODUCED` after 2 patches |
| `b5_unable` | Code has `.cuda()` calls | `UNABLE_TO_EXECUTE`, 0 patches |

**Gate:**
```
python scripts/dev.py calibrate    # writes calibration.json + MEASURED.md
# All 5 case dirs + PDF exist
# b3 in sandbox exits 0 with mean OUTSIDE ±0.01 of paper
# b1 in sandbox is WITHIN tolerance
```

**Deliverables checklist:**
- [ ] `benchmarks/template/` — complete working repo
- [ ] `data/digits.csv` exported and committed
- [ ] `scripts/calibrate_benchmark.py` — finds good_lr/bad_lr pair
- [ ] `scripts/seed_faults.py` — generates all 5 cases
- [ ] `scripts/make_papers.py` — generates `benchmarks/papers/digits_softmax.pdf`
- [ ] `benchmarks/registry.json` with all 5 cases
- [ ] `benchmarks/gold/b1_control.json` through `b5_unable.json`
- [ ] `benchmarks/calibration.json` with measured numbers
- [ ] `benchmarks/MEASURED.md` with sweep table + determinism check

> [!NOTE]
> The template repo deliberately `import yaml` in `train.py` but `requirements.txt` in b2/b4 **omits PyYAML**. The base Docker image also has no PyYAML. This is the planted crash.

---

#### Stage 5 — Baselines & Harness (👤 Member 3)

**What to build:**
- `benchmarks/baselines/b0_fixed.py` — no-AI script (install, run README command, compare)
- `benchmarks/baselines/b2_oneshot.py` — one-shot LLM baseline (stub, can be cut)
- `benchmarks/run_bench.py` — evaluation harness with `SimulatedApprover`

**Key spec sections:** §16.1, §16.3, §16.4

**Gate:**
```
python scripts/dev.py bench --systems B-0
# B-0 passes b1, fails b2/b3/b4 (if not, the benchmark is wrong!)
```

**Deliverables checklist:**
- [ ] B-0 baseline script
- [ ] B-2 baseline stub (can be cut — see cut list)
- [ ] `run_bench.py` with `SimulatedApprover`
- [ ] Results CSV + per-run JSON output

---

### 🧠 Phase 3: The AI Brains (Stages 6–8)

#### Stage 6 — LLM Layer (👤 Member 1)

**What to build:**
- `agent/llm.py` — the `call(role, mode, payload, out_model)` function (§13.1)
- Provider implementations: `gemini`, `replay`
- Cassette record/replay system (§13.2)
- Solver and Critic preambles (§13.4)
- JSON schema validation of LLM outputs against Pydantic models

**Key spec sections:** §4 (config), §13 (entire)

**Gate:**
```
pytest tests/agent/test_llm.py
# invalid JSON → one re-prompt → error
# fallback switch emits llm_fallback
# replay miss raises
# no key appears in any log
```

**Deliverables checklist:**
- [ ] `agent/llm.py` with `call()` function
- [ ] `gemini` provider
- [ ] `replay` provider for testing
- [ ] `replay` provider for cassettes
- [ ] `agent/config.py` with all Appendix B constants
- [ ] Cassette replay for b1-b5
- [ ] Secret scrubbing in all logs
- [ ] Retry + fallback logic

---

#### Stage 7 — Solver Loop (👤 Member 1)

**What to build:**
- `agent/loop.py` — the orchestrator: `run_project(state, deps)` (§7.2)
- `agent/state.py` — `ProjectState` management (extend what Stage 1 built)
- Phase handlers for all 20 phases (§7.1 transition table)
- DIAGNOSE episode logic (§7.3) — the Solver picks tools, orchestrator executes
- Tool gate — rejects calls if phase/permission/budget doesn't allow
- Budget guard (§7.4) — 40 steps, 3 patches, timeouts
- The safety-net nudge — auto-call `compare_configuration` if Solver doesn't within 3 steps
- `agent/solver/prompts.py` and `schemas.py` — all 5 Solver modes (§13.5)

**Key spec sections:** §7 (entire), §8 (tool registry), §13.5 (Solver modes)

**Depends on:** Stage 3 (Sandbox — for real runs), Stage 6 (LLM layer)

**Gate:**
```
pytest tests/agent -k "b1 or b2 or b3 or b4 or b5 or budgets or resume or illegal"
# All green with Replay + FakeSandbox
python scripts/dev.py run --case b2_dependency  # real LLM, human types 'y' to approve
# Reaches REPRODUCED
```

**Deliverables checklist:**
- [ ] `agent/loop.py` with `run_project()` and phase handlers
- [ ] Tool gate enforcing allowed phases/permissions
- [ ] Budget guard with warnings at 80%
- [ ] DIAGNOSE episode with hypothesis tracking
- [ ] Safety-net nudge for `compare_configuration`
- [ ] `agent/solver/prompts.py` with all 5 mode prompts
- [ ] `agent/solver/schemas.py` with Pydantic output models
- [ ] `agent/events.py` — event emission for all §6.3 event types
- [ ] Resume from `state_json` on crash
- [ ] Tests: b1–b5 on replay, budget exhaustion, illegal tool rejection

> [!WARNING]
> This is the **largest and most critical stage**. The DIAGNOSE episode (§7.3) is where the "intelligence" lives. The silent-divergence branch (run exits 0 but wrong number → config audit) is the **key demo moment**.

---

#### Stage 8 — Critic + Arbiter (👤 Member 1)

**What to build:**
- `agent/critic/prompts.py` — Critic system prompts for `patch_review` and `report_review`
- `agent/critic/schemas.py` — `CriticReview` output model
- `agent/critic/review.py` — the Critic call flow (§9.2): build review packet, allow ≤3 fetches, validate
- `agent/arbiter.py` — the decision table (§9.4)
- Verdict override logic — code forces stricter verdict when critical checks fail (§9.3)
- Adversarial fixture runner

**Key spec sections:** §9 (entire)

**The 9 Critic checks (all boolean, §9.3):**
1. `cause_is_cited_and_exists`
2. `evidence_actually_supports_cause`
3. `change_is_minimal`
4. `files_in_scope`
5. `not_metric_chasing`
6. `value_has_paper_or_error_provenance`
7. `no_change_to_evaluation_or_data_semantics`
8. `alternative_explanations_considered`
9. `reversible_and_smoke_testable`

**Gate:**
```
pytest tests/agent/test_critic.py tests/unit/test_arbiter.py   # green
python scripts/dev.py adversarial   # prints per-fixture stopping layer
# Gold patches not blocked (or false-block count reported)
```

**Deliverables checklist:**
- [ ] `agent/critic/review.py` with full review packet construction
- [ ] `agent/critic/prompts.py` for both modes
- [ ] `agent/arbiter.py` with `decide_patch()` decision table
- [ ] Code-enforced verdict override when critical checks fail
- [ ] Adversarial fixtures X1–X9 in `benchmarks/adversarial/`
- [ ] `scripts/run_adversarial.py` (or `dev.py adversarial`)
- [ ] Tests for every arbiter decision branch

---

### 🖥️ Phase 4: UI & Reporting (Stages 9–11)

#### Stage 9 — Backend API (👤 Member 2)

**What to build:**
- `backend/app/main.py` — FastAPI app with CORS
- `backend/app/routes.py` — all API endpoints (§14.1 table)
- `backend/app/sse.py` — SSE streaming with `Last-Event-ID` resume
- `backend/app/db.py` — SQLite connection, table creation, WAL mode
- `backend/app/models.py` — request/response models
- `backend/app/runner.py` — worker thread running the orchestrator

**Key spec sections:** §14.1

**Key API endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/health` | Docker, LLM reachability (no keys) |
| `GET` | `/api/benchmarks` | List cases (no gold labels!) |
| `POST` | `/api/projects` | Create project |
| `POST` | `/api/projects/{id}/start` | Run INGEST→ANALYZE |
| `GET` | `/api/projects/{id}/events` | **SSE stream** |
| `POST` | `/api/projects/{id}/claims/confirm` | Human confirms claims |
| `POST` | `/api/approvals/{id}` | Human approves/rejects patch |
| `GET` | `/api/projects/{id}/report` | Get final report |

**Gate:**
```
pytest tests/e2e/test_b4_api.py   # Replay: create → start → confirm → approve ×2 → report
```

**Deliverables checklist:**
- [ ] FastAPI app with all routes from §14.1
- [ ] SSE implementation with `Last-Event-ID` replay
- [ ] Worker thread for orchestrator (thread-safe event bus)
- [ ] Human pause/resume mechanism
- [ ] Idempotent state-changing endpoints
- [ ] E2E test driving B4 through HTTP

---

#### Stage 10 — Frontend Dashboard (👤 Member 2)

**What to build:**
- React 18 + Vite + TypeScript + Tailwind CSS app
- Three routes: `/` (New project), `/p/:id` (Dashboard), `/p/:id/report` (Report)
- Components: `PhaseBar`, `TracePanel`, `Terminal`, `DiffView`, `ApprovalModal`, `CriticPanel`, `ClaimTable`, `EvidenceDrawer`, `StatusBadge`, `ReportChart`, `Banner`
- `useEventStream(projectId)` hook for SSE
- Design tokens from §14.2

**Key spec sections:** §14.2

**Design tokens:**

| Meaning | Colour |
|---------|--------|
| Background / text | `#0F172A` / `#E2E8F0` |
| Solver | Teal `#14B8A6` |
| Critic | Purple `#A78BFA` |
| Human approval | Amber `#F59E0B` |
| Failure | Red `#EF4444` |
| Verified | Green `#22C55E` |
| Deterministic/tools | Grey `#64748B` |

**Gate:**
```
npm run build   # succeeds
# Human completes B4 by mouse with backend on replay/replay
# Screenshots saved to docs/screens/
```

**Deliverables checklist:**
- [ ] Vite + React + TS + Tailwind project in `frontend/`
- [ ] New Project page with benchmark selector
- [ ] Claim confirmation table (editable)
- [ ] Dashboard with phase bar, trace panel, terminal, diff viewer
- [ ] Approval modal with Critic panel, banners, extra confirmation
- [ ] Report page with charts, status badge, evidence drawer
- [ ] `useEventStream` hook with SSE + `Last-Event-ID`
- [ ] Fonts: Inter + JetBrains Mono (bundled, no CDN)

---

#### Stage 11 — Report (Split: Member 1 generates, Member 2 renders)

**What to build:**
- `tools/report.py` — `generate_report()` (§12.1–12.2) — **Member 1**
- Placeholder resolution (§12.2) — **Member 1**
- `verify_report_claims()` — deterministic verifier V1–V7 (§12.4) — **Member 1**
- Report page rendering in React (§12.3, 12.5) — **Member 2**
- MD/HTML export — **Member 2**

**Gate:**
```
pytest tests/unit/test_report_verifier.py   # green
# Corrupted statement is caught and listed under "Statements removed"
```

---

### 🚀 Phase 5: Final Exams & Polish (Stages 12–14)

#### Stage 12 — Evaluation Sweep (👤 Member 3)

**What to build:**
- Full `python scripts/dev.py bench` run across all cases × systems × 3 repeats
- Full `python scripts/dev.py adversarial` run
- Update `benchmarks/MEASURED.md` with real tables

**Gate:**
```
# MEASURED.md updated with real counts
# Includes cases where Rerun did NOT beat B-0, if any
```

---

#### Stage 13 — Hardening (👤 Member 2)

**What to build:**
- `dev.py demo-check` — full pre-demo verification
- Cassettes recorded for b1–b5
- Resume tested (kill worker mid-run, restart)
- Secret hygiene test
- Orphan cleanup on startup

**Gate:**
```
python scripts/dev.py demo-check    # all PASS (LLM may be WARN)
python scripts/dev.py gpu-smoke     # PASS or SKIP
```

---

#### Stage 14 — Docs & Demo Kit (👤 All three)

**What to build:**
- Final `README.md` (limits first, honest positioning)
- `docs/DEMO_RUNBOOK.md` — step-by-step demo script
- `docs/SECURITY.md` — security model documentation
- `docs/BENCHMARK.md` — benchmark methodology
- Sample reports generated from real runs

**Gate:**
```
# README quickstart works from a clean clone:
# setup → images → wheelhouse → seed-faults → api
```

---

## 🔗 Dependency Graph

```
Stage 0 ─── Stage 1 ─── Stage 2 ──┬── Stage 3 (Sandbox)     → Member 2
(DONE)      (DONE)      (DONE)     │      (DONE)
                                   │      ├── Stage 9 (API)   → Member 2
                                   │      │      │
                                   │      │      └── Stage 10 (UI)  → Member 2
                                   │      │
                                   ├── Stage 4 (Benchmark)    → Member 3
                                   │      (DONE)
                                   │      └── Stage 5 (Baselines) → Member 3
                                   │
                                   └── Stage 6 (LLM Layer)    → Member 1
                                          │
                                          └── Stage 7 (Solver) ← needs Stage 3 too
                                                 │
                                                 └── Stage 8 (Critic)
                                                        │
                            ┌───────────────────────────┤
                            │                           │
                     Stage 11 (Report)           Stage 12 (Eval) → Member 3
                            │                           │
                     Stage 13 (Harden) → Member 2       │
                            │                           │
                            └───────── Stage 14 (Docs) ─┘ → All
```

**What can run in parallel RIGHT NOW:**
- ✅ **Stage 5** (Member 3) — Baselines and harness (Depends on Stage 4)
- ✅ **Stage 6** (Member 1) — LLM layer, providers, replay

> [!TIP]
> Stages 5 and 6 have **zero dependencies on each other**. Member 3 and Member 1 can start them immediately. Stage 7 needs both Stage 3 (Done) and Stage 6, so Member 1 can move straight to it after Stage 6.

---

## 🤖 Antigravity Session Guide

Each team member will use Antigravity independently. Here's how to ensure continuity.

### Starting a New Session

**Copy-paste this prompt to Antigravity at the start of every session:**

> Read `TEAM_PLAN.md` and `rerun_antigravity_build_prompt.md` completely. Check `progress.md` for current status. I am **[Member 1/2/3]** working on **[Track A/B+D/C]**. My current stage is **[Stage N]**. Continue from where I left off. Follow §1 (how you must work), §2 (invariants), and §20 (stop-and-ask rules). Run the gate when the stage is complete and update `progress.md`.

### Rules for All Sessions

1. **Always update `progress.md`** after completing a stage gate — paste real output
2. **Commit after every meaningful step** — message format: `stage-N: <what>`
3. **Never edit files owned by another track** without coordinating (see File Ownership below)
4. **Never change a frozen contract** (§6 data models) without updating `docs/DECISIONS.md`
5. **Never weaken a safety control** to make something pass (§2.1 invariants)
6. **Record design decisions** in `docs/DECISIONS.md` with date and your name

### If Antigravity Stops with `BLOCKED:`

It will write the question at the top of `progress.md`. The triggers are:
1. Docker unavailable (3 attempts)
2. No LLM credentials (stages 0–5 can still finish)
3. Gate still failing after 3 fix attempts
4. Requirement contradiction that changes a frozen contract
5. About to break an invariant or build something in the "do not build" list
6. Calibration can't find good/bad learning rate pair

**Answer the question, then tell it to continue from `progress.md`.**

---

## 🔄 Integration Checkpoints

These are the moments where team members must sync and verify things work together.

| Checkpoint | When | Who Syncs | What to Prove |
|------------|------|-----------|---------------|
| **IC-1** | After Stages 3 + 6 | Member 1 + 2 | Core + sandbox run B2 with replay (skeleton works, zero model risk) |
| **IC-2** | After Stage 7 | Member 1 + 2 + 3 | Real LLM completes B4 from CLI (the agent works, no UI yet) |
| **IC-3** | After Stage 10 | All | UI drives B4 live with approvals (the product exists) |
| **IC-4** | After Stage 12 | All | Full evaluation sweep gives a table (we have honest numbers) |
| **IC-5** | After Stage 13 | All | Fallbacks rehearsed, runbook passes twice in a row (demo survivable) |

### Checkpoint Reports

After **Stages 3, 7, 10, and 13**, whoever finishes writes a short checkpoint in `progress.md`:
- What works
- What is flaky
- What to cut next (from the cut list)

---

## 📁 File Ownership Rules

To avoid merge conflicts, each track owns specific directories:

| Track | Owns (can edit freely) | Reads (do not edit) |
|-------|------------------------|---------------------|
| **A (Agent Core)** | `agent/`, `tools/` (logic files) | `sandbox/`, `backend/`, `benchmarks/` |
| **B+D (Sandbox + UI)** | `sandbox/`, `backend/`, `frontend/`, `scripts/dev.py` | `agent/`, `tools/` |
| **C (Benchmark)** | `benchmarks/`, `scripts/calibrate_benchmark.py`, `scripts/seed_faults.py`, `scripts/make_papers.py` | `agent/`, `sandbox/` |

**Shared files (coordinate before editing):**
- `progress.md` — append only, never delete others' entries
- `docs/DECISIONS.md` — append only
- `requirements.txt` / `requirements-dev.txt`
- `.env.example`
- `pytest.ini`
- `Makefile`

---

## ✂️ Cut List (If Time Runs Out)

**Never cut these (minimum viable Rerun):**
- Hardened no-network run container
- Human claim confirmation
- Comparator + `compute_status`
- Policy checker
- Human approval
- Evidence ledger + verifier
- Cases b1–b4
- B-0 baseline
- Silent-divergence branch
- Unpatched-vs-patched reporting

**Cut in this order (first item goes first):**

| Priority | Cut | Impact |
|----------|-----|--------|
| 0 | GPU mode (keep mocked test only) | Minimal — demo never uses it |
| 1 | React Flow graph, stretch cases, real-repo experiment | Cosmetic |
| 2 | Critic `diagnosis_review` mode | Minor safety reduction |
| 3 | Cross-attempt fix-hint table, HTML export | Cosmetic |
| 4 | B-2 baseline (keep B-0) | Less comparison data |
| 5 | Critic `report_review` (keep deterministic verifier) | Minor safety reduction |
| 6 | Different-model-for-Critic experiment | Less data for slides |
| 7 | Use Streamlit instead of React | Less polished UI |
| 8 | Live b5 demo (keep as recording) | Minor demo impact |

---

## 💬 Communication Protocol

### During the Hackathon

1. **Sync every 2 hours** — 2 min standup: "what I finished, what's next, am I blocked?"
2. **Git pull before starting work** — always work on the latest
3. **Commit + push when finishing a substage** — don't hoard changes
4. **Flag blockers immediately** — don't wait for the standup

### Naming Conventions

- **Commits:** `stage-N: <what>` (e.g., `stage-3: sandbox manager with resource limits`)
- **Branches:** `stage-N/<feature>` if working on a long feature (e.g., `stage-6/llm-providers`)
- **Decisions:** append to `docs/DECISIONS.md` with format:

```markdown
### D-<number>: <title>
**Date:** YYYY-MM-DD  **By:** <name>
**Decision:** <what was decided>
**Reason:** <why>
```

---

## ⚡ Quick Reference: Key Commands

```bash
# Setup & Build
python scripts/dev.py setup              # Initial setup
python scripts/dev.py images             # Build Docker images
python scripts/dev.py wheelhouse         # Build offline package cache

# Testing
python scripts/dev.py test               # Run unit + agent tests (no Docker)
python scripts/dev.py hardened-smoke      # Test sandbox security
python scripts/dev.py selftest           # Full security self-test

# Benchmark
python scripts/dev.py calibrate          # Find good/bad learning rates
python scripts/dev.py seed-faults        # Generate 5 benchmark cases
python scripts/dev.py papers             # Generate synthetic PDF
python scripts/dev.py bench              # Run full evaluation

# Demo
python scripts/dev.py demo-check         # Pre-demo verification
python scripts/dev.py api                # Start backend
python scripts/dev.py run --case b4      # Run a case from CLI

# Frontend
cd frontend && npm run dev               # Start React dev server
cd frontend && npm run build             # Production build

# Adversarial
python scripts/dev.py adversarial        # Run attack fixtures X1-X9

# Cassettes
python scripts/dev.py record --case b4   # Record LLM responses
python scripts/dev.py replay --case b4   # Replay from cassette
```

---

## 📊 Definition of Done (from §21)

- [ ] `python scripts/dev.py demo-check` passes
- [ ] B4 runs end-to-end via the UI with two human approvals, visible Critic panel, final status `REPRODUCED (after 2 approved patches)`, report shows unpatched + patched numbers
- [ ] B1 → zero patches; B5 → `UNABLE_TO_EXECUTE` with blocker evidence
- [ ] `adversarial` results table exists (per-layer catches, false-block count)
- [ ] Security self-test passes, output saved
- [ ] `benchmarks/MEASURED.md` has real tables; no hand-typed numbers
- [ ] Corrupted report statement caught by verifier
- [ ] Demo works from cassette replay with network disabled (REPLAY banner visible)
- [ ] README states limits first; no secrets in repo or logs
- [ ] GPU_ENABLED=false needs no GPU; gpu-smoke passes or SKIPs
- [ ] Tests prove guarded keys work correctly and docs aren't patch provenance
- [ ] Team can answer: "Why not just a generic coding agent?" and "Does the Critic actually help?"

---

*Last updated: 2026-10-07. Update this file after every stage completion.*
