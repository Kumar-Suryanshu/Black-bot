import os
import json
import time
import shutil
import difflib
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from agent.state import (
    ProjectState, Claim, PaperSetting, Plan, Attempt,
    Hypothesis, PatchProposal, Edit, Approval, CriticReview
)
from agent.config import (
    MAX_STEPS, MAX_PATCHES, CRITIC_ROUNDS_MAX,
    DIAGNOSE_STEPS_MAX, RUN_TIMEOUT_S, INSTALL_TIMEOUT_S
)
from agent.events import emit_event
from agent.llm import call as llm_call
from agent.key_rotator import key_rotator
from agent.solver.schemas import (
    ExtractClaimsOutput, PlanExperimentOutput, DiagnoseStepOutput,
    ProposePatchOutput, WriteReportOutput
)
from agent.solver.prompts import (
    EXTRACT_CLAIMS_PROMPT, PLAN_EXPERIMENT_PROMPT,
    DIAGNOSE_STEP_PROMPT, PROPOSE_PATCH_PROMPT, WRITE_REPORT_PROMPT
)
from agent.critic.review import review_patch
from agent.arbiter import decide_patch
from tools.policy import check as check_policy, compute_fix_signature
from tools.patch import apply_edits_in_memory, make_diff, apply_patch, revert_patch
from tools.compare import compare
from tools.status import compute_status
from tools.errors import classify as classify_error
from tools.config_audit import audit as audit_config
from tools.results import validate_results, load_results
from tools.evidence import record_evidence
from tools.repo import inspect_repository
from tools.paper import extract_text, verify_quote as verify_paper_quote
from tools.preflight import preflight_check
from tools.exec_tools import query_package_index
from tools.report import generate_report
from agent.critic.schemas import ReportReviewOutput

# Re-export FakeSandbox for backward compatibility with existing tests
from sandbox.fake import FakeSandbox

_OVERRIDE_SANDBOX = None

def get_sandbox():
    """Returns the active sandbox: DockerSandbox by default, or FakeSandbox if SANDBOX_TYPE=fake."""
    global _OVERRIDE_SANDBOX
    if _OVERRIDE_SANDBOX is not None:
        return _OVERRIDE_SANDBOX
        
    sandbox_type = os.getenv("SANDBOX_TYPE", "docker")
    if sandbox_type == "fake":
        from sandbox.fake import FakeSandbox
        _OVERRIDE_SANDBOX = FakeSandbox()
        return _OVERRIDE_SANDBOX
    from sandbox.docker_sandbox import DockerSandbox
    return DockerSandbox()

def set_sandbox(sb):
    """Override the active sandbox instance (used by test fixtures)."""
    global _OVERRIDE_SANDBOX
    _OVERRIDE_SANDBOX = sb

def guard_budgets(state: ProjectState) -> bool:
    if state.phase in ("STATUS", "REPORT", "REPORT_REVIEW", "DONE"):
        return False
        
    steps_used = state.budgets.get("steps_used", 0)
    max_steps = state.budgets.get("max_steps", MAX_STEPS)
    patches_applied = len([p for p in state.patches if p.status == "applied"])
    
    # Check 80% warning
    if steps_used >= int(max_steps * 0.8) and not state.budgets.get("warned_80", False):
        state.budgets["warned_80"] = True
        emit_event(state, "system", "budget_warning", f"Budget warning: {steps_used}/{max_steps} steps used (80%)")

    if steps_used >= max_steps:
        if "budget exhausted: steps limit reached" not in state.unresolved_issues:
            state.unresolved_issues.append("budget exhausted: steps limit reached")
        state.phase = "STATUS"
        return True

    if patches_applied >= MAX_PATCHES:
        if "budget exhausted: max patches applied" not in state.unresolved_issues:
            state.unresolved_issues.append("budget exhausted: max patches applied")
        state.phase = "STATUS"
        return True

    return False

# ----------------- PHASE HANDLERS -----------------

