# STAGE 1 — REAL DOCKER EXECUTION PROOF

This document contains the verified execution proof for the Stage 1 Gate.
All 5 benchmark cases were executed in real Docker containers (`DockerSandbox`) using `rerun-base:py311`.

## Summary Table

| Case ID | Project ID | Final Status | Attempts | Patches Applied | Real Metric Observed |
|---|---|---|---|---|---|
| `b1_control` | `proj_7e538120` | **REPRODUCED** | 1 | 0 | `0.9555555555555555` |
| `b2_dependency` | `proj_9ae9a023` | **REPRODUCED** | 2 | 1 | `0.9555555555555555` |
| `b3_silent_config` | `proj_59a11c5d` | **REPRODUCED** | 2 | 1 | `0.9555555555555555` |
| `b4_combined` | `proj_182de526` | **REPRODUCED** | 3 | 2 | `0.9555555555555555` |
| `b5_unable` | `proj_62b2c6f5` | **UNABLE_TO_EXECUTE** | 0 | 0 | `N/A` |

---

## Case: `b1_control` (`proj_7e538120`)
- **Final Status**: `REPRODUCED`
- **Attempts**: 1
- **Patches Proposed**: 0

### Attempt 1
- Exit code: `0`
- Error class: `None`
- Metrics: `{'test_accuracy_mean': 0.9555555555555555, 'test_accuracy_std': 0.0017568209223157952}`
```text
# data/runs/proj_7e538120/logs/run_1.log
Seed 0: accuracy 0.9556
Seed 1: accuracy 0.9583
Seed 2: accuracy 0.9556
Seed 3: accuracy 0.9556
Seed 4: accuracy 0.9528
test_accuracy_mean=0.9556
```

---

## Case: `b2_dependency` (`proj_9ae9a023`)
- **Final Status**: `REPRODUCED`
- **Attempts**: 2
- **Patches Proposed**: 1

### Attempt 1
- Exit code: `1`
- Error class: `dependency_missing`
- Metrics: `None`
```text
# data/runs/proj_9ae9a023/logs/run_1.log
Traceback (most recent call last):
  File "/workspace/train.py", line 4, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
```

### Attempt 2
- Exit code: `0`
- Error class: `None`
- Metrics: `{'test_accuracy_mean': 0.9555555555555555, 'test_accuracy_std': 0.0017568209223157952}`
```text
# data/runs/proj_9ae9a023/logs/run_2.log
Seed 0: accuracy 0.9556
Seed 1: accuracy 0.9583
Seed 2: accuracy 0.9556
Seed 3: accuracy 0.9556
Seed 4: accuracy 0.9528
test_accuracy_mean=0.9556
```

### Patch `P-1` (dependency) — Status: `applied`
- Rationale: ModuleNotFoundError: No module named 'yaml' requires PyYAML==6.0.1
```diff
--- a/requirements.txt
+++ b/requirements.txt
@@ -1,2 +1,3 @@
 numpy==1.26.4
 
+PyYAML==6.0.1
```

---

## Case: `b3_silent_config` (`proj_59a11c5d`)
- **Final Status**: `REPRODUCED`
- **Attempts**: 2
- **Patches Proposed**: 1

### Attempt 1
- Exit code: `0`
- Error class: `None`
- Metrics: `{'test_accuracy_mean': 0.8733333333333334, 'test_accuracy_std': 0.0013608276348795385}`
```text
# data/runs/proj_59a11c5d/logs/run_1.log
Seed 0: accuracy 0.8750
Seed 1: accuracy 0.8722
Seed 2: accuracy 0.8722
Seed 3: accuracy 0.8722
Seed 4: accuracy 0.8750
test_accuracy_mean=0.8733
```

### Attempt 2
- Exit code: `0`
- Error class: `None`
- Metrics: `{'test_accuracy_mean': 0.9555555555555555, 'test_accuracy_std': 0.0017568209223157952}`
```text
# data/runs/proj_59a11c5d/logs/run_2.log
Seed 0: accuracy 0.9556
Seed 1: accuracy 0.9583
Seed 2: accuracy 0.9556
Seed 3: accuracy 0.9556
Seed 4: accuracy 0.9528
test_accuracy_mean=0.9556
```

### Patch `P-1` (config_value) — Status: `applied`
- Rationale: Paper specifies lr=0.5 but config uses 0.01
```diff
--- a/configs/default.yaml
+++ b/configs/default.yaml
@@ -1,4 +1,4 @@
-learning_rate: 0.01
+learning_rate: 0.5
 epochs: 20
 batch_size: 32
 l2: 0.0
```

---

## Case: `b4_combined` (`proj_182de526`)
- **Final Status**: `REPRODUCED`
- **Attempts**: 3
- **Patches Proposed**: 2

### Attempt 1
- Exit code: `1`
- Error class: `dependency_missing`
- Metrics: `None`
```text
# data/runs/proj_182de526/logs/run_1.log
Traceback (most recent call last):
  File "/workspace/train.py", line 4, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
```

### Attempt 2
- Exit code: `0`
- Error class: `None`
- Metrics: `{'test_accuracy_mean': 0.8733333333333334, 'test_accuracy_std': 0.0013608276348795385}`
```text
# data/runs/proj_182de526/logs/run_2.log
Seed 0: accuracy 0.8750
Seed 1: accuracy 0.8722
Seed 2: accuracy 0.8722
Seed 3: accuracy 0.8722
Seed 4: accuracy 0.8750
test_accuracy_mean=0.8733
```

### Attempt 3
- Exit code: `0`
- Error class: `None`
- Metrics: `{'test_accuracy_mean': 0.9555555555555555, 'test_accuracy_std': 0.0017568209223157952}`
```text
# data/runs/proj_182de526/logs/run_3.log
Seed 0: accuracy 0.9556
Seed 1: accuracy 0.9583
Seed 2: accuracy 0.9556
Seed 3: accuracy 0.9556
Seed 4: accuracy 0.9528
test_accuracy_mean=0.9556
```

### Patch `P-1` (dependency) — Status: `applied`
- Rationale: Missing yaml module
```diff
--- a/requirements.txt
+++ b/requirements.txt
@@ -1,2 +1,3 @@
 numpy==1.26.4
 
+PyYAML==6.0.1
```

### Patch `P-2` (config_value) — Status: `applied`
- Rationale: Paper specifies lr=0.5 but config uses 0.01
```diff
--- a/configs/default.yaml
+++ b/configs/default.yaml
@@ -1,4 +1,4 @@
-learning_rate: 0.01
+learning_rate: 0.5
 epochs: 20
 batch_size: 32
 l2: 0.0
```

---

## Case: `b5_unable` (`proj_62b2c6f5`)
- **Final Status**: `UNABLE_TO_EXECUTE`
- **Attempts**: 0
- **Patches Proposed**: 0

---
