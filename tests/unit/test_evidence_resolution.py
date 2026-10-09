"""
Regression tests for evidence artifact resolution.

Evidence snapshots are written as `{evidence_id}_{basename}`, ids restart at E-001 on every
run, and the snapshot directory is shared per project. Callers located artifacts with
`f.name.startswith(f"{eid}_")`, so one id could match several unrelated files. The Critic's
verbatim-quote check -- the mechanism that exists to catch hallucinated quotes -- would then
accept a quote found in a *different* artifact that merely shared the id prefix.

This was not hypothetical: tests/unit/test_bridge_custom_pipeline.py passed only because a
stale `E-001_default.yaml` from an earlier run satisfied a quote that the run's actual E-001
(`E-001_results.json`) did not contain.
"""

import json

import pytest

from tools.evidence import load_evidence_artifact


def _project(tmp_path, pid="p_ev"):
    ev = tmp_path / "runs" / pid / "evidence"
    ev.mkdir(parents=True)
    return ev


def test_ledger_is_authoritative_when_ids_collide_on_disk(tmp_path):
    """Two files share the E-001 prefix; the ledger decides which one E-001 means."""
    ev = _project(tmp_path)
    (ev / "E-001_results.json").write_text('{"test_accuracy_mean": 0.6}')
    (ev / "E-001_default.yaml").write_text("learning_rate: 0.01\n")  # stale from an earlier run
    (tmp_path / "runs" / "p_ev" / "evidence.json").write_text(json.dumps([
        {"id": "E-001", "artifact_path": str(ev / "E-001_default.yaml")},   # earlier run
        {"id": "E-001", "artifact_path": str(ev / "E-001_results.json")},   # this run
    ]))

    text = load_evidence_artifact("p_ev", "E-001", data_dir=str(tmp_path))
    assert "test_accuracy_mean" in text
    assert "learning_rate: 0.01" not in text, "stale snapshot leaked into E-001"


def test_distinct_ids_resolve_to_their_own_artifacts(tmp_path):
    ev = _project(tmp_path)
    (ev / "E-001_results.json").write_text('{"test_accuracy_mean": 0.6}')
    (ev / "E-002_default.yaml").write_text("learning_rate: 0.01\n")
    (tmp_path / "runs" / "p_ev" / "evidence.json").write_text(json.dumps([
        {"id": "E-001", "artifact_path": str(ev / "E-001_results.json")},
        {"id": "E-002", "artifact_path": str(ev / "E-002_default.yaml")},
    ]))

    assert "test_accuracy_mean" in load_evidence_artifact("p_ev", "E-001", data_dir=str(tmp_path))
    assert "learning_rate: 0.01" in load_evidence_artifact("p_ev", "E-002", data_dir=str(tmp_path))


def test_single_unambiguous_snapshot_resolves_without_a_ledger(tmp_path):
    """Hand-seeded fixtures write no ledger; one unambiguous file is still usable."""
    ev = _project(tmp_path)
    (ev / "E-001_log.txt").write_text("ModuleNotFoundError: No module named 'yaml'\n")

    text = load_evidence_artifact("p_ev", "E-001", data_dir=str(tmp_path))
    assert "ModuleNotFoundError" in text


def test_ambiguous_snapshots_without_a_ledger_resolve_to_nothing(tmp_path):
    """
    With no ledger and several candidates, guessing is what caused the bug. Refuse instead,
    so the quote check fails closed rather than matching an arbitrary artifact.
    """
    ev = _project(tmp_path)
    (ev / "E-001_a.txt").write_text("alpha\n")
    (ev / "E-001_b.txt").write_text("beta\n")

    assert load_evidence_artifact("p_ev", "E-001", data_dir=str(tmp_path)) is None


@pytest.mark.parametrize("eid", ["E-999", "", "E-00"])
def test_unknown_or_partial_ids_resolve_to_nothing(tmp_path, eid):
    """A prefix of a real id must not resolve, or ids would alias each other."""
    ev = _project(tmp_path)
    (ev / "E-001_log.txt").write_text("x\n")
    assert load_evidence_artifact("p_ev", eid, data_dir=str(tmp_path)) is None


def test_missing_project_directory_resolves_to_nothing(tmp_path):
    assert load_evidence_artifact("no_such_project", "E-001", data_dir=str(tmp_path)) is None


def test_ledger_entry_pointing_at_a_deleted_file_resolves_to_nothing(tmp_path):
    ev = _project(tmp_path)
    (tmp_path / "runs" / "p_ev" / "evidence.json").write_text(json.dumps([
        {"id": "E-001", "artifact_path": str(ev / "gone.txt")},
    ]))
    assert load_evidence_artifact("p_ev", "E-001", data_dir=str(tmp_path)) is None


def test_corrupt_ledger_falls_back_to_the_snapshot_directory(tmp_path):
    ev = _project(tmp_path)
    (ev / "E-001_log.txt").write_text("recoverable\n")
    (tmp_path / "runs" / "p_ev" / "evidence.json").write_text("{ not json")

    assert "recoverable" in load_evidence_artifact("p_ev", "E-001", data_dir=str(tmp_path))
