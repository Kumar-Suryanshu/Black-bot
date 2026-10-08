# Rerun Implementation Progress

> **Team Plan:** See [`TEAM_PLAN.md`](TEAM_PLAN.md) for phase breakdown, track assignments, and collaboration guide.
> **Build Spec:** [`Rerun_Antigravity_Build_Prompt.md`](Rerun_Antigravity_Build_Prompt.md) · **Guide:** [`Rerun_Project_Guide.md`](Rerun_Project_Guide.md)
> **Completion Plan:** [`docs/COMPLETION_PLAN.md`](docs/COMPLETION_PLAN.md) · **Audit:** [`docs/baseline_audit.md`](docs/baseline_audit.md)

---

## Completion Plan Stage Gates

- [x] **Stage 0 (Completion Plan)**: Baseline lock & truth audit
  - *Branch:* `completion/stage-0`
  - *Gate Run Results:* PASS (75 passed, 1 xfailed in `tests/`; all 25 defects D1–D25 confirmed in `docs/baseline_audit.md`; failing baseline test `test_default_sandbox_is_real.py` added)
  - *Status:* PASS

- [x] **Stage 1 (Completion Plan)**: Make the live path real (R0)
  - *Branch:* `completion/stage-1`
  - *Gate Run Results:* PASS (All 5 benchmark cases `b1_control`, `b2_dependency`, `b3_silent_config`, `b4_combined`, `b5_unable` run in real Docker containers via `DockerSandbox` with base image `rerun-base:py311`; `b1` reproduced with 0 patches; `b2` failed on real `ModuleNotFoundError: No module named 'yaml'`, proposed P-1 PyYAML==6.0.1, offline wheelhouse installed, run 2 reproduced; `b3` executed at calibrated bad accuracy 0.8733, proposed P-1 learning_rate: 0.5, run 2 reproduced at 0.9556; `b4` applied dependency patch then config patch, reproduced at 0.9556; `b5` blocked at preflight `gpu_required` -> `UNABLE_TO_EXECUTE`; 0 occurrences of "Execution completed successfully" in Stage 1 runs; `test_default_sandbox_is_real.py` passed; API startup refuses fake sandbox without `ALLOW_FAKE_SANDBOX=1`; all proof recorded in `docs/real_run_proof.md`; full test suite passes 82 tests).
  - *Status:* PASS

- [x] **Stage 2 (Completion Plan)**: Input plumbing: GitHub URL + PDF upload (R1)
  - *Branch:* `completion/stage-2`
  - *Gate Run Results:* PASS:
    - **API `POST /api/projects`:** supports both `multipart/form-data` (`repo_url`, optional `repo_ref`, `paper` PDF) and legacy JSON (`{benchmark_id}`).
    - **URL Validation:** strict regex enforcement `^https://github\.com/[\w.-]+/[\w.-]+(\.git)?$` rejecting non-GitHub hosts, `file://`, SSH/`git@`, and credentials/tokens `@`.
    - **PDF Validation:** `%PDF-` magic header, $\le 25\text{ MB}$, $\le 60$ pages, extractable digital text $\ge 50$ characters (rejects scanned / textless PDFs).
    - **Contract Updates:** `ProjectState` updated with `source`, `repo_url`, `repo_ref`, `repo_commit`, `paper_path`, `paper_sha256`, `user_command`, `simulated`; documented in `docs/CONTRACTS.md`.
    - **Ingest Isolation:** shallow clone (`--depth 1 --no-tags --no-recurse-submodules`, no LFS), 120s timeout, non-interactive terminal prompt disabled, $\le 500\text{ MB}$ size cap, $\le 10{,}000$ files cap, fresh `git init` (remote origin and hooks discarded), escaping symlinks audit, CRLF $\rightarrow$ LF line ending normalization.
    - **Feature Flag & Security Notice:** `ALLOW_CUSTOM_REPOS` feature flag (default on locally, togglable) with required sandbox disclaimer displayed.
    - **Defect D11 Fixed:** custom command at `CLAIMS_CONFIRM` stored in `state.user_command` and honored in `handle_plan`.
    - **Frontend `/new`:** source mode switch (*Benchmark | My paper + repo*), GitHub URL validator, optional branch/ref input, drag-and-drop PDF uploader, consent notice banner, and progressive ingest states.
  - *Status:* PASS

