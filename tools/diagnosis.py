"""
Deterministic diagnosis.

The repair loop used to depend entirely on the Solver choosing the right tool, confirming a
hypothesis and writing an exact patch within DIAGNOSE_STEPS_MAX steps. For faults the system
already classifies that is unnecessary and unreliable: the same benchmark passed on one run
and ran out of steps on the next, even though the evidence needed for the fix was recorded
in both. A missing module named in a traceback, or a configuration key that disagrees with a
value the paper states verbatim, is derivable from evidence rather than a matter of
judgement.

So those two cases are derived here, in code. Everything else still goes to the Solver.

This removes no safeguard. A patch produced here is an ordinary proposal: it carries real
evidence ids, and it still has to pass the policy engine, the Critic, and human approval
before it is applied. What it removes is the chance that a mechanical fix is missed because
the model took a different path.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agent.state import Edit, Hypothesis, PatchProposal, ProjectState

# Modules whose import name differs from the package that provides them.
MODULE_TO_PACKAGE = {
    "yaml": "PyYAML",
    "sklearn": "scikit-learn",
    "cv2": "opencv-python",
    "PIL": "pillow",
    "bs4": "beautifulsoup4",
    "dateutil": "python-dateutil",
    "attr": "attrs",
    "skimage": "scikit-image",
}

MISSING_MODULE_RE = re.compile(r"ModuleNotFoundError: No module named ['\"]([\w\.]+)['\"]")


def _wheelhouse_version(package: str) -> Optional[str]:
    """The exact version available offline, so the pin is real rather than invented."""
    from tools.exec_tools import query_package_index

    versions = query_package_index(package)
    return sorted(versions)[-1] if versions else None


def diagnose_missing_dependency(
    state: ProjectState, workspace: str, log_text: str
) -> Optional[Tuple[Hypothesis, List[Edit], str, str]]:
    """A module named in a traceback, pinned to the version actually in the wheelhouse."""
    match = MISSING_MODULE_RE.search(log_text or "")
    if not match:
        return None

    module = match.group(1).split(".")[0]
    package = MODULE_TO_PACKAGE.get(module, module)
    version = _wheelhouse_version(package)
    if not version:
        return None  # cannot pin it honestly, so leave it to the Solver

    req = Path(workspace) / "requirements.txt"
    existing = req.read_text(encoding="utf-8") if req.exists() else ""
    if re.search(rf"(?im)^\s*{re.escape(package)}\s*==", existing):
        return None  # already declared; the failure is something else

    hypothesis = Hypothesis(
        id=f"H-{len(state.hypotheses) + 1}",
        text=(
            f"The run failed with ModuleNotFoundError for '{module}', which is provided by "
            f"{package}. requirements.txt does not declare it."
        ),
        status="confirmed",
        evidence=[],           # filled by the caller with the recorded log evidence
        tested_with=["inspect_error"],
        error_class="dependency_missing",
    )
    edits = [Edit(file="requirements.txt", op="append_line", new=f"{package}=={version}")]
    rationale = (
        f"ModuleNotFoundError: No module named '{module}'. {package} is imported by the "
        f"experiment but absent from requirements.txt; pinned to {version}, the version "
        f"present in the offline wheelhouse."
    )
    return hypothesis, edits, rationale, "dependency"


def _find_config_assignment(text: str, key: str) -> Optional[str]:
    """The exact line assigning `key`, so replace_text matches once and only once."""
    for line in text.splitlines():
        if re.match(rf"^\s*{re.escape(key)}\s*:", line):
            return line
    return None


def diagnose_config_mismatch(
    state: ProjectState, workspace: str
) -> Optional[Tuple[Hypothesis, List[Edit], str, str]]:
    """A configuration value that disagrees with a value the paper states verbatim."""
    mismatches = [
        d for d in (state.config_diff or [])
        if d.get("status") == "mismatch" and d.get("effective_value") is not None
    ]
    if not mismatches:
        return None

    ws = Path(workspace)
    config_rel = state.plan.config_file if state.plan and state.plan.config_file else None
    candidates = [config_rel] if config_rel else []
    candidates += ["configs/default.yaml", "config.yaml", "configs/config.yaml"]

    for diff in mismatches:
        paper_key = str(diff.get("key"))
        paper_value = diff.get("paper_value")
        if paper_value is None:
            continue
        # The paper must actually state this value; that is what makes the fix legitimate
        # rather than tuning toward the target number.
        setting = next((ps for ps in state.paper_settings if ps.key == paper_key), None)
        if setting is None:
            continue

        for rel in candidates:
            if not rel:
                continue
            path = ws / rel
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for key_variant in {paper_key, paper_key.replace(" ", "_"), setting.repo_key or paper_key}:
                line = _find_config_assignment(text, key_variant)
                if not line:
                    continue
                if text.count(line) != 1:
                    continue
                new_line = f"{key_variant}: {paper_value}"
                if line.strip() == new_line.strip():
                    continue  # already correct
                hypothesis = Hypothesis(
                    id=f"H-{len(state.hypotheses) + 1}",
                    text=(
                        f"The run completed but missed the reported value. {rel} sets "
                        f"{key_variant} to {diff.get('effective_value')}, while the paper "
                        f"states {paper_value}."
                    ),
                    status="confirmed",
                    evidence=[],
                    tested_with=["compare_configuration"],
                    error_class="config_mismatch",
                )
                edits = [Edit(file=rel, op="replace_text", old=line, new=new_line)]
                rationale = (
                    f"The paper states {paper_key} = {paper_value} "
                    f'("{setting.source_quote[:120]}", {setting.source_ref}). '
                    f"{rel} uses {diff.get('effective_value')}. Aligning the configuration "
                    f"with the paper-stated value."
                )
                return hypothesis, edits, rationale, "config_value"
    return None


def derive_patch(
    state: ProjectState, workspace: str, log_text: str = ""
) -> Optional[Dict[str, Any]]:
    """
    The mechanical fix for this failure, or None when judgement is required.

    Returns a dict with hypothesis, edits, rationale and patch type. The caller records the
    supporting evidence and builds the proposal, so the patch cites real evidence ids.
    """
    for rule in (
        lambda: diagnose_missing_dependency(state, workspace, log_text),
        lambda: diagnose_config_mismatch(state, workspace),
    ):
        result = rule()
        if result is None:
            continue
        hypothesis, edits, rationale, patch_type = result
        return {
            "hypothesis": hypothesis,
            "edits": edits,
            "rationale": rationale,
            "type": patch_type,
        }
    return None
