# Data Contracts

This document specifies the fundamental data models and invariants governing the Rerun system, locked in Stage 1.

## Core Invariants
- All state transitions strictly follow `Phase`.
- State must be round-trip serializable to SQLite `projects.state_json` via Pydantic v2.
- No LLM alters state directly; state transitions are handled by the orchestrator.

## Models
(See `agent/state.py` for exact schemas: `Status`, `Phase`, `ProjectState`, `Event`, etc.)

## Database
- SQLite with WAL mode.
- One source of truth for the active run: `state_json`.