- [x] **Stage 3 (Completion Plan)**: Triage and code-completeness check (R2)
  - *Branch:* `completion/stage-3`
  - *Gate Run Results:* PASS:
    - **`tools/triage.py`:** Deterministic, executes zero repo code. Analyzes AST import completeness (`stdlib`, `declared_dependency`, `local_module`, `unresolved`), detects missing local modules, identifies unimplemented stubs (`raise NotImplementedError`, empty `pass`/`...` bodies, `TODO`/`FIXME`), identifies missing files referenced in README/configs/code, detects Python version requirements dynamically (without hardcoding `">=3.11"`), detects frameworks, missing data files, and distributed requirements.
    - **Refined GPU Logic (Fixes D5):** Unguarded `.cuda()` or `device="cuda"` or CUDA-only packages (`cupy`, `apex`, `flash-attn`, `bitsandbytes`, `triton`) produce blocker `NEEDS_GPU`; guarded device selections (`torch.cuda.is_available()`) produce warnings only.
    - **Data Refs Populated (Fixes D6):** Detects missing data references statically and populates `missing_data_refs`.
    - **Verdicts:** Accurately classifies into `FEASIBLE`, `FEASIBLE_WITH_PROVISIONING`, `NEEDS_GPU`, `NEEDS_LARGE_RESOURCES`, `INCOMPLETE_REPO`, `UNSUPPORTED_FORMAT`.
    - **API Route:** `POST /api/projects/{id}/triage` returns triage report and updates project state.
    - **UI:** Repo Triage card on the claims-confirmation screen with verdict badge, frameworks, stubs, and evidence excerpts; plus "Triage Only (Stop Here)" button.
    - **Benchmark Regression:** `b1`–`b4` remain unblocked on real Docker; `b5_unable` expected outcome regenerated and verified with blocker `NEEDS_GPU`.
    - **Gate Tests:** 12 unit tests in `tests/unit/test_stage3_triage.py` covering all fixture mini-repos, safety sentinel (proves zero code executed/imported), and API endpoint.
    - **Real Repos Evaluation:** `docs/triage_samples.md` records complete triage reports for 5 real repos (`karpathy/micrograd`, `karpathy/minGPT`, `lucidrains/denoising-diffusion-pytorch`, `fastai/numerical-linear-algebra`, `eriklindernoren/PyTorch-GAN`) with human evaluation notes.
    - Full test suite passes 118 tests.
  - *Status:* PASS

