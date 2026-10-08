import os
import csv
import json
import pytest
from pathlib import Path

from tools.commands import validate_command, extract_readme_commands
from tools.metrics import extract_metric, record_metric_evidence, MetricExtractionResult
from tools.compare import recommend_tolerance, compare
from agent.state import Claim, MetricExtraction, ProjectState, Tolerance
from agent.loop import handle_validate, handle_compare
from tools.status import compute_status

def test_command_validator_rejects_injection_forms_table(tmp_path):
    """
    Gate requirement: Command validator rejects each injection form (test table)
    and unsupported runners (make, torchrun), but accepts safe python and bash scripts.
    """
    dummy_script = tmp_path / "train.py"
    dummy_script.write_text("print('ok')\n")
    dummy_bash = tmp_path / "run.sh"
    dummy_bash.write_text("echo ok\n")

    test_cases = [
        # (command, expected_valid, expected_reason_keyword)
        ("python train.py | grep 1", False, "pipes"),
        ("python train.py > out.txt", False, "output redirection"),
        ("python train.py >> out.txt", False, "output redirection"),
        ("python train.py < in.txt", False, "input redirection"),
        ("python train.py; rm -rf /", False, "command chaining (;)"),
        ("python train.py && echo 1", False, "command chaining (&&)"),
        ("python train.py || echo 1", False, "command chaining (||)"),
        ("python train.py $(whoami)", False, "command substitution"),
        ("python train.py `id`", False, "backtick"),
        ("python train.py &", False, "background operator"),
        ("python train.py\necho hacked", False, "multiline"),
        ("make run", False, "Unsupported command runner 'make'"),
        ("torchrun --nproc_per_node=2 train.py", False, "Unsupported distributed command runner 'torchrun'"),
        ("deepspeed train.py", False, "Unsupported distributed command runner 'deepspeed'"),
        ("jupyter nbconvert --execute test.ipynb", False, "Unsupported command 'jupyter'"),
        ("pytest tests/", False, "Unsupported command 'pytest'"),
        ("", False, "empty"),
        # Valid cases
        ("python train.py", True, "Valid"),
        ("python train.py --epochs 10 --lr 0.01", True, "Valid"),
        ("python3 train.py", True, "Valid"),
        ("python -m package.train --data digits", True, "Valid"),
        ("bash run.sh", True, "Valid"),
        ("sh run.sh", True, "Valid"),
    ]

    for cmd, expected_valid, kw in test_cases:
        res = validate_command(cmd, workspace=str(tmp_path))
        assert res["valid"] == expected_valid, f"Failed for '{cmd}': expected {expected_valid}, got {res}"
        if not expected_valid:
            assert kw.lower() in res["reason"].lower(), f"Reason for '{cmd}' ({res['reason']}) did not contain '{kw}'"

def test_readme_command_extraction_handles_prompts_and_formats(tmp_path):
    """
    Gate requirement: README parsing handles bash ..., python -m, $ prompts (D7).
    """
    readme_content = """
# Sample Machine Learning Project

Run the following command to train:
$ python train.py --config config.yaml

Or execute via module:
> python -m src.experiment --batch 32

Or using the bash script:
# bash scripts/run_all.sh

```bash
python run_eval.py --eval-only
bash evaluate.sh
```

Unsupported commands mentioned:
$ make train
$ torchrun --nproc=4 train.py
"""
    cmds = extract_readme_commands(readme_content)
    assert "python train.py --config config.yaml" in cmds
    assert "python -m src.experiment --batch 32" in cmds
    assert "bash scripts/run_all.sh" in cmds
    assert "python run_eval.py --eval-only" in cmds
    assert "bash evaluate.sh" in cmds
    assert "make train" in cmds
    assert "torchrun --nproc=4 train.py" in cmds

