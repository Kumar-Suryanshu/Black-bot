import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from tools.triage import triage_report
from backend.app.main import app
from backend.app.db import init_db, save_project_state, get_project_state
from agent.state import ProjectState

def test_triage_clean_repo(tmp_path):
    """Clean repo with valid Python code and standard library should be FEASIBLE."""
    repo = tmp_path / "clean_repo"
    repo.mkdir()
    (repo / "main.py").write_text("import json\nimport math\n\ndef run():\n    return math.sqrt(16)\n")
    
    report = triage_report(str(repo))
    assert report["verdict"] == "FEASIBLE"
    assert len(report["blockers"]) == 0
    assert len(report["stubs"]) == 0

def test_triage_guarded_cuda_warning_only(tmp_path):
    """Guarded torch.cuda.is_available() selection must produce a warning, NOT a blocker (Fixes D5)."""
    repo = tmp_path / "guarded_cuda_repo"
    repo.mkdir()
    (repo / "train.py").write_text(
        "import torch\n\n"
        "device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')\n"
        "def train():\n"
        "    if torch.cuda.is_available():\n"
        "        print('using cuda')\n"
        "    return 1\n"
    )
    (repo / "requirements.txt").write_text("torch>=2.0.0\n")

    report = triage_report(str(repo))
    assert "gpu_required" not in report["blockers"]
    assert report["verdict"] != "NEEDS_GPU"
    assert any("guarded" in w.lower() for w in report["warnings"])
    assert len(report["gpu"]["guarded"]) >= 1
    assert len(report["gpu"]["unguarded"]) == 0

def test_triage_hard_cuda_blocker(tmp_path):
    """Hard-coded .cuda() or device='cuda' must produce NEEDS_GPU blocker."""
    repo = tmp_path / "hard_cuda_repo"
    repo.mkdir()
    (repo / "train.py").write_text(
        "import torch\n\n"
        "device = 'cuda'\n"
        "def train():\n"
        "    x = torch.zeros(10).cuda()\n"
        "    return x\n"
    )

    report = triage_report(str(repo))
    assert report["verdict"] == "NEEDS_GPU"
    assert "gpu_required" in report["blockers"]
    assert len(report["gpu"]["unguarded"]) >= 1

def test_triage_cuda_only_package_blocker(tmp_path):
    """CUDA-only package in requirements must trigger NEEDS_GPU."""
    repo = tmp_path / "cuda_pkg_repo"
    repo.mkdir()
    (repo / "train.py").write_text("import flash_attn\n")
    (repo / "requirements.txt").write_text("flash-attn==2.5.0\n")

    report = triage_report(str(repo))
    assert report["verdict"] == "NEEDS_GPU"
    assert "gpu_required" in report["blockers"]

def test_triage_stub_not_implemented_error(tmp_path):
    """raise NotImplementedError in train path must yield INCOMPLETE_REPO."""
    repo = tmp_path / "stub_repo"
    repo.mkdir()
    (repo / "train.py").write_text(
        "def train_model():\n"
        "    raise NotImplementedError('Complete training loop here')\n"
    )

    report = triage_report(str(repo))
    assert report["verdict"] == "INCOMPLETE_REPO"
    assert "unimplemented_stubs" in report["blockers"]
    assert any(s["type"] == "not_implemented_error" for s in report["stubs"])

def test_triage_stub_empty_body(tmp_path):
    """Empty pass / ellipsis body must yield INCOMPLETE_REPO."""
    repo = tmp_path / "pass_stub_repo"
    repo.mkdir()
    (repo / "model.py").write_text(
        "def forward(x):\n"
        "    pass\n"
    )

    report = triage_report(str(repo))
    assert report["verdict"] == "INCOMPLETE_REPO"
    assert any(s["type"] == "pass_stub" for s in report["stubs"])

def test_triage_missing_local_module(tmp_path):
    """Local module imported that does not exist on disk must yield INCOMPLETE_REPO."""
    repo = tmp_path / "missing_module_repo"
    repo.mkdir()
    (repo / "main.py").write_text(
        "from .unreal_submodule import nonexistent_function\n"
    )

    report = triage_report(str(repo))
    assert report["verdict"] == "INCOMPLETE_REPO"
    assert "missing_local_module" in report["blockers"]
    assert len(report["missing_local_modules"]) >= 1

def test_triage_missing_readme_script(tmp_path):
    """README-mentioned script that doesn't exist on disk must yield INCOMPLETE_REPO."""
    repo = tmp_path / "readme_missing_repo"
    repo.mkdir()
    (repo / "README.md").write_text(
        "# How to run\nRun `python evaluate_custom.py --data train.csv`\n"
    )

    report = triage_report(str(repo))
    assert report["verdict"] == "INCOMPLETE_REPO"
    assert "missing_readme_script" in report["blockers"]

def test_triage_notebook_only_repo(tmp_path):
    """Repository containing only .ipynb and zero .py files must yield UNSUPPORTED_FORMAT."""
    repo = tmp_path / "notebook_repo"
    repo.mkdir()
    (repo / "experiment.ipynb").write_text('{"cells": [], "metadata": {}}')

    report = triage_report(str(repo))
    assert report["verdict"] == "UNSUPPORTED_FORMAT"
    assert "notebook_only" in report["blockers"]

def test_triage_missing_data_file(tmp_path):
    """Referenced dataset file that doesn't exist on disk yields data_unavailable."""
    repo = tmp_path / "missing_data_repo"
    repo.mkdir()
    (repo / "train.py").write_text(
        "import pandas as pd\n"
        "df = pd.read_csv('data/missing_train_set.csv')\n"
    )

    report = triage_report(str(repo))
    assert report["verdict"] == "NEEDS_LARGE_RESOURCES"
    assert "data_unavailable" in report["blockers"]
    assert any("missing_train_set.csv" in d for d in report["missing_data_refs"])