- [x] **Stage 4 (Completion Plan)**: Ops essentials (reliability)
  - *Branch:* `completion/stage-4`
  - *Gate Run Results:* PASS:
    - **Per-Project Worker Lock & Registry (D15):** Thread-safe worker registry `_RUNNING_WORKERS` with `_RUNNING_WORKERS_LOCK` prevents duplicate worker threads on concurrent start requests (`test_double_start_worker_prevention`).
    - **Optimistic Concurrency Locking (D15):** Added `version INTEGER DEFAULT 1` to `projects` table with automatic DB migration; `ConcurrentModificationError` raised on stale state updates (`test_optimistic_locking_version`).
    - **Per-Step Persistence & Resumption (D16):** `run_project` persists project state to SQLite after every loop step; stores runtime dependencies (`workspace`, `latest_log_path`, `silent_divergence`, `active_container_name`); verifies clean resumption mid-run without lost state (`test_per_step_persistence_and_resumption`).
    - **Abort Kills Worker & Active Container (D17):** POST `/api/projects/{id}/abort` halts running worker thread, sets `abort_requested=True`, marks state `DONE` with `status: INCONCLUSIVE`, and terminates/removes active and labeled Docker containers; verified with live Docker container execution and `docker ps` query (`test_stage4_docker_abort.py`, `test_abort_stops_worker_and_container`).
    - **Evidence Ledger Persistence (D12):** `record_evidence` appends to `data/runs/<id>/evidence.json` and writes to SQLite `evidence` table; exposed via `GET /api/projects/{id}/evidence` and `GET /api/projects/{id}/evidence/{eid}` (`test_evidence_persistence_and_retrieval`).
    - **Log Routes Contract Alignment (D13):** Aligned `/api/projects/{id}/runs/{n}/log` and frontend route `/api/projects/{id}/logs/{n}` returning `{"log": ...}` (`test_aligned_log_routes_contract`).
    - **Approval Edit Decision & Policy Re-evaluation (D14):** POST `/api/approvals/{id}` with `decision="edit"` applies edited changes in-memory, re-runs policy check and Critic review; rejects invalid or policy-violating edits with HTTP 400 and reason; applies valid edits and creates approval record (`test_approval_edit_policy_violation_rejected`, `test_approval_edit_valid_applied`).
    - **UX Polish:** Live elapsed session timer with status indicator in `Terminal.tsx`; `Last-Event-ID` persistence via `sessionStorage` in `useEventStream.ts` for reconnect stream replay; interactive JSON Edit Patch modal in `ApprovalModal.tsx`.
    - **FastAPI Lifespan (D25):** Migrated deprecated `@app.on_event("startup")` to `@asynccontextmanager` `lifespan` handler.
    - **Gate Tests:** 8/8 unit tests in `tests/unit/test_stage4_ops.py` passed; 1/1 integration test in `tests/integration/test_stage4_docker_abort.py` passed; full suite passes 127 tests; 3/3 security tests pass with Docker.
    - **Frontend Build:** `npm run build` succeeds cleanly in 1.02s with 0 errors.
  - *Status:* PASS

- [x] **Tier-1 Checkpoint (Completion Plan)**: Track A Evaluation on Real Docker
  - *Gate Run Results:* PASS:
    - **All 45 Real Docker Runs Completed ($5 \times 3 \times 3$):** Sweep across `b1`–`b5` × `{B-0, B-2, Rerun}` × 3 repeats executed on real Docker containers with image `rerun-base:py311` in offline mode.
    - **B-0 (Fixed Baseline):** 6/15 runs matched gold (40.0%). Passes `b1_control` and `b5_unable`; fails `b2_dependency` (crashed on missing PyYAML), `b3_silent_config` (unrepaired learning rate), `b4_combined` (crashed on missing PyYAML).
    - **B-2 (One-Shot LLM Baseline):** 12/15 runs matched gold (80.0%). Passes `b1_control`, `b2_dependency`, `b3_silent_config`, and `b5_unable`; **fails `b4_combined` (0/3)** because single-shot blind repair cannot handle multi-stage cascading failures (dependency failure followed by silent numerical calibration divergence).
    - **Rerun (Autonomous repair with Critic & Policy):** **15/15 runs matched gold (100.0%)**. Autonomously diagnoses root causes, proposes minimal verified patches, validates against policy P1–P10, secures critic review, applies repairs, and verifies reproducibility.
    - **Evidence Recorded:** Full CSV, JSON, and Markdown logs written to `benchmarks/results/20261008_172452/results.md` and committed to `benchmarks/MEASURED.md`.
  - *Status:* PASS