def test_deterministic_tolerance_advisor():
    """
    Gate requirement: Tolerance advisor:
    - paper gives a ± s -> max(s, rounding)
    - 2 decimals -> ±0.005
    - 1 decimal -> ±0.05
    - else suggest ±1 point
    """
    # 1. Uncertainty given: a ± s -> max(s, rounding)
    t1 = recommend_tolerance(reported=93.1, std=0.4)
    assert t1["value"] == 0.4
    assert t1["type"] == "abs"

    # Uncertainty smaller than rounding precision (1 decimal rounding is 0.05)
    t1_b = recommend_tolerance(reported=93.1, std=0.01)
    assert t1_b["value"] == 0.05

    # 2. Uncertainty extracted from paper quote string
    t2 = recommend_tolerance(reported=85.2, raw_paper_str="We achieve 85.2 ± 0.35 on CIFAR-10")
    assert t2["value"] == 0.35

    # 3. 2 decimals -> ±0.005
    t3 = recommend_tolerance(reported=0.95)
    assert t3["value"] == 0.005

    t3_2dec = recommend_tolerance(reported=95.56)
    assert t3_2dec["value"] == 0.005

    # Non-2-decimal float <= 1.0 falls back to 1 point (0.01)
    t3_3dec = recommend_tolerance(reported=0.956)
    assert t3_3dec["value"] == 0.01

    # 4. 1 decimal -> ±0.05
    t4 = recommend_tolerance(reported=93.1)
    assert t4["value"] == 0.05

    # 5. Integer / default point suggestion
    t5 = recommend_tolerance(reported=85.0)
    assert t5["value"] == 1.0

    t6 = recommend_tolerance(reported=0.8)
    assert t6["value"] == 0.05

def test_metric_extraction_fixture_stdout_regex(tmp_path):
    """
    Gate requirement: Fixture repo printing 'Accuracy: 93.1%' to stdout log
    is extracted correctly with evidence snapshot.
    """
    ws = tmp_path / "ws_stdout"
    ws.mkdir()
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_file = log_dir / "run_1.log"
    log_file.write_text(
        "Loading dataset...\n"
        "Epoch 1: loss=0.42\n"
        "Epoch 2: loss=0.21\n"
        "Evaluation results: Accuracy: 93.1%\n"
        "Process finished.\n"
    )

    claim = Claim(
        id="C-1",
        statement="Accuracy of 93.1%",
        metric="accuracy",
        reported=0.931,
        source_ref="Table 1",
        source_quote="Accuracy: 93.1%",
        metric_extraction=MetricExtraction(
            kind="regex_log",
            path=str(log_file),
            regex=r"Accuracy:\s*(?P<val>\d+(?:\.\d+)?%?)"
        )
    )

    res = extract_metric(ws, claim, log_path=str(log_file))
    assert res.success is True
    assert abs(res.value - 0.931) < 1e-6
    assert res.line_number == 4
    assert "Accuracy: 93.1%" in res.excerpt

    # Record evidence snapshot
    state = ProjectState(
        project_id="proj_stdout_test",
        source="custom",
        phase="RUN",
        workspace=str(ws),
        budgets={"steps_used": 0, "patches_used": 0},
        claims=[claim],
        paper_settings=[]
    )
    ev_id = record_metric_evidence(state, res, "call_stdout_ext")
    assert ev_id is not None
    assert ev_id in state.evidence_ids
    assert res.evidence_id == ev_id

def test_metric_extraction_fixture_csv(tmp_path):
    """
    Gate requirement: Fixture repo writing 'metrics.csv' is extracted correctly with evidence snapshot.
    """
    ws = tmp_path / "ws_csv"
    ws.mkdir()
    csv_file = ws / "metrics.csv"

    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "train_loss", "val_accuracy"])
        writer.writerow([1, 0.55, 0.78])
        writer.writerow([2, 0.32, 0.89])
        writer.writerow([3, 0.15, 0.942])

    claim = Claim(
        id="C-2",
        statement="Validation accuracy of 94.2%",
        metric="val_accuracy",
        reported=0.942,
        source_ref="Fig 3",
        source_quote="val_accuracy = 0.942",
        metric_extraction=MetricExtraction(
            kind="csv_file",
            path="metrics.csv",
            column="val_accuracy",
            aggregation="last"
        )
    )

    res = extract_metric(ws, claim)
    assert res.success is True
    assert abs(res.value - 0.942) < 1e-6

    # Test evidence snapshot
    state = ProjectState(
        project_id="proj_csv_test",
        source="custom",
        phase="RUN",
        workspace=str(ws),
        budgets={"steps_used": 0, "patches_used": 0},
        claims=[claim],
        paper_settings=[]
    )
    ev_id = record_metric_evidence(state, res, "call_csv_ext")
    assert ev_id is not None
    assert ev_id in state.evidence_ids

