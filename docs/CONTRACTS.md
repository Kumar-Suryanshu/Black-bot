# Rerun System Contracts & Architecture Specification

This document defines the formal data models, lifecycle phases, deterministic policy limits, verifier rules, human gates, and API routes governing Rerun.

---

## 1. Lifecycle State Machine (20 Phases)

Execution proceeds through an orchestrator-controlled state machine where each transition is logged and persisted to SQLite WAL `projects.state_json`:

```
INGEST ──────► ANALYZE ──────► CLAIMS_CONFIRM [Human Gate 1]
                                    │
                                    ▼
                                  PLAN ──────► PREFLIGHT ──────► SETUP
                                                                   │
                                                                   ▼
       ┌───────────────────────────────────────────────────────── RUN
       │                                                           │
       │                                                           ▼
       │                                                        OBSERVE
       │                                                           │
       ▼                                                           ▼
     STATUS ◄────── COMPARE ◄────── VALIDATE ◄─────────────────────┘
       │                │ (divergence / failure)
       │                ▼
       │            DIAGNOSE ──► PATCH_PROPOSE ──► POLICY_CHECK ──► CRITIC_REVIEW
       │                                                                  │
       │                                                                  ▼
       │               PATCH_APPLY ◄───────── [Human Gate 2] ◄──────── APPROVAL
       │                   │
       │                   └───────► (loops back to SETUP / RUN)
       ▼
     REPORT ──────► REPORT_REVIEW [Gate 3] ──────► DONE
```

### Full Phase Enumeration
1. `INGEST`: Repository cloning and paper extraction.
2. `ANALYZE`: Codebase structural profiling, environment dependency detection, and paper claim parsing.
3. `CLAIMS_CONFIRM`: **Human Gate 1** — user confirms/selects claims and optionally overrides run command.
4. `PLAN`: Experiment plan generation (command, seeds, config files, expected outputs).
5. `PREFLIGHT`: Triage pre-check for required hardware (GPU) or missing local datasets.
6. `SETUP`: Isolated environment provisioning and offline wheelhouse installation.
7. `RUN`: Experiment execution inside network-isolated Docker container (`rerun-base:py311`).
8. `OBSERVE`: Output artifact parsing and metric value extraction.
9. `VALIDATE`: Execution exit code verification and smoke test checks.
10. `COMPARE`: Numerical metric comparison against claimed target within tolerance band.
11. `DIAGNOSE`: Root-cause investigation on error, hypothesis ledger updates.
12. `PATCH_PROPOSE`: Solver patch generation targeted at confirmed hypothesis.
13. `POLICY_CHECK`: Deterministic Python policy validation (P1–P10).
14. `CRITIC_REVIEW`: Independent Critic review packet construction and 9-point checklist evaluation.
15. `APPROVAL`: **Human Gate 2** — human operator reviews patch diff, rationale, and 9-point checklist.
16. `PATCH_APPLY`: Controlled disk application of approved patch with pre-cached backups.
17. `STATUS`: Final status determination (`REPRODUCED`, `NOT_REPRODUCED`, `UNABLE_TO_EXECUTE`, `INCONCLUSIVE`).
18. `REPORT`: Report statement synthesis with placeholder templates.
19. `REPORT_REVIEW`: Deterministic verifier checks V1–V7 on report statements.
20. `DONE`: Final certification packaging, reproduction kit compilation, and terminal state.

---

## 2. Hard Limits & Resource Caps

| Limit Variable | Default Value | Description |
|:---|:---:|:---|
| `MAX_STEPS` | 40 | Maximum total orchestrator loop steps before forced `INCONCLUSIVE`. |
| `MAX_PATCHES` | 3 | Maximum patches allowed across the lifecycle. |
| `MAX_FILES` | 5 | Hard limit on modified files per patch proposal (Rule P1). |
| `MAX_CHANGED_LINES` | 200 | Hard limit on total added + removed lines per patch (Rule P2). |
| `LARGE_PATCH_FILES` | 2 | Soft threshold: more files triggers mandatory warning flag. |
| `LARGE_PATCH_LINES` | 20 | Soft threshold: more lines triggers mandatory warning flag. |
| `DIAGNOSE_STEPS_MAX` | 8 | Maximum tool calls allowed during a single diagnosis phase. |
| `RUN_TIMEOUT_S` | 600 | Maximum execution container runtime before timeout kill. |
| `INSTALL_TIMEOUT_S` | 300 | Maximum setup/install container runtime. |
| `SANDBOX_CPUS` | 2 | CPU core limit assigned to container. |
| `SANDBOX_MEM` | 2g | Memory ceiling before container OOM kill. |
| `SANDBOX_PIDS` | 256 | Process spawn ceiling preventing fork bombs. |

---

## 3. Deterministic Policy Rules (P1–P10)