- [x] **Stage 5 (Completion Plan)**: Security hardening for untrusted repos (R9)
  - *Branch:* `completion/stage-5`
  - *Gate Run Results:* PASS:
    - **Defense-in-Depth Specification (`docs/SECURITY.md`):** Comprehensive document specifying threat model, invariants I1–I5, I8, clone safety, container hardening, prompt injection defense, and secrets management.
    - **Container Runtime Hardening & Bombs Contained:** Tested with Docker (`tests/security/test_hardening_and_bombs.py`, `tests/security/test_selftest.py`). Immutable root filesystem (`read_only=True`), non-root `uid 1000:1000`, `cap_drop=["ALL"]`, `security_opt=["no-new-privileges"]`, `network_mode="none"`. Disk bomb capped by tmpfs (`ENOSPC`), fork bomb capped by PIDs (`256`), memory bomb terminated by container OOM, infinite loop killed by timeout watchdog. Host completely unharmed.
    - **Prompt Injection Resistance:** Tested with `tests/security/test_prompt_injection.py`. System override attempts in README, papers, or logs cannot bypass deterministic Policy P1–P10 (rejected unauthorized files `.env`, `.sh`), cannot bypass line limits (P3), and cannot bypass mandatory human approval (Invariant I8).
    - **Secrets Hygiene:** `tests/security/test_secrets_and_deletion.py` verified that no unredacted API key patterns (`AIza*`, `AQ.*`, `sk-*`) exist across `data/runs/**`.
    - **Data Deletion API (`DELETE /api/projects/{id}`):** Purges project workspace, PDF, logs, outputs, wheelhouse from disk and deletes rows from SQLite `projects`, `events`, and `evidence` tables (`test_data_deletion_removes_workspace_and_db`).
    - **Concurrency Limits & Kill Switch:** Concurrency limit enforced (`MAX_CONCURRENT_PROJECTS=2`) with HTTP 429; `POST /api/admin/kill-switch` halts all running workers and kills labeled Docker containers globally (`test_admin_kill_switch`).
- [x] **Stage 6 (Completion Plan)**: Safe dependency provisioning (R3)
  - *Branch:* `completion/stage-6`
  - *Gate Run Results:* PASS:
    - **Fixture Repo Execution with Data Science Stack:** Fixture repo needing `scikit-learn`, `pandas`, `matplotlib` statically resolves, provisions wheels into per-project wheelhouse `data/runs/<id>/wheelhouse`, installs offline into `/workspace/.site`, and runs successfully (`test_fixture_repo_data_science_stack_installs_and_runs_offline`).
    - **Sdist-only Zero Execution Guard:** Repo requiring an sdist-only package triggers `NEEDS_BUILD` without executing any repository code (`test_sdist_only_dependency_triggers_needs_build_without_code_execution`). Proved repository `setup.py` was never invoked (`TRAP_TRIGGERED.txt` was not created).
    - **Offline Self-Test Invariant:** Execution container remains strictly offline (`network_mode="none"`) after provisioning; self-test confirms outbound socket and HTTP connections are hard-blocked (`test_self_test_after_provisioning_confirms_run_container_offline`).
    - **Evidence Ledger & Package Isolation:** Provisioning log `provisioning.log` is captured as immutable evidence (`E-###`) in SQLite `evidence` table and `data/runs/<id>/evidence/`; unapproved packages are strictly excluded from downloads and wheelhouse (`test_provisioning_log_evidence_and_unapproved_packages_never_downloaded`).
    - **Warnings & Intelligence:** Static resolution identifies typosquatting risks (e.g. `numppy`, `reqeusts`), flags CPU torch risks, and detects unpinned dependency drift versus the paper era (`test_typosquatting_and_dependency_drift_warnings`).
    - **Base Image Selection:** Accurately selects `rerun-base:py39|py310|py311|py312` based on triage report or `pyproject.toml` `requires-python` specification (`test_python_image_selection`).
    - **API & UI Wiring:** Added `GET /api/projects/{id}/provisioning/plan`, `POST /api/projects/{id}/provisioning/approve`, `POST /api/projects/{id}/provisioning/reject`, client methods, and pending action types.
    - **Test Suite Status:** 7/7 tests passing in `tests/unit/test_stage6_provisioning.py`; full suite passing 145/145 tests (`pytest tests -q`); frontend builds cleanly (`npm run build --prefix frontend`).
