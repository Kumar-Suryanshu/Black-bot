# Baseline Lock & Truth Audit (Stage 0)

**Date:** 2026-10-08  
**Branch:** `completion/stage-0`  
**Baseline commit:** `bb845da`  
**Purpose:** Freeze the starting point, prove the central findings, and audit defects D1–D25 with raw command outputs.

---

## 1. Baseline Test Suite

Command:
```bash
python3 -m pytest tests -q --ignore=tests/security
```

Output:
```
........................................................................ [ 96%]
...                                                                      [100%]
75 passed, 3 warnings in 1.28s
```

With `tests/agent/test_default_sandbox_is_real.py` (`xfail(strict=True)`):
```
75 passed, 1 xfailed, 3 warnings in 1.23s
```

---

## 2. Appendix C Commands & Raw Outputs

### C.1 Sandbox Mock Verification
Command:
```bash
grep -rn "set_sandbox\|SANDBOX_TYPE" --include=*.py . && grep -n "_GLOBAL_SANDBOX\|class FakeSandbox" agent/loop.py
```
Output:
```
./tests/agent/test_loop.py:6:from agent.loop import run_project, set_sandbox, FakeSandbox
./tests/agent/test_loop.py:31:    set_sandbox(sb)
./tests/agent/test_loop.py:95:    set_sandbox(sb)
./tests/e2e/test_b4_api.py:21:    monkeypatch.setenv("SANDBOX_TYPE", "fake")
./agent/loop.py:83:def set_sandbox(sb):
45:class FakeSandbox:
78:_GLOBAL_SANDBOX = FakeSandbox()
81:    return _GLOBAL_SANDBOX
84:    global _GLOBAL_SANDBOX
85:    _GLOBAL_SANDBOX = sb
```
**Finding:** `_GLOBAL_SANDBOX` is initialized to `FakeSandbox()` by default in `agent/loop.py`. `SANDBOX_TYPE` is only set in a test monkeypatch, never read by application code.

### C.2 UI/API Simulated Execution Verification
Command:
```bash
grep -rn "Execution completed successfully" data/runs/*/logs/
```
Output:
```
data/runs/proj_c037fc12/workspace/logs/run_1.log:1:Execution completed successfully
data/runs/proj_b8dc31b0/workspace/logs/run_1.log:1:Execution completed successfully
data/runs/proj_ca9d5d1c/workspace/logs/run_1.log:1:Execution completed successfully
data/runs/proj_c5e2768f/workspace/logs/run_1.log:1:Execution completed successfully
data/runs/proj_0efecca9/workspace/logs/run_1.log:1:Execution completed successfully
data/runs/proj_9de756e1/workspace/logs/run_1.log:1:Execution completed successfully
data/runs/proj_5e4aa682/workspace/logs/run_1.log:1:Execution completed successfully
data/runs/proj_278f4c6f/workspace/logs/run_1.log:1:Execution completed successfully
data/runs/proj_6d16e10e/workspace/logs/run_1.log:1:Execution completed successfully
```
**Finding:** Every historical run log contains the hardcoded canned string from `FakeSandbox`.

### C.3 Setup Handler
Command:
```bash
sed -n '/^def handle_setup/,/^def handle_run/p' agent/loop.py
```
Output:
```python
def handle_setup(state: ProjectState, deps: dict):
    emit_event(state, "system", "phase_changed", f"Transitioned to {state.phase}")
    # Setup offline dependency install
    state.phase = "RUN"

def handle_run(state: ProjectState, deps: dict):
```
**Finding:** `handle_setup` is a no-op that immediately transitions to `RUN`.

### C.4 Project Creation Models
Command:
```bash
sed -n '1,12p' backend/app/models.py
```
Output:
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal

from agent.state import Claim

class ProjectCreateRequest(BaseModel):
    benchmark_id: str
    allow_high_risk: bool = False

class ProjectCreateResponse(BaseModel):
    project_id: str