- **P1 (File Count):** Total modified files $\le 5$.
- **P2 (Line Count):** Total modified lines $\le 200$.
- **P3 (Guarded Paths):** Edits to test runners, git files, shell scripts, or hidden files rejected.
- **P4 (Environment Protection):** Edits to `.env`, credentials, or host config rejected.
- **P5 (Metric Tampering):** Edits altering loss functions, metrics, or evaluation thresholds rejected.
- **P6 (Provenance Traceability):** Non-paper parameter modifications require verified traceback provenance.
- **P7 (Sensitive Keys):** Random seeds, batch sizes, and epochs locked strictly to paper-stated values.
- **P8 (No Test Deletion):** Deletion of assertions or test fixtures rejected.
- **P9 (Single Hypothesis Target):** Patch must address exactly one confirmed hypothesis.
- **P10 (Valid Syntax & Diff):** Patch must produce syntactically valid code and clean unified diff.

---

## 4. Deterministic Report Verifier Rules (V1–V7)

Before any solver-generated statement enters the final report or export, it is verified in pure Python:
- **V1 (Placeholder Resolution):** Statement text must not contain unexpanded `{{...}}` tokens.
- **V2 (Numerical Fidelity):** All numbers cited in statement text must match measured execution results or paper claim values within tolerance.
- **V3 (Non-Accusatory Tone):** Accusatory terms (*hallucinated*, *fraud*, *fabricated*, *stole*, *faked*) are strictly stripped.
- **V4 (Status Consistency):** Findings cannot assert reproduction success if project status is `FAILED` or outside tolerance.
- **V5 (Evidence Grounding):** Findings must reference valid evidence ledger IDs (`E-xxx`) present in project run ledger.
- **V6 (Hypothesis Provenance):** Cause statements must cite hypotheses present in `state.hypotheses`.
- **V7 (Confirmed Causality):** Cause statements cannot claim `confidence="confirmed"` without a corresponding confirmed hypothesis.

---

## 5. Human Decision Gates

1. **Gate 1: Claim Intake & Command Override (`CLAIMS_CONFIRM`):**
   - Human operator reviews extracted paper claims, marks primary vs auxiliary claims, confirms tolerance thresholds, and optionally inputs custom run command override (`state.user_command`).
2. **Gate 2: Patch Approval Modal (`APPROVAL`):**
   - Human operator inspects unified diff, rationale, risk class (`environment_fix` vs `code_fix`), and independent 9-point Critic checklist before any file is touched on disk.
3. **Gate 3: Certification & Reproduction Kit (`DONE`):**
   - Operator inspects final verification report, baseline vs patched comparison chart, and downloads self-contained reproduction kit ZIP.

---

## 6. API Route Catalog

| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/api/projects/benchmark` | Initialize a project from built-in benchmarks B1–B5. |
| `POST` | `/api/projects/custom` | Ingest and shallow clone a custom public GitHub repository. |
| `POST` | `/api/projects/{id}/start` | Start orchestrator worker daemon thread. |
| `POST` | `/api/projects/{id}/claims/confirm` | **Gate 1:** Submit confirmed claims and custom command. |
| `POST` | `/api/projects/{id}/approve` | **Gate 2:** Submit human patch approval (`approve` / `reject` / `edit`). |
| `POST` | `/api/projects/{id}/abort` | Immediately abort run and kill associated Docker containers. |
| `GET` | `/api/projects/{id}` | Retrieve full round-trip `ProjectState` JSON. |
| `GET` | `/api/projects/{id}/events` | Retrieve historical events since `last_event_id`. |
| `GET` | `/api/projects/{id}/events/stream` | Server-Sent Events (SSE) live-tail stream with reconnect support. |
| `GET` | `/api/projects/{id}/evidence` | List all structured evidence ledger entries (Defect D12). |
| `GET` | `/api/projects/{id}/evidence/{eid}` | Retrieve specific evidence excerpt and provenance metadata. |
| `GET` | `/api/projects/{id}/runs/{n}/log` | Retrieve execution log for attempt $n$. |
| `GET` | `/api/projects/{id}/patches/{n}/diff` | Retrieve unified diff for patch proposal $n$. |
| `GET` | `/api/projects/{id}/report` | Retrieve verifier-approved reproduction report JSON. |
| `GET` | `/api/projects/{id}/report.md` | Download GitHub-compatible Markdown verification report. |
| `GET` | `/api/projects/{id}/report.html` | Download self-contained, printable HTML report. |
| `GET` | `/api/projects/{id}/kit` | Download self-contained reproduction kit ZIP archive (§R7). |
| `GET` | `/api/keys/stats` | Real-time Gemini API key usage and rotation diagnostics. |
| `GET` | `/api/health` | Service health check and sandbox capability report. |
| `POST` | `/api/admin/kill-all` | Emergency operator kill switch for all active containers. |
