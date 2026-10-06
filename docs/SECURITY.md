# Security Model

This document outlines the security posture of the Rerun sandbox environment. 
- Container runtime: Non-root execution.
- Dropped capabilities: `cap_drop=["ALL"]`.
- `no-new-privileges` enabled.
- Read-only root filesystem (`/workspace` and `/tmp` mounted appropriately).
- CPU/PID/Mem limits enforced.
- Network is explicitly `none`.