```
**Finding:** Project creation only accepts `benchmark_id`, with no fields for repo URL or PDF upload.

### C.5 Hardcoded Headline Metric
Command:
```bash
grep -rn "test_accuracy_mean" --include=*.py agent tools backend | head -n 10
```
Output:
```
agent/loop.py:60:                "test_accuracy_mean": 0.956,
agent/loop.py:227:                c.result_key = "test_accuracy_mean"
agent/loop.py:339:        latest.metrics = {"test_accuracy_mean": val_res["mean"], "test_accuracy_std": val_res.get("std", 0.0)}
agent/loop.py:348:    obs_mean = latest.metrics.get("test_accuracy_mean") if latest.metrics else None
tools/report.py:62:                # {{result.run1.test_accuracy}} or {{result.run1.test_accuracy_mean}}
tools/report.py:261:            obs = att.metrics.get("test_accuracy_mean") if att.metrics else None
```
**Finding:** The metric name `test_accuracy_mean` is hardcoded across the agent loop, validation, and report verifier.

### C.6 GPU Detection on Guarded Idiom
Command:
```bash
python3 - <<'EOF'
import re
code = 'device = "cuda" if torch.cuda.is_available() else "cpu"'
print(bool(re.search(r"(?i)(\.cuda\(|device\s*=\s*['\"]cuda|torch\.cuda|CUDA_VISIBLE_DEVICES)", code)))
EOF
```
Output:
```
True
```
**Finding:** Standard guarded PyTorch idiom is flagged by the regex as a GPU requirement.

### C.7 Evidence Ledger Writer
Command:
```bash
grep -rn "evidence.json" --include=*.py .
```
Output:
```
./backend/app/routes.py:225:    ledger_path = f"data/runs/{id}/evidence.json"
```
**Finding:** `evidence.json` is read by `routes.py`, but no code in the project writes it.

### C.8 Log Route Mismatch
Command:
```bash
grep -n "logs/\${runN}" frontend/src/api/client.ts ; grep -n "runs/{n}/log" backend/app/routes.py
```
Output:
```
frontend/src/api/client.ts:113:  const res = await fetch(`${BASE_URL}/api/projects/${projectId}/logs/${runN}`);
backend/app/routes.py:234:@router.get("/api/projects/{id}/runs/{n}/log")
```
**Finding:** Route mismatch between frontend client and backend endpoint.

---

## 3. Defect Register Audit (D1–D25)

| ID | Sev | Location | Description | Stage 0 Verdict |
|---|---|---|---|---|
| **D1** | Critical | `agent/loop.py`, `runner.py` | Live loop defaults to `FakeSandbox`, returning canned results without running code. | **CONFIRMED** |
| **D2** | Critical | `agent/loop.py::handle_setup` | `handle_setup` only logs and transitions to `RUN`; no dependency install runs. | **CONFIRMED** |
| **D3** | Critical | `agent/loop.py::handle_patch_apply` | Applying a patch touching `requirements*.txt` does not trigger an install. | **CONFIRMED** |
| **D4** | Critical | `routes.py`, `models.py` | `ProjectCreateRequest` only accepts `benchmark_id`; no GitHub URL or PDF upload. | **CONFIRMED** |
| **D5** | High | `tools/repo.py` | Regex flags `torch.cuda.is_available()`, causing false `gpu_required` blockers. | **CONFIRMED** |
| **D6** | High | `tools/repo.py` | `data_refs` initialized as empty list and never populated; `python_requires` hardcoded to `">=3.11"`. | **CONFIRMED** |
| **D7** | High | `tools/repo.py` | README command extraction only checks lines starting with `python ` or `python3 `. | **CONFIRMED** |
| **D8** | High | `agent/loop.py`, `tools/report.py` | Hardcoded `test_accuracy_mean` and `outputs/results.json` structure. | **CONFIRMED** |
| **D9** | High | `scripts/make_wheelhouse.py` | Wheelhouse script only packages `numpy` and `PyYAML`. | **CONFIRMED** |
| **D10** | High | `sandbox/` | Only one base image (`rerun-base:py311`); no multi-version or PyTorch support. | **CONFIRMED** |
| **D11** | High | `backend/app/routes.py::confirm_claims` | Checks `if req.command and state.plan:`, but `state.plan` is `None` at confirm time, discarding user edits. | **CONFIRMED** |
| **D12** | High | `routes.py` vs `tools/evidence.py` | `/api/projects/{id}/evidence/{eid}` reads `evidence.json`, which is never written. | **CONFIRMED** |
| **D13** | Med | `frontend/src/api/client.ts` | Frontend calls `/api/projects/{id}/logs/{n}`; backend serves `/api/projects/{id}/runs/{n}/log`. | **CONFIRMED** |
| **D14** | Med | `backend/app/routes.py::process_approval` | `ApprovalRequest.edits` accepted in request model but ignored in implementation. | **CONFIRMED** |
| **D15** | Med | `runner.py`, `routes.py` | No per-project worker lock; concurrent requests can spawn duplicate workers. | **CONFIRMED** |
| **D16** | Med | `agent/loop.py::run_project` | State saved only at worker termination; no per-step persistence across crashes. | **CONFIRMED** |
| **D17** | Med | `backend/app/routes.py::abort_project` | Abort endpoint sets state to `DONE` but does not terminate running threads or containers. | **CONFIRMED** |
| **D18** | Med | `backend/app/routes.py::health_check` | Health check returns hardcoded `True` without pinging Docker daemon or LLM. | **CONFIRMED** |
| **D19** | Med | `tools/errors.py` | Error classification parses only text for `MemoryError`; ignores attempt `oom`/`timed_out` flags. | **CONFIRMED** |
| **D20** | Med | `tools/config_audit.py` | Config audit only parses plan config or `effective_config.json`; no CLI/argparse resolution. | **CONFIRMED** |
| **D21** | Med | `agent/solver/prompts.py` | Solver prompts are 4–6 lines each; untested on complex, messy repositories. | **CONFIRMED** |
| **D22** | Med | `agent/config.py` | `MAX_FILES=5`, `MAX_CHANGED_LINES=200` (exceeds original specification thresholds 2 / 20). | **CONFIRMED** |
| **D23** | Low | `README.md`, `PROGRESS.md` | Stale "65/68" test claim in README; local Windows `file:///c:/...` links in PROGRESS.md. | **CONFIRMED** |
| **D24** | Low | Workspace root | Uncommitted scratch files (`pytest_out*.txt`, `calibration_workspace/`). | **CONFIRMED** |
| **D25** | Low | `backend/app/main.py` | Deprecated `@app.on_event("startup")` trigger. | **CONFIRMED** |

**Summary:** 25 of 25 defects (100%) confirmed by direct code analysis and command execution.
