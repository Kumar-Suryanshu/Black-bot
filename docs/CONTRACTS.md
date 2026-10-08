# Data Contracts

This document specifies the fundamental data models and invariants governing the Rerun system, locked in Stage 1.

## Core Invariants
- All state transitions strictly follow `Phase`.
- State must be round-trip serializable to SQLite `projects.state_json` via Pydantic v2.
- No LLM alters state directly; state transitions are handled by the orchestrator.

## Models
(See `agent/state.py` for exact schemas: `Status`, `Phase`, `ProjectState`, `Event`, etc.)

### ProjectState (Stage 2 Additions)
- `source`: `"benchmark" | "custom"` (indicates origin of input)
- `repo_url`: Optional GitHub URL (`^https://github\.com/[\w.-]+/[\w.-]+(\.git)?$`)
- `repo_ref`: Optional branch / tag / commit ref
- `paper_path`: Canonical path to the extracted research paper PDF (persisted directly on state, not transient `deps`)
- `paper_sha256`: SHA-256 digest of uploaded/selected research paper PDF
- `user_command`: User-edited or override command confirmed at `CLAIMS_CONFIRM` phase (honored by `handle_plan`)
- `simulated`: Boolean flag indicating whether sandbox execution is mock/simulated

## Database
- SQLite with WAL mode.
- One source of truth for the active run: `state_json`.

