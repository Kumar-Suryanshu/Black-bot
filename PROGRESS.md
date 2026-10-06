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
  - *Gate Run Results:* PASS (`pytest tests/agent/test_llm.py` passed; `agent/llm.py` with `call()`, providers `openai_compat`, `anthropic`, `fake`, `replay`; cassette record/replay verified; secret scrubbing verified; fallback on primary failure verified; schema validation with 1 re-prompt verified)
- [x] **Stage 7**: Solver loop — *Owner: Member 1 (Track A)*
  - *Gate Run Results:* PASS (`pytest tests/agent/test_loop.py` passed; `tools/policy.py` completed with P1–P10, hard limits MAX_FILES=5, MAX_CHANGED_LINES=200, guarded sensitive keys; `agent/loop.py` orchestrator verified end-to-end on B1 control, B2 dependency with approval, and budget exhaustion; safety-net nudge verified)
- [x] **Stage 8**: Critic + Arbiter — *Owner: Member 1 (Track A)*
  - *Gate Run Results:* PASS (`pytest tests/unit/test_arbiter.py tests/agent/test_critic.py` passed; `python scripts/dev.py adversarial` passed; all adversarial fixtures X1–X9 blocked by Policy or Critic; gold patch false-block count = 0 verified)
- [ ] **Stage 9**: Backend — *Owner: TBD (Track B+D)*
- [ ] **Stage 10**: Frontend — *Owner: TBD (Track B+D)*
- [ ] **Stage 11**: Report — *Owner: Track A (generation) + Track B+D (rendering)*
- [ ] **Stage 12**: Evaluation sweep — *Owner: TBD (Track C)*
- [ ] **Stage 13**: Hardening & fallbacks — *Owner: TBD (Track B+D)*
- [ ] **Stage 14**: Docs & demo kit — *Owner: All*

## Checkpoint Reports
*(Updated after Stages 3, 7, 10, and 13)*

### After Stage 7 & Stage 8 (Checkpoint IC-2 Ready)
- **What works:**
  - **LLM Layer**: Unified `call()` interface supporting OpenAI-compatible endpoints, Anthropic, FakeLLM, and Cassette Replay. Automated fallback and secret scrubbing active.
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
- **What is incomplete:** Backend FastAPI endpoints (Stage 9), Frontend React dashboard (Stage 10), and Full Report generator/verifier (Stage 11).
- **What's next:** Phase 4: UI & Reporting (Backend API & Frontend Dashboard).

## Blockers (STOP-AND-ASK)
*(None currently)*

## Decision Log
*(Append new decisions below. Full log in `docs/DECISIONS.md`)*

---

*Last updated: 2026-10-06*
