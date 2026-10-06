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