def handle_ingest(state: ProjectState, deps: dict):
    emit_event(state, "system", "phase_changed", f"Transitioned to {state.phase}")
    ws_path = state.workspace or deps.get("workspace", f"data/runs/{state.project_id}/workspace")
    state.workspace = ws_path
    deps["workspace"] = ws_path
    os.makedirs(ws_path, exist_ok=True)

    if state.source == "custom":
        if not any(Path(ws_path).iterdir()) and state.repo_url:
            from tools.ingest import ingest_custom_repo
            ingest_res = ingest_custom_repo(state.repo_url, state.repo_ref, ws_path)
            state.repo_commit = ingest_res.get("commit_sha", state.repo_commit)
    else:
        registry_path = deps.get("registry_path", "benchmarks/registry.json")
        if not os.path.exists(registry_path):
            state.phase = "DONE"
            state.final = {"status": "UNABLE_TO_EXECUTE", "reason": "Registry not found"}
            return

        with open(registry_path, "r", encoding="utf-8") as f:
            reg = json.load(f)

        case_info = next((c for c in reg.get("cases", []) if c["id"] == state.benchmark_id), None)
        if not case_info:
            state.phase = "DONE"
            state.final = {"status": "UNABLE_TO_EXECUTE", "reason": f"Benchmark {state.benchmark_id} not allow-listed"}
            return

        repo_src = case_info.get("repo_path")
        if repo_src:
            repo_src = repo_src.replace("\\","/")
        if repo_src and os.path.exists(repo_src):
            for item in Path(repo_src).iterdir():
                dest = Path(ws_path) / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)

        state.paper_path = case_info.get("paper_path")
        deps["paper_path"] = state.paper_path

    state.phase = "ANALYZE"

def handle_analyze(state: ProjectState, deps: dict):
    emit_event(state, "system", "phase_changed", f"Transitioned to {state.phase}")
    ws = deps.get("workspace", f"data/runs/{state.project_id}/workspace")
    state.repo_profile = inspect_repository(ws)
    
    paper_path = state.paper_path or deps.get("paper_path", "benchmarks/papers/digits_softmax.pdf")
    paper_text_data = extract_text(paper_path) if paper_path and os.path.exists(paper_path) else {"full_text": "", "marked_text": ""}
    
    # Solver extract_claims
    try:
        out = llm_call(
            "solver", "extract_claims",
            {"paper_text": paper_text_data["marked_text"]},
            ExtractClaimsOutput,
            benchmark_id=state.benchmark_id
        )
        # Filter quotes against full paper text
        verified_claims = []
        for idx, c in enumerate(out.claims):
            c.id = f"C-{idx + 1}"
            if verify_paper_quote(paper_text_data["full_text"], c.source_quote):
                c.primary = True
                verified_claims.append(c)
            else:
                state.unresolved_issues.append(f"Claim {c.id} quote not found in paper text")
        state.claims = verified_claims

        verified_settings = []
        for ps in out.paper_settings:
            if verify_paper_quote(paper_text_data["full_text"], ps.source_quote):
                verified_settings.append(ps)
        state.paper_settings = verified_settings
    except Exception as e:
        emit_event(state, "solver", "error", f"Claim extraction failed: {str(e)}")

    state.phase = "CLAIMS_CONFIRM"
    state.pending = {"kind": "claims", "id": "confirm_claims"}

def handle_claims_confirm(state: ProjectState, deps: dict):
    if not state.command_confirmed:
        # Paused waiting for human confirm
        state.pending = {"kind": "claims", "id": "confirm_claims"}
        return

    # Check confirmed claims
    confirmed = [c for c in state.claims if c.confirmed_by_human]
    if not confirmed:
        state.phase = "DONE"
        state.final = {"status": "INCONCLUSIVE", "reason": "no claim confirmed", "after_n_fixes": 0}
        state.pending = None
        return

    state.pending = None
    state.phase = "PLAN"

def handle_plan(state: ProjectState, deps: dict):
    emit_event(state, "system", "phase_changed", f"Transitioned to {state.phase}")
    try:
        plan_out = llm_call(
            "solver", "plan_experiment",
            {"claims": [c.model_dump() for c in state.claims], "repo_profile": state.repo_profile},
            PlanExperimentOutput,
            benchmark_id=state.benchmark_id
        )
        state.plan = Plan(
            command=plan_out.command,
            config_file=plan_out.config_file,
            output_file=plan_out.output_file,
            effective_config_file=plan_out.effective_config_file,
            seeds=plan_out.seeds,
            notes=plan_out.notes
        )
        # Wire claim result_key
        for c in state.claims:
            if c.id in plan_out.claim_result_keys:
                c.result_key = plan_out.claim_result_keys[c.id]
            elif not c.result_key:
                c.result_key = "test_accuracy_mean"
    except Exception as e:
        emit_event(state, "solver", "error", f"Planning failed: {str(e)}")
        state.plan = Plan(
            command="python train.py --config configs/default.yaml",
            config_file="configs/default.yaml",
            output_file="outputs/results.json",
            effective_config_file="outputs/effective_config.json",
            seeds=[0, 1, 2, 3, 4]
        )

    # Honor user-edited command confirmed at claims-confirm (Fix D11)
    if state.user_command and state.user_command.strip():
        state.plan.command = state.user_command.strip()
        emit_event(state, "human", "command_customized", f"Honored user-customized command: {state.plan.command}")

    state.phase = "PREFLIGHT"