def test_triage_never_executes_repo_code(tmp_path):
    """
    Critical Safety Invariant:
    Triage must NEVER import or execute repository code.
    If __init__.py contains malicious execution or side-effects, it must NOT execute.
    """
    repo = tmp_path / "hostile_repo"
    repo.mkdir()
    sentinel_file = tmp_path / "LEAK_SENTINEL_EXECUTED.txt"
    
    # __init__.py writes sentinel if executed
    (repo / "__init__.py").write_text(
        f"with open('{sentinel_file}', 'w') as f:\n"
        f"    f.write('EXECUTED')\n"
    )
    (repo / "main.py").write_text(
        f"import os\n"
        f"print('hello')\n"
    )

    # Run triage
    report = triage_report(str(repo))
    
    # Assert sentinel file was NEVER created
    assert not sentinel_file.exists(), "SECURITY VIOLATION: Triage imported or executed repo code!"
    assert report["verdict"] == "FEASIBLE"

def test_triage_api_endpoint(tmp_path, monkeypatch):
    """Tests POST /api/projects/{id}/triage route."""
    test_db = str(tmp_path / "rerun_triage.db")
    init_db(test_db)
    monkeypatch.setattr("backend.app.routes.get_project_state", lambda db, pid: get_project_state(test_db, pid))
    monkeypatch.setattr("backend.app.routes.save_project_state", lambda db, pid, b, r, p, s: save_project_state(test_db, pid, b, r, p, s))

    # Create dummy project workspace
    ws = Path("data/runs/proj_triage_test/workspace")
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "main.py").write_text("import math\nprint(math.pi)\n")

    try:
        project_id = "proj_triage_test"
        state = ProjectState(
            project_id=project_id,
            source="custom",
            repo_commit="c1",
            phase="CLAIMS_CONFIRM",
            budgets={"steps_used": 0, "patches_used": 0},
            claims=[],
            paper_settings=[],
            repo_profile={}
        )
        save_project_state(test_db, project_id, None, "c1", "CLAIMS_CONFIRM", state)

        client = TestClient(app)
        resp = client.post(f"/api/projects/{project_id}/triage")
        assert resp.status_code == 200
        data = resp.json()
        assert data["verdict"] == "FEASIBLE"
        assert "imports" in data
    finally:
        import shutil
        if Path("data/runs/proj_triage_test").exists():
            shutil.rmtree("data/runs/proj_triage_test")


# ---------------------------------------------------------------------------
# Stub severity and finding masking (regression)
#
# Any single `pass` body used to make a whole repository INCOMPLETE_REPO, which blocked
# essentially every real-world research repo at preflight. Because the verdict ladder was a
# chain of elif, it also discarded genuine GPU and missing-data findings underneath.
# ---------------------------------------------------------------------------

def _write_realistic_repo(root):
    root.mkdir()
    (root / "requirements.txt").write_text("numpy==1.26.4\ntorch==2.1.0\n")
    (root / "model.py").write_text(
        "import torch\n"
        "import torch.nn as nn\n"
        "\n"
        "class Net(nn.Module):\n"
        "    def __init__(self):\n"
        "        super().__init__()\n"
        "        self.fc = nn.Linear(10, 2)\n"
        "\n"
        "    def forward(self, x):\n"
        "        return self.fc(x)\n"
        "\n"
        "class BaseTrainer:\n"
        "    def on_epoch_end(self):\n"
        "        pass  # hook for subclasses\n"
    )
    (root / "train.py").write_text(
        "import torch\n"
        "from model import Net\n"
        "\n"
        "def main():\n"
        "    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')\n"
        "    net = Net().to(device)\n"
        "    print('accuracy: 0.91')\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    main()\n"
    )
    return root


def test_single_no_op_hook_does_not_block_a_real_repository(tmp_path):
    """One idiomatic `pass` hook is a warning, not a blocker."""
    repo = _write_realistic_repo(tmp_path / "realistic_repo")

    report = triage_report(str(repo))
    assert report["verdict"] != "INCOMPLETE_REPO"
    assert "unimplemented_stubs" not in report["blockers"]
    # Still reported, just not as a blocker.
    assert any("empty function" in w for w in report["warnings"])
    assert any(s["type"] == "pass_stub" for s in report["stubs"])


def test_not_implemented_error_still_blocks_in_a_real_repository(tmp_path):
    """An explicit NotImplementedError is an author saying the code path is absent."""
    repo = _write_realistic_repo(tmp_path / "ni_repo")
    (repo / "evaluate.py").write_text(
        "def evaluate(model):\n"
        "    raise NotImplementedError('fill this in')\n"
    )

    report = triage_report(str(repo))
    assert report["verdict"] == "INCOMPLETE_REPO"
    assert "unimplemented_stubs" in report["blockers"]


def test_lower_priority_findings_are_not_masked_by_higher_priority_ones(tmp_path):
    """
    A repo with both a syntax error and a hard GPU requirement must report both blockers.
    The old elif ladder returned only the first and silently dropped the rest.
    """
    repo = tmp_path / "multi_fault_repo"
    repo.mkdir()
    (repo / "requirements.txt").write_text("flash-attn==2.5.0\n")
    (repo / "broken.py").write_text("def f(:\n    pass\n")
    (repo / "train.py").write_text("import flash_attn\ndevice = 'cuda'\n")

    report = triage_report(str(repo))
    assert "syntax_error" in report["blockers"]
    assert "gpu_required" in report["blockers"], (
        f"GPU finding was masked; blockers={report['blockers']}"
    )
    # Headline verdict still follows documented priority.
    assert report["verdict"] == "INCOMPLETE_REPO"
