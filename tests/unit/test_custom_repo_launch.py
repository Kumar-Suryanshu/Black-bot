"""
Regression tests for launching a custom repository.

Adding https://github.com/greydanus/hamiltonian-nn triaged as FEASIBLE_WITH_PROVISIONING
but the launch button did nothing. Four separate defects combined:

1. The console pre-filled an invented command, "python train.py --config
   configs/default.yaml". HNN's entry points are experiment-*/train.py, so the server
   rejected it with 400 "Target script 'train.py' not found in workspace".
2. The console swallowed that 400, so the button looked inert.
3. README commands are written inline in backticks, which the extractor ignored, so there
   were no real candidates to offer instead.
4. HNN declares no dependencies at all, so no provisioning plan was ever built and the run
   could only ever die at `import torch`.
"""

import json
from pathlib import Path

import pytest

from tools.commands import extract_readme_commands
from tools.provisioning import build_provisioning_plan, infer_packages_from_imports


# ---------------------------------------------------------------------------
# 3. README commands written in inline backticks
# ---------------------------------------------------------------------------

HNN_README = """# Hamiltonian Neural Networks

Train:
 * Task 1: Ideal mass-spring system: `python3 experiment-spring/train.py --verbose`
 * Task 2: Ideal pendulum: `python3 experiment-pend/train.py --verbose`
 * Task 5: Pixel pendulum (from OpenAI Gym): `python3 experiment-pixels/train.py --verbose`
"""


def test_inline_backtick_commands_are_extracted():
    """A command documented inline on a bullet line must be found."""
    commands = extract_readme_commands(HNN_README)
    assert "python3 experiment-spring/train.py --verbose" in commands
    assert "python3 experiment-pend/train.py --verbose" in commands
    assert len(commands) == 3


def test_fenced_block_commands_still_extracted():
    """The inline support must not regress fenced code blocks."""
    readme = "## Run\n\n```bash\npython train.py --config configs/default.yaml\n```\n"
    assert "python train.py --config configs/default.yaml" in extract_readme_commands(readme)


def test_prose_mentioning_python_is_not_treated_as_a_command():
    readme = "We used Python for all experiments. See `requirements.txt` for versions.\n"
    assert extract_readme_commands(readme) == []


# ---------------------------------------------------------------------------
# 4. A repository that declares no dependencies must still be provisionable
# ---------------------------------------------------------------------------

def _undeclared_repo(tmp_path):
    """A repo with real third-party imports and no dependency file at all, like HNN."""
    repo = tmp_path / "undeclared"
    (repo / "experiment-spring").mkdir(parents=True)
    (repo / "utils.py").write_text("import numpy as np\n")
    (repo / "data.py").write_text("import autograd\n")
    (repo / "experiment-spring" / "train.py").write_text(
        "import torch\nimport numpy as np\nfrom data import get_dataset\n"
        "from utils import L2_loss\n\nif __name__ == '__main__':\n    pass\n"
    )
    return repo


def test_plan_is_inferred_when_no_dependency_file_exists(tmp_path):
    from tools.triage import triage_report

    repo = _undeclared_repo(tmp_path)
    plan = build_provisioning_plan(str(repo), "p_undeclared", triage_report=triage_report(str(repo)))

    assert plan["needed"] is True
    assert plan["status"] == "PROPOSED"
    assert plan.get("inferred_from_imports") is True
    names = {p["name"] for p in plan["packages"]}
    assert "torch" in names
    # And the operator is told the list was inferred and is unpinned.
    assert any("declares no dependencies" in w for w in plan["warnings"])


def test_local_modules_are_never_proposed_as_packages(tmp_path):
    """
    `from data import get_dataset` resolves to the repo's own data.py. Proposing to pip
    install a package called "data" would be both wrong and a supply-chain hazard.
    """
    from tools.triage import triage_report

    repo = _undeclared_repo(tmp_path)
    plan = build_provisioning_plan(str(repo), "p_local", triage_report=triage_report(str(repo)))

    names = {p["name"] for p in plan["packages"]}
    assert "data" not in names
    assert "utils" not in names


def test_declared_dependencies_still_take_precedence(tmp_path):
    """Inference is a fallback; a real requirements.txt must still win."""
    from tools.triage import triage_report

    repo = _undeclared_repo(tmp_path)
    (repo / "requirements.txt").write_text("numpy==1.26.4\n")

    plan = build_provisioning_plan(str(repo), "p_declared", triage_report=triage_report(str(repo)))
    assert plan.get("inferred_from_imports") is not True
    assert {p["name"] for p in plan["packages"]} == {"numpy"}


def test_import_name_is_mapped_to_its_pip_name(tmp_path):
    """`import yaml` must become a request for pyyaml, not for a package called yaml."""
    packages = infer_packages_from_imports(
        {"imports": {"unresolved": ["yaml", "sklearn", "cv2"]}}, workspace=str(tmp_path)
    )
    names = {p["name"] for p in packages}
    assert "pyyaml" in names
    assert "scikit-learn" in names
    assert "yaml" not in names


def test_inference_is_skipped_without_a_triage_report(tmp_path):
    assert infer_packages_from_imports(None, workspace=str(tmp_path)) == []
    assert infer_packages_from_imports({}, workspace=str(tmp_path)) == []