def handle_preflight(state: ProjectState, deps: dict):
    emit_event(state, "system", "phase_changed", f"Transitioned to {state.phase}")
    ws = deps.get("workspace", f"data/runs/{state.project_id}/workspace")
    res = preflight_check(ws, state.repo_profile, gpu_enabled=False, gpu_usable=False)
    state.preflight = res
    if res["blockers"]:
        # Record blocker evidence
        state.phase = "STATUS"
    else:
        state.phase = "SETUP"

def handle_setup(state: ProjectState, deps: dict):
    emit_event(state, "system", "phase_changed", f"Transitioned to {state.phase}")
    ws = deps.get("workspace", f"data/runs/{state.project_id}/workspace")
    sb = deps.get("sandbox", get_sandbox())
    
    req_file = Path(ws) / "requirements.txt"
    if req_file.exists():
        exit_code, log_path, res = sb.install(state, ws, len(state.attempts) + 1)
        if log_path:
            deps["latest_log_path"] = log_path
            state.latest_log_path = log_path
        if exit_code != 0:
            emit_event(state, "system", "setup_failed", f"Setup dependency install failed with exit code {exit_code}")
            att = Attempt(
                n=len(state.attempts) + 1,
                patches_applied=[p.id for p in state.patches if p.status == "applied"],
                exit_code=exit_code,
                started_at=time.ctime(),
                ended_at=time.ctime(),
                duration_s=getattr(res, "duration_s", 0.0),
                timed_out=getattr(res, "timed_out", False),
                oom=getattr(res, "oom", False)
            )
            state.attempts.append(att)
            state.phase = "OBSERVE"
            return
            
    state.phase = "RUN"

def handle_run(state: ProjectState, deps: dict):
    emit_event(state, "system", "phase_changed", f"Transitioned to {state.phase}")
    ws = deps.get("workspace", f"data/runs/{state.project_id}/workspace")
    sb = deps.get("sandbox", get_sandbox())
    
    n = len(state.attempts) + 1
    t0 = time.time()
    cmd = state.plan.command if state.plan else "python train.py"
    
    res = sb.execute(state, ws, cmd, "run", n)
    if hasattr(res, "exit_code"):
        exit_code = res.exit_code
        log_path = res.log_path
        out_dir = res.output_dir
        duration = getattr(res, "duration_s", time.time() - t0)
        timed_out = getattr(res, "timed_out", False)
        oom = getattr(res, "oom", False)
    elif isinstance(res, tuple):
        exit_code, log_path, out_dir = res[:3]
        duration = time.time() - t0
        timed_out = False
        oom = False
    else:
        exit_code, log_path, out_dir = 0, "", ""
        duration = time.time() - t0
        timed_out = False
        oom = False
    deps["latest_log_path"] = log_path
    state.latest_log_path = log_path
    
    att = Attempt(
        n=n,
        patches_applied=[p.id for p in state.patches if p.status == "applied"],
        exit_code=exit_code,
        started_at=time.ctime(t0),
        ended_at=time.ctime(),
        duration_s=duration,
        timed_out=timed_out,
        oom=oom
    )
    state.attempts.append(att)
    state.phase = "OBSERVE"

def handle_observe(state: ProjectState, deps: dict):
    emit_event(state, "system", "phase_changed", f"Transitioned to {state.phase}")
    latest = state.attempts[-1]
    ws = deps.get("workspace", f"data/runs/{state.project_id}/workspace")
    log_candidates = [
        Path(deps.get("latest_log_path", "")),
        Path("data/runs") / state.project_id / "logs" / f"run_{latest.n}.log",
        Path(ws) / "logs" / f"run_{latest.n}.log"
    ]
    log_text = ""
    for lc in log_candidates:
        if lc and lc.is_file():
            try:
                log_text = lc.read_text(encoding="utf-8")
                break
            except Exception:
                pass
    
    # Classify errors if crashed
    if latest.exit_code != 0:
        err_info = classify_error(log_text)
        latest.error_class = err_info["error_class"]
        state.phase = "DIAGNOSE"
    else:
        res_file = Path(ws) / "outputs" / "results.json"
        if not res_file.exists():
            state.phase = "DIAGNOSE"
        else:
            state.phase = "VALIDATE"