- [x] **Stage 7 (Completion Plan)**: Generic command + metric extraction (R4)
  - *Branch:* `completion/stage-7`
  - *Gate Run Results:* PASS:
    - **Command Validator & Runner Safety:** `validate_command()` enforces commands execute strictly as argv lists, never via `sh -c`. Rejects forbidden shell operators (pipes `|`, redirects `>`, `<`, `>>`, chaining `;`, `&&`, `||`, substitutions `$()`, backticks, backgrounding `&`, and multiline strings). Rejects unsupported runners (`make`, `torchrun`, `deepspeed`, `accelerate`, `jupyter`, `pytest`) with helpful diagnostic guidance. Verifies target script exists when workspace directory is present (`test_command_validator_rejects_injection_forms_table`).
    - **README Command Extraction (D7):** `extract_readme_commands()` cleanly strips `$ `, `# `, `> ` shell prompts, detects `python -m <module>` invocations, handles bash scripts and markdown code fences (`test_readme_command_extraction_handles_prompts_and_formats`).
    - **Deterministic Tolerance Advisor:** `recommend_tolerance()` calculates deterministic suggestions: uncertainty $a \pm s \to \max(s, \text{rounding})$; 2 decimals $\to \pm 0.005$; 1 decimal $\to \pm 0.05$; integers / defaults $\to$ suggested $\pm 1$ point ($0.01$ for fractions $\le 1.0$, else $1.0$) (`test_deterministic_tolerance_advisor`).
    - **Generic Metric Extraction Engine (D8):** `extract_metric()` supports `results.json` convention, arbitrary JSON files with nested dot notation, CSV files with column matching/aggregations, text files, and stdout/log regex with named capture groups `(?P<val>...)` and percentage normalization. On failure, returns `MetricExtractionResult(success=False, value=None)`, **NEVER** defaulting to 0 (`test_metric_extraction_fixture_stdout_regex`, `test_metric_extraction_fixture_csv`, `test_metric_extraction_fixture_custom_json_key`, `test_non_matching_regex_produces_inconclusive_never_zero`).
    - **Evidence Ledger Integration:** `record_metric_evidence()` snapshots extracted result files and log snippets into the immutable evidence ledger (`E-###`).
    - **Status & Confidence Factor Calibration:** Non-matching extractions yield `INCONCLUSIVE` (reason: `metric extraction failed`). Single-run results ($n=1$) record `variance: "n=1, variance unknown"` in `confidence_factors` (`test_single_run_records_variance_unknown_confidence_factor`).
    - **Configurable Timeout:** Added `run_timeout_s` (hard-capped at 1800s / 30m) with runtime override in `DockerSandbox`.
    - **Absence of Hardcoded Metrics:** Confirmed via codebase grep that `test_accuracy_mean` appears only in backward-compatible benchmark shims and documentation.
    - **Test Suite Status:** 8/8 tests passing in `tests/unit/test_stage7_commands_metrics.py`; full suite passing 153/153 tests (`pytest tests -q`); frontend builds cleanly (`npm run build --prefix frontend`).
  - *Status:* PASS — ready for Stage 8.