def test_metric_extraction_fixture_custom_json_key(tmp_path):
    """
    Gate requirement: Fixture repo writing custom JSON with different key is extracted correctly.
    """
    ws = tmp_path / "ws_custom_json"
    ws.mkdir()
    eval_file = ws / "eval_results.json"
    eval_file.write_text(json.dumps({
        "metadata": {"model": "transformer"},
        "eval": {
            "test_bleu_score": 38.65,
            "test_rouge": 45.2
        }
    }))

    claim = Claim(
        id="C-3",
        statement="BLEU score of 38.65",
        metric="bleu",
        reported=38.65,
        source_ref="Table 2",
        source_quote="BLEU 38.65",
        metric_extraction=MetricExtraction(
            kind="json_file",
            path="eval_results.json",
            key="eval.test_bleu_score"
        )
    )

    res = extract_metric(ws, claim)
    assert res.success is True
    assert abs(res.value - 38.65) < 1e-6

    # Test evidence snapshot
    state = ProjectState(
        project_id="proj_json_test",
        source="custom",
        phase="RUN",
        workspace=str(ws),
        budgets={"steps_used": 0, "patches_used": 0},
        claims=[claim],
        paper_settings=[]
    )
    ev_id = record_metric_evidence(state, res, "call_json_ext")
    assert ev_id is not None
    assert ev_id in state.evidence_ids

def test_non_matching_regex_produces_inconclusive_never_zero(tmp_path):
    """
    Gate requirement: Non-matching regex produces INCONCLUSIVE with clear reason,
    NEVER defaults to 0.
    """
    ws = tmp_path / "ws_nonmatch"
    ws.mkdir()
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_file = log_dir / "run_nonmatch.log"
    log_file.write_text(
        "Traceback (most recent call last):\n"
        "  File 'train.py', line 12, in <module>\n"
        "ZeroDivisionError: division by zero\n"
    )

    claim = Claim(
        id="C-1",
        statement="Accuracy 95%",
        metric="accuracy",
        reported=0.95,
        source_ref="p.2",
        source_quote="acc 95%",
        confirmed_by_human=True,
        primary=True,
        metric_extraction=MetricExtraction(
            kind="regex_log",
            path=str(log_file),
            regex=r"Final Score:\s*(?P<val>\d+\.\d+)"
        )
    )

    res = extract_metric(ws, claim, log_path=str(log_file))
    # Extraction must fail and value must NOT default to 0
    assert res.success is False
    assert res.value is None, f"Expected None on failure, got {res.value}!"
    assert "produced no match" in res.error

    # Simulate loop handle_validate & status computation
    from agent.state import Attempt
    state = ProjectState(
        project_id="proj_nonmatch",
        source="custom",
        phase="RUN",
        workspace=str(ws),
        budgets={"steps_used": 1, "patches_used": 0},
        claims=[claim],
        paper_settings=[],
        attempts=[
            Attempt(
                n=1,
                patches_applied=[],
                exit_code=0,
                started_at="2026-10-08T10:00:00"
            )
        ]
    )
    state.attempts[-1].log_path = str(log_file)
    deps = {"workspace": str(ws)}

    handle_validate(state, deps)
    assert state.phase == "DIAGNOSE"
    assert state.attempts[-1].error_class == "metric_extraction_failed"

    # Status computation must yield INCONCLUSIVE with metric extraction failed
    state.phase = "STATUS"
    status_res = compute_status(state)
    assert status_res["status"] == "INCONCLUSIVE"
    assert "metric extraction failed" in status_res["reason"].lower()

def test_single_run_records_variance_unknown_confidence_factor():
    """
    Gate requirement: For single-run results (n=1), record 'n=1, variance unknown'
    in confidence_factors.
    """
    from agent.state import Attempt, Plan
    claim = Claim(
        id="C-1",
        statement="Accuracy 90%",
        metric="accuracy",
        reported=0.90,
        source_ref="p.1",
        source_quote="acc 90%",
        confirmed_by_human=True,
        primary=True
    )
    state = ProjectState(
        project_id="proj_single_run",
        source="custom",
        phase="STATUS",
        budgets={"steps_used": 1, "patches_used": 0},
        claims=[claim],
        paper_settings=[],
        plan=Plan(
            command="python train.py",
            output_file="outputs/results.json",
            seeds=[0]  # n=1
        ),
        attempts=[
            Attempt(
                n=1,
                patches_applied=[],
                exit_code=0,
                started_at="2026-10-08T10:00:00",
                metrics={"accuracy": 0.82, "test_accuracy_mean": 0.82},
                comparison=[{
                    "claim_id": "C-1",
                    "reported": 0.90,
                    "observed": 0.82,
                    "within_tolerance": False
                }]
            )
        ]
    )

    status_res = compute_status(state)
    assert "confidence_factors" in status_res
    assert status_res["confidence_factors"].get("variance") == "n=1, variance unknown"