def handle_validate(state: ProjectState, deps: dict):
    emit_event(state, "system", "phase_changed", f"Transitioned to {state.phase}")
    ws = deps.get("workspace", f"data/runs/{state.project_id}/workspace")
    res_file = Path(ws) / "outputs" / "results.json"
    data = load_results(str(res_file))
    
    claim = state.claims[0] if state.claims else None
    val_res = validate_results(data, state.plan, claim)
    
    latest = state.attempts[-1]
    if val_res["valid"]:
        latest.metrics = {"test_accuracy_mean": val_res["mean"], "test_accuracy_std": val_res.get("std", 0.0)}
        state.phase = "COMPARE"
    else:
        latest.error_class = "numerical_invalid"
        state.phase = "DIAGNOSE"

def handle_compare(state: ProjectState, deps: dict):
    emit_event(state, "system", "phase_changed", f"Transitioned to {state.phase}")
    latest = state.attempts[-1]
    obs_mean = latest.metrics.get("test_accuracy_mean") if latest.metrics else None
    
    comparisons = []
    all_within = True
    for c in state.claims:
        res = compare(c, obs_mean)
        comparisons.append(res)
        if not res.get("within_tolerance"):
            all_within = False
            
    latest.comparison = comparisons
    if all_within:
        state.phase = "STATUS"
    else:
        deps["silent_divergence"] = True
        state.silent_divergence = True
        state.phase = "DIAGNOSE"

