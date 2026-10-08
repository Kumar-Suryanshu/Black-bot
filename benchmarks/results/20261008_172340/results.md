# Track A Benchmark Evaluation Results

**Timestamp:** 2026-10-08 17:24:12 UTC
**Sandbox:** Docker (`DockerSandbox`, image: `rerun-base:py311`, offline network)
**Repeats:** 1 per condition

## Summary Table (Counts Only)

| Case | Gold Expected | Rerun |
|---|---|---|
| `b1_control` | `REPRODUCED` | 1/1 (REPRODUCED) |
| `b2_dependency` | `REPRODUCED` | 1/1 (REPRODUCED) |
| `b3_silent_config` | `REPRODUCED` | 1/1 (REPRODUCED) |
| `b4_combined` | `REPRODUCED` | 1/1 (REPRODUCED) |
| `b5_unable` | `UNABLE_TO_EXECUTE` | 1/1 (UNABLE_TO_EXECUTE) |

## Total Success Counts

- **Rerun**: 5/5 runs matched gold (100.0%)

## Detailed Per-Run Log

| Case | System | Run | Final Status | Matches Gold | Patches | Retries | Time (s) |
|---|---|---|---|---|---|---|---|
| `b1_control` | Rerun | 1 | `REPRODUCED` | True | 0 | 0 | 5.77 |
| `b2_dependency` | Rerun | 1 | `REPRODUCED` | True | 1 | 1 | 7.46 |
| `b3_silent_config` | Rerun | 1 | `REPRODUCED` | True | 1 | 1 | 6.53 |
| `b4_combined` | Rerun | 1 | `REPRODUCED` | True | 2 | 2 | 8.44 |
| `b5_unable` | Rerun | 1 | `UNABLE_TO_EXECUTE` | True | 0 | 0 | 3.6 |
