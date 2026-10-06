# Rerun

**Rerun** is an autonomous AI coding agent designed to verify if code from a research paper reproduces the claimed headline numbers.

## Limits and Capabilities
- The system runs code exclusively in a **hardened, network-isolated Docker sandbox**.
- **No secrets or credentials** are passed to the sandbox or written to logs.
- The AI **cannot** execute code directly, apply patches without human approval, write evidence itself, type metrics, or determine the final success status.
- Designed strictly for Python 3.11 with limited runtime dependencies. GPU support is explicitly unsupported.
- Uses `data/` and `wheelhouse/` strictly for local file and dependency management.

## Quickstart
1. Review `.env.example` and set up your `.env`.
2. Run `make setup`
3. Run `make images`
4. Run `make wheelhouse`
5. Run `make seed-faults`
6. Run `make api` and start exploring.

## Folder Structure

```text
.
├── agent
│   ├── critic
│   │   └── __init__.py
│   ├── __init__.py
│   ├── solver
│   │   └── __init__.py
│   └── state.py
├── backend
│   ├── app
│   │   ├── db.py
│   │   └── __init__.py
│   └── __init__.py
├── benchmarks
│   ├── adversarial
│   ├── gold
│   ├── papers
│   └── template
├── data
│   └── cassettes
├── docs
│   ├── CONTRACTS.md
│   └── SECURITY.md
├── frontend
├── Makefile
├── PROGRESS.md
├── README.md
├── requirements-dev.txt
├── requirements.txt
├── sandbox
│   ├── images
│   │   ├── Dockerfile.base
│   │   └── requirements.base.txt
│   └── __init__.py
├── scripts
│   └── dev.py
├── tests
│   ├── agent
│   │   └── __init__.py
│   ├── e2e
│   │   └── __init__.py
│   ├── __init__.py
│   ├── security
│   │   └── __init__.py
│   └── unit
│       ├── __init__.py
│       ├── test_compare.py
│       ├── test_config_audit.py
│       ├── test_contracts.py
│       ├── test_errors.py
│       ├── test_evidence.py
│       ├── test_policy.py
│       ├── test_results.py
│       └── test_status.py
└── tools
    ├── compare.py
    ├── config_audit.py
    ├── errors.py
    ├── evidence.py
    ├── __init__.py
    ├── policy.py
    ├── registry.py
    ├── results.py
    └── status.py
```