def handle_diagnose(state: ProjectState, deps: dict):
    emit_event(state, "system", "phase_changed", f"Transitioned to {state.phase}")
    ws = deps.get("workspace", f"data/runs/{state.project_id}/workspace")
    state.budgets["steps_used"] = state.budgets.get("steps_used", 0) + 1
    
    # Safety net nudge for silent divergence
    step_num = state.budgets["steps_used"]
    silent_div = deps.get("silent_divergence", False)
    if silent_div and step_num >= 3 and not state.config_diff:
        state.config_diff = audit_config(ws, state.plan, state.paper_settings)
        emit_event(state, "system", "orchestrator_forced", "Safety-net nudge: auto-ran compare_configuration")

    # Mode diagnose_step
    try:
        diag_out = llm_call(
            "solver", "diagnose_step",
            {
                "state_summary": f"Step {step_num}, silent_divergence={silent_div}",
                "observation": "See latest run results/logs",
                "allowed_tools": [
                    {"name": "inspect_file"},
                    {"name": "search_repository"},
                    {"name": "inspect_repository"},
                    {"name": "read_logs"},
                    {"name": "inspect_error"},
                    {"name": "query_package_index"},
                    {"name": "compare_configuration"},
                    {"name": "run_command"},
                    {"name": "propose_patch"},
                    {"name": "conclude_no_cause"}
                ]
            },
            DiagnoseStepOutput,
            benchmark_id=state.benchmark_id
        )
        
        # §7.3: Updates hypotheses only if every evidence ID exists in the ledger
        all_eids_valid = True
        for h in diag_out.hypotheses:
            for eid in h.evidence:
                if eid not in state.evidence_ids:
                    all_eids_valid = False
                    emit_event(state, "solver", "warning", f"Hypothesis {h.id} cited unrecorded evidence {eid}; rejected update")
                    break
            if not all_eids_valid:
                break
        if all_eids_valid:
            state.hypotheses = diag_out.hypotheses

        action_tool = diag_out.next_action.tool
        action_args = diag_out.next_action.args or {}

        if action_tool == "propose_patch":
            has_confirmed = any(h.status == "confirmed" and len(h.evidence) >= 1 for h in state.hypotheses)
            if has_confirmed:
                state.phase = "PATCH_PROPOSE"
            else:
                emit_event(state, "solver", "error", "propose_patch rejected: no confirmed hypothesis with >= 1 evidence ID")
                if step_num >= DIAGNOSE_STEPS_MAX:
                    state.phase = "STATUS"
        elif action_tool == "conclude_no_cause":
            state.phase = "STATUS"
        elif action_tool == "compare_configuration":
            state.config_diff = audit_config(ws, state.plan, state.paper_settings)
            emit_event(state, "tool", "tool_finished", "Executed compare_configuration")
        elif action_tool == "read_logs":
            log_candidates = [
                Path(deps.get("latest_log_path", "")),
                Path("data/runs") / state.project_id / "logs" / f"run_{len(state.attempts)}.log",
                Path(ws) / "logs" / f"run_{len(state.attempts)}.log"
            ]
            found = next((lc for lc in log_candidates if lc and lc.is_file()), None)
            if found:
                ev = record_evidence(state, "log", str(found), action_args.get("line_start"), action_args.get("line_end"), "read_logs", f"diag_step_{step_num}")
                emit_event(state, "tool", "evidence_recorded", "Read logs", evidence_ids=[ev.id])
            else:
                emit_event(state, "solver", "error", "No log file found")
            if step_num >= DIAGNOSE_STEPS_MAX:
                state.phase = "STATUS"
        elif action_tool == "inspect_error":
            log_candidates = [
                Path(deps.get("latest_log_path", "")),
                Path("data/runs") / state.project_id / "logs" / f"run_{len(state.attempts)}.log",
                Path(ws) / "logs" / f"run_{len(state.attempts)}.log"
            ]
            found = next((lc for lc in log_candidates if lc and lc.is_file()), None)
            if found:
                ev = record_evidence(state, "log", str(found), None, None, "inspect_error", f"diag_step_{step_num}")
                emit_event(state, "tool", "evidence_recorded", "Inspected error in logs", evidence_ids=[ev.id])
            else:
                emit_event(state, "solver", "error", "No log file found")
            if step_num >= DIAGNOSE_STEPS_MAX:
                state.phase = "STATUS"
        elif action_tool == "run_command":
            cmd = action_args.get("command", "")
            if not cmd:
                emit_event(state, "solver", "error", "run_command requires 'command'")
            else:
                cmd_trim = cmd.strip()
                if cmd_trim.startswith("pip list") or cmd_trim.startswith("pip show") or cmd_trim.startswith("python -c") or cmd_trim.startswith("ls") or cmd_trim.startswith("cat"):
                    sb = deps.get("sandbox", get_sandbox())
                    res = sb.execute(state, ws, cmd, "investigate", step_num)
                    log_p = res.log_path if hasattr(res, "log_path") else (res[1] if isinstance(res, tuple) else "")
                    if log_p and Path(log_p).is_file():
                        ev = record_evidence(state, "log", log_p, None, None, "run_command", f"diag_step_{step_num}")
                        emit_event(state, "tool", "evidence_recorded", f"Ran {cmd}", evidence_ids=[ev.id])
                    else:
                        emit_event(state, "tool", "tool_finished", f"Ran {cmd} but no log produced")
                else:
                    emit_event(state, "solver", "error", f"Command not allowed: {cmd}")
            if step_num >= DIAGNOSE_STEPS_MAX:
                state.phase = "STATUS"
        elif action_tool == "inspect_file":
            fpath = action_args.get("file") or action_args.get("path")
            if fpath:
                target = (Path(ws) / fpath).resolve()
                ws_resolved = Path(ws).resolve()
                if ws_resolved in target.parents or target == ws_resolved:
                    if target.is_file():
                        ev = record_evidence(
                            state, "file", str(target),
                            action_args.get("line_start"),
                            action_args.get("line_end"),
                            "inspect_file",
                            f"diag_step_{step_num}"
                        )
                        emit_event(state, "tool", "evidence_recorded", f"Inspected {fpath}", evidence_ids=[ev.id])
            if step_num >= DIAGNOSE_STEPS_MAX:
                state.phase = "STATUS"
        elif action_tool == "search_repository":
            q = action_args.get("query", "")
            matches = []
            if q:
                for f in Path(ws).rglob("*"):
                    if f.is_file() and not any(p in str(f) for p in [".git", "__pycache__", ".site"]):
                        try:
                            txt = f.read_text(encoding="utf-8", errors="ignore")
                            if q in txt:
                                matches.append(str(f.relative_to(ws)))
                        except Exception:
                            pass
            emit_event(state, "tool", "tool_finished", f"search_repository found {len(matches)} matches")
            if step_num >= DIAGNOSE_STEPS_MAX:
                state.phase = "STATUS"
        elif action_tool == "inspect_repository":
            state.repo_profile = inspect_repository(ws)
            emit_event(state, "tool", "tool_finished", "inspect_repository executed")
            if step_num >= DIAGNOSE_STEPS_MAX:
                state.phase = "STATUS"
        elif action_tool == "query_package_index":
            pkg = action_args.get("package") or action_args.get("name") or ""
            vers = query_package_index(pkg) if pkg else []
            emit_event(state, "tool", "tool_finished", f"query_package_index found {vers}")
            if step_num >= DIAGNOSE_STEPS_MAX:
                state.phase = "STATUS"
        else:
            if step_num >= DIAGNOSE_STEPS_MAX:
                state.phase = "STATUS"
    except Exception as e:
        emit_event(state, "solver", "error", f"Diagnose failed: {str(e)}")
        state.phase = "STATUS"