- [x] **Stage 8 (Completion Plan)**: Real-paper claim intake (R5)
  - *Branch:* `completion/stage-8`
  - *Gate Run Results:* PASS:
    - **Extraction Engine (`tools/paper.py`):** Layout-aware block sorting (`_sort_blocks_layout_aware`) preserves two-column reading order without interleaving paragraphs. Extracts native PyMuPDF markdown tables with `[pN:Tk]` identifiers (`_extract_tables`). Filters running headers and footers (`_clean_header_footer`).
    - **Deterministic Page Scoring & Prompt Capping:** Scores pages based on results, metrics (`accuracy`, `f1`, `bleu`, `auc`, `error rate`), hyperparameters, and table presence. Caps prompt context text to $\le 60\text{k}$ characters while preserving Page 1 (title/abstract) and top-scoring evidence/appendix pages in ascending order.
    - **Verbatim Quote Verification:** Normalizes Unicode ligatures (`ﬁ` $\to$ `fi`, `ﬂ` $\to$ `fl`), dashes, and whitespace; verifies substrings against paper prose and extracted tables; rejects hallucinated quotes (`test_hallucinated_quote_rejected_real_quote_accepted`).
    - **Hyperparameter Aliasing & Code Validation:** Maps paper keys (`learning_rate`, `batch_size`, `epochs`, etc.) to repo config keys via default aliases and LLM candidate proposals, validated statically against YAML, JSON, and AST `argparse.add_argument` definitions (`test_hyperparameter_alias_mapping_and_code_validation`).
    - **Defense-in-Depth & Injection Resistance:** Untrusted PDF text cannot alter execution policy P1–P10 or escalate permissions. Command validator strictly rejects execution via `-c` (`sh -c`, `bash -c`), and policy engine blocks unauthorized file access (`test_pdf_prompt_injection_does_not_change_policy_or_permissions`).
    - **Claim Picker & Human Selection:** Supports selecting 1–3 claims (`selected=True`), designating a single primary (`primary=True`), with unselected claims tracked for reporting under "not checked" (`test_claim_picker_selection_and_primary_assignment`).
    - **Evaluation on 3 Real Peer-Reviewed Papers (`docs/intake_eval.md`):** Tested across `Neural Networks Fail to Learn Periodic Functions.pdf` (NeurIPS 2020), `Learning to Deceive with Attention-Based Explanations.pdf` (ACL 2020), and `Hamiltonian Neural Network.pdf` (NeurIPS 2019). Discovered $\ge 8$ candidates per paper; achieved **100% (8/8) verbatim quote verification** across all 3 papers; verified true headline claim is captured in top 3 on all 3 papers (**3/3 passed vs $\ge 2/3$ gate target**).
    - **Test Suite Status:** 10/10 tests passing in `tests/unit/test_stage8_paper_intake.py`; full regression passing 163/163 tests (`pytest tests -q`); frontend builds cleanly (`npm run build --prefix frontend`).
  - *Status:* PASS — ready for Stage 9.

---

## Initial Build Stage Gates and Deliverables

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
- [x] **Stage 13**: Hardening & fallbacks — *Owner: Track B+D*
  - *Gate Run Results:* PASS (Multi-key Gemini API rotation engine `agent/key_rotator.py` implemented; task-boundary aware soft threshold at ~100 requests/key; emergency 429 failover with 60s cooldown; UTC daily quota reset; Invariant I4 secret scrubbing across all keys; `/api/keys/stats` diagnostic route; `tests/unit/test_key_rotator.py` passing with 9/9 tests; full suite passing 75 tests).
- [ ] **Stage 14**: Docs & demo kit — *Owner: All*

## Checkpoint Reports
*(Updated after Stages 3, 7, 10, 11, and 13)*

### After Stage 13 (Multi-Key Gemini API Rotation Engine Complete)
- **What works:**
  - **Task-Boundary-Aware Key Rotator (`agent/key_rotator.py`)**:
    - Manages multi-account API key pools (`GEMINI_API_KEYS` in `.env`).
    - Enforces soft rotation thresholds (`KEY_ROTATION_THRESHOLD`, default 100 requests) so key switching never occurs mid-task/mid-phase.
    - Preserves in-flight task continuity: keys that cross the threshold during an atomic phase continue until `end_task()`, after which the rotator cycles round-robin to the next account.
    - Automatic 429 rate limit failover: marks exhausted keys with a 60-second cooldown and retries instantly with the next available key.
    - Automated UTC midnight reset for daily request quotas.
    - Thread-safe singleton with persistent tracking in `data/key_stats.json`.
  - **Secret Scrubbing & Invariant I4 Protection**: All keys in the rotation pool and Gemini regex patterns are automatically registered and scrubbed (`[REDACTED_API_KEY]`) across all logs, tool outputs, and LLM diagnostics.
  - **API Key Diagnostic Route**: `/api/keys/stats` returns real-time key usage, active index, cooldown states, and masked key identifiers.
  - **Full Test Suite Validation**: 75 passed, 3 skipped (Docker), 0 failed.

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
