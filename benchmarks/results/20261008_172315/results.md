# Track A Benchmark Evaluation Results

**Timestamp:** 2026-10-08 17:23:28 UTC
**Sandbox:** Docker (`DockerSandbox`, image: `rerun-base:py311`, offline network)
**Repeats:** 1 per condition

## Summary Table (Counts Only)

| Case | Gold Expected | B-2 |
|---|---|---|
| `b1_control` | `REPRODUCED` | 1/1 (REPRODUCED) |
| `b2_dependency` | `REPRODUCED` | 1/1 (REPRODUCED) |
| `b3_silent_config` | `REPRODUCED` | 1/1 (REPRODUCED) |
| `b4_combined` | `REPRODUCED` | 0/1 (NUMBER_MISMATCH) |
| `b5_unable` | `UNABLE_TO_EXECUTE` | 1/1 (UNABLE_TO_EXECUTE) |

## Total Success Counts

- **B-2**: 4/5 runs matched gold (80.0%)

## Detailed Per-Run Log

| Case | System | Run | Final Status | Matches Gold | Patches | Retries | Time (s) |
|---|---|---|---|---|---|---|---|
| `b1_control` | B-2 | 1 | `REPRODUCED` | True | 0 | 0 | 2.16 |
| `b2_dependency` | B-2 | 1 | `REPRODUCED` | True | 1 | 1 | 3.96 |
| `b3_silent_config` | B-2 | 1 | `REPRODUCED` | True | 1 | 1 | 2.5 |
| `b4_combined` | B-2 | 1 | `NUMBER_MISMATCH` | False | 1 | 1 | 3.82 |
| `b5_unable` | B-2 | 1 | `UNABLE_TO_EXECUTE` | True | 0 | 0 | 0.01 |