def handle_patch_propose(state: ProjectState, deps: dict):
    emit_event(state, "system", "phase_changed", f"Transitioned to {state.phase}")
    ws = deps.get("workspace", f"data/runs/{state.project_id}/workspace")
    
    try:
        patch_out = llm_call(
            "solver", "propose_patch",
            {
                "hypothesis": state.hypotheses[-1].model_dump() if state.hypotheses else {},
                "paper_settings": [ps.model_dump() for ps in state.paper_settings],
                "failed_fixes": state.failed_fixes
            },
            ProposePatchOutput,
            benchmark_id=state.benchmark_id
        )
        
        if not patch_out.edits:
            emit_event(state, "solver", "error", "Patch proposal contained no edits")
            regen_count = state.budgets.get("patch_regenerations", 0)
            if regen_count < 2:
                state.budgets["patch_regenerations"] = regen_count + 1
                state.phase = "PATCH_PROPOSE"
            else:
                state.budgets["patch_regenerations"] = 0
                state.phase = "DIAGNOSE"
            return
            
        # Build diff in-memory
        new_texts = apply_edits_in_memory(ws, patch_out.edits)
        diff_str = make_diff(ws, new_texts)
        
        # Compute signature
        sig = compute_fix_signature(patch_out.edits[0].file, patch_out.edits[0].op, patch_out.edits[0].new)
        
        proposal = PatchProposal(
            id=f"P-{len(state.patches) + 1}",
            hypothesis_id=patch_out.hypothesis_id,
            type=patch_out.type,
            rationale=patch_out.rationale,
            evidence=patch_out.evidence,
            alternatives_considered=patch_out.alternatives_considered,
            edits=patch_out.edits,
            diff=diff_str,
            fix_signature=sig
        )
        state.patches.append(proposal)
        state.phase = "POLICY_CHECK"
    except Exception as e:
        emit_event(state, "solver", "error", f"Patch proposal failed: {str(e)}")
        regen_count = state.budgets.get("patch_regenerations", 0)
        if regen_count < 2:
            state.budgets["patch_regenerations"] = regen_count + 1
            state.phase = "PATCH_PROPOSE"
        else:
            state.budgets["patch_regenerations"] = 0
            state.phase = "DIAGNOSE"

def handle_policy_check(state: ProjectState, deps: dict):
    emit_event(state, "system", "phase_changed", f"Transitioned to {state.phase}")
    patch = state.patches[-1]
    ws = deps.get("workspace", f"data/runs/{state.project_id}/workspace")
    
    pol_res = check_policy(state, patch, ws)
    patch.policy_result = pol_res
    patch.risk_class = pol_res["risk_class"]
    
    if not pol_res["passed"]:
        patch.status = "rejected"
        state.failed_fixes.append(patch.fix_signature)
        regen_count = state.budgets.get("patch_regenerations", 0)
        if regen_count < 2:
            state.budgets["patch_regenerations"] = regen_count + 1
            state.phase = "PATCH_PROPOSE"
        else:
            state.budgets["patch_regenerations"] = 0
            for v in pol_res.get("violations", []):
                if "sensitive_key_locked" in v:
                    state.unresolved_issues.append("config mismatch on guarded key not patched (policy)")
            state.phase = "DIAGNOSE"
    else:
        state.budgets["patch_regenerations"] = 0
        state.phase = "CRITIC_REVIEW"

def handle_critic_review(state: ProjectState, deps: dict):
    emit_event(state, "system", "phase_changed", f"Transitioned to {state.phase}")
    patch = state.patches[-1]
    round_num = len([r for r in state.critic_reviews if r.patch_id == patch.id]) + 1
    
    review = review_patch(state, patch, round_num=round_num)
    state.critic_reviews.append(review)
    patch.critic_status = review.verdict.lower()
    
    decision = decide_patch(patch.policy_result, review, round_num, CRITIC_ROUNDS_MAX)
    
    if decision.action == "DROP":
        patch.status = "dropped"
        state.failed_fixes.append(patch.fix_signature)
        state.phase = "DIAGNOSE"
    elif decision.action == "REVISE":
        state.phase = "PATCH_PROPOSE"
    elif decision.action == "TO_HUMAN":
        app_id = f"A-{len(state.approvals) + 1}"
        state.pending = {"kind": "approval", "id": app_id, "patch_id": patch.id, "banner": decision.banner}
        state.phase = "APPROVAL"

def handle_approval(state: ProjectState, deps: dict):
    patch = state.patches[-1]
    # Check if approved
    matching_app = next((a for a in state.approvals if a.patch_id == patch.id), None)
    if not matching_app:
        # Still paused for human
        return
        
    state.pending = None
    if matching_app.decision in ("approve", "edit"):
        state.phase = "PATCH_APPLY"
    else:
        patch.status = "rejected"
        state.failed_fixes.append(patch.fix_signature)
        state.phase = "DIAGNOSE"

def handle_patch_apply(state: ProjectState, deps: dict):
    emit_event(state, "system", "phase_changed", f"Transitioned to {state.phase}")
    patch = state.patches[-1]
    ws = deps.get("workspace", f"data/runs/{state.project_id}/workspace")
    sb = deps.get("sandbox", get_sandbox())
    
    success = apply_patch(state, patch, ws)
    if success:
        emit_event(state, "system", "patch_applied", f"Patch {patch.id} applied successfully")
        
        # Check if patch touched requirements*.txt or dependency files
        touched_deps = False
        if hasattr(patch, "edits") and patch.edits:
            for ed in patch.edits:
                filename = getattr(ed, "file", "")
                if "requirements" in filename or filename.endswith((".txt", "setup.py", "pyproject.toml")):
                    touched_deps = True
                    break
                    
        if touched_deps:
            emit_event(state, "system", "install_triggered", "Patch touched dependency files; running install")
            install_exit, install_log, install_res = sb.install(state, ws, len(state.attempts) + 1)
            if install_log:
                deps["latest_log_path"] = install_log
                state.latest_log_path = install_log
            if install_exit != 0:
                emit_event(state, "system", "install_failed", f"Install failed with exit code {install_exit}")
                att = Attempt(
                    n=len(state.attempts) + 1,
                    patches_applied=[p.id for p in state.patches if p.status == "applied"],
                    exit_code=install_exit,
                    started_at=time.ctime(),
                    ended_at=time.ctime(),
                    duration_s=getattr(install_res, "duration_s", 0.0),
                    timed_out=getattr(install_res, "timed_out", False),
                    oom=getattr(install_res, "oom", False)
                )
                state.attempts.append(att)
                state.phase = "OBSERVE"
                return

        state.phase = "RUN"
    else:
        patch.status = "reverted"
        state.failed_fixes.append(patch.fix_signature)
        state.phase = "DIAGNOSE"

def handle_status(state: ProjectState, deps: dict):
    emit_event(state, "system", "phase_changed", f"Transitioned to {state.phase}")
    status_res = compute_status(state)
    state.final = status_res
    state.phase = "REPORT"

def handle_report(state: ProjectState, deps: dict):
    emit_event(state, "system", "phase_changed", f"Transitioned to {state.phase}")
    raw_statements = []
    try:
        rep_out = llm_call(
            "solver", "write_report",
            {
                "final_status": state.final,
                "claims": [c.model_dump() for c in state.claims],
                "patches": [p.model_dump() for p in state.patches],
                "unresolved_issues": state.unresolved_issues
            },
            WriteReportOutput,
            benchmark_id=state.benchmark_id
        )
        if rep_out and hasattr(rep_out, "statements"):
            raw_statements = rep_out.statements
            deps["report_statements"] = [s.model_dump() if hasattr(s, "model_dump") else s for s in rep_out.statements]
    except Exception as e:
        emit_event(state, "solver", "warning", f"Write report skipped or failed: {str(e)}")

    # Deterministic report generation & verification
    report_data = generate_report(state, raw_statements=raw_statements)
    if state.final is None:
        state.final = {}
    state.final["report"] = report_data
    deps["report"] = report_data
    emit_event(
        state, "solver", "report_ready",
        f"Generated report: {report_data['verification_summary']['summary_text']}",
        payload={"verification": report_data["verification_summary"]}
    )

    state.phase = "REPORT_REVIEW"

def handle_report_review(state: ProjectState, deps: dict):
    emit_event(state, "system", "phase_changed", f"Transitioned to {state.phase}")
    # Optional Critic review of statements (§12.5)
    raw_stmts = deps.get("report_statements", [])
    if raw_stmts:
        try:
            rev_out = llm_call(
                "critic", "report_review",
                {"statements": raw_stmts},
                ReportReviewOutput,
                benchmark_id=state.benchmark_id
            )
            if rev_out and hasattr(rev_out, "flags") and state.final and "report" in state.final:
                state.final["report"]["critic_flags"] = [f.model_dump() for f in rev_out.flags]
                emit_event(state, "critic", "report_reviewed", f"Critic reviewed report: {rev_out.verdict} with {len(rev_out.flags)} flags")
        except Exception:
            pass

    state.phase = "DONE"

PHASE_HANDLERS = {
    "INGEST": handle_ingest,
    "ANALYZE": handle_analyze,
    "CLAIMS_CONFIRM": handle_claims_confirm,
    "PLAN": handle_plan,
    "PREFLIGHT": handle_preflight,
    "SETUP": handle_setup,
    "RUN": handle_run,
    "OBSERVE": handle_observe,
    "VALIDATE": handle_validate,
    "COMPARE": handle_compare,
    "DIAGNOSE": handle_diagnose,
    "PATCH_PROPOSE": handle_patch_propose,
    "POLICY_CHECK": handle_policy_check,
    "CRITIC_REVIEW": handle_critic_review,
    "APPROVAL": handle_approval,
    "PATCH_APPLY": handle_patch_apply,
    "STATUS": handle_status,
    "REPORT": handle_report,
    "REPORT_REVIEW": handle_report_review,
    "DONE": lambda state, deps: None
}

def run_project(state: ProjectState, deps: Optional[dict] = None):
    """
    Main orchestrator execution loop (§7.2).
    Transitions through phases until DONE or paused for a human.
    Persists state after each step (D16) and supports clean abort / resumption.
    """
    from backend.app.db import save_project_state
    deps_dict = deps or {}

    # Restore runtime context from state if not present in deps
    if state.workspace:
        deps_dict.setdefault("workspace", state.workspace)
    else:
        state.workspace = deps_dict.get("workspace", f"data/runs/{state.project_id}/workspace")
        deps_dict["workspace"] = state.workspace
        
    if state.latest_log_path and "latest_log_path" not in deps_dict:
        deps_dict["latest_log_path"] = state.latest_log_path
    if state.silent_divergence:
        deps_dict["silent_divergence"] = True

    while state.phase != "DONE":
        if getattr(state, "abort_requested", False):
            state.phase = "DONE"
            if not state.final:
                state.final = {"status": "INCONCLUSIVE", "reason": "aborted by user", "after_n_fixes": len(state.patches)}
            try:
                save_project_state("data/rerun.db", state.project_id, state.benchmark_id, state.repo_commit, "DONE", state)
            except Exception:
                pass
            return

        if guard_budgets(state):
            try:
                status = state.final.get("status") if state.final else state.phase
                save_project_state("data/rerun.db", state.project_id, state.benchmark_id, state.repo_commit, status, state)
            except Exception:
                pass
            continue

        handler = PHASE_HANDLERS.get(state.phase)
        if not handler:
            break
        current_phase = state.phase
        key_rotator.begin_task(f"phase_{current_phase}")
        try:
            handler(state, deps_dict)
        finally:
            key_rotator.end_task()

        # Sync runtime fields back to state
        if "workspace" in deps_dict:
            state.workspace = deps_dict["workspace"]
        if "latest_log_path" in deps_dict:
            state.latest_log_path = deps_dict["latest_log_path"]
        if deps_dict.get("silent_divergence"):
            state.silent_divergence = True

        # Check abort requested mid-step
        if getattr(state, "abort_requested", False):
            state.phase = "DONE"
            if not state.final:
                state.final = {"status": "INCONCLUSIVE", "reason": "aborted by user", "after_n_fixes": len(state.patches)}
            try:
                save_project_state("data/rerun.db", state.project_id, state.benchmark_id, state.repo_commit, "DONE", state)
            except Exception:
                pass
            return

        # Per-step persistence (D16)
        try:
            status = state.final.get("status") if state.final else state.phase
            save_project_state("data/rerun.db", state.project_id, state.benchmark_id, state.repo_commit, status, state)
        except Exception:
            pass

        if state.pending:
            return  # Paused for human approval or claim confirmation
